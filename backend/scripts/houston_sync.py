"""
Houston Pickleball / Badminton Sync
=====================================
Uses DailyStaffSchedule API with session cookie (same as Create The Finish).
Cookie is obtained manually from DevTools → GetTokens request.

Run:
  python houston_sync_v2.py pickleball --cookie-file cookie_pickleball.txt
  python houston_sync_v2.py badminton  --cookie-file cookie_badminton.txt
  python houston_sync_v2.py pickleball --cookie-file cookie_pickleball.txt --no-upload
"""

import os, csv, time, datetime, argparse, requests, calendar
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FACILITIES = {
    "pickleball": {
        "name":      "Houston Pickleball Center",
        "studio_id": "5736211",
        "tab_id":    "9",
        "batch":     False,
        "cc_id":     "2224",
        "cc_user":   "localloginformaint.e.nan.ce1.99.4.0@gmail.com",
        "cc_pass":   "sCJlY5OLHI^NZ8ueTleb*RH@$jMBdk",
        "days":      230,
        "resource_map": {
            "3":  "Court 01", "4":  "Court 02", "5":  "Court 03",
            "6":  "Court 04", "7":  "Court 05", "8":  "Court 06",
            "9":  "Court 07", "10": "Court 08", "11": "Court 09",
            "12": "Court 10", "13": "Private Court",
            "100000020": "Outdoor Ct 01", "100000021": "Outdoor Ct 02",
            "100000025": "",
        },
    },
    "badminton": {
        "name":      "Houston Badminton Center",
        "studio_id": "253992",
        "tab_id":    "9",
        "batch":     True,
        "cc_id":     "2225",
        "cc_user":   "localloginformaint.e.nan.ce1.9.940@gmail.com",
        "cc_pass":   "gi!8RyFRTexnkc61Hj*q#%E6RyZEPr",
        "days":      210,
        "resource_map": {
            "100000030": "Court 01", "100000020": "Court 02", "8":  "Court 03",
            "100000021": "Court 04", "9":         "Court 05", "100000022": "Court 06",
            "100000000": "Court 07", "100000023": "Court 08", "100000009": "Court 09",
            "100000001": "Court 10", "100000031": "Court 11", "100000008": "Court 12",
        },
    },
}

# ── API ────────────────────────────────────────────────────────────────────────

def make_session(cookie):
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

def fetch_day(session, studio_id, tab_id, epoch_day):
    url = (
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
        f"?studioID={studio_id}&isLibAsync=true&isJson=true"
        f"&startDate={epoch_day}&endDate={epoch_day}&view=day&tabID={tab_id}"
    )
    r = session.get(url, timeout=30)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:150]}")
    return r.json()

# ── Collect ────────────────────────────────────────────────────────────────────

def parse_payload(payload, resource_map):
    all_rows = []
    for day_obj in payload:
        day_epoch = day_obj.get("Day", 0)
        day_date  = datetime.datetime.fromtimestamp(day_epoch, tz=datetime.timezone.utc).date()
        staff_id  = str(int(day_obj.get("StaffID", 0)))
        court     = resource_map.get(staff_id, f"Staff {staff_id}")
        date_str  = day_date.strftime("%Y-%m-%d")
        for appt in day_obj.get("Appointments") or []:
            all_rows.append({"Date": date_str, "Start Time": epoch_to_time(appt["Start"]),
                              "End Time": epoch_to_time(appt["End"]), "Court": court})
        for unav in day_obj.get("Unavailabilities") or []:
            all_rows.append({"Date": date_str, "Start Time": minutes_to_time(day_epoch, unav["StartTime"]),
                              "End Time": minutes_to_time(day_epoch, unav["EndTime"]), "Court": court})
    return all_rows


def collect(fac, cookie, start_date, end_date):
    num_days = (end_date - start_date).days + 1
    print(f"[2/4] Collecting {num_days} days ({start_date} → {end_date})...")
    session = make_session(cookie)
    resource_map = fac["resource_map"]
    all_rows = []

    if fac.get("batch", False):
        # Single request for full range (badminton)
        epoch_start = calendar.timegm((start_date.year, start_date.month, start_date.day, 0, 0, 0))
        epoch_end   = calendar.timegm((end_date.year,   end_date.month,   end_date.day,   0, 0, 0))
        url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
               f"?studioID={fac['studio_id']}&isLibAsync=true&isJson=true"
               f"&startDate={epoch_start}&endDate={epoch_end}&tabID={fac['tab_id']}")
        print(f"      Fetching full range in one request...")
        r = session.get(url, timeout=60)
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
        all_rows = parse_payload(r.json().get("json") or [], resource_map)
    else:
        # Day by day with &view=day (pickleball)
        current = start_date
        while current <= end_date:
            epoch = calendar.timegm((current.year, current.month, current.day, 0, 0, 0))
            url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
                   f"?studioID={fac['studio_id']}&isLibAsync=true&isJson=true"
                   f"&startDate={epoch}&endDate={epoch}&view=day&tabID={fac['tab_id']}")
            try:
                r = session.get(url, timeout=30)
                if r.status_code != 200:
                    raise ValueError(f"HTTP {r.status_code}")
                rows = parse_payload(r.json().get("json") or [], resource_map)
                all_rows.extend(rows)
                if rows:
                    print(f"      {current}: {len(rows)} rows")
            except Exception as e:
                print(f"      {current}: ERROR - {e}")
            current += datetime.timedelta(days=1)

    print(f"      Total: {len(all_rows)} rows.")
    return all_rows

# ── Transform ──────────────────────────────────────────────────────────────────

def epoch_to_time(epoch_seconds):
    """UTC as-is — matches Mindbody display timezone."""
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def minutes_to_time(base_epoch, minutes):
    dt = datetime.datetime.fromtimestamp(base_epoch + minutes * 60, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def transform_day(data, date, resource_map):
    rows = []
    payload = data.get("json") or []
    date_str = date.strftime("%Y-%m-%d")

    for day_obj in payload:
        staff_id = str(int(day_obj.get("StaffID", 0)))
        court = resource_map.get(staff_id, f"Staff {staff_id}")
        day_epoch = day_obj.get("Day", 0)

        for appt in day_obj.get("Appointments") or []:
            rows.append({
                "Date": date_str,
                "Start Time": epoch_to_time(appt["Start"]),
                "End Time":   epoch_to_time(appt["End"]),
                "Court": court,
            })

        for unav in day_obj.get("Unavailabilities") or []:
            rows.append({
                "Date": date_str,
                "Start Time": minutes_to_time(day_epoch, unav["StartTime"]),
                "End Time":   minutes_to_time(day_epoch, unav["EndTime"]),
                "Court": court,
            })

    return rows

# ── Save CSV ───────────────────────────────────────────────────────────────────

def save_csv(rows, name):
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"houston_{name}_output_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date","Start Time","End Time","Court"])
        w.writeheader(); w.writerows(rows)
    print(f"[3/4] CSV: {path} ({len(rows)} rows)")
    if rows: print(f"      Sample: {rows[0]}")
    return path

# ── Upload ─────────────────────────────────────────────────────────────────────

def upload(fac, csv_path):
    print(f"[4/4] Uploading to CatchCorner ({fac['cc_id']})...")
    h = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0",
        "x-cc-platform": "1",
    }
    r = requests.Session().post(
        "https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom":"Corporate","email":fac["cc_user"],"loginPlatform":1,"password":fac["cc_pass"]},
        headers=h, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token: raise ValueError("No CC token")
    del h["Content-Type"]
    h["Authorization"] = f"Bearer {token}"
    with open(csv_path, "rb") as f:
        resp = requests.Session().post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{fac['cc_id']}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h, timeout=60)
    if not resp.ok:
        print(f"      Error {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
    print("      Uploaded OK.")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("facility", choices=["pickleball", "badminton"])
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cookie", help="Cookie string directly")
    parser.add_argument("--cookie-file", help="Path to file with cookie string")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    fac   = FACILITIES[args.facility]
    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=fac["days"])

    print("="*55)
    print(f"  {fac['name']} Sync")
    print(f"  Range: {start} → {end} ({(end-start).days+1} days)")
    print("="*55)

    # Get cookie
    if args.cookie_file:
        with open(args.cookie_file, 'r', encoding='utf-8') as cf:
            cookie = cf.read().strip()
        print(f"[1/4] Cookie loaded from file ({len(cookie)} chars).")
    elif args.cookie:
        cookie = args.cookie
        print("[1/4] Cookie provided.")
    else:
        raise ValueError("Provide --cookie or --cookie-file")

    if args.debug:
        print("\n[DEBUG] Testing API...")
        session = make_session(cookie)
        epoch = calendar.timegm((today.year, today.month, today.day, 0, 0, 0))
        url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
               f"?studioID={fac['studio_id']}&isLibAsync=true&isJson=true"
               f"&startDate={epoch}&endDate={epoch}&view=day&tabID={fac['tab_id']}")
        r = session.get(url, timeout=30)
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text[:300]!r}")
        return

    rows     = collect(fac, cookie, start, end)
    if not rows:
        print("WARNING: No rows. Check cookie or date range.")
        return
    csv_path = save_csv(rows, args.facility)
    if not args.no_upload:
        upload(fac, csv_path)
    print(f"\nDone. {len(rows)} records.")

if __name__ == "__main__":
    main()