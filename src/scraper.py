import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS, API_URL

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过正确的API获取空房数据
    """
    # 构建API请求参数
    params = target['params'].copy()
    params['pageIndex'] = '0'
    params['shikibetu'] = '0'
    
    print(f"   📡 请求API: {API_URL}")
    print(f"   📦 参数: {params}")
    
    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=15
        )
        
        print(f"   📊 状态码: {response.status_code}")
        
        if response.status_code != 200:
            return [], f"API返回状态码: {response.status_code}"
        
        # 检查返回内容是否为JSON
        if not response.text.strip().startswith('[') and not response.text.strip().startswith('{'):
            print(f"   ⚠️ API返回非JSON数据，前200字符: {response.text[:200]}")
            return [], "API返回格式错误（非JSON）"
        
        # 解析JSON（注意：API返回的是一个数组）
        data = response.json()
        
        # 如果返回的是数组，直接使用
        if isinstance(data, list):
            rooms_data = data
        # 如果返回的是对象，尝试提取room字段
        elif isinstance(data, dict):
            rooms_data = data.get('room', [])
            if not rooms_data:
                # 可能是其他格式，尝试直接使用
                rooms_data = [data] if data else []
        else:
            return [], f"未知的数据格式: {type(data)}"
        
        if not rooms_data:
            return [], "暂无空房"
        
        # 格式化房间信息
        formatted_rooms = []
        for room in rooms_data:
            # 提取房间ID
            room_id = room.get('id', '')
            if not room_id:
                link = room.get('roomDetailLink', '')
                id_match = re.search(r'JKSS=(\d+)', link)
                if id_match:
                    room_id = id_match.group(1)
                else:
                    room_id = f"{target['params']['danchi']}_{room.get('name', 'unknown')}"
            
            # 清理面积单位
            floorspace = room.get('floorspace', '')
            if '&#13217;' in floorspace:
                floorspace = floorspace.replace('&#13217;', '㎡')
            
            # 提取租金
            rent = room.get('rent', '不明')
            common_fee = room.get('commonfee', '不明')
            
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
                'requirement': room.get('requirement', '不明'),
                'madori': room.get('madori', '')  # 户型图URL
            }
            formatted_rooms.append(formatted_room)
        
        return formatted_rooms, f"发现 {len(formatted_rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求失败: {str(e)}"
    except json.JSONDecodeError as e:
        return [], f"JSON解析失败: {str(e)}"
    except Exception as e:
        return [], f"未知错误: {str(e)}"

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
