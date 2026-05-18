"""
Jump Shot Gym — Sync script (Acuity scheduling, scraping con regex)

Uso:
  python jump_shot_gym_sync.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-upload]
"""
import os
import csv
import sys
import datetime
import argparse
import requests
import re
import time

SYNC_DAYS = 60

CC_USER = os.environ.get("CC_JUMP_SHOT_USER", "")
CC_PASS = os.environ.get("CC_JUMP_SHOT_PASS", "")
CC_FAC = os.environ.get("CC_JUMP_SHOT_FAC", "0")

RESOURCES = {"66689328": "Half Court", "66839988": "Full Court"}


def fetch_resource(resource_type, start, end):
    """Fetch disponibilidad para un recurso específico"""
    rows = []
    cur = start

    while cur <= end:
        payload = {
            "MIME Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "type": resource_type,
            "calendar": "9796667",
            "month": cur.strftime("%Y-%m-%d"),
            "timezone": "America/New_York",
            "skip": "true",
            "options[numDays]": 5,
            "ignoreAppointment": "",
            "appointmentType": "category:Reservations",
            "calendarID": "",
        }
        h = {"User-Agent": "Mozilla/5.0"}

        try:
            r = requests.post(
                "https://jumpshotgym.as.me/schedule.php?action=showCalendar&fulldate=1&owner=31676056&template=weekly",
                data=payload,
                headers=h,
                timeout=30,
            )
            # Regex para extraer datetime: value="YYYY-MM-DD HH:MM"
            matches = re.findall(r'value="(.{16})', r.text)

            for m in matches:
                try:
                    dt = datetime.datetime.strptime(m, "%Y-%m-%d %H:%M")
                    end_dt = dt + datetime.timedelta(minutes=45)
                    rows.append(
                        {
                            "Date": dt.strftime("%m/%d/%Y"),
                            "Start": dt.strftime("%I:%M:%S %p").lstrip("0"),
                            "End": end_dt.strftime("%I:%M:%S %p").lstrip("0"),
                            "Resource": RESOURCES[resource_type],
                        }
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"      {resource_type} {cur}: {e}")

        time.sleep(2)
        cur += datetime.timedelta(days=5)

    return rows


def collect(start, end):
    """Recolectar datos para ambos recursos"""
    print(f"[1/3] Fetching Jump Shot Gym ({start} → {end})...")
    all_rows = []

    for rt, name in RESOURCES.items():
        rows = fetch_resource(rt, start, end)
        all_rows.extend(rows)
        print(f"      {name}: {len(rows)} rows")

    # Deduplicate
    seen = set()
    unique = []
    for r in all_rows:
        k = (r["Date"], r["Start"], r["Resource"])
        if k not in seen:
            seen.add(k)
            unique.append(r)

    print(f"      Total: {len(unique)} rows")
    return unique


def save_csv(rows, path=None):
    """Guardar CSV"""
    if not path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"jump_shot_gym_{ts}.csv"
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

    rows = collect(start, end)

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