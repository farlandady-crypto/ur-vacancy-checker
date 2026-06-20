import re
from typing import List, Dict, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time

from .config import UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    使用Selenium获取动态加载的空房数据
    """
    driver = None
    try:
        # 配置Chrome选项
        options = Options()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 在GitHub Actions中使用chromium
        chrome_path = os.environ.get('CHROME_PATH', '/usr/bin/chromium-browser')
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
        
        # 创建驱动
        driver = webdriver.Chrome(options=options)
        print(f"   🌐 正在加载页面: {target['url']}")
        driver.get(target['url'])
        
        # 等待页面加载（最多15秒）
        wait = WebDriverWait(driver, 15)
        
        # 等待空房表格出现
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(., '部屋名') or contains(., '間取図')]")))
            print("   ✅ 空房表格已加载")
        except TimeoutException:
            # 检查是否真的没有空房
            page_text = driver.page_source
            if "ご案内できるお部屋がございません" in page_text:
                return [], "页面显示：目前没有可立即入住的空房"
            print("   ⚠️ 未找到空房表格，尝试继续...")
            time.sleep(3)
        
        # 获取渲染后的HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找空房表格
        table = None
        tables = soup.find_all('table')
        for t in tables:
            text = t.get_text()
            if '部屋名' in text or '間取図' in text or ('家賃' in text and '床面積' in text):
                table = t
                break
        
        if not table:
            # 如果没有表格，尝试用正则提取
            page_text = soup.get_text(separator=' ', strip=True)
            rooms = extract_rooms_with_regex(page_text, target)
            if rooms:
                return rooms, f"通过正则表达式发现 {len(rooms)} 套空房"
            return [], "未找到空房表格，且无法通过正则提取"
        
        # 解析表格
        rooms = parse_room_table(table, target)
        if rooms:
            return rooms, f"发现 {len(rooms)} 套空房"
        else:
            # 表格解析失败，尝试正则
            page_text = soup.get_text(separator=' ', strip=True)
            rooms = extract_rooms_with_regex(page_text, target)
            if rooms:
                return rooms, f"通过正则表达式发现 {len(rooms)} 套空房"
            return [], "表格解析失败，且正则提取也为空"
        
    except Exception as e:
        return [], f"Selenium抓取失败: {str(e)}"
    finally:
        if driver:
            driver.quit()

def parse_room_table(table_element, target: Dict) -> List[Dict]:
    """解析空房表格"""
    rooms = []
    rows = table_element.find_all('tr')
    if len(rows) < 2:
        return rooms
    
    # 获取表头
    header_row = rows[0]
    header_cells = header_row.find_all(['th', 'td'])
    headers = [cell.get_text(strip=True) for cell in header_cells]
    
    # 确定列索引
    col_idx = {'name': -1, 'rent': -1, 'type': -1, 'space': -1, 'floor': -1}
    for i, h in enumerate(headers):
        if '部屋名' in h:
            col_idx['name'] = i
        elif '家賃' in h or '賃料' in h:
            col_idx['rent'] = i
        elif '間取' in h:
            col_idx['type'] = i
        elif '床面積' in h or '面積' in h:
            col_idx['space'] = i
        elif '階数' in h or '階' in h:
            col_idx['floor'] = i
    
    # 如果找不到表头，使用默认顺序
    if col_idx['name'] == -1:
        col_idx = {'name': 1, 'rent': 2, 'type': 3, 'space': 4, 'floor': 5}
    
    # 遍历数据行
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue
        
        name = cells[col_idx['name']].get_text(strip=True) if col_idx['name'] < len(cells) else ''
        if not name or name in ['間取図', '部屋名', ''] or not re.search(r'\d', name):
            continue
        
        rent_text = cells[col_idx['rent']].get_text(strip=True) if col_idx['rent'] < len(cells) else ''
        rent_match = re.search(r'([\d,]+)円', rent_text)
        rent = rent_match.group(1) + '円' if rent_match else rent_text
        
        fee_match = re.search(r'\(([\d,]+)円\)', rent_text)
        common_fee = fee_match.group(1) + '円' if fee_match else '不明'
        
        room_type = cells[col_idx['type']].get_text(strip=True) if col_idx['type'] < len(cells) else ''
        floor_space = cells[col_idx['space']].get_text(strip=True) if col_idx['space'] < len(cells) else ''
        floor = cells[col_idx['floor']].get_text(strip=True) if col_idx['floor'] < len(cells) else ''
        
        link_tag = row.find('a')
        room_link = link_tag['href'] if link_tag and link_tag.get('href') else ''
        room_id = extract_room_id(room_link) or f"{target['params']['danchi']}_{name}"
        
        room = {
            'id': room_id,
            'name': name,
            'rent': rent,
            'common_fee': common_fee,
            'type': room_type,
            'floor_space': floor_space.replace('&#13217;', '㎡'),
            'floor': floor,
            'status': '常规募集',
            'url': room_link,
            'shikikin': '不明',
            'requirement': '不明'
        }
        rooms.append(room)
    
    return rooms

def extract_rooms_with_regex(page_text: str, target: Dict) -> List[Dict]:
    """使用正则表达式提取房间信息"""
    rooms = []
    pattern = r'(\d+号室)\s*[|｜]\s*([\d,]+)円\s*\(([\d,]+)円\)\s*[|｜]\s*([^\|｜]+)\s*[|｜]\s*([\d.]+)㎡?\s*[|｜]\s*([^\|｜]+?)(?:階|階／)'
    
    matches = re.findall(pattern, page_text)
    for match in matches:
        name, rent, fee, r_type, space, floor = match
        room_id = f"{target['params']['danchi']}_{name}"
        rooms.append({
            'id': room_id,
            'name': name.strip(),
            'rent': f"{rent}円",
            'common_fee': f"{fee}円",
            'type': r_type.strip(),
            'floor_space': f"{space}㎡",
            'floor': f"{floor}階",
            'status': '常规募集',
            'url': '',
            'shikikin': '不明',
            'requirement': '不明'
        })
    
    return rooms

def extract_room_id(url: str) -> str:
    """从URL中提取房间ID"""
    if not url:
        return None
    match = re.search(r'/(\d+)_room\.html', url)
    return match.group(1) if match else None

def format_room_info(room: Dict) -> Dict:
    """格式化房间信息"""
    return room

def check_all_targets() -> Dict:
    """检查所有目标物件"""
    results = {}
    
    for target in UR_TARGETS:
        print(f"🔍 检查: {target['name']}")
        rooms, message = fetch_rooms(target)
        print(f"   {message}")
        
        formatted_rooms = [format_room_info(room) for room in rooms]
        
        results[target['name']] = {
            'url': target['url'],
            'rooms': formatted_rooms,
            'count': len(formatted_rooms),
            'message': message,
            'check_time': datetime.now().isoformat()
        }
    
    return results
