"""The St. James — Sync script (Tripleseat, cookie + CSRF)"""
import os,csv,sys,datetime,argparse,requests,urllib.parse

SYNC_DAYS=60
CC_USER=os.environ.get("CC_ST_JAMES_USER",""); CC_PASS=os.environ.get("CC_ST_JAMES_PASS",""); CC_FAC=os.environ.get("CC_ST_JAMES_FAC","0")

# Room IDs from LINK sheet — filtered sports/fitness rooms
ROOM_IDS=["391645","391646","391647","85949","85950","391648","391649","391650","85951","85952","86100","86101","86102","86103"]

def get_cookie():
    c=os.environ.get("SYNC_COOKIE","").strip()
    if not c: print("ERROR: No cookie. Upload via SyncHub 🍪"); sys.exit(1)
    return c

def get_csrf():
    return os.environ.get("ST_JAMES_CSRF","").strip()

def fetch(start,end,cookie,csrf):
    print(f"[1/3] Fetching St. James ({start} → {end})...")
    rows=[]; cur=start
    while cur<=end:
        start_param=cur.strftime("%m/%d/%Y")
        params={"utf8":"✓","view":"week","timeline_span":"resourceTimelineDay","timeline_blocking":"true",
                "coloring":"room","setup_teardown":"separate","room_ids":",".join(ROOM_IDS),"start":start_param}
        url="https://thestjames.tripleseat.com/calendar?"+urllib.parse.urlencode(params)
        h={"Accept":"text/javascript","X-Requested-With":"XMLHttpRequest",
           "X-CSRF-Token":csrf,"Cookie":cookie,"Referer":"https://thestjames.tripleseat.com/calendar","User-Agent":"Mozilla/5.0"}
        try:
            r=requests.get(url,headers=h,timeout=30)
            if r.status_code in(401,403): print("ERROR: Cookie/CSRF expired."); sys.exit(1)
            if r.status_code!=200: cur+=datetime.timedelta(days=1); continue
            data=r.json(); isoday=cur.strftime("%Y-%m-%d")
            for ev in data.get("events",[]):
                st=datetime.datetime.fromisoformat(ev["start"].replace("Z",""))
                en=datetime.datetime.fromisoformat(ev["end"].replace("Z",""))
                if st.strftime("%Y-%m-%d")!=isoday: continue
                for rid in ev.get("room_ids",[]):
                    rows.append({"Date":st.strftime("%Y/%m/%d"),"StartTime":st.strftime("%I:%M %p").lstrip("0"),
                                 "EndTime":en.strftime("%I:%M %p").lstrip("0"),"Court":str(rid)})
        except Exception as e:
            print(f"      {cur}: {e}")
        cur+=datetime.timedelta(days=1)
    print(f"      {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"st_james_{ts}.csv")
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
    cookie=get_cookie(); csrf=get_csrf(); rows=fetch(start,end,cookie,csrf)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
