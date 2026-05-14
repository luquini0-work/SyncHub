"""
BreakAway Speed Sports Training — Sync script
==============================================
Uses Selenium to automate the manual JS console workflow:

  1. Login Mindbody → search "15652" → click Visita
  2. Enter credentials on signin page
  3. Navigate to Cage Schedule calendar
  4. Switch to the correct iframe/frame context
  5. Run clearData() JS to reset localStorage
  6. Run collectData() JS in a loop for each day (auto-advances date)
  7. Run exportCSV() JS to get the data out
  8. Format and save as CSV
  9. Upload to CatchCorner

Run:
  python breakaway_sync.py
  python breakaway_sync.py --start 2026-05-09 --end 2026-07-09
  python breakaway_sync.py --no-upload
"""

import os
import re
import csv
import sys
import json
import time
import datetime
import argparse
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(facility_key: str = "breakaway") -> dict:
    """Load credentials from config.json in the same folder as this script."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config.json not found at {config_path}")
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    facility = cfg["facilities"][facility_key]
    cc_account_key = facility["cc_account"]
    cc = cfg["catchcorner_accounts"][cc_account_key]
    return {
        "mb_email":        facility["mb_email"],
        "mb_password":     facility["mb_password"],
        "mb_business_id":  facility["mb_business_id"],
        "cc_username":     cc["username"],
        "cc_password":     cc["password"],
        "cc_facility":     facility["cc_facility_id"],
        "cc_access_from":  cc["access_from"],
        "sync_days":       facility.get("sync_days_forward", 60),
    }

_CFG           = load_config()
MB_EMAIL       = _CFG["mb_email"]
MB_PASSWORD    = _CFG["mb_password"]
MB_BUSINESS_ID = _CFG["mb_business_id"]
CC_USERNAME    = _CFG["cc_username"]
CC_PASSWORD    = _CFG["cc_password"]
CC_FACILITY    = _CFG["cc_facility"]
CC_ACCESS_FROM = _CFG["cc_access_from"]

# ── JS snippets (extracted from the docx) ─────────────────────────────────────

JS_CLEAR = "function clearData(){localStorage.removeItem('collectedEvents')}clearData()"

JS_COLLECT = """
(function collectData() {
    let e = JSON.parse(localStorage.getItem('collectedEvents')) || [];
    let t = Array.from(document.querySelectorAll('#resource-schedule th.whiteHeader.center'));
    let r = t.map(h => h.textContent.trim());
    let l = document.getElementById('cur-date-long-edit') || document.getElementById('txtDate');
    let n = l ? l.value : null;
    let o = new Date(n);
    let p = x => String(x).padStart(2, '0');
    let u = [p(o.getMonth() + 1), p(o.getDate()), o.getFullYear()].join('/');

    function f(x, s) {
        let [a, b] = x.split(':');
        let h = Number(a);
        s = s.toLowerCase();
        if ('pm' === s && h < 12) h += 12;
        else if ('am' === s && h === 12) h = 0;
        let d = new Date;
        d.setHours(h, Number(b), 0, 0);
        return d.toLocaleTimeString('en-US', {hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit'});
    }

    document.querySelectorAll('#resource-schedule .resourceItem').forEach(c => {
        let d = c.querySelector('div.center');
        if (!d) return;
        let [x1, x2] = d.textContent.replace(/\\u00A0/g, ' ').trim().split(/\\s*-\\s*/);
        let row = c.parentElement;
        let s = (row.querySelector('.timeLeft div')?.textContent.replace(/\\u00A0/g, ' ').trim().split(' ')[1] || 'am');
        let st = f(x1, s);
        let et = f(x2, s);
        let cells = Array.from(row.querySelectorAll('.resourceItem, .scheduleRoomCell'));
        let idx = cells.indexOf(c);
        let g = r[idx] || `Col ${idx}`;
        e.push({Date: u, StartTime: st, EndTime: et, Court: g});
    });

    localStorage.setItem('collectedEvents', JSON.stringify(e));

    // Auto-advance to next day
    let nextBtn = document.getElementById('day-arrow-r');
    if (nextBtn) nextBtn.click();

    return e.length;
})()
"""

JS_GET_DATA = "return JSON.parse(localStorage.getItem('collectedEvents') || '[]')"

JS_GET_DATE = """
return (document.getElementById('cur-date-long-edit') || document.getElementById('txtDate'))?.value || null
"""


# ── Browser ────────────────────────────────────────────────────────────────────

def get_driver(download_dir: str = None) -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service()
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for(driver, by, value, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


# ── Login ──────────────────────────────────────────────────────────────────────

def login_mindbody(driver, download_dir: str):
    """
    Login flow:
      /launch → search business → Visita → signin SPA
      → Cash Register "Continue" → Dashboard
    """
    print("      Opening /launch...")
    driver.get("https://clients.mindbodyonline.com/launch")
    time.sleep(3)

    # Search business by ID
    search_el = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='search']"))
    )
    print(f"      Searching for business ID {MB_BUSINESS_ID}...")
    search_el.clear()
    search_el.send_keys(MB_BUSINESS_ID)

    buscar_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Buscar') or contains(text(),'Search')]"))
    )
    buscar_btn.click()
    time.sleep(3)

    # Click Visita
    visita_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Visita') or contains(text(),'Visit')]"))
    )
    driver.execute_script("arguments[0].click();", visita_btn)
    time.sleep(4)
    print(f"      Redirected to signin...")

    # Wait for SPA to render (React app)
    time.sleep(6)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
    )

    # Enter credentials
    username_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    print("      Entering credentials...")
    username_el.clear()
    username_el.send_keys(MB_EMAIL)

    pwd_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    pwd_el.clear()
    pwd_el.send_keys(MB_PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("      Credentials submitted, waiting...")
    time.sleep(5)
    print(f"      Post-login URL: {driver.current_url[:80]}...")

    # Handle "Select Cash Register" interstitial — click Continue
    try:
        continue_btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH,
                "//input[@value='Continue'] | //button[contains(text(),'Continue')]"
            ))
        )
        print("      Cash Register screen detected — clicking Continue...")
        continue_btn.click()
        time.sleep(4)
        print(f"      Post-continue URL: {driver.current_url[:80]}...")
    except Exception:
        print("      No Cash Register screen — continuing.")

    driver.save_screenshot(os.path.join(download_dir, "step1_after_login.png"))

    if "signin" in driver.current_url.lower():
        raise RuntimeError("Login failed — still on signin page.")


# ── Collect data via JS ────────────────────────────────────────────────────────

def collect_data(driver, start_date: datetime.date, end_date: datetime.date, download_dir: str) -> list[dict]:
    """
    Navigate to Cage Schedule, switch into main_resrc.asp iframe,
    run JS collector for each day (JS auto-advances date via day-arrow-r).
    """
    # ── Step 1: Click "Cage Schedule" in the sidebar ──────────────────────────
    print("[2/5] Clicking Cage Schedule in sidebar...")
    try:
        cage_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                "//a[normalize-space()='Cage Schedule'] "
                "| //span[normalize-space()='Cage Schedule'] "
                "| //*[contains(@class,'nav') and contains(text(),'Cage Schedule')]"
            ))
        )
        driver.execute_script("arguments[0].click();", cage_link)
        print(f"      Clicked Cage Schedule link.")
        time.sleep(5)
    except Exception as e:
        print(f"      Could not find sidebar link ({e})")
        print("      Trying direct URL...")
        driver.get("https://clients.mindbodyonline.com/ASP/main_resrc.asp")
        time.sleep(5)

    driver.save_screenshot(os.path.join(download_dir, "step2_cage_schedule.png"))
    print(f"      URL after Cage Schedule: {driver.current_url[:80]}...")

    # ── Step 2: Switch into the calendar iframe (main_resrc.asp) ─────────────
    # The docx says to select "parent (main_resrc.asp)" in DevTools console
    print("[3/5] Switching to calendar iframe...")
    calendar_frame = _switch_to_calendar_frame(driver)
    print(f"      Frame: {calendar_frame}")

    driver.save_screenshot(os.path.join(download_dir, "step3_in_frame.png"))

    # ── Step 3: Navigate calendar to start_date ───────────────────────────────
    print(f"      Setting start date to {start_date}...")
    date_str = start_date.strftime("%m/%d/%Y")
    date_set = False
    for field_id in ("cur-date-long-edit", "txtDate"):
        try:
            el = driver.find_element(By.ID, field_id)
            driver.execute_script(f"arguments[0].value = '{date_str}';", el)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", el)
            driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", el)
            print(f"      Date set via #{field_id}: {date_str}")
            time.sleep(3)
            date_set = True
            break
        except Exception:
            pass

    if not date_set:
        print(f"      WARNING: Could not set date — will collect from current date.")

    driver.save_screenshot(os.path.join(download_dir, "step4_date_set.png"))

    # ── Step 4: Clear localStorage and collect ────────────────────────────────
    print("[4/5] Clearing previous data...")
    driver.execute_script(JS_CLEAR)
    time.sleep(0.5)

    num_days = (end_date - start_date).days + 1
    print(f"      Collecting {num_days} days ({start_date} → {end_date})...")

    for day_idx in range(num_days):
        target = start_date + datetime.timedelta(days=day_idx)
        try:
            count = driver.execute_script(JS_COLLECT)
            print(f"      Day {day_idx + 1}/{num_days} ({target}) — {count} records so far")
        except Exception as e:
            print(f"      Day {day_idx + 1}/{num_days} ({target}) — JS error: {e}")
        time.sleep(1.5)  # wait for calendar to advance to next day

    # ── Step 5: Read collected data ───────────────────────────────────────────
    raw_data = driver.execute_script(JS_GET_DATA)
    print(f"      Collected {len(raw_data)} raw booking records.")
    return raw_data


def _switch_to_calendar_frame(driver) -> str:
    """
    Switch Selenium into the iframe that contains the Mindbody resource calendar.
    The manual process uses 'parent (main_resrc.asp)' in DevTools console dropdown.

    Strategy:
      1. Look for iframe whose src contains 'resrc' or 'resource'
      2. Look for iframe by name 'portal' (same as Academy USA)
      3. Look for any iframe that contains #resource-schedule
      4. Fall back to main document
    """
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"      Found {len(iframes)} iframe(s) on page")

    for iframe in iframes:
        src  = (iframe.get_attribute("src")  or "").lower()
        name = (iframe.get_attribute("name") or "").lower()
        iid  = (iframe.get_attribute("id")   or "").lower()
        print(f"        iframe: id={iid!r} name={name!r} src={src[:60]!r}")

        if any(k in src or k in name or k in iid for k in ("resrc", "resource", "portal", "calendar")):
            try:
                driver.switch_to.frame(iframe)
                # Verify the calendar is inside
                time.sleep(1)
                if driver.find_elements(By.ID, "resource-schedule") or                    driver.find_elements(By.ID, "cur-date-long-edit") or                    driver.find_elements(By.ID, "txtDate"):
                    return f"iframe:{src[:50]}"
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()

    # Try ALL iframes looking for the calendar elements
    for idx, iframe in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            time.sleep(0.5)
            if driver.find_elements(By.ID, "resource-schedule") or                driver.find_elements(By.ID, "cur-date-long-edit") or                driver.find_elements(By.ID, "txtDate"):
                src = iframe.get_attribute("src") or f"iframe_{idx}"
                print(f"      Found calendar in iframe #{idx}: {src[:60]}")
                return f"iframe_{idx}:{src[:40]}"
        except Exception:
            pass

    # Last resort: try switching by name "portal"
    try:
        driver.switch_to.default_content()
        driver.switch_to.frame("portal")
        print("      Switched to frame by name 'portal'")
        return "frame:portal"
    except Exception:
        pass

    driver.switch_to.default_content()
    print("      WARNING: No calendar frame found — running JS in main document")
    return "main_document"


# ── Transform & save ───────────────────────────────────────────────────────────

def _fmt_time_from_locale(time_str: str) -> str:
    """
    The JS produces times like '08:00:00 AM' (toLocaleTimeString).
    CatchCorner wants 'hh:mm:ss tt' → '10:00:00 AM'.
    """
    time_str = str(time_str).strip()
    try:
        # Try parsing with seconds: "08:00:00 AM"
        t = datetime.datetime.strptime(time_str, "%I:%M:%S %p")
    except ValueError:
        try:
            # Try without seconds: "08:00 AM"
            t = datetime.datetime.strptime(time_str, "%I:%M %p")
        except ValueError:
            return time_str
    # Output: hh:mm:ss tt (zero-padded, with seconds)
    return t.strftime("%I:%M:%S %p")


def _fmt_date(date_str: str) -> str:
    """Convert MM/DD/YYYY (JS output) to MM/dd/yyyy for CatchCorner (already correct)."""
    return date_str  # JS already outputs MM/DD/YYYY


def save_csv(raw_data: list[dict], output_path: str = None) -> str:
    """
    Transform raw JS data to CatchCorner CSV format.

    JS output fields: Date (MM/DD/YYYY), StartTime, EndTime, Court
    CC expected:      Date (MM/dd/yyyy), Start (h:mm AM), End (h:mm AM), Resource
    """
    if not output_path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"breakaway_output_{ts}.csv"

    rows = []
    for r in raw_data:
        rows.append({
            "Date":     _fmt_date(r.get("Date", "")),
            "Start":    _fmt_time_from_locale(r.get("StartTime", "")),
            "End":      _fmt_time_from_locale(r.get("EndTime", "")),
            "Resource": r.get("Court", ""),
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Start", "End", "Resource"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[5b] CSV saved: {output_path} ({len(rows)} rows)")
    if rows:
        print(f"      Sample: {rows[0]}")
    return output_path


# ── CatchCorner upload ─────────────────────────────────────────────────────────

def login_cc_corporate(username: str, password: str, access_from: str) -> str:
    login_url = "https://www.catchcorner.com/api/shared/authentication/Login"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-cc-platform": "1",
    }
    data = {"accessFrom": access_from, "email": username, "loginPlatform": 1, "password": password}
    res = requests.Session().post(login_url, json=data, headers=headers, timeout=15)
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise ValueError("No access token received — check CatchCorner credentials.")
    print("      CatchCorner login OK.")
    return token


def upload_csv_corporate_api(access_token: str, corporate_id: str, csv_path: str):
    file_upload_url = "https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-cc-platform": "1",
        "Authorization": f"Bearer {access_token}",
    }
    with open(csv_path, "rb") as f:
        files = {"file": (csv_path, f, "multipart/form-data")}
        resp = requests.Session().post(
            f"{file_upload_url}/{corporate_id}/0",
            files=files, headers=headers, timeout=60,
        )
    if not resp.ok:
        print(f"      Upload failed: {resp.status_code}")
        print(f"      Response body: {resp.text[:500]}")
        resp.raise_for_status()
    print("      CSV uploaded to CatchCorner successfully.")


def upload_to_catchcorner(csv_path: str):
    print("[5c] Logging in to CatchCorner...")
    token = login_cc_corporate(CC_USERNAME, CC_PASSWORD, CC_ACCESS_FROM)
    print(f"[5d] Uploading to CatchCorner (facility ID: {CC_FACILITY})...")
    upload_csv_corporate_api(token, CC_FACILITY, csv_path)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BreakAway Speed Sports Training sync")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--end",   help="End date YYYY-MM-DD (default: +60 days)")
    parser.add_argument("--output-file", help="Output CSV path (optional)")
    parser.add_argument("--no-upload", action="store_true", help="Skip CatchCorner upload")
    args = parser.parse_args()

    today      = datetime.date.today()
    start_date = datetime.date.fromisoformat(args.start) if args.start else today
    end_date   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=_CFG["sync_days"])

    print("=" * 55)
    print("  BreakAway Speed Sports Training Sync")
    print(f"  Range: {start_date} → {end_date} ({(end_date - start_date).days + 1} days)")
    print("=" * 55)

    import tempfile
    download_dir = tempfile.mkdtemp(prefix="breakaway_")
    print(f"  Screenshots: {download_dir}")
    driver = get_driver()

    try:
        # Step 1: Login
        print("\n[1/5] Logging in to Mindbody...")
        login_mindbody(driver, download_dir)

        # Steps 2–4: Navigate to calendar and collect data via JS
        raw_data = collect_data(driver, start_date, end_date, download_dir)

        if not raw_data:
            print("WARNING: No data collected — check screenshots in", download_dir)
            return

        # Step 5: Save CSV
        csv_path = save_csv(raw_data, args.output_file)

        # Step 6: Upload
        if not args.no_upload:
            upload_to_catchcorner(csv_path)

        print()
        print(f"Done. {len(raw_data)} records synced.")
        print(f"CSV: {csv_path}")

    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        traceback.print_exc()
        driver.save_screenshot(os.path.join(download_dir, "error.png"))
        print(f"Error screenshot: {download_dir}\\error.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()