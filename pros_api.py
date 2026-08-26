#!/usr/bin/env python3
"""
FantasyPros Projections Scraper
--------------------------------
Fetches player projection tables from fantasypros.com/nfl/projections/<pos>.php
using your own logged-in session cookie, and writes them out as clean CSV files
(one per position, plus a combined file).

USAGE
-----
1. Get your session cookie from your browser:
   - Log into fantasypros.com in your browser
   - Open DevTools (F12) -> Network tab -> reload the projections page
   - Click the page request -> Headers -> Request Headers -> copy the full "Cookie" value
   - Paste it into COOKIE_STRING below (or pass it via the FP_COOKIE env var)

2. Adjust POSITIONS, SCORING, and WEEK below as needed.

3. Run:
   python3 fantasypros_projections.py

OUTPUT
------
CSVs written to ./output/<position>_projections.csv and ./output/all_projections.csv
"""

import os
import re
import csv
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ------------------------- CONFIG -------------------------

# Paste your browser's Cookie header value here, or set the FP_COOKIE env var instead
# (env var takes precedence so you don't have to hardcode auth in the file).
COOKIE_STRING = os.environ.get("FP_COOKIE", "fp_prefs=eyJjb21tYW5kX2NlbnRlcl9ob21lIjoibGVnYWN5IiwiZnBfc2l0ZV92ZXJzaW9uIjozLCJob21lcGFnZV9sb2dnZWRvdXRfaHlicmlkX3ZhcmlhbnRfdjIiOiJzYWFzX2xlZ2FjeSIsImhvbWVwYWdlX2xvZ2dlZG91dF92YXJpYW50IjoiZHJhZnRfdmFyaWFudF9iIn0=; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Aug+21+2026+21%3A16%3A21+GMT-0400+(Eastern+Daylight+Time)&version=202607.1.0&browserGpcFlag=1&isDntEnabled=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&GPPCookiesCount=1&gppSid=7&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CBG35%3A1&AwaitingReconsent=false&geolocation=US%3BMA; OTGPPConsent=DBABLA~BVQqAAAAAAJY.YA; OptanonAlertBoxClosed=2026-08-22T00:04:20.968Z; fp_rankings_visits=1; fpdefloc=MA; sessionid=bdyjy6rpimw1nc8j7mahsmbkemht3113; is5vHOtZn65zpLqA=bdyjy6rpimw1nc8j7mahsmbkemht3113; fptoken=gAAAAABqiPIvGU2oXK6QE7wtZQlkggkrUUQWrS1AcE9-_TfkbzmGdpQftErCz9dqvBefsDA1VbSlYuI29a1bCWjYa8gyl1NV7KGc4leEMF_4hyBUydNwz20%3D%3A1787384998; fp_level=YmFzaWM=; fp_recent_visit=1; dismissed_upsell_add_team=1; fp_userdata=eyJsYXN0X2xvZ2luIjoiNjc3NDk1OSIsInVzZXJuYW1lIjoiZGVhbml6em8yMiIsImVtYWlsIjoiZGVhbml6em8yMkBnbWFpbC5jb20iLCJlbWFpbF9oYXNoZXMiOnsic2hhMSI6ImZmOTUwMjBkMWU0ZTkwNGRmM2RiMWQ2MDBhNTgzNzUzYWFjNjk4ODYiLCJzaGEyNTYiOiJhZGUyNmU3OTM5ZTViNWExZmNiYTg2ZDE1NGRhNjEwNmM4Nzg2ZTkxZmM3MzljNWFhNTliZGFiY2QxZjg3NGI5IiwibWQ1IjoiNDYwY2E0ODU0ODAzNmUxODhmYzYxODdhZDA0MjMxYTkifSwidXVpZCI6InVzZXJfMzUxYTMyNWMtNDQzZi00MTcwLWFhYTEtZWNkNmEwMmNlNjZjIiwicGFzdF9wYWlkX3Nwb3J0cyI6W10sInVzZXJfYXBpX2tleSI6ImY1MzVkMjllMDBiODQwNzdiYmQ0NTI1ZTEiLCJzaXRlX3ZlcnNpb24iOjMsInN1Yl9sZXZlbCI6IiIsImhhc19wYXN0X3RyaWFsIjpmYWxzZSwiY2FuX2RlcG9zaXRfZHJhZnQiOmZhbHNlLCJjYW5fZGVwb3NpdF9mYW5kdWVsIjpmYWxzZSwiZGVwb3NpdF9zaXRlcyI6W10sIm1sYl9sZWFndWVzIjowLCJuZmxfbGVhZ3VlcyI6MCwibmJhX2xlYWd1ZXMiOjB9")

# Positions to pull. Valid: qb, rb, wr, te, k, dst
POSITIONS = ["qb", "rb", "wr", "te"]

# Scoring format: STD, HALF, PPR  (only affects the FPTS column / sort, not raw stats)
SCORING = "PPR"

# Set to None for full-season (draft) projections, or an int (1-18) for a specific week
WEEK = None

BASE_URL = "https://www.fantasypros.com/nfl/projections/{pos}.php"

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ------------------------------------------------------------


def build_url(pos: str) -> str:
    url = BASE_URL.format(pos=pos)
    params = [f"scoring={SCORING}"]
    if WEEK:
        params.append(f"week={WEEK}")
    return url + "?" + "&".join(params)


def fetch_html(pos: str) -> str:
    url = build_url(pos)
    cookies = {}
    if COOKIE_STRING and COOKIE_STRING != "PASTE_YOUR_COOKIE_HEADER_HERE":
        # Turn "a=1; b=2; c=3" into a dict
        for part in COOKIE_STRING.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k] = v

    resp = requests.get(url, headers=HEADERS, cookies=cookies, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_table(html: str, pos: str):
    """
    Parses the #data table on a FantasyPros projections page into a list of dicts.
    Handles the two-row header (grouped labels like RUSHING/RECEIVING + stat abbreviations).
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="data")
    if table is None:
        raise ValueError(f"Could not find projections table for position={pos}. "
                          f"Your cookie may be missing/expired, or the page structure changed.")

    thead = table.find("thead")
    header_rows = thead.find_all("tr")
    # The last header row has the actual column abbreviations (ATT, YDS, TDS, FPTS, etc.)
    stat_header_row = header_rows[-1]
    stat_cols = [th.get_text(strip=True) for th in stat_header_row.find_all(["th", "td"])]
    # First column is "Player"
    stat_cols[0] = "Player"

    # If there's a grouping row (RUSHING / RECEIVING / MISC), map column index -> group label
    group_labels = [""] * len(stat_cols)
    if len(header_rows) > 1:
        group_row = header_rows[0]
        idx = 0
        for cell in group_row.find_all(["th", "td"]):
            colspan = int(cell.get("colspan", 1))
            label = cell.get_text(strip=True)
            for _ in range(colspan):
                if idx < len(group_labels):
                    group_labels[idx] = label
                idx += 1

    # Build final column names, prefixing stat abbreviations with their group
    # e.g. RUSHING + YDS -> "RUSH_YDS", RECEIVING + YDS -> "REC_YDS"
    final_cols = []
    for i, col in enumerate(stat_cols):
        if col == "Player":
            final_cols.append("Player")
        elif group_labels[i]:
            prefix = re.sub(r"[^A-Z]", "", group_labels[i].upper())[:4]
            final_cols.append(f"{prefix}_{col}")
        else:
            final_cols.append(col)

    rows = []
    tbody = table.find("tbody")
    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue

        player_cell = cells[0]
        link = player_cell.find("a", class_="fp-player-link")
        player_name = link.get("fp-player-name") if link else player_cell.get_text(strip=True)

        # Team is usually the trailing text/abbreviation after the link in the player cell
        full_text = player_cell.get_text(" ", strip=True)
        team = full_text.replace(player_name, "").strip() if player_name else ""

        row = {"Player": player_name, "Team": team, "Position": pos.upper()}
        for col_name, cell in zip(final_cols[1:], cells[1:]):
            row[col_name] = cell.get_text(strip=True)

        rows.append(row)

    return rows


def write_csv(rows, path: Path):
    if not rows:
        print(f"No rows to write for {path}")
        return
    # Union of all keys, preserving first-seen order, Player/Team/Position first
    fieldnames = ["Player", "Team", "Position"]
    for row in rows:
        for k in row.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {len(rows)} rows -> {path}")


def main():
    all_rows = []
    for pos in POSITIONS:
        print(f"Fetching {pos.upper()} projections...")
        try:
            html = fetch_html(pos)
            rows = parse_table(html, pos)
        except Exception as e:
            print(f"  FAILED for {pos}: {e}", file=sys.stderr)
            continue

        write_csv(rows, OUTPUT_DIR / f"{pos}_projections.csv")
        all_rows.extend(rows)
        time.sleep(1)  # be polite between requests

    if all_rows:
        write_csv(all_rows, OUTPUT_DIR / "all_projections.csv")


if __name__ == "__main__":
    main()