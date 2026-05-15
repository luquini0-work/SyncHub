"""Christ's Haven — Sync script (perfectvenue.com GraphQL, cookie)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS=60; VENUE_ID="13331"
CC_USER=os.environ.get("CC_CHRISTS_HAVEN_USER",""); CC_PASS=os.environ.get("CC_CHRISTS_HAVEN_PASS",""); CC_FAC=os.environ.get("CC_CHRISTS_HAVEN_FAC","0")

def get_cookie():
    c=os.environ.get("SYNC_COOKIE","").strip()
    if not c: print("ERROR: No cookie. Upload via SyncHub 🍪"); sys.exit(1)
    return c

def mins_to_time(mins):
    h,m=divmod(int(mins),60); t=datetime.time(h%24,m)
    return t.strftime("%I:%M:%S %p").lstrip("0")

def fetch(start,end,cookie):
    print(f"[1/3] Fetching Christ's Haven ({start} → {end})...")
    url="https://api.perfectvenue.com/graphql"
    base_h={"Accept":"*/*","Content-Type":"application/json","Origin":"https://app.perfectvenue.com",
             "Referer":"https://app.perfectvenue.com","User-Agent":"Mozilla/5.0","Cookie":cookie}
    s=start.strftime("%Y-%m-%d"); e=end.strftime("%Y-%m-%d")
    rows=[]

    # CalendarEvents
    payload={"operationName":"CalendarEvents","variables":{"venueIds":[VENUE_ID],"dateTimeRange":{"startDate":s,"endDate":e}},
             "query":"query CalendarEvents($venueIds:[ID!]!,$dateTimeRange:DateTimeRangeInput!){calendarEvents(venueIds:$venueIds,dateTimeRange:$dateTimeRange){id name startDate startOffset endDate endOffset status spaces{id name __typename} sessions{id name startDate startOffset endDate endOffset spaces{id name __typename} __typename} __typename}}"}
    r=requests.post(url,json=payload,headers=base_h,timeout=60)
    if r.status_code in(401,403): print("ERROR: Cookie expired."); sys.exit(1)
    for ev in r.json().get("data",{}).get("calendarEvents",[]) or []:
        if ev.get("sessions"):
            for sess in ev["sessions"]:
                if not sess.get("startDate") or not(s<=sess["startDate"]<=e): continue
                court=", ".join(sp["name"] for sp in (sess.get("spaces") or ev.get("spaces") or []) if sp.get("name"))
                rows.append({"Date":sess["startDate"],"Start Time":mins_to_time(sess.get("startOffset",0)),
                             "End Time":mins_to_time(sess.get("endOffset",0)),"Court":court})
        elif ev.get("startDate") and s<=ev["startDate"]<=e:
            court=", ".join(sp["name"] for sp in (ev.get("spaces") or []) if sp.get("name"))
            rows.append({"Date":ev["startDate"],"Start Time":mins_to_time(ev.get("startOffset",0)),
                         "End Time":mins_to_time(ev.get("endOffset",0)),"Court":court})

    # RecurringEvents
    payload2={"operationName":"RecurringEvents2","variables":{"venueIds":[VENUE_ID],"dateTimeRange":{"startDate":s,"endDate":e}},
              "query":"query RecurringEvents2($venueIds:[ID!]!){recurringEvents(venueIds:$venueIds){id name startDate startOffset endOffset spaces{id name __typename} recurringDateTimeRanges{startDate startOffset endDate endOffset __typename} __typename}}"}
    r2=requests.post(url,json=payload2,headers=base_h,timeout=60)
    for ev in r2.json().get("data",{}).get("recurringEvents",[]) or []:
        court=", ".join(sp["name"] for sp in (ev.get("spaces") or []) if sp.get("name"))
        for rng in ev.get("recurringDateTimeRanges") or []:
            if not rng.get("startDate") or not(s<=rng["startDate"]<=e): continue
            so=rng.get("startOffset") if rng.get("startOffset") is not None else ev.get("startOffset",0)
            eo=rng.get("endOffset") if rng.get("endOffset") is not None else ev.get("endOffset",0)
            rows.append({"Date":rng["startDate"],"Start Time":mins_to_time(so),"End Time":mins_to_time(eo),"Court":court})

    print(f"      {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"christs_haven_{ts}.csv")
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
    cookie=get_cookie(); rows=fetch(start,end,cookie)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
