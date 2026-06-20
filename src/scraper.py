import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    模拟浏览器行为获取空房数据
    """
    # 使用正确的API地址
    api_url = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"
    
    # 构建请求参数（从您成功抓取的请求中复制）
    params = {
        'block': target['params']['block'],
        'tdfk': target['params']['tdfk'],
        'shisya': target['params']['shisya'],
        'danchi': target['params']['danchi'],
        'pageIndex': '0',
        'shikibetu': '0'
    }
    
    # 完整的请求头（模拟浏览器）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': target['url'],
        'Origin': 'https://www.ur-net.go.jp',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    print(f"   📡 请求API: {api_url}")
    print(f"   📦 参数: {params}")
    
    try:
        # 创建会话，保持Cookie
        session = requests.Session()
        
        # 先访问主页面获取Cookie（重要！）
        print("   🔄 先访问主页面获取会话...")
        main_response = session.get(target['url'], headers=HEADERS, timeout=10)
        print(f"   📊 主页面状态码: {main_response.status_code}")
        
        # 然后请求API
        print("   📡 请求API...")
        response = session.get(api_url, headers=headers, params=params, timeout=15)
        
        print(f"   📊 API状态码: {response.status_code}")
        
        if response.status_code != 200:
            # 如果GET失败，尝试POST
            print("   ⚠️ GET失败，尝试POST...")
            response = session.post(api_url, headers=headers, json=params, timeout=15)
            print(f"   📊 POST状态码: {response.status_code}")
        
        if response.status_code != 200:
            return [], f"API请求失败，状态码: {response.status_code}"
        
        # 检查返回内容
        if not response.text or not response.text.strip():
            return [], "API返回空内容"
        
        # 尝试解析JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            # 如果返回的不是JSON，可能是其他格式
            print(f"   ⚠️ 非JSON响应，前200字符: {response.text[:200]}")
            return [], "API返回非JSON数据"
        
        # 处理响应数据
        rooms_data = []
        if isinstance(data, list):
            rooms_data = data
        elif isinstance(data, dict):
            # 尝试多种可能的字段
            if 'room' in data:
                rooms_data = data['room']
            elif 'data' in data:
                rooms_data = data['data']
            elif 'result' in data:
                rooms_data = data['result']
            else:
                # 如果data本身包含房间信息，尝试直接使用
                if 'id' in data or 'name' in data:
                    rooms_data = [data]
                else:
                    return [], f"无法解析数据格式: {list(data.keys()) if isinstance(data, dict) else '未知'}"
        
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
