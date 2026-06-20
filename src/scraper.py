import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
from .config import API_URL, HEADERS, UR_TARGETS

def fetch_rooms(danchi_params: Dict) -> Tuple[List[Dict], str]:
    """
    获取指定物件的空房列表
    返回: (房间列表, 状态信息)
    """
    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=danchi_params,
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        all_count = int(data.get('allCount', 0))
        
        if all_count == 0:
            return [], "暂无空房"
        
        rooms = data.get('room', [])
        return rooms, f"发现 {all_count} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except json.JSONDecodeError as e:
        return [], f"数据解析失败: {str(e)}"
    except Exception as e:
        return [], f"未知错误: {str(e)}"

def format_room_info(room: Dict) -> Dict:
    """格式化房间信息"""
    # 清理面积单位
    floorspace = room.get('floorspace', '')
    if '&#13217;' in floorspace:
        floorspace = floorspace.replace('&#13217;', '㎡')
    
    return {
        'id': room.get('id', ''),
        'name': room.get('name', '未知房号'),
        'rent': room.get('rent', '不明'),
        'common_fee': room.get('commonfee', '不明'),
        'type': room.get('type', '不明'),
        'floor_space': floorspace,
        'floor': room.get('floor', '不明'),
        'status': room.get('status', '常规募集'),
        'url': room.get('roomDetailLink', ''),
        'shikikin': room.get('shikikin', '不明'),
        'requirement': room.get('requirement', '不明')
    }

def check_all_targets() -> Dict:
    """检查所有目标物件"""
    results = {}
    total_new_rooms = []
    
    for target in UR_TARGETS:
        print(f"🔍 检查: {target['name']}")
        rooms, message = fetch_rooms(target['params'])
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
