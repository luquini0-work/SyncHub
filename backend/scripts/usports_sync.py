"""USports — Sync script (calengoo.com public API)"""
import os,csv,sys,datetime,argparse,requests

SYNC_DAYS=60; ACCOUNT_ID="a36ec52299d704737e83c85c5b56365b86980ccc"; BLOCK_MINUTES=60
CC_USER=os.environ.get("CC_USPORTS_USER",""); CC_PASS=os.environ.get("CC_USPORTS_PASS",""); CC_FAC=os.environ.get("CC_USPORTS_FAC","0")

def fetch(start,end):
    print(f"[1/3] Fetching USports ({start} → {end})...")
    days=(end-start).days+1
    url=(f"https://android.calengoo.com/store/booking/bookings_users_any_v34.php"
         f"?email=&password=&appAccessToken=&accountid={ACCOUNT_ID}"
         f"&starttime={start.strftime('%Y-%m-%dT00:00:00')}&days={days}&bookingUserCode=&bookToken=")
    h={"Referer":"https://www.calengoo.com/","User-Agent":"Mozilla/5.0"}
    r=requests.get(url,headers=h,timeout=60); r.raise_for_status()
    data=r.json(); items=data.get("items",[]) if isinstance(data,dict) else []
    print(f"      {len(items)} account blocks"); return items

def transform(items):
    rows=[]
    for block in items:
        court=str(block.get("accountid","")).strip()
        for it in block.get("items",[]):
            try:
                s=it.get("starttime",""); parts=s.split(" ")
                dt=datetime.datetime.strptime(s,"%Y-%m-%d %H:%M:%S") if len(parts)==2 else None
                if not dt: continue
                en=dt+datetime.timedelta(minutes=BLOCK_MINUTES)
                rows.append({"Date":dt.strftime("%Y/%m/%d"),"StartTime":dt.strftime("%H:%M:%S"),
                             "EndTime":en.strftime("%H:%M:%S"),"Court":court})
            except: pass
    print(f"[2/3] {len(rows)} rows"); return rows

def save_csv(rows,path=None):
    if not path:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),f"usports_{ts}.csv")
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
    items=fetch(start,end); rows=transform(items)
    if not rows: print("No rows"); sys.exit(0)
    path=save_csv(rows)
    if not args.no_upload: upload(path)
    print(f"Done. {len(rows)} records.")

if __name__=="__main__": main()
