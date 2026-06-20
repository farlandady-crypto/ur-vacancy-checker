import os
import json
import requests
import subprocess

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = str(os.environ["CHAT_ID"])

STATE_FILE = "state.json"
CONFIG_FILE = "config.json"
OFFSET_FILE = "offset.json"

print("send test")


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30
    )


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_updates(offset):
    r = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
        params={"offset": offset, "timeout": 20},
        timeout=30
    )
    return r.json().get("result", [])


# ---------------- 每次都读取最新状态（避免漂移） ----------------
offset = load_json(OFFSET_FILE, {}).get("offset", 0)

state = load_json(STATE_FILE, {})
config = load_json(CONFIG_FILE, {"interval": 5, "paused": False})


updates = get_updates(offset)

for u in updates:

    offset = u["update_id"] + 1

    if "message" not in u:
        continue

    text = u["message"].get("text", "")
    chat_id = str(u["message"]["chat"]["id"])

    if chat_id != CHAT_ID:
        continue

    # 🔄 每条命令都刷新 config（避免旧值）
    config = load_json(CONFIG_FILE, {"interval": 5, "paused": False})

    # ---------------- /status ----------------
    if text == "/status":
        state = load_json(STATE_FILE, {})
        stats = state.get("stats", {})

        send(
            f"🟢 状态\n\n"
            f"interval: {config.get('interval',5)} min\n"
            f"paused: {config.get('paused',False)}\n"
            f"new: {stats.get('new',0)}\n"
            f"changed: {stats.get('changed',0)}\n"
            f"fail: {stats.get('fail',0)}"
        )

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

    # ---------------- /set interval 5 ----------------
    elif text.startswith("/set"):
        try:
            parts = text.split()
            if len(parts) == 3 and parts[1] == "interval":
                val = int(parts[2])
                config["interval"] = val
                save_json(CONFIG_FILE, config)
                send(f"⚙️ interval 已设置为 {val} 分钟")
            else:
                send("用法：/set interval 5")
        except:
            send("用法：/set interval 5")

    # ---------------- /test（安全版）----------------
    elif text == "/test":
        send("🧪 已触发 monitor（GitHub Actions）")

        # ❗不再 subprocess.run（避免阻塞/冲突）
        requests.post(
            f"https://api.github.com/repos/{os.environ.get('GITHUB_REPOSITORY')}/dispatches",
            headers={
                "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github+json"
            },
            json={"event_type": "run-monitor"},
            timeout=30
        )


# ---------------- offset 每次写入（防重复）----------------
save_json(OFFSET_FILE, {"offset": offset})
save_json(CONFIG_FILE, config)
