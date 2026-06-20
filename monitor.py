import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

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

API_URL = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=30
    )


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
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

    room_ids = set()

    for room in rooms:

        room_id = room["id"]

        room_ids.add(room_id)

        old_ids = set(old_state.get(danchi_name, []))

        if room_id not in old_ids:

            link = (
                "https://www.ur-net.go.jp"
                + room["roomDetailLink"]
            )

            msg = f"""🏠 UR空室通知

団地：
{danchi_name}

{name}

間取り：
{room["type"]}

面積：
{room["floorspace"]}

階数：
{room["floor"]}

家賃：
{room["rent"]}

詳細：
{link}
"""

            send_telegram(msg)

    new_state[danchi_name] = list(room_ids)

save_state(new_state)
