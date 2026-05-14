"""
Academy USA — Full sync script
==============================
1. Login to Mindbody → navigate to ScheduleAtAGlance report
2. Set date range → Export to Excel → download
3. Transform Input data into Output format (replicates Excel logic)
4. Save as CSV
5. Upload CSV to CatchCorner

Transformation logic (mirrors the Excel Convert/Output sheets):
  - HC bookings: Notes contains "HC" and NOT "FC"
      Resource = "{court_number} {COLOR}"  e.g. "1 BLUE", "2 RED"
  - FC bookings: Notes contains "FC" OR does not contain "HC"
      Resource = "FC {COLOR}"              e.g. "FC YELLOW", "FC BLUE"
  - Sorted by Date ASC, Start ASC

Run:
  python academy_usa_sync.py
  python academy_usa_sync.py --start 2026-05-01 --end 2026-05-31
  python academy_usa_sync.py --input-file schedule_export.xlsx  # skip download
"""

import os
import re
import csv
import glob
import time
import argparse
import tempfile
import datetime
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Config ────────────────────────────────────────────────────────────────────

MB_REPORT_URL = (
    "https://clients.mindbodyonline.com/app/business/Report/Staff"
    "/ScheduleAtAGlance/Generate?reportID=undefined"
)

def load_config(facility_key: str = "academy_usa") -> dict:
    """Load credentials from config.json in the same folder as this script."""
    import json
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config.json not found at {config_path}")
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    facility = cfg["facilities"][facility_key]
    cc_account_key = facility["cc_account"]
    cc = cfg["catchcorner_accounts"][cc_account_key]
    return {
        "mb_email":       facility["mb_email"],
        "mb_password":    facility["mb_password"],
        "mb_business_id": facility["mb_business_id"],
        "cc_username":    cc["username"],
        "cc_password":    cc["password"],
        "cc_facility":    facility["cc_facility_id"],
        "cc_access_from": cc["access_from"],
    }

# Load config at startup
_CFG = load_config()
MB_EMAIL       = _CFG["mb_email"]
MB_PASSWORD    = _CFG["mb_password"]
MB_BUSINESS_ID = _CFG["mb_business_id"]
CC_USERNAME    = _CFG["cc_username"]
CC_PASSWORD    = _CFG["cc_password"]
CC_FACILITY    = _CFG["cc_facility"]
CC_ACCESS_FROM = _CFG["cc_access_from"]


# ── Step 1: Headless Chrome ───────────────────────────────────────────────────

def get_driver(download_dir: str) -> webdriver.Chrome:
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
    opts.add_experimental_option("prefs", {
        "download.default_directory":   download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade":   True,
        "safebrowsing.enabled":         True,
    })
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


def wait_clickable(driver, by, value, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


# ── Step 2: Download ScheduleAtAGlance export ─────────────────────────────────

def download_schedule_excel(start_date: datetime.date, end_date: datetime.date) -> str:
    """
    Full Mindbody login + ScheduleAtAGlance export flow for Academy USA.

    Login flow:
      1. /launch → search "610481" → click "Visita"
      2. signin page (SPA) → id="username" + id="password" → submit
      3. Navigate to ScheduleAtAGlance report

    Export flow:
      4. Set Start date / End date fields
      5. Try Export to Excel directly (no GO needed)
         If no download after 15s → click GO first, wait, then Export
      6. Return path to downloaded .xls/.xlsx file
    """
    download_dir = tempfile.mkdtemp(prefix="academy_usa_")
    print(f"[1/5] Starting Mindbody login... (screenshots: {download_dir})")
    driver = get_driver(download_dir)

    try:
        # ── STEP 1: Search business by ID and click Visita ────────────────────
        print("      Opening /launch...")
        driver.get("https://clients.mindbodyonline.com/launch")
        time.sleep(3)

        search_el = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='search']"))
        )
        print(f"      Typing business ID {MB_BUSINESS_ID}...")
        search_el.clear()
        search_el.send_keys(MB_BUSINESS_ID)

        buscar_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Buscar') or contains(text(),'Search')]"))
        )
        buscar_btn.click()
        time.sleep(3)

        visita_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Visita') or contains(text(),'Visit')]"))
        )
        driver.execute_script("arguments[0].click();", visita_btn)
        time.sleep(4)
        print(f"      Redirected to signin: {driver.current_url[:60]}...")

        # ── STEP 2: Login (SPA — wait for JS render) ──────────────────────────
        print("      Waiting for signin SPA to render...")
        time.sleep(6)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
        )

        # Username field (id="username", type="text")
        username_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("      Entering email...")
        username_el.clear()
        username_el.send_keys(MB_EMAIL)

        # Password field (id="password")
        pwd_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("      Entering password...")
        pwd_el.clear()
        pwd_el.send_keys(MB_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("      Credentials submitted, waiting for dashboard...")
        time.sleep(6)
        driver.save_screenshot(os.path.join(download_dir, "step2_after_login.png"))
        print(f"      Post-login URL: {driver.current_url[:80]}...")

        if "signin" in driver.current_url.lower():
            driver.save_screenshot(os.path.join(download_dir, "step2_FAILED_still_on_signin.png"))
            raise RuntimeError(f"Login failed — still on signin page. Check credentials.")

        # ── STEP 3: Navigate to ScheduleAtAGlance ─────────────────────────────
        print(f"[2/5] Navigating to Schedule at a Glance report...")
        driver.get(MB_REPORT_URL)
        time.sleep(5)
        driver.save_screenshot(os.path.join(download_dir, "step3_report.png"))
        print(f"      Report URL: {driver.current_url[:80]}...")

        if "signin" in driver.current_url.lower() or "login" in driver.current_url.lower():
            raise RuntimeError(f"Not authenticated — redirected back to login.")

        # ── STEP 4: Set date range ─────────────────────────────────────────────
        print(f"[3/5] Setting dates: {start_date.strftime('%m/%d/%Y')} → {end_date.strftime('%m/%d/%Y')}")

        # Report content loads inside iframe id="portal" — switch into it by name
        print("      Waiting for iframe id='portal'...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "portal"))
        )
        time.sleep(2)  # let iframe content render

        # Switch into the portal iframe by ID
        driver.switch_to.frame("portal")
        print("      Switched into iframe 'portal'")

        # Wait for date fields inside iframe
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "requiredtxtDateStart"))
        )

        # Dump all inputs for info
        inputs = driver.find_elements(By.CSS_SELECTOR, "input")
        print(f"      Inputs inside iframe ({len(inputs)}):")
        for inp in inputs:
            print(f"        id={inp.get_attribute('id')!r:30} name={inp.get_attribute('name')!r:25} value={inp.get_attribute('value')!r}")

        # Set Start date
        start_el = driver.find_element(By.ID, "requiredtxtDateStart")
        driver.execute_script("arguments[0].value = '';", start_el)
        start_el.clear()
        start_el.send_keys(start_date.strftime("%m/%d/%Y"))
        print(f"      Start date set: {start_date.strftime('%m/%d/%Y')}")

        # Set End date
        end_el = driver.find_element(By.ID, "requiredtxtDateEnd")
        driver.execute_script("arguments[0].value = '';", end_el)
        end_el.clear()
        end_el.send_keys(end_date.strftime("%m/%d/%Y"))
        print(f"      End date set: {end_date.strftime('%m/%d/%Y')}")

        time.sleep(1)
        driver.save_screenshot(os.path.join(download_dir, "step4_dates_set.png"))

        # ── STEP 5: Export to Excel ────────────────────────────────────────────
        # Note: we are still in the iframe context from Step 4
        # Strategy A: Click GO first, wait for report, then Export to Excel
        print("[4/5] Clicking GO to generate report...")
        try:
            go_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//input[@value='Go!'] | //input[@value='Go'] "
                    "| //button[normalize-space()='Go!'] | //button[normalize-space()='Go'] "
                    "| //a[normalize-space()='Go!']"
                ))
            )
            go_btn.click()
            print("      GO clicked, waiting for report to load...")
            time.sleep(10)
            driver.save_screenshot(os.path.join(download_dir, "step5_after_go.png"))
        except Exception as e:
            print(f"      GO button not found or click failed: {e}")

        # Now click Export to Excel
        print("[5/5] Clicking Export to Excel...")
        export_btn = _find_export_button(driver)
        export_btn.click()
        xlsx_path = _wait_for_download(download_dir, timeout=45)

        if not xlsx_path:
            driver.save_screenshot(os.path.join(download_dir, "step5_FAILED_no_download.png"))
            raise FileNotFoundError(
                f"Excel export did not download.\n"
                f"Screenshots: {download_dir}"
            )

        print(f"[5/5] Downloaded: {xlsx_path}")
        return xlsx_path

    finally:
        driver.quit()


def _set_date_field(driver, start_str: str, end_str: str):
    """Set start and end date fields in the report form."""
    # Try common field selectors for Mindbody date inputs
    for name in ("StartDate", "startDate", "start_date"):
        try:
            el = driver.find_element(By.NAME, name)
            el.clear()
            el.send_keys(start_str)
            break
        except Exception:
            pass

    for name in ("EndDate", "endDate", "end_date"):
        try:
            el = driver.find_element(By.NAME, name)
            el.clear()
            el.send_keys(end_str)
            break
        except Exception:
            pass


def _find_export_button(driver):
    """
    Find the Export to Excel button on the ScheduleAtAGlance page.
    From screenshot: appears as an XLS icon link with text "Export to Excel"
    """
    selectors = [
        # Actual element: <li id="excel-button">Export to Excel</li>
        (By.ID,    "excel-button"),
        (By.XPATH, "//li[contains(text(),'Export to Excel')]"),
        (By.XPATH, "//li[@id='excel-button']"),
        # Fallbacks
        (By.XPATH, "//a[contains(text(),'Export to Excel')]"),
        (By.XPATH, "//button[contains(text(),'Export to Excel')]"),
        (By.XPATH, "//a[normalize-space(text())='Export to Excel']"),
        (By.CSS_SELECTOR, "[class*='export-to-excel']"),
        (By.CSS_SELECTOR, "a[href*='excel' i]"),
    ]
    for by, sel in selectors:
        try:
            el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
            print(f"      Export button found: {sel}")
            return el
        except Exception:
            pass

    # Debug: dump all links on page
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"      Links on page ({len(links)}):")
    for lnk in links:
        txt = lnk.text.strip()
        href = lnk.get_attribute("href") or ""
        if txt or "xls" in href.lower() or "export" in href.lower():
            print(f"        text={txt!r:30} href={href[:60]!r}")
    raise RuntimeError("Could not find Export to Excel button.")


def _wait_for_download(directory: str, timeout: int = 45) -> str | None:
    """Poll directory for a completed xlsx/xls download."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for ext in ("*.xlsx", "*.xls"):
            matches = [
                f for f in glob.glob(os.path.join(directory, ext))
                if not f.endswith(".crdownload") and not f.endswith(".tmp")
            ]
            if matches:
                time.sleep(0.5)  # small wait to ensure write is complete
                return matches[0]
        time.sleep(1)
    return None


# ── Step 3: Transform Input → Output (Python replication of Excel logic) ──────

def transform_schedule(xlsx_path: str) -> list[dict]:
    """
    Read the downloaded ScheduleAtAGlance Excel file and apply the same
    transformation logic as the Excel Convert/Output sheets.

    Input columns used:
      A = Date
      B = Start time
      C = End time
      E = Staff  →  "1, BLUE", "2, RED", "1, YELLOW", etc.
      N = Appointment Notes  →  "HC", "FC", "FC Clinic", etc.

    Output columns:
      Date, Start, End, Resource

    Rules:
      HC booking  (Notes matches HC and NOT FC):
        Resource = "{court_num} {COLOR}"   e.g. "1 BLUE"
      FC booking  (Notes matches FC, OR does not match HC):
        Resource = "FC {COLOR}"            e.g. "FC YELLOW"

    Sorted by: Date ASC, Start ASC, Resource ASC
    """
    import openpyxl

    print(f"[5a] Reading Excel: {xlsx_path}")
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    # Find the right sheet — prefer "Input", fall back to first sheet
    sheet_name = next(
        (s for s in wb.sheetnames if s.lower() == "input"),
        wb.sheetnames[0]
    )
    ws = wb[sheet_name]
    print(f"      Using sheet: '{sheet_name}' ({ws.max_row} rows)")

    # Detect header row and column positions
    col_map = _detect_columns(ws)
    print(f"      Column map: {col_map}")

    rows = []
    for row in ws.iter_rows(min_row=col_map["header_row"] + 1, values_only=True):
        date_val  = row[col_map["date"]]
        start_val = row[col_map["start"]]
        end_val   = row[col_map["end"]]
        staff_val = row[col_map["staff"]]
        notes_val = row[col_map["notes"]]

        if date_val is None:
            continue

        date_str  = _parse_date(date_val)
        start_str = _parse_time(start_val)
        end_str   = _parse_time(end_val)
        resource  = _make_resource(staff_val, notes_val)

        if date_str and start_str and end_str and resource:
            rows.append({
                "Date":     date_str,
                "Start":    start_str,
                "End":      end_str,
                "Resource": resource,
            })

    # Sort: Date → Start → Resource
    rows.sort(key=lambda r: (r["Date"], r["Start"], r["Resource"]))
    print(f"      Transformed {len(rows)} rows.")
    return rows


def _detect_columns(ws) -> dict:
    """
    Find the index (0-based) of required columns by scanning header row.
    Falls back to known Academy USA positions if headers not found.
    """
    # Academy USA known positions (0-indexed): A=0 B=1 C=2 E=4 N=13
    defaults = {
        "header_row": 1,
        "date":  0,   # A
        "start": 1,   # B
        "end":   2,   # C
        "staff": 4,   # E
        "notes": 13,  # N
    }

    # Try to find headers in first 3 rows
    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=3, values_only=True), 1):
        row_lower = [str(v).lower().strip() if v else "" for v in row]
        if "date" in row_lower and "start" in row_lower:
            return {
                "header_row": row_idx,
                "date":  row_lower.index("date"),
                "start": next((i for i, v in enumerate(row_lower) if "start" in v), 1),
                "end":   next((i for i, v in enumerate(row_lower) if "end" in v), 2),
                "staff": next((i for i, v in enumerate(row_lower) if "staff" in v), 4),
                "notes": next((i for i, v in enumerate(row_lower) if "note" in v), 13),
            }

    return defaults


def _parse_date(val) -> str | None:
    """Convert various date types to YYYY-MM-DD string."""
    if val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, (int, float)):
        # Excel serial date
        epoch = datetime.date(1899, 12, 30)
        return (epoch + datetime.timedelta(days=int(val))).strftime("%Y-%m-%d")
    try:
        return str(val)[:10]
    except Exception:
        return None


def _parse_time(val) -> str | None:
    """Convert various time types to HH:MM string."""
    if val is None:
        return None
    if isinstance(val, datetime.time):
        return val.strftime("%H:%M")
    if isinstance(val, datetime.datetime):
        return val.strftime("%H:%M")
    if isinstance(val, float):
        # Excel time fraction: 0.333... = 08:00
        total_minutes = round(val * 24 * 60)
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"
    try:
        s = str(val).strip()
        # Try "08:00:00" or "08:00"
        t = datetime.datetime.strptime(s[:5], "%H:%M")
        return t.strftime("%H:%M")
    except Exception:
        return None


def _make_resource(staff: str, notes: str) -> str | None:
    """
    Determine the Resource string from Staff and Notes columns.

    Staff format:  "1, BLUE"  "2, RED"  "1, Black"
    Output:
      HC booking → "1 BLUE"   (court number + color, no comma)
      FC booking → "FC BLUE"  (FC prefix + color)
    """
    if not staff:
        return None

    # Parse court number and color from Staff column ("1, BLUE" → "1", "BLUE")
    staff = str(staff).strip()
    match = re.match(r"(\d+),\s*(.+)", staff)
    if not match:
        return None
    court_num = match.group(1)
    color     = match.group(2).strip()  # BLUE, RED, YELLOW, Black, etc.

    notes_str = str(notes).strip() if notes else ""

    # Match HC/FC anywhere in the notes string (no word boundary required)
    # This handles cases like "HCLA Select", "HCJr. Hoops", "FCLA Select"
    is_hc = bool(re.search(r"HC", notes_str, re.IGNORECASE))
    is_fc = bool(re.search(r"FC", notes_str, re.IGNORECASE))

    # HC booking: notes has HC and NOT FC
    if is_hc and not is_fc:
        return f"{court_num} {color}"

    # FC booking: notes has FC, OR notes has neither (treat as FC per Excel logic)
    return f"FC {color}"


# ── Step 4: Save CSV ──────────────────────────────────────────────────────────

def _fmt_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to MM/dd/yyyy for CatchCorner."""
    try:
        d = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d")
        return d.strftime("%m/%d/%Y")
    except Exception:
        return date_str


def _fmt_time(time_str: str) -> str:
    """Convert HH:MM (24h) to h:mm AM/PM for CatchCorner."""
    try:
        t = datetime.datetime.strptime(str(time_str).strip()[:5], "%H:%M")
        # strftime %I gives zero-padded hour — strip leading zero for h format
        hour = t.strftime("%I").lstrip("0") or "12"
        mins = t.strftime("%M")
        ampm = t.strftime("%p")
        return f"{hour}:{mins} {ampm}"
    except Exception:
        return time_str


def save_csv(rows: list[dict], output_path: str = None) -> str:
    """
    Save transformed rows as CSV in CatchCorner format:
      Date     → MM/dd/yyyy   (e.g. 05/09/2026)
      Start    → h:mm AM/PM   (e.g. 8:00 AM)
      End      → h:mm AM/PM   (e.g. 10:00 AM)
      Resource → as-is        (e.g. 1 BLUE, FC RED)
    """
    if not output_path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"academy_usa_output_{ts}.csv"

    formatted = [
        {
            "Date":     _fmt_date(r["Date"]),
            "Start":    _fmt_time(r["Start"]),
            "End":      _fmt_time(r["End"]),
            "Resource": r["Resource"],
        }
        for r in rows
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Start", "End", "Resource"])
        writer.writeheader()
        writer.writerows(formatted)

    # Show a few sample rows so you can verify the format
    print(f"[5b] CSV saved: {output_path} ({len(formatted)} rows)")
    print(f"      Sample: {formatted[0]}")
    return output_path


# ── Step 5: Upload to CatchCorner ─────────────────────────────────────────────

def login_cc_corporate(username: str, password: str, access_from: str) -> str:
    """Login to CatchCorner corporate and return the access token."""
    login_url = "https://www.catchcorner.com/api/shared/authentication/Login"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br",
        "x-cc-platform": "1",
    }
    data = {
        "accessFrom": access_from,
        "email": username,
        "loginPlatform": 1,
        "password": password,
    }
    session = requests.Session()
    res = session.post(login_url, json=data, headers=headers, timeout=15)
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise ValueError("No access token received — check CatchCorner credentials.")
    print("      CatchCorner login OK.")
    return token


def upload_csv_corporate_api(access_token: str, corporate_id: str, csv_path: str):
    """Upload CSV to CatchCorner using the same API as main.py."""
    file_upload_url = "https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://cc-stage-corporate.azurewebsites.net",
        "Referer": "https://cc-stage-corporate.azurewebsites.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br",
        "x-cc-platform": "1",
        "Authorization": f"Bearer {access_token}",
    }
    with open(csv_path, "rb") as f:
        files = {"file": (csv_path, f, "multipart/form-data")}
        resp = requests.Session().post(
            f"{file_upload_url}/{corporate_id}/0",
            files=files,
            headers=headers,
            timeout=60,
        )
    resp.raise_for_status()
    print(f"      CSV uploaded successfully.")


def upload_to_catchcorner(csv_path: str):
    """Full CatchCorner upload flow: login → upload CSV."""
    print("[5c] Logging in to CatchCorner...")
    token = login_cc_corporate(CC_USERNAME, CC_PASSWORD, CC_ACCESS_FROM)

    print(f"[5d] Uploading to CatchCorner (facility ID: {CC_FACILITY})...")
    upload_csv_corporate_api(token, CC_FACILITY, csv_path)
    print(f"      Done. {csv_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Academy USA sync script")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--end",   help="End date YYYY-MM-DD (default: 30 days from today)")
    parser.add_argument("--input-file", help="Skip download, use this xlsx file directly")
    parser.add_argument("--output-file", help="Output CSV path (optional)")
    parser.add_argument("--no-upload", action="store_true", help="Skip CatchCorner upload")
    args = parser.parse_args()

    today      = datetime.date.today()
    start_date = datetime.date.fromisoformat(args.start) if args.start else today
    end_date   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=30)

    print("=" * 55)
    print("  Academy USA Sync")
    print(f"  Range: {start_date} → {end_date}")
    print("=" * 55)

    # Step 1-2: Download (or use provided file)
    if args.input_file:
        xlsx_path = args.input_file
        print(f"[1-4] Using provided file: {xlsx_path}")
    else:
        xlsx_path = download_schedule_excel(start_date, end_date)

    # Step 3: Transform
    rows = transform_schedule(xlsx_path)
    if not rows:
        print("WARNING: No rows produced after transformation. Check the input file.")
        return

    # Step 4: Save CSV
    csv_path = save_csv(rows, args.output_file)

    # Step 5: Upload
    if not args.no_upload:
        upload_to_catchcorner(csv_path)

    print()
    print(f"Done. {len(rows)} records synced.")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()