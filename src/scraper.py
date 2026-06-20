import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过正则表达式从HTML中提取空房列表，更稳定地应对结构变化
    """
    url = target['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取页面的文本内容，并清理多余空白
        page_text = soup.get_text(separator=' ', strip=True)
        
        # 查找空房信息区域 - 通常包含"空室情報"或"空室"关键词
        vacancy_area = None
        # 尝试在HTML中查找包含空房列表的父级元素
        possible_sections = soup.find_all(['div', 'section', 'table'], 
                                          string=re.compile(r'空室情報|間取図|部屋名|家賃', re.IGNORECASE))
        
        if possible_sections:
            # 使用找到的第一个包含关键词的父元素
            vacancy_area = possible_sections[0]
            # 如果父元素是table，直接使用；否则在其内部查找table
            if vacancy_area.name != 'table':
                table_in_area = vacancy_area.find('table')
                if table_in_area:
                    vacancy_area = table_in_area
        else:
            # 如果没找到特定区域，尝试直接找所有表格
            tables = soup.find_all('table')
            for table in tables:
                if re.search(r'間取図|部屋名|家賃|床面積|階数', table.get_text()):
                    vacancy_area = table
                    break
        
        rooms = []
        # 如果找到了包含空房信息的表格，尝试解析它
        if vacancy_area and vacancy_area.name == 'table':
            rooms = parse_room_table(vacancy_area, target)
        
        # 如果表格解析结果为空，或者没找到表格，使用正则表达式直接从文本中提取
        if not rooms:
            print("   ⚠️ 表格解析为空或未找到表格，尝试使用正则表达式提取...")
            rooms = extract_rooms_with_regex(page_text, target)
        
        if not rooms:
            # 最后检查：页面是否明确提示没有空房
            if re.search(r'ご案内できるお部屋がございません|ただいま空室はございません', page_text):
                return [], "页面显示：目前没有可立即入住的空房"
            
            # 调试信息
            title = soup.find('title')
            title_text = title.get_text() if title else "未知"
            print(f"   🔍 页面标题: {title_text}")
            # 打印部分文本用于调试
            text_sample = page_text[:500].replace('\n', ' ')
            print(f"   📄 页面文本预览: {text_sample}...")
            return [], f"未找到空房信息。页面标题: {title_text}"
        
        return rooms, f"发现 {len(rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except Exception as e:
        return [], f"解析失败: {str(e)}"

def parse_room_table(table_element, target: Dict) -> List[Dict]:
    """尝试解析表格元素"""
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
        if '部屋名' in h or 'room' in h.lower():
            col_idx['name'] = i
        elif '家賃' in h or '賃料' in h:
            col_idx['rent'] = i
        elif '間取' in h:
            col_idx['type'] = i
        elif '床面積' in h or '面積' in h:
            col_idx['space'] = i
        elif '階数' in h or '階' in h:
            col_idx['floor'] = i
    
    # 如果找不到表头，使用常见顺序 [图, 房名, 家賃, 間取, 面積, 階数]
    if col_idx['name'] == -1:
        col_idx = {'name': 1, 'rent': 2, 'type': 3, 'space': 4, 'floor': 5}
    
    # 遍历数据行
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue
        
        name = cells[col_idx['name']].get_text(strip=True) if col_idx['name'] < len(cells) else ''
        # 通过房名判断是否为有效数据行（避免解析到表头或其他无关行）
        if not name or name in ['間取図', '部屋名', ''] or not re.search(r'\d', name):
            continue
        
        # 提取租金和共益费
        rent_text = cells[col_idx['rent']].get_text(strip=True) if col_idx['rent'] < len(cells) else ''
        rent_match = re.search(r'([\d,]+)円', rent_text)
        rent = rent_match.group(1) + '円' if rent_match else rent_text
        
        fee_match = re.search(r'\(([\d,]+)円\)', rent_text)
        common_fee = fee_match.group(1) + '円' if fee_match else '不明'
        
        # 提取其他信息
        room_type = cells[col_idx['type']].get_text(strip=True) if col_idx['type'] < len(cells) else ''
        floor_space = cells[col_idx['space']].get_text(strip=True) if col_idx['space'] < len(cells) else ''
        floor = cells[col_idx['floor']].get_text(strip=True) if col_idx['floor'] < len(cells) else ''
        
        # 获取房间链接
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
    """使用正则表达式从文本中提取房间信息"""
    rooms = []
    # 匹配模式：房号 | 租金(共益费) | 户型 | 面积 | 楼层
    # 示例: "1601号室 | 202,000円 (17,600円) | 1K | 33㎡ | 16階／22階"
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
    
    if rooms:
        print(f"   ✅ 通过正则表达式成功提取 {len(rooms)} 套空房")
    
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
