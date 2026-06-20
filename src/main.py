#!/usr/bin/env python3
"""
UR空房监控主程序
运行在GitHub Actions上，每5分钟执行一次
"""
import sys
from datetime import datetime
from .config import validate_config
from .scraper import check_all_targets
from .storage import save_status, find_new_rooms, save_current_rooms, load_previous_rooms
from .telegram import send_vacancy_notification, check_and_reply_commands, send_status_report

def main():
    print(f"🚀 UR空房监控启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. 验证配置
    try:
        validate_config()
        print("✅ 配置验证通过")
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)
    
    # 2. 检查所有目标物件
    print("\n🔍 开始检查空房...")
    results = check_all_targets()
    
    # 3. 保存当前状态
    save_status(results)
    print("✅ 状态已保存")
    
    # 4. 检查是否有新空房
    new_rooms = find_new_rooms(results)
    
    # 5. 如果有新空房，发送通知
    if new_rooms:
        print(f"\n🎉 发现新空房! {sum(len(rooms) for rooms in new_rooms.values())} 套")
        send_vacancy_notification(new_rooms)
        
        # 更新已通知的房间ID
        current_ids = set()
        for data in results.values():
            for room in data['rooms']:
                current_ids.add(room['id'])
        save_current_rooms(current_ids)
    else:
        print("\n✅ 没有发现新空房")
    
    # 6. 处理Telegram命令
    print("\n📨 检查Telegram命令...")
    check_and_reply_commands()
    
    # 7. 打印汇总
    total = sum(data['count'] for data in results.values())
    print(f"\n📊 汇总: 共 {total} 套空房")
    for object_name, data in results.items():
        print(f"   {object_name}: {data['count']} 套")
    
    print("\n✅ 执行完成")

if __name__ == "__main__":
    main()
