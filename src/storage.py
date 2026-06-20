import json
import os
from typing import Dict, List, Set
from datetime import datetime
from pathlib import Path

# 使用绝对路径
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
STATUS_FILE = DATA_DIR / 'latest_status.json'
PREVIOUS_FILE = DATA_DIR / 'previous_rooms.json'

def ensure_data_dir():
    """确保数据目录存在"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        print(f"📁 数据目录已确认: {DATA_DIR}")
        return True
    except Exception as e:
        print(f"❌ 创建数据目录失败: {e}")
        return False

def load_previous_rooms() -> Set[str]:
    """加载上次检查的房间ID集合"""
    ensure_data_dir()
    if not PREVIOUS_FILE.exists():
        print(f"📄 没有之前的记录文件: {PREVIOUS_FILE}")
        return set()
    
    try:
        with open(PREVIOUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            room_ids = set(data.get('room_ids', []))
            print(f"📖 加载了 {len(room_ids)} 个之前的房间ID")
            return room_ids
    except Exception as e:
        print(f"⚠️ 读取之前记录失败: {e}")
        return set()

def save_current_rooms(room_ids: Set[str]):
    """保存当前房间ID"""
    if not ensure_data_dir():
        return
    
    try:
        with open(PREVIOUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'room_ids': list(room_ids), 
                'updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存 {len(room_ids)} 个房间ID到: {PREVIOUS_FILE}")
    except Exception as e:
        print(f"❌ 保存房间ID失败: {e}")

def save_status(results: Dict):
    """保存当前状态"""
    if not ensure_data_dir():
        return
    
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'updated': datetime.now().isoformat(),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 状态已保存到: {STATUS_FILE}")
    except Exception as e:
        print(f"❌ 保存状态失败: {e}")

def load_status() -> Dict:
    """加载最新状态"""
    ensure_data_dir()
    if not STATUS_FILE.exists():
        print(f"📄 没有状态文件: {STATUS_FILE}")
        return {}
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📖 状态加载成功，更新时间: {data.get('updated', '未知')}")
            return data
    except Exception as e:
        print(f"⚠️ 读取状态失败: {e}")
        return {}

def find_new_rooms(current_results: Dict) -> Dict[str, List[Dict]]:
    """找出新出现的空房"""
    previous_ids = load_previous_rooms()
    print(f"🔍 对比之前的 {len(previous_ids)} 个房间ID")
    
    new_rooms_by_object = {}
    
    for object_name, data in current_results.items():
        new_rooms = []
        for room in data['rooms']:
            if room['id'] not in previous_ids:
                new_rooms.append(room)
                print(f"  🆕 新房间: {room['name']} (ID: {room['id']})")
        if new_rooms:
            new_rooms_by_object[object_name] = new_rooms
    
    return new_rooms_by_object
