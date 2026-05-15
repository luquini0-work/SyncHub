"""Commish Field / Soccer Post Cherry Hill — Sync script (sportskey.com, cookie)"""
import os,csv,sys,datetime,argparse,requests,re,time

SYNC_DAYS=60
CC_USER=os.environ.get("CC_COMMISH_USER","localloginformainte.n.anc.e.1.99.40@gmail.com")
CC_PASS=os.environ.get("CC_COMMISH_PASS","H#r6v8npPgpuqXayO6x*nqKQJDU524")
CC_FAC=os.environ.get("CC_COMMISH_FAC","1591")

FACILITIES={14919:"Indoor Turf Field",14920:"Indoor Turf Field Half A",14921:"Indoor Turf Field Half B",16522:"Outdoor Field"}

def get_cookie():
    c=os.environ.get("SYNC_COOKIE","").strip()
    if not c: print("ERROR: No cookie. Upload via SyncHub 🍪"); sys.exit(1)
    return c

def fetch_week(fac_id, date_str, cookie):
    url=f"https://portal.sportskey.com/venues/soccer-post-cherry-hill/facilities/{fac_id}/time_slots?date={date_str}"
    h={"Cookie":cookie,"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"}
    r=requests.get(url,headers=h,timeout=30,allow_redirects=True)
    if r.status_code in(401,403): print("ERROR: Cookie expired."); sys.exit(1)
    # Update cookie from response
    new_cookie=cookie
    try:
        set_cookie=r.headers.get("Set-Cookie","")
        m=re.search(r'_sportskey_session=[^;]+',set_cookie)
        if m: new_cookie=m.group(0)
    except: pass
    html=r.text.replace(re.search(r"d-lg-none'>\s*?<div class='d-none.+","",re.DOTALL) and "" or "","")
    matches=re.findall(r'(?:strong>(.+?)<\/strong)|(?:time me-1\'>(.+?)<)|(?:time\'>(.+?)<)',html)
    data=[m[0] or m[1] or m[2] for m in matches]
    return data, new_cookie

def parse_week_data(data, fac_id, start_date):
    """Parse scraped HTML data into bookings."""
    rows=[]
    # Data comes as: date, start, end, date, start, end...
    i=0
    court=FACILITIES.get(fac_id,str(fac_id))
    while i+2<len(data):
        try:
            date_str=data[i]; start_str=data[i+1]; end_str=data[i+2]
            dt=datetime.datetime.strptime(date_str,"%B %d, %Y") if "," in date_str else None
            if dt:
                rows.append({"Date":dt.strftime("%m/%d/%Y"),"Start Time":start_str,"End Time":end_str,"Court":court})
                i+=3
            else:
                i+=1
        except: i+=1
    return rows

def collect(start,end,cookie):
    print(f"[1/3] Fetching Commish Field ({start} → {end})...")
    all_rows=[]; current_cookie=cookie
    for fac_id in FACILITIES:
        cur=start
        while cur<=end:
            date_str=cur.strftime("%Y-%m-%d")
            try:
                data,current_cookie=fetch_week(fac_id,date_str,current_cookie)
                rows=parse_week_data(data,fac_id,cur)
                all_rows.extend(rows)
            except Exception as e:
                print(f"      {fac_id} {date_str}: {e}")
            time.sleep(1)
            cur+=datetime.timedelta(days=7)
    print(f"      {len(all_rows)} rows"); return all_rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"commish_field_{ts}.csv")
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
