import json
import os
from typing import Dict, List, Set
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
STATUS_FILE = DATA_DIR / 'latest_status.json'
PREVIOUS_FILE = DATA_DIR / 'previous_rooms.json'

def ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(exist_ok=True)

def load_previous_rooms() -> Set[str]:
    """加载上次检查的房间ID集合"""
    ensure_data_dir()
    if not PREVIOUS_FILE.exists():
        return set()
    
    try:
        with open(PREVIOUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('room_ids', []))
    except:
        return set()

def save_current_rooms(room_ids: Set[str]):
    """保存当前房间ID"""
    ensure_data_dir()
    with open(PREVIOUS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'room_ids': list(room_ids), 'updated': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

def save_status(results: Dict):
    """保存当前状态"""
    ensure_data_dir()
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'updated': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

def load_status() -> Dict:
    """加载最新状态"""
    ensure_data_dir()
    if not STATUS_FILE.exists():
        return {}
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def find_new_rooms(current_results: Dict) -> Dict[str, List[Dict]]:
    """找出新出现的空房"""
    previous_ids = load_previous_rooms()
    new_rooms_by_object = {}
    
    for object_name, data in current_results.items():
        new_rooms = []
        for room in data['rooms']:
            if room['id'] not in previous_ids:
                new_rooms.append(room)
        if new_rooms:
            new_rooms_by_object[object_name] = new_rooms
    
    return new_rooms_by_object
