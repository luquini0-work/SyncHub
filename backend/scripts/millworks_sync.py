"""MillWorks Setmore — Sync script (setmore GraphQL, cookie)"""
import os,csv,sys,datetime,argparse,requests,time

SYNC_DAYS=60; COMPANY_ID="8b29cd69-3c48-4514-9048-19b17ff825f3"
CC_USER=os.environ.get("CC_MILLWORKS_USER",""); CC_PASS=os.environ.get("CC_MILLWORKS_PASS",""); CC_FAC=os.environ.get("CC_MILLWORKS_FAC","0")

SERVICE_MAP={
    "d18f87bd-707d-48fc-bec7-2b73f464291a":"Baseball 60 Min. Hitting Rental",
    "2d2a0401-9508-4ccd-b2d4-0d33f06ccabf":"Softball 60 Min. Hitting Rental",
    "a55eacee-1779-4f80-a32f-9b3e2c4d7e11":"Batting Cage Rental",
    "e53fba2d-e0b7-4c3e-a9f1-2b8c5d6e7f12":"Pitching Machine Rental",
}

QUERY="query GetSlots($companyId:ID!,$durationMins:Int!,$endDateISO:String!,$serviceIds:[ID!]!,$startDateISO:String!,$timeZone:String!){slots(where:{companyId:$companyId,durationMins:$durationMins,endDateISO:$endDateISO,serviceIds:$serviceIds,startDateISO:$startDateISO,timeZone:$timeZone}){ms}}"

def get_cookie():
    c=os.environ.get("SYNC_COOKIE","").strip()
    if not c: print("ERROR: No cookie. Upload via SyncHub 🍪"); sys.exit(1)
    return c

def fetch_service(service_id, court_name, start, end, cookie, tz="America/New_York"):
    payload={"operationName":"GetSlots","variables":{
        "companyId":COMPANY_ID,"durationMins":60,
        "endDateISO":end.strftime("%Y-%m-%d")+"T23:59:59.000Z",
        "serviceIds":[service_id],
        "startDateISO":start.strftime("%Y-%m-%d")+"T00:00:00.000Z",
        "timeZone":tz},"query":QUERY}
    h={"Content-Type":"application/json","Cookie":cookie,
       "origin":"https://millworksbrickyard.setmore.com","x-cbp-origin":"https://millworksbrickyard.setmore.com","User-Agent":"Mozilla/5.0"}
    r=requests.post("https://cbphandlers.setmore.com/handlers/graphql?operation=GetSlots",json=payload,headers=h,timeout=60)
    if r.status_code in(401,403): print("ERROR: Cookie expired."); sys.exit(1)
    slots=r.json().get("data",{}).get("slots",[]) or []
    available_ms={int(s["ms"]) for s in slots}
    for s in slots: available_ms.add(int(s["ms"])+1800000)
    rows=[]
    cur=start
    while cur<=end:
        for h_val in range(24):
            for m_val in [0,30]:
                st=datetime.datetime(cur.year,cur.month,cur.day,h_val,m_val)
                ms=int(st.timestamp()*1000)
                if ms not in available_ms:
                    en=st+datetime.timedelta(minutes=30)
                    rows.append({"Date":cur.strftime("%Y-%m-%d"),
                                 "Start Time":st.strftime("%I:%M %p").lstrip("0"),
                                 "End Time":en.strftime("%I:%M %p").lstrip("0"),"Court":court_name})
        cur+=datetime.timedelta(days=1)
    return rows

def collect(start,end,cookie):
    print(f"[1/3] Fetching MillWorks ({start} → {end})...")
    all_rows=[]
    for sid,name in SERVICE_MAP.items():
        try:
            rows=fetch_service(sid,name,start,end,cookie)
            all_rows.extend(rows); print(f"      {name}: {len(rows)} rows")
        except Exception as e:
            print(f"      {name}: {e}")
        time.sleep(1)
    print(f"      Total: {len(all_rows)} rows"); return all_rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"millworks_{ts}.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["Date","Start Time","End Time","Court"]); w.writeheader(); w.writerows(rows)
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
    cookie=get_cookie(); rows=collect(start,end,cookie)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
