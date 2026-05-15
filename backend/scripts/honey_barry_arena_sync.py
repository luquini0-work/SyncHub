"""
Honey Barry Arena — Sync script
=================================
Fetches bookings from the Finnly Sport API using a JWT Bearer token,
transforms the data to CatchCorner CSV format, and uploads it.

Token is read from the FINNLY_TOKEN environment variable (Railway → Variables).
To update: go to SyncHub dashboard → 🔑 Token on Honey Barry Arena.

Run:
  python honey_barry_arena_sync.py
  python honey_barry_arena_sync.py --start 2026-05-01 --end 2026-05-31
  python honey_barry_arena_sync.py --no-upload
"""

import csv
import sys
import datetime
import argparse
import os
import requests

# ── Config ─────────────────────────────────────────────────────────────────────

SITE_ID = 218
FACILITY_IDS = [2841, 2817, 3492, 2842, 2579, 2570, 2569]

FACILITY_MAP = {
    2841: "Arena Lounge",
    2817: "Boardroom",
    3492: "Concession",
    2842: "Holidays",
    2579: "Mini Training Rink",
    2570: "North Rink 2",
    2569: "South Rink 1",
}

API_URL   = "https://app.finnlysport.com/event/aaa_event/calendarschedule"
SYNC_DAYS = 60

CC_USERNAME    = "localloginformaint.e.na.n.c.e1.9.9.40@gmail.com"
CC_PASSWORD    = "z2bVyt!JHrAF8KdNm#3m!z*$8NJgbR"
CC_FACILITY    = "2354"
CC_ACCESS_FROM = "Corporate"


def get_finnly_token() -> str:
    """
    Get Finnly token from environment variable FINNLY_TOKEN.
    Falls back to SYNC_COOKIE for backwards compatibility.
    Prints a clear error if not found.
    """
    token = os.environ.get("FINNLY_TOKEN", "").strip()
    if not token:
        # Also try SYNC_COOKIE (set by SyncHub when cookie is updated via dashboard)
        token = os.environ.get("SYNC_COOKIE", "").strip()
    if not token:
        print()
        print("=" * 60)
        print("ERROR: FINNLY_TOKEN environment variable is not set.")
        print("To fix:")
        print("  1. Go to SyncHub dashboard")
        print("  2. Click 🔑 Token on Honey Barry Arena")
        print("  3. Paste the Bearer token from Finnly DevTools")
        print("     (Authorization header from calendarschedule request)")
        print("=" * 60)
        sys.exit(1)
    # Ensure it starts with "Bearer "
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
    return token


# ── Fetch from Finnly Sport API ────────────────────────────────────────────────

def fetch_events(start_date: datetime.date, end_date: datetime.date, token: str) -> list:
    start_str = start_date.strftime("%Y-%m-%dT00:00:00")
    end_str   = end_date.strftime("%Y-%m-%dT00:00:00")

    payload = {
        "SiteId": SITE_ID,
        "FacilityIdList": FACILITY_IDS,
        "StartDate": start_str,
        "EndDate": end_str,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code in (401, 403):
        print()
        print("=" * 60)
        print("ERROR: Finnly Sport token is invalid or expired.")
        print("To renew the token:")
        print("  1. Go to https://app.finnlysport.com/security/login")
        print("  2. Login with localloginformaint.e.na.n.c.e1.99.40@gmail.com")
        print("  3. Open Facility Management → Calendar (old)")
        print("  4. DevTools → Network → search 'calendarschedule'")
        print("  5. Copy the Authorization header value")
        print("  6. In SyncHub dashboard → 🔑 Token on Honey Barry Arena → paste")
        print("=" * 60)
        sys.exit(1)

    resp.raise_for_status()

    try:
        data = resp.json()
    except Exception as e:
        print(f"ERROR: Could not parse JSON response: {e}")
        print(f"Response text (first 500 chars): {resp.text[:500]}")
        sys.exit(1)

    if not isinstance(data, list):
        print(f"ERROR: Expected a list from API, got: {type(data)}")
        sys.exit(1)

    return data


# ── Transform ──────────────────────────────────────────────────────────────────

def _parse_iso(dt_str: str) -> datetime.datetime:
    dt_str = dt_str.rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse datetime: {dt_str!r}")


def transform(events: list) -> list:
    rows = []
    for item in events:
        try:
            start_dt = _parse_iso(item["eventStartTime"])
            end_dt   = _parse_iso(item["eventEndTime"])
        except (KeyError, ValueError) as e:
            print(f"  WARNING: Skipping malformed event ({e}): {item}")
            continue

        # Add 10 minutes to end time (mirrors App Script behaviour)
        end_dt += datetime.timedelta(minutes=10)

        facility_id = item.get("facilityId")
        court_name  = FACILITY_MAP.get(facility_id, str(facility_id))

        rows.append({
            "Date":      start_dt.strftime("%m/%d/%Y"),
            "StartTime": start_dt.strftime("%I:%M:%S %p"),
            "EndTime":   end_dt.strftime("%I:%M:%S %p"),
            "Court":     court_name,
        })

    return rows


# ── Save CSV ───────────────────────────────────────────────────────────────────

def save_csv(rows: list, output_path: str = None) -> str:
    if not output_path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, f"honey_barry_arena_{ts}.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "StartTime", "EndTime", "Court"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CSV] Saved: {output_path} ({len(rows)} rows)")
    if rows:
        print(f"      Sample: {rows[0]}")
    return output_path


# ── CatchCorner upload ─────────────────────────────────────────────────────────

def login_cc_corporate(username: str, password: str, access_from: str) -> str:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "x-cc-platform": "1",
    }
    data = {"accessFrom": access_from, "email": username, "loginPlatform": 1, "password": password}
    res = requests.Session().post(
        "https://www.catchcorner.com/api/shared/authentication/Login",
        json=data, headers=headers, timeout=15
    )
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise ValueError("No access token received — check CatchCorner credentials.")
    print("      CatchCorner login OK.")
    return token


def upload_csv_corporate_api(access_token: str, corporate_id: str, csv_path: str):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "x-cc-platform": "1",
        "Authorization": f"Bearer {access_token}",
    }
    with open(csv_path, "rb") as f:
        files = {"file": (os.path.basename(csv_path), f, "multipart/form-data")}
        resp = requests.Session().post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{corporate_id}/0",
            files=files, headers=headers, timeout=60,
        )
    if not resp.ok:
        print(f"      Upload failed: {resp.status_code}")
        print(f"      Response body: {resp.text[:500]}")
        resp.raise_for_status()
    print("      CSV uploaded to CatchCorner successfully.")


def upload_to_catchcorner(csv_path: str):
    print("[4] Logging in to CatchCorner...")
    token = login_cc_corporate(CC_USERNAME, CC_PASSWORD, CC_ACCESS_FROM)
    print(f"[5] Uploading to CatchCorner (facility ID: {CC_FACILITY})...")
    upload_csv_corporate_api(token, CC_FACILITY, csv_path)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Honey Barry Arena sync")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--end",   help="End date YYYY-MM-DD (default: today + 60 days)")
    parser.add_argument("--output-file", help="Output CSV path (optional)")
    parser.add_argument("--no-upload", action="store_true", help="Skip CatchCorner upload")
    args = parser.parse_args()

    # Get token from environment
    finnly_token = get_finnly_token()

    today      = datetime.date.today()
    start_date = datetime.date.fromisoformat(args.start) if args.start else today
    end_date   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=SYNC_DAYS)

    print("=" * 55)
    print("  Honey Barry Arena Sync")
    print(f"  Range: {start_date} → {end_date} ({(end_date - start_date).days + 1} days)")
    print("=" * 55)

    print("\n[1] Fetching data from Finnly Sport API...")
    events = fetch_events(start_date, end_date, finnly_token)
    print(f"      Got {len(events)} events from API.")

    if not events:
        print("WARNING: No events returned. Check the token and date range.")
        sys.exit(0)

    print("\n[2] Transforming data...")
    rows = transform(events)
    print(f"      {len(rows)} booking rows produced.")

    print("\n[3] Saving CSV...")
    csv_path = save_csv(rows, args.output_file)

    if not args.no_upload:
        upload_to_catchcorner(csv_path)

    print()
    print(f"Done. {len(rows)} records synced.")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()