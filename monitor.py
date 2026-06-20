import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"
STATE_FILE = "state.json"

TARGETS = {
    "かわさきテクノピア堀川町ハイツ": {
        "shisya": "40",
        "danchi": "248"
    },
    "川崎旭町ハイツ": {
        "shisya": "40",
        "danchi": "260"
    }
}


def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=30
    )


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_rooms(shisya, danchi):
    payload = {
        "shisya": shisya,
        "danchi": danchi,
        "shikibetu": "0",
        "pageIndex": "0"
    }

    r = requests.post(API_URL, data=payload, timeout=30)
    data = r.json()

    if data is None:
        return []

    return data


old_state = load_state()
new_state = {}

for danchi_name, target in TARGETS.items():

    rooms = get_rooms(
        target["shisya"],
        target["danchi"]
    )

    current_rooms = {}

    old_rooms = old_state.get(danchi_name, {})

    for room in rooms:

        room_id = room["id"]

        info = {
            "name": room["name"],
            "rent": room["rent"],
            "type": room["type"],
            "floorspace": room["floorspace"],
            "floor": room["floor"]
        }

        current_rooms[room_id] = info

        if room_id not in old_rooms:

            send_telegram(
f"""🏠【UR新房源】

団地：
{danchi_name}

部屋：
{info['name']}

間取り：
{info['type']}

面積：
{info['floorspace']}

階数：
{info['floor']}

家賃：
{info['rent']}
"""
            )

        else:

            old_info = old_rooms[room_id]

            if old_info != info:

                msg = f"""🔄【房源信息变化】

団地：
{danchi_name}

部屋：
{info['name']}
"""

                if old_info["rent"] != info["rent"]:
                    msg += f"\n家賃：{old_info['rent']} → {info['rent']}"

                if old_info["type"] != info["type"]:
                    msg += f"\n間取り：{old_info['type']} → {info['type']}"

                if old_info["floorspace"] != info["floorspace"]:
                    msg += f"\n面積：{old_info['floorspace']} → {info['floorspace']}"

                send_telegram(msg)

    new_state[danchi_name] = current_rooms

save_state(new_state)
