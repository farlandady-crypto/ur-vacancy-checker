import os
import json
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.json"


def send(msg: str):
    """
    发送 Telegram 消息（带基础容错）
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] BOT_TOKEN or CHAT_ID missing")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=30
        )
    except Exception as e:
        print(f"[ERROR] send failed: {e}")


def load_state():
    """
    读取 state.json（不存在则返回默认结构）
    """
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def format_time(value):
    """
    统一时间展示
    """
    if not value:
        return "unknown"
    return str(value)


def main():
    state = load_state()

    stats = state.get("stats", {})
    last = state.get("last_run")

    now = datetime.utcnow().isoformat()

    msg = (
        "🟢 心跳\n"
        f"new: {stats.get('new', 0)}\n"
        f"changed: {stats.get('changed', 0)}\n"
        f"fail: {stats.get('fail', 0)}\n"
        f"last_run: {format_time(last)}\n"
        f"heartbeat: {now} UTC"
    )

    send(msg)


if __name__ == "__main__":
    main()
