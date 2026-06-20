import os
from typing import List, Dict

# Telegram配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 监控的物件列表
UR_TARGETS = [
    {
        "name": "かわさきテクノピア堀川町ハイツ",
        "url": "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_2480.html",
        "params": {
            "block": "kanto",
            "tdfk": "kanagawa",
            "shisya": "40",
            "danchi": "2480"
        }
    },
    {
        "name": "川崎旭町ハイツ",
        "url": "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_2600.html",
        "params": {
            "block": "kanto",
            "tdfk": "kanagawa",
            "shisya": "40",
            "danchi": "2600"
        }
    },
    {
        "name": "横浜ヴェールタワー",
        "url": "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_4270.html",
        "params": {
            "block": "kanto",
            "tdfk": "kanagawa",
            "shisya": "40",
            "danchi": "4270"
        }
    }
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
    "Referer": "https://www.ur-net.go.jp/",
    "X-Requested-With": "XMLHttpRequest",
}

# 正确的API端点
API_URL = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"

def validate_config():
    """验证必要的配置是否存在"""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        print(f"⚠️ 警告: 以下配置缺失，通知功能将不可用: {', '.join(missing)}")
    else:
        print("✅ Telegram配置完整")
