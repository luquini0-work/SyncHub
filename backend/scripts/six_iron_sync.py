"""6ix Iron — Sync script (albaplay.com GraphQL, public)"""
import os,csv,sys,datetime,argparse,requests,time

SYNC_DAYS=60; SLUG="6ix-iron"; RESOURCE_TYPE="SIM"
CC_USER=os.environ.get("CC_SIX_IRON_USER",""); CC_PASS=os.environ.get("CC_SIX_IRON_PASS",""); CC_FAC=os.environ.get("CC_SIX_IRON_FAC","0")

QUERY='query GetLocationCalendarHookExplicitV2($slug:String!,$date:String!,$resourceType:ResourceType!){locationBySlugForCalendar(slug:$slug,date:$date,resourceType:$resourceType){timezone locationCalendar{resourceWithCalendar{id name slots{resourceName startTime endTime availability{state}}}}}}'

def fetch_day(day_str):
    payload={"operationName":"GetLocationCalendarHookExplicitV2",
              "variables":{"slug":SLUG,"date":day_str,"resourceType":RESOURCE_TYPE},"query":QUERY}
    h={"Accept":"*/*","Content-Type":"application/json","Origin":"https://albaplay.com",
       "Referer":f"https://albaplay.com/en/venue/{SLUG}?date={day_str}","User-Agent":"Mozilla/5.0"}
    r=requests.post("https://albaplay.com/api/graphql",json=payload,headers=h,timeout=30)
    if r.status_code!=200: return []
    data=r.json(); loc=data.get("data",{}).get("locationBySlugForCalendar",{})
    tz=loc.get("timezone","UTC")
    resources=loc.get("locationCalendar",{}).get("resourceWithCalendar",[]) or []
    rows=[]
    for res in resources:
        for slot in res.get("slots",[]):
            if slot.get("availability",{}).get("state")=="AVAILABLE": continue
            try:
                st=datetime.datetime.fromisoformat(slot["startTime"].replace("Z","+00:00")).astimezone(datetime.timezone.utc).replace(tzinfo=None)
                en=datetime.datetime.fromisoformat(slot["endTime"].replace("Z","+00:00")).astimezone(datetime.timezone.utc).replace(tzinfo=None)
                rows.append({"Date":st.strftime("%m/%d/%Y"),"StartTime":st.strftime("%I:%M %p").lstrip("0"),
                             "EndTime":en.strftime("%I:%M %p").lstrip("0"),"Court":slot.get("resourceName","")})
            except Exception: pass
    return rows

def collect(start,end):
    print(f"[1/3] Fetching 6ix Iron ({start} → {end})...")
    rows=[]; cur=start
    while cur<=end:
        rows.extend(fetch_day(cur.strftime("%Y-%m-%d"))); time.sleep(0.3); cur+=datetime.timedelta(days=1)
    print(f"      {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"six_iron_{ts}.csv")
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
    rows=collect(start,end)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
