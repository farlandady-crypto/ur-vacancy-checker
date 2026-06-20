import os
import json
import requests
from datetime import datetime
from heartbeat import heartbeat

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"

STATE_FILE = "state.json"
OFFSET_FILE = "offset.json"
CONFIG_FILE = "config.json"

TARGETS = {
    "かわさきテクノピア堀川町ハイツ": {"shisya": "40", "danchi": "248"},
    "川崎旭町ハイツ": {"shisya": "40", "danchi": "260"}
}


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


def get_rooms(shisya, danchi):
    try:
        r = requests.post(API_URL, data={
            "shisya": shisya,
            "danchi": danchi,
            "shikibetu": "0",
            "pageIndex": "0"
        }, timeout=30)

        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])

    except Exception as e:
        return []


def run():

    print("🔥 DISPATCHER STARTED")

    config = load_json(CONFIG_FILE, {"paused": False})

    if config.get("paused"):
        print("⏸ paused")
        return

    old_state = load_json(STATE_FILE, {})
    offset = load_json(OFFSET_FILE, {})

    stats = {"new": 0, "changed": 0, "fail": 0}
    new_state = {}

    for name, t in TARGETS.items():

        rooms = get_rooms(t["shisya"], t["danchi"])
        old_rooms = old_state.get(name, {})
        current = {}

        print(f"🏠 {name} rooms={len(rooms)}")

        for r in rooms:

            rid = r.get("id")
            if not rid:
                continue

            info = {
                "name": r.get("name"),
                "rent": r.get("rent"),
                "type": r.get("type"),
                "floorspace": r.get("floorspace"),
                "floor": r.get("floor")
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

    save_json(STATE_FILE, new_state)

    heartbeat(stats)
