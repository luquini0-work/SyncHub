"""
Pure Soccer - Woodlands Sync
==============================
Uses DailyStaffSchedule API with session cookie — same approach as Create The Finish.
Cookie obtained manually from DevTools → GetTokens request.

Run:
  python pure_soccer_woodlands_sync.py --cookie-file cookie_puresoccer.txt
  python pure_soccer_woodlands_sync.py --cookie-file cookie_puresoccer.txt --no-upload
"""

import os, csv, datetime, argparse, requests, calendar, json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STUDIO_ID  = "629106"
TAB_ID     = "9"
SYNC_DAYS  = 200

CC_USER     = "localloginformain.te.na.n.ce1994.0@gmail.com"
CC_PASS     = "M2^QeQa7m5^h*egFDlA@AOo^5bULmv"
CC_FACILITY = "2858"

RESOURCE_MAP = {
    2043: "TOCA 5",
    2044: "Woodlands Indoor",
    2035: "Full Indoor and Outdoor Field",
    2042: "FYS Fields",
    2034: "Indoor Field 2 - Woodlands",
    2040: "KYSC Field 2",
    2037: "KYSC Fields",
    2041: "Pearland Soccer - Blue Bridge",
    2039: "PSI Classroom",
    2033: "TOCA 4",
    2036: "Training Room",
    2038: "Training Room",
    2032: "TOCA 3",
    2031: "TOCA 2",
    2030: "TOCA 1",
    2025: "Indoor Field 1",
    2029: "Indoor Field 1 - Woodlands",
    2026: "Memorial Herman Sports Park",
    2028: "Outdoor Field",
    2027: "Party Room 2",
    6:    "TOCA 1",
    7:    "TOCA 2",
    8:    "TOCA 3",
    9:    "TOCA 4",
    10:   "TOCA 5",
    11:   "TOCA 6",
    12:   "TOCA 7",
    13:   "TOCA 8",
    19:   "Full Outdoor Field",
    1020: "Full Indoor Field",
    5:    "Indoor Field 1",
    3:    "Indoor Field 2",
    14:   "Party Room 1",
    15:   "Party Room 2",
    1023: "Complete Indoor",
    2023: "Outdoor Field",
    18:   "Half Outdoor Field 2",
    17:   "Half Outdoor Field 1",
    2:    "Field 1 & 2",
    1022: "Indoor Field",
    1021: "Indoor Field",
    1019: "Indoor Field",
    4:    "The Cage",
    16:   "Outdoor Field",
    1:    "Indoor Field 1",
    268435459: "Daniel Barra Chavez (W)",
    268435461: "Ernesto Barra Chavez (W)",
    268435464: "Elijah Betancourt",
    268435458: "Noah Betancourt",
    268435576: "Outdoor Field rental",
    268435509: "Ashton Frazier (W)",
    268435513: "Brennan Huerta",
    268435462: "Brandon Lopez (W)",
    268435495: "Herbert Lopez (W)",
    268435507: "Daniel Luque",
    268435493: "Grisham Marques",
    268435638: "Jasmine Marquez (W)",
    268435473: "Rodrigo Mazariego",
    268435569: "James McBride (W)",
    268435457: "Stuart Mckenzie",
    268435616: "Javier Mestre",
    268435620: "Yukio Mishima",
    268435585: "Lucas Ordosgoitia Heenan",
    268435624: "Peter Osipchuk",
    268435625: "Gabriel Pereira",
    268435589: "Faris Qaddoura",
    268435608: "Omar Quintana (W)",
    268435623: "Matthias Rodriguez",
    268435604: "Angela Ruiz (W)",
    268435635: "Carlos Soto (W)",
    268435606: "Drew Stedman (W)",
    268435561: "Leo Urribarri",
    268435494: "Outdoor Field Rental Woodlands",
    268435617: "Gabriel Yuji Da Silva",
    # Staff IDs (100000xxx format) — from xlsx Data tab
    100000230: "Daniel Barra Chavez (W)",
    100000205: "Ernesto Barra Chavez (W)",
    100000208: "Elijah Betancourt",
    100000202: "Noah Betancourt",
    100000078: "Outdoor Field rental",
    100000135: "Ashton Frazier (W)",
    100000239: "Brennan Huerta",
    100000206: "Brandon Lopez (W)",
    100000127: "Herbert Lopez (W)",
    100000131: "Daniel Luque",
    100000125: "Grisham Marques",
    100000276: "Jasmine Marquez (W)",
    100000011: "Rodrigo Mazariego",
    100000171: "James McBride (W)",
    100000001: "Stuart Mckenzie",
    100000259: "Megan McQuiller",
    100000260: "Javier Mestre",
    100000264: "Yukio Mishima",
    100000189: "Lucas Ordosgoitia Heenan",
    100000268: "Peter Osipchuk",
    100000269: "Gabriel Pereira",
    100000225: "Faris Qaddoura",
    100000258: "Omar Quintana (W)",
    100000267: "Matthias Rodriguez",
    100000254: "Angela Ruiz (W)",
    100000275: "Carlos Soto (W)",
    100000236: "Drew Stedman (W)",
    100000003: "Everick Stoelwinder",
    100000169: "Leo Urribarri",
    100000126: "Outdoor Field Rental Woodlands",
    100000261: "Gabriel Yuji Da Silva",
    2045: "",
}


def _resolve_name(resource_id) -> str:
    if resource_id is None:
        return ""
    try:
        rid = int(resource_id)
    except (TypeError, ValueError):
        return str(resource_id)
    return RESOURCE_MAP.get(rid, "")


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


def _fmt_12h(dt) -> str:
    h = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{h:02d}:{dt.minute:02d}:{dt.second:02d} {ampm}"


def epoch_to_time(epoch_seconds):
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return _fmt_12h(dt)


def minutes_to_time(base_epoch, minutes):
    dt = datetime.datetime.fromtimestamp(base_epoch + minutes * 60, tz=datetime.timezone.utc)
    return _fmt_12h(dt)


def parse_payload(day_obj, date_str):
    """Parse one day_obj into rows. Matches Apps Script logic exactly."""
    rows = []
    day_epoch  = day_obj.get("Day", 0)
    staff_id   = day_obj.get("StaffID")
    court_name = _resolve_name(staff_id)  # '' if not in map

    # Appointments: use ResourceIDs[0] for court (same as Apps Script)
    for appt in day_obj.get("Appointments") or []:
        resource_ids = appt.get("ResourceIDs") or []
        cn = _resolve_name(resource_ids[0]) if resource_ids else ""
        rows.append({
            "Date":       date_str,
            "Start Time": epoch_to_time(appt["Start"]),
            "End Time":   epoch_to_time(appt["End"]),
            "Court":      cn,
        })

    # Unavailabilities: use StaffID for court (same as Apps Script)
    for unav in day_obj.get("Unavailabilities") or []:
        rows.append({
            "Date":       date_str,
            "Start Time": minutes_to_time(day_epoch, unav["StartTime"]),
            "End Time":   minutes_to_time(day_epoch, unav["EndTime"]),
            "Court":      court_name,
        })
    return rows


def collect(cookie, start_date, end_date):
    num_days = (end_date - start_date).days + 1
    print(f"[2/4] Collecting {num_days} days ({start_date} → {end_date})...")
    session = make_session(cookie)

    epoch_start = calendar.timegm((start_date.year, start_date.month, start_date.day, 0, 0, 0))
    epoch_end   = calendar.timegm((end_date.year,   end_date.month,   end_date.day,   0, 0, 0))
    url = (
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
        f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
        f"&startDate={epoch_start}&endDate={epoch_end}&tabID={TAB_ID}"
    )
    print("      Fetching full range in one request...")
    r = session.get(url, timeout=120)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")

    payload = r.json().get("json") or []
    all_rows = []
    for day_obj in payload:
        day_epoch = day_obj.get("Day", 0)
        day_date  = datetime.datetime.fromtimestamp(day_epoch, tz=datetime.timezone.utc).date()
        date_str  = day_date.strftime("%Y-%m-%d")
        all_rows.extend(parse_payload(day_obj, date_str))

    days_found = len(set(r["Date"] for r in all_rows))
    print(f"      Total: {len(all_rows)} rows across {days_found} days.")
    return all_rows


def save_csv(rows):
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"pure_soccer_woodlands_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Start Time", "End Time", "Court"])
        w.writeheader()
        w.writerows(rows)
    print(f"[3/4] CSV: {path} ({len(rows)} rows)")
    if rows:
        print(f"      Sample: {rows[0]}")
    return path


def upload(csv_path):
    print(f"[4/4] Uploading to CatchCorner ({CC_FACILITY})...")
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
        json={"accessFrom": "Corporate", "email": CC_USER, "loginPlatform": 1, "password": CC_PASS},
        headers=h, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise ValueError("No CC token")
    del h["Content-Type"]
    h["Authorization"] = f"Bearer {token}"
    with open(csv_path, "rb") as f:
        resp = requests.Session().post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FACILITY}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h, timeout=60)
    if not resp.ok:
        print(f"      Error {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
    print("      Uploaded OK.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cookie-file")
    parser.add_argument("--cookie")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=SYNC_DAYS)

    print("=" * 55)
    print("  Pure Soccer - Woodlands Sync")
    print(f"  Range: {start} → {end} ({(end - start).days + 1} days)")
    print("=" * 55)

    if args.cookie_file:
        with open(args.cookie_file, "r", encoding="utf-8") as cf:
            cookie = cf.read().strip()
        print(f"[1/4] Cookie loaded ({len(cookie)} chars).")
    elif args.cookie:
        cookie = args.cookie
        print("[1/4] Cookie provided.")
    else:
        raise ValueError("Provide --cookie-file or --cookie")

    if args.debug:
        session = make_session(cookie)
        epoch = calendar.timegm((today.year, today.month, today.day, 0, 0, 0))
        url = (f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
               f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
               f"&startDate={epoch}&endDate={epoch}&tabID={TAB_ID}")
        r = session.get(url, timeout=30)
        print(f"Status: {r.status_code} | Response: {r.text[:300]!r}")
        return

    rows = collect(cookie, start, end)
    if not rows:
        print("WARNING: No rows. Check cookie.")
        return
    csv_path = save_csv(rows)
    if not args.no_upload:
        upload(csv_path)
    print(f"\nDone. {len(rows)} records.")


if __name__ == "__main__":
    main()