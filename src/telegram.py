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
                for room in data['rooms'][:5]:  # 最多显示5套
                    lines.append(f"  • {room['name']} - {room['rent']} - {room['type']}")
                if data['count'] > 5:
                    lines.append(f"  ... 还有 {data['count'] - 5} 套")
    else:
        lines.append("✅ 目前没有空房")
    
    send_telegram_message("\n".join(lines))

def check_and_reply_commands():
    """检查并回复Telegram命令（防止重复发送）"""
    if not TELEGRAM_BOT_TOKEN:
        return
    
    # 添加一个标记，防止同一次运行重复处理
    if hasattr(check_and_reply_commands, '_processed'):
        return
    check_and_reply_commands._processed = True
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, params={'timeout': 10}, timeout=15)
        response.raise_for_status()
        updates = response.json()
        
        if not updates.get('ok'):
            return
        
        # 记录已处理的update_id，防止重复
        processed_ids = set()
        
        for update in updates.get('result', []):
            update_id = update.get('update_id')
            if update_id in processed_ids:
                continue
            processed_ids.add(update_id)
            
            message = update.get('message')
            if not message:
                continue
            
            text = message.get('text', '')
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            if chat_id != TELEGRAM_CHAT_ID:
                continue
            
            if text == '/status':
                send_status_report()
            elif text == '/help':
                send_help_message()
            elif text == '/check':
                send_telegram_message("⏳ 正在检查，请等待下一次定时任务（最多5分钟）")
                
    except Exception as e:
        print(f"⚠️ 处理Telegram命令失败: {e}")

def send_help_message():
    """发送帮助信息"""
    help_text = """
🤖 <b>UR空房监控机器人</b>

<b>可用命令:</b>
/status  - 查看当前空房状态
/check   - 手动触发检查（等待下次定时任务）
/help    - 显示此帮助信息

<b>监控信息:</b>
• 检查间隔: 每5分钟
• 监控物件: 2个UR物件
• 通知方式: 发现新空房时自动推送

📌 <i>注意: 命令响应可能有0-5分钟延迟</i>
    """
    send_telegram_message(help_text)
