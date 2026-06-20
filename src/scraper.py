import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    通过POST请求获取空房数据
    """
    api_url = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"
    
    params = {
        'block': target['params']['block'],
        'tdfk': target['params']['tdfk'],
        'shisya': target['params']['shisya'],
        'danchi': target['params']['danchi'],
        'pageIndex': '0',
        'shikibetu': '0'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
        'Referer': target['url'],
        'Origin': 'https://www.ur-net.go.jp',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }
    
    print(f"   📡 请求API: {api_url}")
    print(f"   📦 参数: {params}")
    
    try:
        session = requests.Session()
        
        # 先访问主页面获取Cookie
        print("   🔄 先访问主页面获取会话...")
        main_response = session.get(target['url'], headers=HEADERS, timeout=10)
        print(f"   📊 主页面状态码: {main_response.status_code}")
        
        # POST请求
        print("   📡 发送POST请求...")
        response = session.post(api_url, headers=headers, json=params, timeout=15)
        print(f"   📊 POST状态码: {response.status_code}")
        
        if response.status_code != 200:
            return [], f"API请求失败，状态码: {response.status_code}"
        
        # 【调试】打印原始响应
        print(f"   📄 响应内容（前500字符）: {response.text[:500]}")
        
        # 解析JSON
        try:
            data = response.json()
            print(f"   📊 数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"   📊 数据键: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"   📊 数据长度: {len(data)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            return [], f"JSON解析失败: {response.text[:200]}"
        
        # 处理响应数据（根据实际格式调整）
        rooms_data = []
        if isinstance(data, list):
            rooms_data = data
        elif isinstance(data, dict):
            # 尝试常见的字段名
            for key in ['room', 'rooms', 'data', 'result', 'list', 'items']:
                if key in data and data[key]:
                    rooms_data = data[key]
                    print(f"   ✅ 从 '{key}' 字段提取数据")
                    break
            if not rooms_data:
                # 如果data本身包含房间信息
                if 'id' in data or 'name' in data:
                    rooms_data = [data]
                    print("   ✅ data本身包含房间信息")
                else:
                    print(f"   ⚠️ 未能从data中找到房间数据，data包含: {list(data.keys())}")
                    return [], f"未找到房间数据，响应键: {list(data.keys())}"
        else:
            return [], f"未知数据类型: {type(data)}"
        
        if not rooms_data:
            return [], "暂无空房"
        
        # 格式化房间信息
        formatted_rooms = []
        for room in rooms_data:
            formatted_room = {
                'id': room.get('id', ''),
                'name': room.get('name', '未知房号'),
                'rent': room.get('rent', '不明'),
                'common_fee': room.get('commonfee', '不明'),
                'type': room.get('type', '不明'),
                'floor_space': room.get('floorspace', '').replace('&#13217;', '㎡'),
                'floor': room.get('floor', '不明'),
                'status': room.get('status', '常规募集'),
                'url': room.get('roomDetailLink', ''),
                'shikikin': room.get('shikikin', '不明'),
                'requirement': room.get('requirement', '不明'),
                'madori': room.get('madori', '')
            }
            formatted_rooms.append(formatted_room)
        
        return formatted_rooms, f"发现 {len(formatted_rooms)} 套空房"
        
    except requests.exceptions.RequestException as e:
        return [], f"请求异常: {str(e)}"
    except Exception as e:
        return [], f"处理异常: {str(e)}"

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
