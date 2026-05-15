"""D-BAT — Sync script (upperhand API, X-Jwt-Token)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS=60; CUSTOMER_ID="361"
CC_USER=os.environ.get("CC_DBAT_USER",""); CC_PASS=os.environ.get("CC_DBAT_PASS",""); CC_FAC=os.environ.get("CC_DBAT_FAC","0")

RESOURCE_MAP={
    3231:"Cage 1",3232:"Cage 2",3233:"Cage 3",3234:"Cage 4",3235:"Cage 5",
    3236:"Cage 6",3237:"Cage 7",3238:"Cage 8",3239:"Cage 9",3240:"Cage 10",
    3241:"Cage 11",3242:"Party Room",3248:"Waitlist",3385:"Pitching Machine Cage 1",
}

def get_token():
    t=os.environ.get("SYNC_COOKIE","").strip()
    if not t: print("ERROR: No token. Upload via SyncHub 🍪"); sys.exit(1)
    return t

def fetch(start,end,token):
    print(f"[1/3] Fetching D-BAT ({start} → {end})...")
    tz_offset="-0500"
    s=start.strftime(f"%a+%b+%d+%Y+00:00:00+GMT{tz_offset}")
    e=end.strftime(f"%a+%b+%d+%Y+23:59:59+GMT{tz_offset}")
    url=f"https://api.dbathub.com/api//calendar?fields[]=team_type&start_date={s}&end_date={e}"
    r=requests.get(url,headers={"X-Customer-Id":CUSTOMER_ID,"X-Jwt-Token":token},timeout=60)
    if r.status_code in(401,403): print("ERROR: Token expired. Update via SyncHub."); sys.exit(1)
    r.raise_for_status()
    data=r.json().get("event_times",[]); print(f"      {len(data)} slots"); return data

def transform(data):
    rows=[]
    for slot in data:
        for rid in slot.get("resource_ids",[]):
            court=RESOURCE_MAP.get(int(rid),str(rid))
            rows.append({"Date":slot["event_date"],"Start":slot["start_time"],"End":slot["end_time"],"Resource":court})
    print(f"[2/3] {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"dbat_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","Start","End","Resource"]); w.writeheader(); w.writerows(rows)
    print(f"      CSV: {path} ({len(rows)} rows)"); return path

def upload(csv_path):
    h={"Accept":"application/json, text/plain, */*","Content-Type":"application/json",
       "Origin":"https://cc-stage-corporate.azurewebsites.net","Referer":"https://cc-stage-corporate.azurewebsites.net/","User-Agent":"Mozilla/5.0","x-cc-platform":"1"}
    r=requests.post("https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom":"Corporate","email":CC_USER,"loginPlatform":1,"password":CC_PASS},headers=h,timeout=15); r.raise_for_status()
    token=r.json().get("access_token"); del h["Content-Type"]; h["Authorization"]=f"Bearer {token}"
    with open(csv_path,"rb") as f:
        resp=requests.post(f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FAC}/0",
            files={"file":(os.path.basename(csv_path),f,"multipart/form-data")},headers=h,timeout=60)
    resp.raise_for_status(); print("      Uploaded OK")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--no-upload",action="store_true"); args=p.parse_args()
    today=datetime.date.today()
    start=datetime.date.fromisoformat(args.start) if args.start else today
    end=datetime.date.fromisoformat(args.end) if args.end else today+datetime.timedelta(days=SYNC_DAYS)
    token=get_token(); data=fetch(start,end,token); rows=transform(data)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
