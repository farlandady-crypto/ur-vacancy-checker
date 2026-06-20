import os
import json
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"

STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

TARGETS = {
    "かわさきテクノピア堀川町ハイツ": {"shisya": "40", "danchi": "248"},
    "川崎旭町ハイツ": {"shisya": "40", "danchi": "260"}
}

stats = {"new": 0, "changed": 0, "fail": 0}

print("MAIN STARTED")

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


config = load_json(CONFIG_FILE, {"interval": 5, "paused": False})
if config.get("paused"):
    exit(0)


def get_rooms(shisya, danchi):
    try:
        r = requests.post(API_URL, data={
            "shisya": shisya,
            "danchi": danchi,
            "shikibetu": "0",
            "pageIndex": "0"
        }, timeout=30)
        return r.json() or []
    except Exception as e:
        stats["fail"] += 1
        send(f"🔴 API失败\n{str(e)}")
        return []


old_state = load_json(STATE_FILE, {})
new_state = {}

for name, t in TARGETS.items():

    rooms = get_rooms(t["shisya"], t["danchi"])
    old_rooms = old_state.get(name, {})
    current = {}

    for r in rooms:
        rid = r["id"]

        info = {
            "name": r["name"],
            "rent": r["rent"],
            "type": r["type"],
            "floorspace": r["floorspace"],
            "floor": r["floor"]
        }

        current[rid] = info

        if rid not in old_rooms:
            stats["new"] += 1
            send(f"🏠 新房源\n{name}\n{info['name']}\n{info['rent']}")

        elif old_rooms[rid] != info:
            stats["changed"] += 1
            send(f"🔄 变化\n{name}\n{info['name']}\n{info['rent']}")

    new_state[name] = current

new_state["stats"] = stats
new_state["last_run"] = datetime.now().isoformat()

json.dump(new_state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
