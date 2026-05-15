"""Western Fair — Sync script (Finnly, no auth needed)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS=60; SITE_ID=152
FACILITY_MAP={2161:"A - London Major Appliances Rink",2162:"B - Chick-Fil-A Wharncliffe & Wonderland Rink",
              2163:"C - Collins Clothiers Rink",2164:"D - Tony's Pizza Rink",2165:"Tournament Office",2166:"Concession Area"}
CC_USER=os.environ.get("CC_WESTERN_FAIR_USER","catchcornersetup206@gmail.com")
CC_PASS=os.environ.get("CC_WESTERN_FAIR_PASS","@SsU*BOr8$onh03&EiWc%$zuEh^qFt")
CC_FAC=os.environ.get("CC_WESTERN_FAIR_FAC","572")

def fetch(start,end):
    print(f"[1/3] Fetching Western Fair ({start} → {end})...")
    payload={"SiteId":SITE_ID,"FacilityIdList":list(FACILITY_MAP.keys()),
              "StartDate":start.strftime("%Y-%m-%dT00:00:00"),
              "EndDate":end.strftime("%Y-%m-%dT00:00:00")}
    h={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
    r=requests.post("https://app.finnlysport.com/event/aaa_event/calendarschedule",json=payload,headers=h,timeout=60)
    r.raise_for_status(); data=r.json(); print(f"      {len(data)} events"); return data

def transform(data):
    rows=[]
    for ev in data:
        try:
            st=datetime.datetime.fromisoformat(ev["blockStartTime"].rstrip("Z"))
            en=datetime.datetime.fromisoformat(ev["blockEndTime"].rstrip("Z"))
            en+=datetime.timedelta(minutes=10)
            fac=FACILITY_MAP.get(ev.get("facilityId",""),str(ev.get("facilityId","")))
            rows.append({"Date":st.strftime("%m/%d/%Y"),"Start":st.strftime("%I:%M:%S %p").lstrip("0"),
                         "End":en.strftime("%I:%M:%S %p").lstrip("0"),"Facility":fac})
        except Exception: pass
    print(f"[2/3] {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"western_fair_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","Start","End","Facility"]); w.writeheader(); w.writerows(rows)
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
    data=fetch(start,end); rows=transform(data)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
