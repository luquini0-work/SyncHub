"""Home Court — Sync script (gymmasteronline.com, cookie)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS=60
CC_USER=os.environ.get("CC_HOME_COURT_USER",""); CC_PASS=os.environ.get("CC_HOME_COURT_PASS",""); CC_FAC=os.environ.get("CC_HOME_COURT_FAC","0")
BASE="https://thehomecourt.gymmasteronline.com"

def get_cookie():
    c=os.environ.get("SYNC_COOKIE","").strip()
    if not c: print("ERROR: No cookie. Upload via SyncHub 🍪"); sys.exit(1)
    return c

def fetch(start,end,cookie):
    print(f"[1/3] Fetching Home Court ({start} → {end})...")
    h={"Accept":"application/json","X-Requested-With":"XMLHttpRequest","Cookie":cookie,
       "Referer":f"{BASE}/booking/schedule","User-Agent":"Mozilla/5.0"}
    rows=[]; cur=start
    while cur<=end:
        iso=cur.strftime("%Y-%m-%d")
        for endpoint in [f"{BASE}/v1/schedule/daily/bookings/-1/{iso}",
                         f"{BASE}/v1/schedule/daily/bookings/modifier/-1/{iso}/unavailable"]:
            try:
                r=requests.get(endpoint,headers=h,timeout=30)
                if r.status_code in(401,403): print("ERROR: Cookie expired."); sys.exit(1)
                if r.status_code!=200: continue
                for ev in r.json().get("response",[]):
                    rows.append({"Date":ev.get("arrival",iso),"StartTime":ev.get("starttime",""),
                                 "EndTime":ev.get("endtime",""),"Court":ev.get("resourcename","")})
            except Exception as e:
                print(f"      {iso}: {e}")
        cur+=datetime.timedelta(days=1)
    print(f"      {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"home_court_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","StartTime","EndTime","Court"]); w.writeheader(); w.writerows(rows)
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
    cookie=get_cookie(); rows=fetch(start,end,cookie)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
