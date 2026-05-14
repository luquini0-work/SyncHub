"""
Infinite Hitting Sync — Humble & Sugar Land
=============================================
Uses DailyStaffSchedule API with session cookie.
Cookie obtained manually from DevTools → GetTokens request.

Run:
  python infinite_hitting_sync.py humble    --cookie-file cookie_humble.txt
  python infinite_hitting_sync.py sugarland --cookie-file cookie_sugarland.txt
  python infinite_hitting_sync.py humble    --cookie-file cookie_humble.txt --no-upload
"""

import os, csv, datetime, argparse, requests, calendar
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FACILITIES = {
    "humble": {
        "name":      "Infinite Hitting - Humble",
        "studio_id": "5734614",
        "tab_id":    "9",
        "cc_id":     "2246",
        "cc_user":   "localloginformaint.e.nan.c.e19.94.0@gmail.com",
        "cc_pass":   "%vDzoSCSBA$BQcu%25KV4pqceDOJ*5",
        "days":      30,
        "resource_map": {
            "4": "Evaluations Humble",
            "7": "Cage Rental 1",
        },
    },
    "sugarland": {
        "name":      "Infinite Hitting - Sugar Land",
        "studio_id": "5738940",
        "tab_id":    "9",
        "cc_id":     "2245",
        "cc_user":   "localloginformaint.e.nan.c.e19.940@gmail.com",
        "cc_pass":   "6v7gMWQm07q1r5mYr5%nDpCdT5IWRI",
        "days":      30,
        "resource_map": {
            "100000014": "Cage Rental 2",
            "5":         "Sugarland Evaluations",
            "4":         "Cage Rental 1",
            "100000009": "Automatic Pitching Rental",
        },
    },
}

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

def epoch_to_time(epoch_seconds):
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def minutes_to_time(base_epoch, minutes):
    dt = datetime.datetime.fromtimestamp(base_epoch + minutes * 60, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def parse_payload(payload, resource_map):
    rows = []
    for day_obj in payload:
        day_epoch = day_obj.get("Day", 0)
        day_date  = datetime.datetime.fromtimestamp(day_epoch, tz=datetime.timezone.utc).date()
        staff_id  = str(int(day_obj.get("StaffID", 0)))
        court     = resource_map.get(staff_id, f"Staff {staff_id}")
        date_str  = day_date.strftime("%Y-%m-%d")
        for appt in day_obj.get("Appointments") or []:
            rows.append({"Date": date_str, "Start Time": epoch_to_time(appt["Start"]),
                         "End Time": epoch_to_time(appt["End"]), "Court": court})
        for unav in day_obj.get("Unavailabilities") or []:
            rows.append({"Date": date_str, "Start Time": minutes_to_time(day_epoch, unav["StartTime"]),
                         "End Time": minutes_to_time(day_epoch, unav["EndTime"]), "Court": court})
    return rows

def collect(fac, cookie, start_date, end_date):
    num_days = (end_date - start_date).days + 1
    print(f"[2/4] Collecting {num_days} days ({start_date} → {end_date})...")
    session = make_session(cookie)

    epoch_start = calendar.timegm((start_date.year, start_date.month, start_date.day, 0, 0, 0))
    epoch_end   = calendar.timegm((end_date.year,   end_date.month,   end_date.day,   0, 0, 0))
    url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
           f"?studioID={fac['studio_id']}&isLibAsync=true&isJson=true"
           f"&startDate={epoch_start}&endDate={epoch_end}&tabID={fac['tab_id']}")
    print(f"      Fetching full range in one request...")
    r = session.get(url, timeout=60)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
    rows = parse_payload(r.json().get("json") or [], fac["resource_map"])
    days_found = len(set(r['Date'] for r in rows))
    print(f"      Total: {len(rows)} rows across {days_found} days.")
    return rows

def save_csv(rows, name):
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"infinite_{name}_output_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date","Start Time","End Time","Court"])
        w.writeheader(); w.writerows(rows)
    print(f"[3/4] CSV: {path} ({len(rows)} rows)")
    if rows: print(f"      Sample: {rows[0]}")
    return path

def upload(fac, csv_path):
    if not fac["cc_id"]:
        print("[4/4] Skipping upload — cc_id not set.")
        return
    print(f"[4/4] Uploading to CatchCorner ({fac['cc_id']})...")
    h = {"Accept":"application/json, text/plain, */*","Content-Type":"application/json",
         "Origin":"https://cc-stage-corporate.azurewebsites.net",
         "Referer":"https://cc-stage-corporate.azurewebsites.net/",
         "User-Agent":"Mozilla/5.0","x-cc-platform":"1"}
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("facility", choices=["humble","sugarland"])
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cookie-file")
    parser.add_argument("--cookie")
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

    if args.cookie_file:
        with open(args.cookie_file, 'r', encoding='utf-8') as cf:
            cookie = cf.read().strip()
        print(f"[1/4] Cookie loaded ({len(cookie)} chars).")
    elif args.cookie:
        cookie = args.cookie
        print("[1/4] Cookie provided.")
    else:
        raise ValueError("Provide --cookie or --cookie-file")

    if args.debug:
        session = make_session(cookie)
        epoch = calendar.timegm((today.year, today.month, today.day, 0, 0, 0))
        url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
               f"?studioID={fac['studio_id']}&isLibAsync=true&isJson=true"
               f"&startDate={epoch}&endDate={epoch}&tabID={fac['tab_id']}")
        r = session.get(url, timeout=30)
        print(f"Status: {r.status_code} | Response: {r.text[:500]!r}")
        return

    rows = collect(fac, cookie, start, end)
    if not rows:
        print("WARNING: No rows collected. Saving empty CSV anyway.")
    csv_path = save_csv(rows, args.facility)
    if not args.no_upload:
        upload(fac, csv_path)
    print(f"\nDone. {len(rows)} records.")

if __name__ == "__main__":
    main()