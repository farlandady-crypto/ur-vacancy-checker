import requests
from typing import List, Dict
from datetime import datetime
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from .storage import load_status

def send_telegram_message(text: str, parse_mode: str = 'HTML'):
    """发送Telegram消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram配置不完整，跳过发送")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 发送Telegram消息失败: {e}")
        return False

def format_vacancy_notification(rooms_by_object: Dict[str, List[Dict]]) -> str:
    """格式化空房通知消息"""
    lines = ["🏠 <b>发现新空房！</b>", ""]
    
    for object_name, rooms in rooms_by_object.items():
        lines.append(f"📌 <b>{object_name}</b>")
        for room in rooms:
            lines.append(f"  🏢 {room['name']}")
            lines.append(f"  💰 家賃: {room['rent']} (共益費: {room['common_fee']})")
            lines.append(f"  📐 {room['type']} · {room['floor_space']} · {room['floor']}")
            if room['shikikin'] != '不明':
                lines.append(f"  💵 敷金: {room['shikikin']}")
            lines.append("")
        lines.append("")
    
    lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)

def send_vacancy_notification(rooms_by_object: Dict[str, List[Dict]]):
    """发送空房通知"""
    if not rooms_by_object:
        return
    
    message = format_vacancy_notification(rooms_by_object)
    send_telegram_message(message)

def send_status_report():
    """发送状态报告（响应 /status 命令）"""
    status = load_status()
    if not status:
        send_telegram_message("⚠️ 暂无状态数据，请等待下一次检查")
        return
    
    results = status.get('results', {})
    total_vacancies = sum(data['count'] for data in results.values())
    
    lines = ["📊 <b>实时状态报告</b>", ""]
    lines.append(f"🕐 最后更新: {status['updated']}")
    lines.append(f"🏠 监控物件: {len(results)}个")
    lines.append(f"📋 当前空房: {total_vacancies}套")
    lines.append("")
    
    if total_vacancies > 0:
        lines.append("<b>空房详情:</b>")
        for object_name, data in results.items():
            if data['count'] > 0:
                lines.append(f"\n📌 {object_name} ({data['count']}套)")
                for room in data['rooms'][:5]:
                    lines.append(f"  • {room['name']} - {room['rent']} - {room['type']}")
                if data['count'] > 5:
                    lines.append(f"  ... 还有 {data['count'] - 5} 套")
    else:
        lines.append("✅ 目前没有空房")
    
    send_telegram_message("\n".join(lines))

def check_and_reply_commands():
    """检查并回复Telegram命令（精简版，只处理 /status）"""
    if not TELEGRAM_BOT_TOKEN:
        return
    
    import os
    offset_file = "data/offset.txt"
    os.makedirs("data", exist_ok=True)
    
    last_update_id = 0
    try:
        with open(offset_file, 'r') as f:
            last_update_id = int(f.read().strip())
    except:
        pass
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        params = {'timeout': 10}
        if last_update_id > 0:
            params['offset'] = last_update_id + 1
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        updates = response.json()
        
        if not updates.get('ok') or not updates.get('result'):
            return
        
        commands_to_process = []
        max_update_id = last_update_id
        
        for update in updates.get('result', []):
            update_id = update.get('update_id')
            if update_id <= last_update_id:
                continue
            
            message = update.get('message')
            if not message:
                continue
            
            text = message.get('text', '')
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            if chat_id != TELEGRAM_CHAT_ID:
                continue
            
            # 只处理 /status 命令
            if text == '/status':
                commands_to_process.append((update_id, text))
                if update_id > max_update_id:
                    max_update_id = update_id
        
        if max_update_id > last_update_id:
            with open(offset_file, 'w') as f:
                f.write(str(max_update_id))
        
        for update_id, text in commands_to_process:
            send_status_report()
        
    except Exception as e:
        print(f"⚠️ 处理Telegram命令失败: {e}")
