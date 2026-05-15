"""Crestwood Pickleball — Sync script (crestwoodcurling.com public API)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS = 60
CC_USER = os.environ.get("CC_CRESTWOOD_USER","")
CC_PASS = os.environ.get("CC_CRESTWOOD_PASS","")
CC_FAC  = os.environ.get("CC_CRESTWOOD_FAC","0")

COURT_MAP = {"7":"Court 1","8":"Court 2","9":"Court 3","10":"Court 4","11":"Court 5","12":"Court 6","13":"Lounge"}

def fetch(start,end,tz="America/Toronto"):
    print(f"[1/3] Fetching Crestwood ({start} → {end})...")
    url="https://crestwoodcurling.com/index.php/events/index.php?option=com_facilitycalendar&task=calendar.getevents"
    payload={"calview":"resourceTimeGridDay","types":"",
              "start":start.strftime("%Y-%m-%dT00:00:00"),
              "end":end.strftime("%Y-%m-%dT00:00:00"),"timeZone":tz}
    h={"Accept":"*/*","Origin":"https://crestwoodcurling.com",
       "Referer":"https://crestwoodcurling.com/index.php/events/club-calendar","User-Agent":"Mozilla/5.0"}
    r=requests.post(url,data=payload,headers=h,timeout=60); r.raise_for_status()
    events=r.json(); print(f"      {len(events)} events"); return events

def transform(events):
    rows=[]
    for ev in events:
        try:
            rid=str(ev.get("resourceId") or ev.get("resource_id",""))
            court=COURT_MAP.get(rid)
            if not court: continue
            st=datetime.datetime.fromisoformat(ev["start"]); en=datetime.datetime.fromisoformat(ev["end"])
            rows.append({"Date":st.strftime("%m/%d/%Y"),
                         "Start Time":st.strftime("%I:%M:%S %p").lstrip("0"),
                         "End Time":en.strftime("%I:%M:%S %p").lstrip("0"),"Court":court})
        except Exception: pass
    print(f"[2/3] {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"crestwood_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","Start Time","End Time","Court"])
        w.writeheader();w.writerows(rows)
    print(f"      CSV: {path} ({len(rows)} rows)"); return path

def upload(csv_path):
    h={"Accept":"application/json, text/plain, */*","Content-Type":"application/json",
       "Origin":"https://cc-stage-corporate.azurewebsites.net",
       "Referer":"https://cc-stage-corporate.azurewebsites.net/","User-Agent":"Mozilla/5.0","x-cc-platform":"1"}
    r=requests.post("https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom":"Corporate","email":CC_USER,"loginPlatform":1,"password":CC_PASS},
        headers=h,timeout=15); r.raise_for_status()
    token=r.json().get("access_token")
    del h["Content-Type"]; h["Authorization"]=f"Bearer {token}"
    with open(csv_path,"rb") as f:
        resp=requests.post(f"https://www.catchcorner.com/api/back-office-shared/csvdump/dump/upload/0/{CC_FAC}/0",
            files={"file":(os.path.basename(csv_path),f,"multipart/form-data")},headers=h,timeout=60)
    resp.raise_for_status(); print("      Uploaded OK")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--no-upload",action="store_true"); args=p.parse_args()
    today=datetime.date.today()
    start=datetime.date.fromisoformat(args.start) if args.start else today
    end=datetime.date.fromisoformat(args.end) if args.end else today+datetime.timedelta(days=SYNC_DAYS)
    events=fetch(start,end); rows=transform(events)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
