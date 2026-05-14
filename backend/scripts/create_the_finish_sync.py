"""
Create The Finish Sync
======================
Uses the DailyStaffSchedule API (same as the Google Apps Script approach)
to collect bookings and upload to CatchCorner.

The API requires a valid session cookie from Mindbody.
This script auto-logs in via Selenium to get a fresh cookie,
then calls the API directly (no browser scraping needed).

Run:
  python create_the_finish_sync.py --start 2026-05-09 --end 2026-07-09
  python create_the_finish_sync.py --start 2026-05-09 --end 2026-07-09 --no-upload
  python create_the_finish_sync.py --start 2026-05-09 --end 2026-07-09 --cookie "ASP.NET_SessionId=..."
"""

import os, csv, time, datetime, argparse, requests, json, re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ─────────────────────────────────────────────────────────────────────

STUDIO_ID   = "5723070"
TAB_ID      = "9"
MB_EMAIL    = "localloginformaint.e.na.n.c.e.19.9.40@gmail.com"
MB_PASS     = "CCorner1!"
CC_USER     = "localloginformaint.e.na.n.c.e.1.9940@gmail.com"
CC_PASS     = "SK27!72yQB0ypN3l*dGfqXNLJbrVKa"
CC_FACILITY = "2361"

# StaffID → Court name (from xlsx Data tab)
# All map to "Turf" for Create The Finish
RESOURCE_MAP = {
    "100000001": "Turf",
    "100000002": "Turf",
    "100000003": "Turf",
    "100000004": "Turf",
    "100000005": "Turf",
    "100000006": "Turf",
    "100000007": "Turf",
    "100000008": "Turf",
    "100000009": "Turf",
    "100000010": "Turf",
    "100000011": "Turf",
    "100000012": "Turf",
    "100000013": "Turf",
    "100000014": "Turf",
    "100000015": "Turf",
    "100000016": "Turf",
    "100000017": "Turf",
    "100000018": "Turf",
    "100000019": "Turf",
    "100000020": "Turf",
    "100000021": "Turf",
    "100000022": "Turf",
    "100000023": "Turf",
    "100000024": "Turf",
    "100000025": "Turf",
}
DEFAULT_COURT = "Turf"  # fallback for any unmapped staff ID

# ── Login to get cookie ────────────────────────────────────────────────────────

def get_cookie_via_selenium():
    """Login via Selenium and return cookie string."""
    print("  Getting session cookie via Selenium...")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        svc = Service(ChromeDriverManager().install())
    except Exception:
        svc = Service()

    driver = webdriver.Chrome(service=svc, options=opts)

    try:
        driver.get("https://clients.mindbodyonline.com/launch")
        time.sleep(3)

        # Search for studio
        search = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'],input[type='search']"))
        )
        search.send_keys(STUDIO_ID)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Buscar') or contains(.,'Search')]"))
        ).click()
        time.sleep(3)

        visita = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Visita') or contains(.,'Visit')]"))
        )
        driver.execute_script("arguments[0].click();", visita)
        time.sleep(6)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input")))

        # Login
        u = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "username")))
        u.clear(); u.send_keys(MB_EMAIL)
        p = driver.find_element(By.ID, "password")
        p.clear(); p.send_keys(MB_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(8)

        # Handle Cash Register
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Continue'] | //button[contains(.,'Continue')]"))
            ).click()
            time.sleep(4)
        except Exception:
            pass

        # Navigate to mainappointments to trigger the session
        driver.get(f"https://clients.mindbodyonline.com/app/business/mainappointments/index")
        time.sleep(4)

        # Collect all cookies
        cookies = driver.get_cookies()
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"  Got {len(cookies)} cookies.")
        return cookie_str

    finally:
        driver.quit()


# ── Fetch data from API ────────────────────────────────────────────────────────

def fetch_day(cookie, epoch_day):
    """Fetch one day's data from the DailyStaffSchedule API."""
    url = (
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
        f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
        f"&startDate={epoch_day}&endDate={epoch_day}&view=day&tabID={TAB_ID}"
    )
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Cookie": cookie,
        "Referer": "https://clients.mindbodyonline.com/mainappointments/index",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    return data


def fetch_day_session(session, epoch_day):
    """Fetch one day using a persistent session."""
    url = (
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules"
        f"?studioID={STUDIO_ID}&isLibAsync=true&isJson=true"
        f"&startDate={epoch_day}&endDate={epoch_day}&view=day&tabID={TAB_ID}"
    )
    r = session.get(url, timeout=30)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


def debug_api(cookie):
    """Test multiple API URL variants to find which one works."""
    import datetime as dt
    today = dt.date.today()
    import calendar as cal
    epoch = cal.timegm((today.year, today.month, today.day, 0, 0, 0))

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Cookie": cookie,
        "Referer": "https://clients.mindbodyonline.com/mainappointments/index",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    urls = [
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/DailyStaffSchedules?studioID={STUDIO_ID}&isLibAsync=true&isJson=true&startDate={epoch}&endDate={epoch}&view=day&tabID={TAB_ID}",
        f"https://clients.mindbodyonline.com/ASP/adm/DailyStaffSchedule/DailyStaffSchedules?studioID={STUDIO_ID}&isLibAsync=true&isJson=true&startDate={epoch}&endDate={epoch}&tabID={TAB_ID}",
        f"https://clients.mindbodyonline.com/asp/adm/adm_resrc_sched_ajax.asp?studioid={STUDIO_ID}&isLibAsync=true&isJson=true&startDate={epoch}&endDate={epoch}&tabID={TAB_ID}",
        f"https://clients.mindbodyonline.com/DailyStaffSchedule/GetDailyStaffSchedules?studioID={STUDIO_ID}&isJson=true&startDate={epoch}&endDate={epoch}&tabID={TAB_ID}",
        f"https://clients.mindbodyonline.com/mainappointments/DailyStaffSchedules?studioID={STUDIO_ID}&isLibAsync=true&isJson=true&startDate={epoch}&endDate={epoch}&tabID={TAB_ID}",
    ]

    for url in urls:
        print("  Testing: " + url[:80] + "...")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                print(f"  SUCCESS! Response: {r.text[:300]!r}")
                break
            else:
                print(f"  Body: {r.text[:100]!r}")
        except Exception as e:
            print(f"  Error: {e}")


def collect(cookie, start_date, end_date):
    """Collect all days between start and end."""
    num_days = (end_date - start_date).days + 1
    print(f"[2/4] Collecting {num_days} days ({start_date} → {end_date})...")

    if not cookie or cookie.strip() in ['', '...', '"..."', "'"]:
        raise ValueError("Invalid cookie. Paste the full cookie string from DevTools.")

    # Use a persistent session
    session = requests.Session()
    session.verify = False
    session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Cookie": cookie,
        "Referer": "https://clients.mindbodyonline.com/mainappointments/index",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })

    all_rows = []
    current = start_date
    while current <= end_date:
        # Use UTC midnight (same as Apps Script: new Date(startDate).getTime() / 1000)
        import calendar
        epoch = calendar.timegm((current.year, current.month, current.day, 0, 0, 0))
        try:
            data = fetch_day_session(session, epoch)
            day_rows = transform_day(data, current)
            all_rows.extend(day_rows)
            if day_rows:
                print(f"      {current}: {len(day_rows)} rows")
        except Exception as e:
            print(f"      {current}: ERROR - {e}")
        current += datetime.timedelta(days=1)

    print(f"      Total: {len(all_rows)} rows collected.")
    return all_rows


# ── Transform ──────────────────────────────────────────────────────────────────

def epoch_to_time(epoch_seconds):
    """Convert epoch to time string — no timezone conversion (UTC as-is, matches Mindbody display)."""
    dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def epoch_day_to_date(epoch_seconds):
    """Convert epoch day timestamp to yyyy-MM-dd string (UTC)."""
    dt = datetime.datetime.fromtimestamp(epoch_seconds)
    return dt.strftime("%Y-%m-%d")

def minutes_to_time(base_epoch, minutes):
    """Convert base epoch + offset minutes to time string (UTC, no conversion)."""
    dt = datetime.datetime.fromtimestamp(base_epoch + minutes * 60, tz=datetime.timezone.utc)
    return dt.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM"

def transform_day(data, date):
    """Transform one day's API response into CSV rows."""
    rows = []
    payload = data.get("json") or []
    if payload is None:
        return rows
    date_str = date.strftime("%Y-%m-%d")

    for day_obj in payload:
        staff_id = str(int(day_obj.get("StaffID", 0)))
        court = RESOURCE_MAP.get(staff_id, DEFAULT_COURT)
        day_epoch = day_obj.get("Day", 0)

        # Appointments
        for appt in day_obj.get("Appointments") or []:
            start_t = epoch_to_time(appt["Start"])
            end_t   = epoch_to_time(appt["End"])
            rows.append({"Date": date_str, "Start Time": start_t, "End Time": end_t, "Court": court})

        # Unavailabilities (blocks)
        for unav in day_obj.get("Unavailabilities") or []:
            start_t = minutes_to_time(day_epoch, unav["StartTime"])
            end_t   = minutes_to_time(day_epoch, unav["EndTime"])
            rows.append({"Date": date_str, "Start Time": start_t, "End Time": end_t, "Court": court})

    return rows


# ── Save CSV ───────────────────────────────────────────────────────────────────

def save_csv(rows):
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"create_the_finish_output_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date","Start Time","End Time","Court"])
        w.writeheader(); w.writerows(rows)
    print(f"[3/4] CSV saved: {path} ({len(rows)} rows)")
    if rows: print(f"      Sample: {rows[0]}")
    return path


# ── Upload to CatchCorner ──────────────────────────────────────────────────────

def upload(csv_path):
    print(f"[4/4] Uploading to CatchCorner (facility {CC_FACILITY})...")
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
        json={"accessFrom":"Corporate","email":CC_USER,"loginPlatform":1,"password":CC_PASS},
        headers=h, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token: raise ValueError("No CC token received")

    del h["Content-Type"]
    h["Authorization"] = f"Bearer {token}"

    with open(csv_path, "rb") as f:
        resp = requests.Session().post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FACILITY}/0",
            files={"file": (os.path.basename(csv_path), f, "multipart/form-data")},
            headers=h, timeout=60)

    if not resp.ok:
        print(f"      Upload error {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    print("      Uploaded OK.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cookie", help="Paste cookie string directly to skip login")
    parser.add_argument("--cookie-file", help="Path to text file containing the cookie string")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Test API and print raw response")
    args = parser.parse_args()

    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=250)

    print("="*55)
    print("  Create The Finish Sync")
    print(f"  Range: {start} → {end} ({(end-start).days+1} days)")
    print("="*55)

    # Get cookie
    if args.cookie_file:
        with open(args.cookie_file, 'r', encoding='utf-8') as cf:
            cookie = cf.read().strip()
        print(f"[1/4] Cookie loaded from file ({len(cookie)} chars).")
    elif args.cookie:
        cookie = args.cookie
        print("[1/4] Using provided cookie.")
    else:
        print("[1/4] Logging in to get session cookie...")
        cookie = get_cookie_via_selenium()

    # Debug mode
    if args.debug:
        print("[DEBUG] Testing API with today date...")
        debug_api(cookie)
        return
        return

    # Collect
    rows = collect(cookie, start, end)

    if not rows:
        print("WARNING: No rows collected. Cookie may be expired or invalid.")
        print("         Try running with --cookie 'paste_cookie_here'")
        return

    # Save
    csv_path = save_csv(rows)

    # Upload
    if not args.no_upload:
        upload(csv_path)

    print(f"\nDone. {len(rows)} records. CSV: {csv_path}")


if __name__ == "__main__":
    main()