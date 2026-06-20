import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS, API_URL

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过API获取空房数据（方案3）
    """
    # 构建API请求参数
    params = target['params'].copy()
    params['pageIndex'] = '0'
    params['shikibetu'] = '0'
    
    # 构建完整的请求头（关键：必须带上Referer）
    api_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "Referer": target['url'],  # 关键：告诉服务器请求来自哪个页面
        "X-Requested-With": "XMLHttpRequest",  # 关键：模拟AJAX请求
        "Connection": "keep-alive",
    }
    
    try:
        print(f"   📡 请求API: {API_URL}")
        print(f"   📦 参数: {params}")
        
        response = requests.get(
            API_URL,
            headers=api_headers,
            params=params,
            timeout=15
        )
        
        print(f"   📊 状态码: {response.status_code}")
        
        # 如果返回的不是JSON，打印部分内容用于调试
        if not response.text.startswith('{'):
            print(f"   ⚠️ API返回非JSON数据，前200字符: {response.text[:200]}")
            return [], f"API返回格式错误（非JSON）"
        
        data = response.json()
        all_count = int(data.get('allCount', 0))
        
        if all_count == 0:
            return [], "暂无空房"
        
        rooms = data.get('room', [])
        if not rooms:
            return [], "API返回了空数组"
        
        # 格式化房间信息
        formatted_rooms = []
        for room in rooms:
            # 提取房间ID
            room_id = room.get('id', '')
            if not room_id:
                # 如果没有ID，尝试从链接提取
                link = room.get('roomDetailLink', '')
                id_match = re.search(r'/(\d+)_room\.html', link)
                if id_match:
                    room_id = id_match.group(1)
                else:
                    room_id = f"{target['params']['danchi']}_{room.get('name', 'unknown')}"
            
            # 清理面积单位
            floorspace = room.get('floorspace', '')
            if '&#13217;' in floorspace:
                floorspace = floorspace.replace('&#13217;', '㎡')
            
            # 提取租金数字
            rent = room.get('rent', '不明')
            common_fee = room.get('commonfee', '不明')
            
            # 如果租金包含共益费，尝试分离（有些API返回格式可能不同）
            if '(' in rent and ')' in rent:
                # 格式如 "114,100円 (4,400円)"
                rent_match = re.search(r'([\d,]+)円', rent)
                fee_match = re.search(r'\(([\d,]+)円\)', rent)
                if rent_match:
                    rent = rent_match.group(1) + '円'
                if fee_match:
                    common_fee = fee_match.group(1) + '円'
            
            formatted_room = {
                'id': room_id,
                'name': room.get('name', '未知房号'),
                'rent': rent,
                'common_fee': common_fee,
                'type': room.get('type', '不明'),
                'floor_space': floorspace,
                'floor': room.get('floor', '不明'),
                'status': room.get('status', '常规募集'),
                'url': room.get('roomDetailLink', ''),
                'shikikin': room.get('shikikin', '不明'),
                'requirement': room.get('requirement', '不明')
            }
            formatted_rooms.append(formatted_room)
        
        return formatted_rooms, f"发现 {len(formatted_rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except json.JSONDecodeError as e:
        return [], f"JSON解析失败: {str(e)}，返回内容: {response.text[:200] if 'response' in locals() else '无响应'}"
    except Exception as e:
        return [], f"未知错误: {str(e)}"

def parse_room_table(table_element, target: Dict) -> List[Dict]:
    """备用：从HTML表格解析（方案2的备用逻辑）"""
    # 这个函数保留但不使用，以防API完全失效
    return []

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
