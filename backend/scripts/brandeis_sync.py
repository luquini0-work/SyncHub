"""Brandeis Athletic — Sync script (dserec.com public API)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS = 60
CC_USER = os.environ.get("CC_BRANDEIS_USER","")
CC_PASS = os.environ.get("CC_BRANDEIS_PASS","")
CC_FAC  = os.environ.get("CC_BRANDEIS_FAC","0")

SPACE_MAP = {
    "1":"Auerbach Arena","2":"Batting Cage 1","3":"Batting Cage 2","4":"Dance Studio",
    "5":"Indoor Tennis Court 1","6":"Indoor Tennis Court 2","7":"Indoor Tennis Court 3",
    "8":"Indoor Track","9":"Multipurpose Room","10":"Pole Vault Pit","11":"Climbing Wall",
    "12":"TRX Room (Sq Ct 2)","13":"Squash Court 4","14":"Squash Court 5","15":"Squash Court 6",
    "16":"Squash Court 7","17":"Varsity Weight Room","30":"Diving Area","31":"Mpr 1 (Cycle Room)",
    "32":"Mpr 3 (Mat Room)","33":"Mpr 4","34":"Pool","35":"Baseball Field","36":"Club Field",
    "37":"Outdoor Tennis Court 01","38":"Outdoor Tennis Court 02","39":"Outdoor Tennis Court 03",
    "40":"Outdoor Tennis Court 04","41":"Outdoor Tennis Court 05","42":"Outdoor Tennis Court 06",
    "43":"Outdoor Tennis Court 07","44":"Outdoor Tennis Court 08","45":"Outdoor Tennis Court 09",
    "46":"Outdoor Tennis Court 10","47":"Outdoor Tennis Court 11","48":"Outdoor Tennis Court 12",
    "49":"Outdoor Track","50":"Soccer Field (Turf)","51":"Softball Field",
    "52":"Shapiro Court 1","53":"Shapiro Court 2","54":"Shapiro Court 3 / Pickleball",
    "67":"General Weight Room","68":"Fencing Room","69":"Throwing Area","72":"Long Jump Pit",
}

def fetch(start,end):
    print(f"[1/3] Fetching Brandeis ({start} → {end})...")
    url = f"https://brandeis.dserec.com/online/fcscheduling/api/reservation?start={start}&end={end}"
    h = {"accept":"application/json, text/plain, */*","x-requested-with":"XMLHttpRequest",
         "referer":"https://brandeis.dserec.com/online/fcscheduling/availabilitycalendar"}
    r = requests.get(url,headers=h,timeout=60); r.raise_for_status()
    data = r.json()
    events = data.get("data",[]) if isinstance(data,dict) else data
    print(f"      {len(events)} events"); return events

def transform(events):
    rows = []
    for ev in events:
        try:
            st = datetime.datetime.fromisoformat(ev["start"])
            en = datetime.datetime.fromisoformat(ev["end"])
            sid = str(ev.get("space_id","")).strip()
            court = SPACE_MAP.get(sid, sid)
            if st.date() != en.date():
                # split overnight
                rows.append({"Date":st.strftime("%m/%d/%Y"),
                             "StartTime":st.strftime("%I:%M:%S %p").lstrip("0"),
                             "EndTime":"11:59:00 PM","Court":court})
                d = st.date() + datetime.timedelta(days=1)
                while d <= en.date():
                    s_str = "12:00:00 AM"; e_str = "11:59:00 PM" if d < en.date() else en.strftime("%I:%M:%S %p").lstrip("0")
                    rows.append({"Date":d.strftime("%m/%d/%Y"),"StartTime":s_str,"EndTime":e_str,"Court":court})
                    d += datetime.timedelta(days=1)
            else:
                rows.append({"Date":st.strftime("%m/%d/%Y"),
                             "StartTime":st.strftime("%I:%M:%S %p").lstrip("0"),
                             "EndTime":en.strftime("%I:%M:%S %p").lstrip("0"),"Court":court})
        except Exception: pass
    print(f"[2/3] {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"brandeis_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","StartTime","EndTime","Court"])
        w.writeheader();w.writerows(rows)
    print(f"      CSV: {path} ({len(rows)} rows)"); return path

def upload(csv_path):
    h={"Accept":"application/json, text/plain, */*","Content-Type":"application/json",
       "Origin":"https://cc-stage-corporate.azurewebsites.net",
       "Referer":"https://cc-stage-corporate.azurewebsites.net/","User-Agent":"Mozilla/5.0","x-cc-platform":"1"}
    r=requests.post("https://www.catchcorner.com/api/shared/authentication/Login",
        json={"accessFrom":"Organization","email":CC_USER,"loginPlatform":1,"password":CC_PASS},
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
