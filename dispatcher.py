import os
import requests

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["GH_REPO"]

API = f"https://api.github.com/repos/{REPO}/dispatches"

print("DISPATCHER RUNNING")

def dispatch(event_type, payload):
    requests.post(
        API,
        json={
            "event_type": event_type,
            "client_payload": payload
        },
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json"
        }
    )


# 示例
# dispatch("pause", {})
# dispatch("resume", {})
