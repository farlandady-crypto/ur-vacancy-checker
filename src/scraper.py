import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import re
from .config import HEADERS, UR_TARGETS

def fetch_rooms(target: Dict) -> Tuple[List[Dict], str]:
    """
    完全模拟浏览器POST请求获取空房数据
    """
    api_url = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"
    
    # 【关键修正】使用正确的danchi值（去掉末尾0）
    danchi_value = target['params']['danchi']
    if danchi_value.endswith('0'):
        danchi_value = danchi_value[:-1]
    
    # 构建请求参数
    params = {
        'block': target['params']['block'],
        'tdfk': target['params']['tdfk'],
        'shisya': target['params']['shisya'],
        'danchi': danchi_value,
        'pageIndex': '0',
        'shikibetu': '0'
    }
    
    # 【关键】完全复制浏览器的请求头
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',  # 明确告诉服务器发送的是JSON
        'Origin': 'https://www.ur-net.go.jp',
        'Referer': target['url'],
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    print(f"   📡 请求API (POST): {api_url}")
    print(f"   📦 参数: {params}")
    
    try:
        session = requests.Session()
        
        # 【重要】先访问主页面获取必要的Cookie
        print("   🔄 先访问主页面获取会话...")
        main_response = session.get(target['url'], headers=HEADERS, timeout=10)
        print(f"   📊 主页面状态码: {main_response.status_code}")
        
        # 发送POST请求，参数以JSON格式放在请求体中
        print("   📡 发送POST请求 (JSON body)...")
        response = session.post(
            api_url, 
            headers=headers, 
            json=params,  # 使用json参数，会自动设置正确的Content-Type
            timeout=15
        )
        
        print(f"   📊 POST状态码: {response.status_code}")
        print(f"   📊 响应长度: {len(response.text)} 字符")
        
        if response.status_code != 200:
            return [], f"API请求失败，状态码: {response.status_code}"
        
        # 检查响应是否为空
        if not response.text or response.text.strip() == 'null':
            print("   ⚠️ API返回null，尝试使用form-data方式...")
            # 备用方案：使用form-data格式
            response = session.post(
                api_url,
                headers=headers,
                data=params,  # 使用data参数，发送form-data
                timeout=15
            )
            print(f"   📊 POST (form-data) 状态码: {response.status_code}")
            print(f"   📊 响应长度: {len(response.text)} 字符")
        
        if response.status_code != 200:
            return [], f"备用请求也失败，状态码: {response.status_code}"
        
        # 打印响应的前200个字符用于调试
        print(f"   📄 响应预览: {response.text[:200]}...")
        
        # 解析JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            return [], f"JSON解析失败: {response.text[:200]}"
        
        # 如果数据是None或空
        if not data:
            return [], "API返回空数据"
        
        # 处理响应数据
        rooms_data = []
        if isinstance(data, list):
            rooms_data = data
            print(f"   ✅ 直接获得数组，包含 {len(rooms_data)} 项")
        elif isinstance(data, dict):
            # 尝试多种可能的字段名
            found = False
            for key in ['room', 'rooms', 'data', 'result', 'list', 'items', 'detail']:
                if key in data and data[key]:
                    rooms_data = data[key]
                    print(f"   ✅ 从 '{key}' 字段提取数据，包含 {len(rooms_data)} 项")
                    found = True
                    break
            if not found:
                # 如果data本身包含房间信息
                if 'id' in data or 'name' in data or 'rent' in data:
                    rooms_data = [data]
                    print("   ✅ data本身包含房间信息")
                    found = True
            if not found:
                print(f"   ⚠️ 未能找到房间数据，响应键: {list(data.keys())}")
                return [], f"响应中未找到房间数据，可用键: {list(data.keys())}"
        else:
            return [], f"未知数据类型: {type(data)}"
        
        if not rooms_data:
            return [], "解析后房间列表为空"
        
        # 格式化房间信息
        formatted_rooms = []
        for room in rooms_data:
            # 尝试多种可能的ID字段
            room_id = room.get('id') or room.get('roomId') or room.get('number')
            if not room_id:
                link = room.get('roomDetailLink', '')
                id_match = re.search(r'JKSS=(\d+)', link)
                if id_match:
                    room_id = id_match.group(1)
                else:
                    room_id = f"{danchi_value}_{room.get('name', 'unknown')}"
            
            # 清理面积单位
            floorspace = room.get('floorspace', '')
            if '&#13217;' in floorspace:
                floorspace = floorspace.replace('&#13217;', '㎡')
            
            formatted_room = {
                'id': str(room_id),
                'name': room.get('name', '未知房号'),
                'rent': room.get('rent', '不明'),
                'common_fee': room.get('commonfee', '不明'),
                'type': room.get('type', '不明'),
                'floor_space': floorspace,
                'floor': room.get('floor', '不明'),
                'status': room.get('status', '常规募集'),
                'url': room.get('roomDetailLink', ''),
                'shikikin': room.get('shikikin', '不明'),
                'requirement': room.get('requirement', '不明'),
                'madori': room.get('madori', '')
            }
            formatted_rooms.append(formatted_room)
            print(f"   ✅ 解析房间: {formatted_room['name']} - {formatted_room['rent']}")
        
        return formatted_rooms, f"成功发现 {len(formatted_rooms)} 套空房"
        
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
