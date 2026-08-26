"""
ESPN Auction Draft Watcher — Python client
-------------------------------------------
Connects to the local server.js over Server-Sent Events (SSE) and receives
each pick live as it happens, as a Python dict.

Requires: pip install requests pandas

Run this alongside server.js (server.js must be running first):
    python draft_listener.py
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

STREAM_URL = "http://localhost:3789/stream"

# --- Discord webhook config -------------------------------------------------
# Add Discord Webook Here
# Server Settings -> Integrations -> Webhooks -> New Webhook -> Copy URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

# Fire-and-forget executor so a slow/failed Discord POST never blocks the
# SSE loop that's reading live draft events.
_discord_executor = ThreadPoolExecutor(max_workers=4)


def _post_to_discord(content: str):
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=5)
        if resp.status_code >= 300:
            print(f"[discord] webhook returned {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as e:
        print(f"[discord] send failed: {e}")


def send_discord(content: str):
    """Non-blocking Discord webhook send. Discord's 2000-char message limit
    is truncated defensively here in case a message ever runs long."""
    if len(content) > 1990:
        content = content[:1990] + "…"
    _discord_executor.submit(_post_to_discord, content)


# -----------------------------------------------------------------------------


def on_nominee(event: dict, df: pd.DataFrame):
    """
    Called whenever a new player is put up for auction (before a price is set).
    `event` looks like: {"type": "nominee", "player": "...", "nflTeam": "...", "position": "..."}
    """
    line1 = f"[PYTHON] >>> Now nominated: {event.get('player')} ({event.get('nflTeam')} {event.get('position')})"

    matches = df[df["name"] == event.get("player")]
    if not matches.empty:
        value_diff = matches["Value Difference"].values[0]
        espn = matches["projected_points"].values[0]
        fpros = matches["Consensus"].values[0]
        line2 = f"Consensus value diff: {value_diff}    Espn: {espn}    FPros: {fpros}"
    else:
        line2 = "(no guide_values.csv match found for this player)"

    print(line1)
    print(line2)

    send_discord(f"**{line1}**\n{line2}")


def on_pick(event: dict):
    """
    Called once per pick, live, in real time.
    `event` looks like:
    {
        "type": "pick",
        "pickNumber": 1,
        "player": "Jaylen Warren",
        "team": "PIT RB",
        "amount": 1,
        "owner": "Steez Spoke Pipeline",
        "stats": {
            "spent": 1,
            "picks": 1,
            "remaining": 199,
            "spotsLeft": 15,
            "maxBid": 185
        }
    }
    ---- Put your own logic here ----
    e.g. check against a watchlist, log to a database, trigger a text
    message, update a spreadsheet, feed a value model, etc.
    """
    player = event.get("player")
    amount = event.get("amount")
    owner = event.get("owner")
    stats = event.get("stats")

    print(f"[PYTHON] {player} went for ${amount} to {owner}")

    if stats:
        print(f"         {owner} now has ${stats['remaining']} left, max bid ${stats['maxBid']}")

    # Example: alert if a player on your watchlist gets picked
    WATCHLIST = {"George Kittle", "Xavier Worthy"}
    if player in WATCHLIST:
        print(f"         !!! WATCHLIST ALERT: {player} is off the board !!!")


def listen():
    df = pd.read_csv("guide_values.csv")
    print(f"Connecting to {STREAM_URL} ...")
    while True:
        try:
            with requests.get(STREAM_URL, stream=True, timeout=None) as resp:
                print("Connected. Waiting for picks...\n")
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "pick":
                        on_pick(event)
                    elif event.get("type") == "nominee":
                        on_nominee(event, df)
        except requests.exceptions.RequestException as e:
            print(f"Connection lost ({e}). Retrying in 3s... (is server.js running?)")
            time.sleep(3)


if __name__ == "__main__":
    listen()
