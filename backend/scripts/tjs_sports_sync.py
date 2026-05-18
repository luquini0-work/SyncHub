"""
TJ's Sports Club — Sync script (Glofox API, Bearer token)

Uso:
  python tjs_sports_sync.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-upload]

Nota: Token se carga vía SyncHub 🍪 (SYNC_COOKIE env var)
"""
import os
import csv
import sys
import datetime
import argparse
import requests
import time

SYNC_DAYS = 60

CC_USER = os.environ.get("CC_TJS_USER", "")
CC_PASS = os.environ.get("CC_TJS_PASS", "")
CC_FAC = os.environ.get("CC_TJS_FAC", "0")


def get_token():
    """Obtener token desde env var SYNC_COOKIE (cargado vía SyncHub 🍪)"""
    t = os.environ.get("SYNC_COOKIE", "").strip()
    if not t:
        print("ERROR: No token. Upload via SyncHub 🍪")
        sys.exit(1)
    return t if t.startswith("Bearer ") else f"Bearer {t}"


def fetch(start, end, token):
    """Fetch eventos unavailable"""
    print(f"[1/3] Fetching TJ's Sports ({start} → {end})...")
    s = int(datetime.datetime.combine(start, datetime.time.min).timestamp())
    e = int(
        datetime.datetime.combine(end, datetime.time(23, 59, 59)).timestamp()
    )
    rows = []
    page = 1
    has_more = True

    while has_more:
        url = f"https://api.glofox.com/2.0/events?end={e}&include=trainers,facility,program,users_booked&page={page}&private=false&sort_by=time_start&start={s}"
        r = requests.get(url, headers={"Authorization": token}, timeout=60)

        if r.status_code in (401, 403):
            print("ERROR: Token expired. Update via SyncHub.")
            sys.exit(1)

        r.raise_for_status()
        data = r.json()
        has_more = data.get("has_more", False)

        for slot in data.get("data", []):
            # Solo tomamos slots que NO están AVAILABLE (unavailable, booked, etc)
            if slot.get("status") != "AVAILABLE":
                st = datetime.datetime.fromtimestamp(int(slot["time_start"]))
                en = st + datetime.timedelta(hours=1)
                rows.append(
                    {
                        "Date": st.strftime("%m/%d/%Y"),
                        "Start": st.strftime("%I:%M:%S %p").lstrip("0"),
                        "End": en.strftime("%I:%M:%S %p").lstrip("0"),
                        "Resource": slot.get("name", ""),
                    }
                )

        page += 1
        time.sleep(3)

    print(f"      {len(rows)} rows")
    return rows


def save_csv(rows, path=None):
    """Guardar CSV"""
    if not path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"tjs_sports_{ts}.csv"
        )

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Start", "End", "Resource"])
        w.writeheader()
        w.writerows(rows)

    print(f"      CSV: {path} ({len(rows)} rows)")
    return path


def upload(csv_path):
    """Upload CSV a CatchCorner"""
    h = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0",
        "x-cc-platform": "1",
    }
    r = requests.post(
        "https://www.catchcorner.com/api/shared/authentication/Login",
        json={
            "accessFrom": "Corporate",
            "email": CC_USER,
            "loginPlatform": 1,
            "password": CC_PASS,
        },
        headers=h,
        timeout=15,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    del h["Content-Type"]
    h["Authorization"] = f"Bearer {token}"

    with open(csv_path, "rb") as f:
        resp = requests.post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FAC}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h,
            timeout=60,
        )
    resp.raise_for_status()
    print("      Uploaded OK")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--no-upload", action="store_true")
    args = p.parse_args()

    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end = (
        datetime.date.fromisoformat(args.end)
        if args.end
        else today + datetime.timedelta(days=SYNC_DAYS)
    )

    token = get_token()
    rows = fetch(start, end, token)

    if not rows:
        print("No rows")
        sys.exit(0)

    path = save_csv(rows)

    if not args.no_upload:
        print("[3/3] Uploading...")
        upload(path)

    print(f"Done. {len(rows)} records.")


if __name__ == "__main__":
    main()