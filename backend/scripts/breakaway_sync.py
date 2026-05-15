"""
BreakAway Speed Sports Training — Sync script (cookie-based, no Selenium)
=========================================================================
Uses the same DailyStaffSchedule API as Houston Pickleball/Badminton,
with a Mindbody session cookie.

How to get the cookie:
  1. Login at https://clients.mindbodyonline.com (business 15652)
  2. Navigate to Cage Schedule calendar
  3. DevTools → Network → any DailyStaffSchedules request → copy Cookie header
  4. Paste into SyncHub dashboard → 🍪 Cookie on BreakAway

NOTE: BreakAway uses business ID 15652. The studio_id used in the API
may differ — if this script returns 0 rows, check DevTools for the
exact studioID in the DailyStaffSchedules request URL and update below.

Run:
  python breakaway_sync.py --cookie-file cookie_breakaway.txt
  python breakaway_sync.py --start 2026-05-01 --end 2026-07-01
  python breakaway_sync.py --no-upload
"""

import os, re, csv, sys, datetime, argparse, calendar, requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ────────────────────────────────────────────────────────────────────

# BreakAway business ID is 15652. The studio_id for the API is typically
# the same or found in the DailyStaffSchedules URL in DevTools Network tab.
# Update STUDIO_ID if needed after checking DevTools.
STUDIO_ID = "15652"
TAB_ID    = "9"     # Default resource schedule tab — update if needed
SYNC_DAYS = 60

# Resource map: staffID → Court name
# These are the Cage IDs for BreakAway. Update from DevTools if needed.
# Pattern: check the DailyStaffSchedules response for StaffID values.
RESOURCE_MAP = {
    # Will be populated dynamically if unknown — script prints all StaffIDs
    # Common pattern for cage-based facilities:
    "1":  "Cage 1",
    "2":  "Cage 2",
    "3":  "Cage 3",
    "4":  "Cage 4",
    "5":  "Cage 5",
    "6":  "Cage 6",
    "7":  "Cage 7",
    "8":  "Cage 8",
    "9":  "Cage 9",
    "10": "Cage 10",
}

CC_USERNAME    = os.environ.get("CC_BREAKAWAY_USER", "localloginformaint.e.na.nce.19.9.4.0@gmail.com")
CC_PASSWORD    = os.environ.get("CC_BREAKAWAY_PASS", "u$tm23fRZaY#Xj7PcPMo7fVhO7uoeo")
CC_FACILITY    = "2284"
CC_ACCESS_FROM = "Corporate"

# ── Cookie ────────────────────────────────────────────────────────────────────

def get_cookie() -> str:
    cookie = os.environ.get("SYNC_COOKIE", "").strip()
    if not cookie:
        print("ERROR: No cookie. Set SYNC_COOKIE or upload via SyncHub dashboard.")
        sys.exit(1)
    return cookie

def make_session(cookie: str) -> requests.Session:
    s = requests.Session()
    s.verify = False
    s.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Cookie": cookie,
        "Referer": "https://clients.mindbodyonline.com/mainappointments/index",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    return s

# ── Fetch from Mindbody DailyStaffSchedule API ───────────────────────────────

def epoch_to_time(epoch_seconds: int) -> str:
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def minutes_to_time(base_epoch: int, minutes: int) -> str:
    dt = datetime.datetime.fromtimestamp(base_epoch + minutes * 60, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def parse_payload(payload: list, resource_map: dict) -> list:
    rows = []
    unknown_ids = set()
    for day_obj in payload:
        day_epoch = day_obj.get("Day", 0)
        day_date  = datetime.datetime.fromtimestamp(day_epoch, tz=datetime.timezone.utc).date()
        staff_id  = str(int(day_obj.get("StaffID", 0)))
        court     = resource_map.get(staff_id)
        if court is None:
            unknown_ids.add(staff_id)
            court = f"Resource {staff_id}"
        date_str  = day_date.strftime("%Y-%m-%d")
        for appt in day_obj.get("Appointments") or []:
            rows.append({"Date": date_str, "Start Time": epoch_to_time(appt["Start"]),
                         "End Time": epoch_to_time(appt["End"]), "Court": court})
        for unav in day_obj.get("Unavailabilities") or []:
            rows.append({"Date": date_str, "Start Time": minutes_to_time(day_epoch, unav["StartTime"]),
                         "End Time": minutes_to_time(day_epoch, unav["EndTime"]), "Court": court})
    if unknown_ids:
        print(f"      Unknown StaffIDs: {sorted(unknown_ids)} — update RESOURCE_MAP in script")
    return rows

def collect(cookie: str, start_date: datetime.date, end_date: datetime.date) -> list:
    num_days = (end_date - start_date).days + 1
    print(f"[2/4] Collecting {num_days} days ({start_date} → {end_date})...")
    session = make_session(cookie)
    all_rows = []

    # Try batch first (same as Badminton)
    epoch_start = calendar.timegm((start_date.year, start_date.month, start_date.day, 0, 0, 0))
    epoch_end   = calendar.timegm((end_date.year,   end_date.month,   end_date.day,   0, 0, 0))
    url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
           f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
           f"&startDate={epoch_start}&endDate={epoch_end}&tabID={TAB_ID}")
    print(f"      Trying batch request...")
    try:
        r = session.get(url, timeout=60)
        if r.status_code == 200:
            data = r.json()
            payload = data.get("json") or data if isinstance(data, list) else []
            if payload:
                all_rows = parse_payload(payload, RESOURCE_MAP)
                print(f"      Batch: {len(all_rows)} rows")
                return all_rows
            else:
                print(f"      Batch returned empty. Trying day-by-day...")
        else:
            print(f"      Batch returned {r.status_code}. Trying day-by-day...")
    except Exception as e:
        print(f"      Batch error: {e}. Trying day-by-day...")

    # Fallback: day by day (same as Pickleball)
    current = start_date
    while current <= end_date:
        epoch = calendar.timegm((current.year, current.month, current.day, 0, 0, 0))
        url_day = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
                   f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
                   f"&startDate={epoch}&endDate={epoch}&view=day&tabID={TAB_ID}")
        try:
            r = session.get(url_day, timeout=30)
            if r.status_code != 200:
                print(f"      {current}: HTTP {r.status_code}")
            else:
                rows = parse_payload(r.json().get("json") or [], RESOURCE_MAP)
                all_rows.extend(rows)
                if rows:
                    print(f"      {current}: {len(rows)} rows")
        except Exception as e:
            print(f"      {current}: ERROR {e}")
        current += datetime.timedelta(days=1)

    print(f"      Total: {len(all_rows)} rows.")
    return all_rows

# ── Save CSV ──────────────────────────────────────────────────────────────────

def save_csv(rows: list, output_path: str = None) -> str:
    if not output_path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, f"breakaway_output_{ts}.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Start Time", "End Time", "Court"])
        w.writeheader()
        w.writerows(rows)

    print(f"[3/4] CSV: {output_path} ({len(rows)} rows)")
    if rows:
        print(f"      Sample: {rows[0]}")
    return output_path

# ── CatchCorner upload ────────────────────────────────────────────────────────

def upload_to_catchcorner(csv_path: str):
    print("[4/4] Uploading to CatchCorner...")
    h = {"Accept": "application/json, text/plain, */*", "Content-Type": "application/json",
         "Origin": "https://cc-stage-corporate.azurewebsites.net",
         "Referer": "https://cc-stage-corporate.azurewebsites.net/",
         "User-Agent": "Mozilla/5.0", "x-cc-platform": "1"}
    r = requests.Session().post(
        "https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom": CC_ACCESS_FROM, "email": CC_USERNAME, "loginPlatform": 1, "password": CC_PASSWORD},
        headers=h, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise ValueError("No CatchCorner token")
    print("      Login OK.")
    del h["Content-Type"]
    h["Authorization"] = f"Bearer {token}"
    with open(csv_path, "rb") as f:
        resp = requests.Session().post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FACILITY}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h, timeout=60)
    if not resp.ok:
        print(f"      Upload failed {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
    print("      Uploaded OK.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--output-file")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--cookie-file", help="Path to file with cookie string")
    args = parser.parse_args()

    today      = datetime.date.today()
    start_date = datetime.date.fromisoformat(args.start) if args.start else today
    end_date   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=SYNC_DAYS)

    if args.cookie_file:
        with open(args.cookie_file, encoding="utf-8") as cf:
            os.environ["SYNC_COOKIE"] = cf.read().strip()

    print("=" * 55)
    print("  BreakAway Speed Sports Training Sync")
    print(f"  Range: {start_date} → {end_date} ({(end_date - start_date).days + 1} days)")
    print("=" * 55)

    cookie = get_cookie()
    rows   = collect(cookie, start_date, end_date)

    if not rows:
        print("WARNING: No rows collected.")
        print("Check: 1) cookie is valid  2) STUDIO_ID is correct  3) TAB_ID is correct")
        print("To find correct values: DevTools → Network → filter 'DailyStaffSchedules' → check URL params")
        sys.exit(0)

    csv_path = save_csv(rows, args.output_file)

    if not args.no_upload:
        upload_to_catchcorner(csv_path)

    print(f"\nDone. {len(rows)} records synced.")

if __name__ == "__main__":
    main()