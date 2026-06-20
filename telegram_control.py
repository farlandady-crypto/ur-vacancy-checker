import os
import json
import requests
import subprocess

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"
CONFIG_FILE = "config.json"
OFFSET_FILE = "offset.json"


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30
    )


def load_json(path, default):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default


def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def get_updates(offset):
    r = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
        params={"offset": offset},
        timeout=30
    )
    return r.json()["result"]


offset = load_json(OFFSET_FILE, {}).get("offset", 0)
config = load_json(CONFIG_FILE, {"interval": 5, "paused": False})
state = load_json(STATE_FILE, {})

for u in get_updates(offset):

    offset = u["update_id"] + 1

    if "message" not in u:
        continue

    text = u["message"].get("text", "")
    chat_id = str(u["message"]["chat"]["id"])

    if chat_id != str(CHAT_ID):
        continue

    # ---------------- /status ----------------
    if text == "/status":
        stats = state.get("stats", {})
        send(f"""🟢 状态

interval: {config['interval']} min
paused: {config['paused']}
new: {stats.get('new',0)}
changed: {stats.get('changed',0)}
fail: {stats.get('fail',0)}
""")

    # ---------------- /pause ----------------
    elif text == "/pause":
        config["paused"] = True
        save_json(CONFIG_FILE, config)
        send("⛔ 已暂停监控")

    # ---------------- /resume ----------------
    elif text == "/resume":
        config["paused"] = False
        save_json(CONFIG_FILE, config)
        send("🟢 已恢复监控")

    # ---------------- /set interval ----------------
    elif text.startswith("/set"):
        try:
            _, _, val = text.split()
            config["interval"] = int(val)
            save_json(CONFIG_FILE, config)
            send(f"⚙️ interval 已设置为 {val} 分钟")
        except:
            send("用法：/set interval 5")

    # ---------------- /test ----------------
    elif text == "/test":
        send("🧪 手动触发检测")
        subprocess.run(["python", "main.py"])

save_json(OFFSET_FILE, {"offset": offset})
save_json(CONFIG_FILE, config)
