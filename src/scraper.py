import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过解析物件详情页HTML来获取空房列表
    """
    url = target['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 寻找空房表格。根据之前提供的HTML结构，空房信息在 <table class="vacant-room"> 或类似表格中
        # 这里提供一个更通用的查找方式：寻找包含"間取図"、"部屋名"等关键词的表格
        room_table = None
        tables = soup.find_all('table')
        for table in tables:
            if '間取図' in table.text or '部屋名' in table.text or '家賃' in table.text:
                room_table = table
                break
        
        if not room_table:
            return [], "未找到空房表格，可能目前没有空房或页面结构已变化"
        
        rooms = []
        rows = room_table.find_all('tr')
        for row in rows[1:]:  # 跳过表头
            cols = row.find_all('td')
            if len(cols) < 5:
                continue
            
            # 提取房间信息，需要根据实际页面结构调整
            room = {
                'id': None,  # 从链接中提取
                'name': cols[1].get_text(strip=True) if len(cols) > 1 else '未知房号',
                'rent': cols[2].get_text(strip=True) if len(cols) > 2 else '不明',
                'common_fee': '不明',
                'type': cols[3].get_text(strip=True) if len(cols) > 3 else '不明',
                'floor_space': cols[4].get_text(strip=True) if len(cols) > 4 else '不明',
                'floor': '不明',
                'status': '常规募集',
                'url': '',
                'shikikin': '不明',
                'requirement': '不明'
            }
            
            # 尝试从房名或链接中提取ID
            link = row.find('a')
            if link and link.get('href'):
                room['url'] = link['href']
                # 尝试从URL中提取ID，如 .../40_3290_room.html?...
                id_match = re.search(r'/(\d+)_room\.html', link['href'])
                if id_match:
                    room['id'] = id_match.group(1)
            else:
                # 如果没有链接，生成一个临时ID
                room['id'] = f"{target['params']['danchi']}_{room['name']}"
            
            # 清理租金字段，提取数字
            rent_text = room['rent']
            rent_match = re.search(r'([\d,]+)円', rent_text)
            if rent_match:
                room['rent'] = rent_match.group(1) + '円'
            
            # 清理面积字段
            if '&#13217;' in room['floor_space']:
                room['floor_space'] = room['floor_space'].replace('&#13217;', '㎡')
            
            rooms.append(room)
        
        return rooms, f"发现 {len(rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except Exception as e:
        return [], f"解析失败: {str(e)}"

def format_room_info(room: Dict) -> Dict:
    """格式化房间信息（保持不变）"""
    return room

def check_all_targets() -> Dict:
    """检查所有目标物件"""
    results = {}
    total_new_rooms = []
    
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
        
        total_new_rooms.extend(formatted_rooms)
    
    return results
