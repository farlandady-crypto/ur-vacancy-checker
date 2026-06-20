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
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        chrome_path = os.environ.get('CHROME_PATH', '/usr/bin/chromium-browser')
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
        
        driver = webdriver.Chrome(options=options)
        print(f"   🌐 正在加载页面: {target['url']}")
        driver.get(target['url'])
        
        # 等待页面加载
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("   ✅ 页面加载完成")
        
        # 获取渲染后的HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 【关键修正】直接查找包含空房信息的表格
        # 从您提供的页面内容来看，空房在表格中，表头包含"間取図"、"部屋名"等
        table = None
        tables = soup.find_all('table')
        for t in tables:
            text = t.get_text()
            if '部屋名' in text and '家賃' in text:
                table = t
                break
        
        if not table:
            # 如果找不到表格，尝试用正则从页面文本提取
            page_text = soup.get_text(separator=' ', strip=True)
            rooms = extract_rooms_with_regex(page_text, target)
            if rooms:
                return rooms, f"通过正则表达式发现 {len(rooms)} 套空房"
            return [], "未找到空房表格，且无法通过正则提取"
        
        # 解析表格（修正版）
        rooms = parse_room_table_v2(table, target)
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

def parse_room_table_v2(table_element, target: Dict) -> List[Dict]:
    """修正版的表格解析函数"""
    rooms = []
    rows = table_element.find_all('tr')
    if len(rows) < 2:
        return rooms
    
    # 直接遍历所有行，查找包含"号室"的行
    for row in rows:
        row_text = row.get_text()
        # 检查是否是房间行（包含"号室"）
        if '号室' not in row_text:
            continue
        
        cells = row.find_all('td')
        if len(cells) < 5:
            continue
        
        # 提取房间名
        name = cells[1].get_text(strip=True) if len(cells) > 1 else ''
        if not name or '号室' not in name:
            # 尝试从其他列提取
            for cell in cells:
                text = cell.get_text(strip=True)
                if '号室' in text:
                    name = text
                    break
        
        if not name or '号室' not in name:
            continue
        
        # 提取租金
        rent_text = ''
        for cell in cells:
            text = cell.get_text(strip=True)
            if '円' in text and '号室' not in text:
                rent_text = text
                break
        
        rent_match = re.search(r'([\d,]+)円', rent_text)
        rent = rent_match.group(1) + '円' if rent_match else '不明'
        
        fee_match = re.search(r'\(([\d,]+)円\)', rent_text)
        common_fee = fee_match.group(1) + '円' if fee_match else '不明'
        
        # 提取户型、面积、楼层
        room_type = ''
        floor_space = ''
        floor = ''
        
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'K' in text or 'LDK' in text:
                room_type = text
            elif '㎡' in text:
                floor_space = text
            elif '階' in text and '号室' not in text:
                floor = text
        
        # 提取房间ID
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
        print(f"   ✅ 解析房间: {name} - {rent}")
    
    return rooms

def extract_rooms_with_regex(page_text: str, target: Dict) -> List[Dict]:
    """使用正则表达式提取房间信息"""
    rooms = []
    # 更灵活的正则模式
    pattern = r'(\d+号室)\s*[|｜]\s*([\d,]+)円\s*\(([\d,]+)円\)\s*[|｜]\s*([^\|｜]+)\s*[|｜]\s*([\d.]+)㎡\s*[|｜]\s*([^\|｜]+?)(?:階|階／)'
    
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
    match = re.search(r'JKSS=(\d+)', url)
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
