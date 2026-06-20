import os
import json
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"


def heartbeat(stats):

    state = {}
    if os.path.exists(STATE_FILE):
        state = json.load(open(STATE_FILE, "r", encoding="utf-8"))

    last = state.get("last_run", "unknown")

    msg = (
        f"🟢 心跳\n"
        f"new:{stats.get('new',0)} "
        f"changed:{stats.get('changed',0)} "
        f"fail:{stats.get('fail',0)}\n"
        f"last:{last}"
    )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30
    )
