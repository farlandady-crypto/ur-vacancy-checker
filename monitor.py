import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

URL = "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_2480_room.html"
STATE_FILE = "state.json"

resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")
text = soup.get_text("\n", strip=True)

has_room = "現在、募集中の住宅はありません" not in text

old_state = {"has_room": False}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        old_state = json.load(f)

if has_room and not old_state["has_room"]:
    body = f"""发现「かわさきテクノピア堀川町ハイツ」有空房！

请立即查看：
{URL}
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "【UR空室通知】かわさきテクノピア堀川町ハイツ"
    msg["From"] = os.environ["EMAIL_ADDRESS"]
    msg["To"] = os.environ["RECEIVER_EMAIL"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["EMAIL_ADDRESS"], os.environ["EMAIL_PASSWORD"])
        smtp.send_message(msg)

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump({"has_room": has_room}, f)
