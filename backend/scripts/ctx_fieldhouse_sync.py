"""
CTX Fieldhouse — Sync script
API pública rectimes.com, sin cookie.
"""
import os, csv, sys, datetime, argparse, requests

SYNC_DAYS  = 60
CC_USER    = os.environ.get("CC_CTX_USER", "")
CC_PASS    = os.environ.get("CC_CTX_PASS", "")
CC_FAC     = "0"  # SET IN RAILWAY

VENUE_IDS  = [915,914,913,912,911,887,888,889,890,891,892,893,894,895,896,899,898,897]

def fetch(start: datetime.date, end: datetime.date) -> list:
    print(f"[1/3] Fetching CTX Fieldhouse ({start} → {end})...")
    url = "https://api.rectimes.com/api/v1/facilities/ctxfieldhouse/bookings/get_for_calendar"
    payload = {
        "venueIds": VENUE_IDS,
        "startTimeLocal": start.strftime("%Y-%m-%dT00:00:00Z"),
        "endTimeLocal":   end.strftime("%Y-%m-%dT00:00:00Z"),
    }
    h = {"Accept": "*/*", "Content-Type": "application/json",
         "Origin": "https://app.rectimes.com", "Referer": "https://app.rectimes.com/",
         "User-Agent": "Mozilla/5.0"}
    r = requests.post(url, json=payload, headers=h, timeout=60)
    r.raise_for_status()
    data = r.json()
    slots = data if isinstance(data, list) else data.get("bookings", [])
    print(f"      {len(slots)} bookings")
    return slots

def transform(slots: list) -> list:
    rows = []
    for s in slots:
        try:
            st = datetime.datetime.fromisoformat(s["startTimeLocal"].replace("Z",""))
            en = datetime.datetime.fromisoformat(s["endTimeLocal"].replace("Z",""))
            rows.append({"Date": st.strftime("%m/%d/%Y"),
                         "Start Time": st.strftime("%I:%M:%S %p").lstrip("0"),
                         "End Time":   en.strftime("%I:%M:%S %p").lstrip("0"),
                         "Court": s.get("venueName","")})
        except Exception: pass
    rows.sort(key=lambda r: (r["Date"], r["Start Time"]))
    print(f"[2/3] {len(rows)} rows")
    return rows

def save_csv(rows, path=None):
    if not path:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"ctx_fieldhouse_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Date","Start Time","End Time","Court"])
        w.writeheader(); w.writerows(rows)
    print(f"      CSV: {path} ({len(rows)} rows)")
    return path

def upload(csv_path):
    print(f"[3/3] Uploading to CatchCorner ({CC_FAC})...")
    h = {"Accept":"application/json, text/plain, */*","Content-Type":"application/json",
         "Origin":"https://cc-stage-corporate.azurewebsites.net",
         "Referer":"https://cc-stage-corporate.azurewebsites.net/","User-Agent":"Mozilla/5.0","x-cc-platform":"1"}
    r = requests.post("https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom":"Corporate","email":CC_USER,"loginPlatform":1,"password":CC_PASS},
        headers=h, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    del h["Content-Type"]; h["Authorization"] = f"Bearer {token}"
    with open(csv_path,"rb") as f:
        resp = requests.post(
            f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FAC}/0",
            files={"file":(os.path.basename(csv_path),f,"multipart/form-data")},headers=h,timeout=60)
    resp.raise_for_status(); print("      OK")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start"); p.add_argument("--end")
    p.add_argument("--no-upload", action="store_true")
    args = p.parse_args()
    today = datetime.date.today()
    start = datetime.date.fromisoformat(args.start) if args.start else today
    end   = datetime.date.fromisoformat(args.end)   if args.end   else today + datetime.timedelta(days=SYNC_DAYS)
    slots = fetch(start, end)
    rows  = transform(slots)
    if not rows: print("No rows"); sys.exit(0)
    path  = save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__ == "__main__": main()
