"""
OpenCourt — Sync script (getopencourt.com API, sin auth)
Soporta: Fieldhouse, Barton Rooftop, Downtown

Uso:
  python opencourt_sync.py fieldhouse [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-upload]
  python opencourt_sync.py barton [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-upload]
  python opencourt_sync.py downtown [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-upload]
"""
import os
import csv
import sys
import datetime
import argparse
import requests
import time

SYNC_DAYS = 60

FACILITIES = {
    "fieldhouse": {
        "name": "OpenCourt - The Fieldhouse",
        "slug": "the-fieldhouse",
        "cc_fac": os.environ.get("CC_OPENCOURT_FIELDHOUSE_FAC", "0"),
        "cc_user": os.environ.get("CC_OPENCOURT_FIELDHOUSE_USER", ""),
        "cc_pass": os.environ.get("CC_OPENCOURT_FIELDHOUSE_PASS", ""),
    },
    "barton": {
        "name": "Capital City Pickleball - Barton Rooftop",
        "slug": "urbanpc-barton",
        "cc_fac": os.environ.get("CC_BARTON_FAC", "0"),
        "cc_user": os.environ.get("CC_BARTON_USER", ""),
        "cc_pass": os.environ.get("CC_BARTON_PASS", ""),
    },
    "downtown": {
        "name": "Capital City Pickleball - Downtown",
        "slug": "waterloo",
        "cc_fac": os.environ.get("CC_DOWNTOWN_FAC", "0"),
        "cc_user": os.environ.get("CC_DOWNTOWN_USER", ""),
        "cc_pass": os.environ.get("CC_DOWNTOWN_PASS", ""),
    },
}


def fetch_day(slug, day_str):
    """Fetch reservations para un día específico"""
    url = (
        f"https://app.getopencourt.com/api/club/{slug}/schedule"
        f"?from={day_str}&to={day_str}&includeHidden=true"
    )
    h = {
        "accept": "*/*",
        "user-agent": "Mozilla/5.0",
        "referer": f"https://app.getopencourt.com/club/{slug}/schedule",
    }
    r = requests.get(url, headers=h, timeout=30)
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("remappedReservations", {}).get(day_str, {}).get("reservations", [])


def collect(fac, start, end):
    """Recolectar datos para el rango de fechas"""
    slug = fac["slug"]
    rows = []
    cur = start

    while cur <= end:
        day_str = cur.strftime("%Y-%m-%d")
        try:
            reservations = fetch_day(slug, day_str)
            for rv in reservations:
                st_iso = rv.get("startTime", "")
                en_iso = rv.get("endTime", "")
                if not st_iso:
                    continue

                st = datetime.datetime.fromisoformat(st_iso.replace("Z", ""))
                en = datetime.datetime.fromisoformat(en_iso.replace("Z", ""))
                court = (rv.get("court") or {}).get("name") or rv.get("courtId", "")

                rows.append(
                    {
                        "Date": st.strftime("%m/%d/%Y"),
                        "Start": st.strftime("%I:%M:%S %p").lstrip("0"),
                        "End": en.strftime("%I:%M:%S %p").lstrip("0"),
                        "Court": court,
                    }
                )
        except Exception as e:
            print(f"      {day_str}: {e}")

        time.sleep(0.15)
        cur += datetime.timedelta(days=1)

    return rows


def save_csv(rows, name, path=None):
    """Guardar CSV"""
    if not path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"opencourt_{name}_{ts}.csv"
        )

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Start", "End", "Court"])
        w.writeheader()
        w.writerows(rows)

    print(f"      CSV: {path} ({len(rows)} rows)")
    return path


def upload(fac, csv_path):
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
            "email": fac["cc_user"],
            "loginPlatform": 1,
            "password": fac["cc_pass"],
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
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{fac['cc_fac']}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h,
            timeout=60,
        )
    resp.raise_for_status()
    print("      Uploaded OK")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("facility", choices=["fieldhouse", "barton", "downtown"])
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--no-upload", action="store_true")
    args = p.parse_args()

    fac = FACILITIES[args.facility]
    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end = (
        datetime.date.fromisoformat(args.end)
        if args.end
        else today + datetime.timedelta(days=SYNC_DAYS)
    )

    print(f"[1/3] Fetching {fac['name']} ({start} → {end})...")
    rows = collect(fac, start, end)

    if not rows:
        print("No rows")
        sys.exit(0)

    path = save_csv(rows, args.facility)

    if not args.no_upload:
        print("[3/3] Uploading...")
        upload(fac, path)

    print(f"Done. {len(rows)} records.")


if __name__ == "__main__":
    main()