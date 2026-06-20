import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"

TARGETS = {
    "かわさきテクノピア堀川町ハイツ":
        "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_2480_room.html",

    "川崎旭町ハイツ":
        "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_2600_room.html"
}


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )


# 读取历史状态
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {}

new_state = {}

headers = {
    "User-Agent": "Mozilla/5.0"
}

for name, url in TARGETS.items():

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text()

    has_room = "現在、募集中の住宅はありません" not in text

    new_state[name] = has_room

    old_has_room = state.get(name, False)

    # 之前没房，现在有房
    if has_room and not old_has_room:

        msg = f"""🏠 UR空室通知

団地：
{name}

发现新的空房！

立即查看：
{url}
"""

        send_telegram(msg)

# 保存状态
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(new_state, f, ensure_ascii=False)
