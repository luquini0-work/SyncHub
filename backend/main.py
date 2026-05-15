"""
SyncHub Backend — FastAPI
"""

import os, json, re, subprocess, threading, datetime, sqlite3, asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

BASE_DIR    = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR    = BASE_DIR / "data"
DB_PATH     = DATA_DIR / "synchub.db"
COOKIES_DIR = DATA_DIR / "cookies"
FAC_CONFIG  = DATA_DIR / "facilities.json"

DATA_DIR.mkdir(exist_ok=True)
COOKIES_DIR.mkdir(exist_ok=True)
SCRIPTS_DIR.mkdir(exist_ok=True)

API_KEY = os.environ.get("SYNCHUB_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_key(key: str = Security(api_key_header)):
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(403, "Invalid API key")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL DEFAULT 'running',
                rows INTEGER,
                duration_s REAL,
                trigger TEXT DEFAULT 'manual',
                log_output TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                facility_id TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS csv_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                rows INTEGER,
                size_bytes INTEGER,
                created_at TEXT NOT NULL,
                log_id INTEGER,
                content BLOB NOT NULL
            )
        """)
        db.commit()

# 4x/dia en horario Miami (UTC-4): 8am, 10:30am, 1pm, 3:30pm Miami = 12:00, 14:30, 17:00, 19:30 UTC
MIAMI_SCHEDULES = ["0 12 * * *", "30 14 * * *", "0 17 * * *", "30 19 * * *"]

DEFAULT_FACILITIES = {
    "create_the_finish": {
        "name": "Create The Finish", "platform": "mindbody",
        "script": "create_the_finish_sync.py", "has_cookie": True,
        "cc_facility": "2361", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "houston_pickleball": {
        "name": "Houston Pickleball", "platform": "mindbody",
        "script": "houston_sync.py", "script_args": ["pickleball"], "has_cookie": True,
        "cc_facility": "2224", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "houston_badminton": {
        "name": "Houston Badminton", "platform": "mindbody",
        "script": "houston_sync.py", "script_args": ["badminton"], "has_cookie": True,
        "cc_facility": "2225", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "infinite_humble": {
        "name": "Infinite Hitting - Humble", "platform": "mindbody",
        "script": "infinite_hitting_sync.py", "script_args": ["humble"], "has_cookie": True,
        "cc_facility": "2246", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "infinite_sugarland": {
        "name": "Infinite Hitting - Sugar Land", "platform": "mindbody",
        "script": "infinite_hitting_sync.py", "script_args": ["sugarland"], "has_cookie": True,
        "cc_facility": "2245", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "pure_soccer_woodlands": {
        "name": "Pure Soccer - Woodlands", "platform": "mindbody",
        "script": "pure_soccer_woodlands_sync.py", "has_cookie": True,
        "cc_facility": "2858", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "honey_barry_arena": {
        "name": "Honey Barry Arena", "platform": "finnly",
        "script": "honey_barry_arena_sync.py", "has_cookie": False,
        "cc_facility": "2354", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "academy_usa": {
        "name": "Academy USA", "platform": "mindbody",
        "script": "academy_usa_sync.py", "has_cookie": False,
        "cc_facility": "2105", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "breakaway": {
        "name": "BreakAway Speed Sports", "platform": "mindbody",
        "script": "breakaway_sync.py", "has_cookie": False,
        "cc_facility": "2284", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
}

def load_facilities():
    if FAC_CONFIG.exists():
        with open(FAC_CONFIG) as f:
            return json.load(f)
    with open(FAC_CONFIG, "w") as f:
        json.dump(DEFAULT_FACILITIES, f, indent=2)
    return DEFAULT_FACILITIES

def save_facilities(facs):
    with open(FAC_CONFIG, "w") as f:
        json.dump(facs, f, indent=2)

def get_cookie(fac_id: str) -> Optional[str]:
    with get_db() as db:
        row = db.execute("SELECT value FROM cookies WHERE facility_id=?", (fac_id,)).fetchone()
    return row["value"] if row else None

def set_cookie(fac_id: str, value: str):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO cookies (facility_id, value, updated_at) VALUES (?,?,?)",
            (fac_id, value.strip(), datetime.datetime.utcnow().isoformat())
        )
        db.commit()

def cookie_age_hours(fac_id: str) -> Optional[float]:
    with get_db() as db:
        row = db.execute("SELECT updated_at FROM cookies WHERE facility_id=?", (fac_id,)).fetchone()
    if not row:
        return None
    updated = datetime.datetime.fromisoformat(row["updated_at"])
    return (datetime.datetime.utcnow() - updated).total_seconds() / 3600

def store_csv(fac_id: str, filepath: Path, log_id: int, row_count: int):
    try:
        if not filepath.exists():
            return
        content = filepath.read_bytes()
        with get_db() as db:
            db.execute(
                "INSERT INTO csv_files (facility_id, filename, rows, size_bytes, created_at, log_id, content) VALUES (?,?,?,?,?,?,?)",
                (fac_id, filepath.name, row_count, len(content), datetime.datetime.utcnow().isoformat(), log_id, content)
            )
            db.commit()
        print(f"[csv_store] Stored {filepath.name} for {fac_id}")
    except Exception as e:
        print(f"[csv_store] Error: {e}")

def cleanup_csvs_db():
    """Delete all CSV records and physical files. Runs at 11pm Miami = 3am UTC."""
    with get_db() as db:
        result = db.execute("DELETE FROM csv_files")
        db.commit()
    for f in SCRIPTS_DIR.glob("*.csv"):
        try:
            f.unlink()
        except Exception:
            pass
    print(f"[cleanup] Daily CSV cleanup done")

def build_env(fac_id: str) -> dict:
    env = os.environ.copy()
    cookie = get_cookie(fac_id)
    if cookie:
        env["SYNC_COOKIE"] = cookie
    if fac_id == "honey_barry_arena":
        finnly = get_cookie("honey_barry_arena") or os.environ.get("FINNLY_TOKEN", "")
        if finnly:
            env["FINNLY_TOKEN"] = finnly
    return env

def build_cmd(fac_id: str, fac: dict) -> list:
    script = SCRIPTS_DIR / fac["script"]
    cmd = ["python", str(script)] + fac.get("script_args", [])
    if fac.get("has_cookie"):
        cookie = get_cookie(fac_id)
        if cookie:
            tmp = COOKIES_DIR / f"{fac_id}.txt"
            tmp.write_text(cookie, encoding="utf-8")
            cmd += ["--cookie-file", str(tmp)]
    return cmd

def run_sync_blocking(fac_id: str, fac: dict, trigger: str = "manual") -> int:
    started = datetime.datetime.utcnow().isoformat()
    t0 = datetime.datetime.utcnow()

    with get_db() as db:
        cur = db.execute(
            "INSERT INTO sync_logs (facility_id, started_at, status, trigger) VALUES (?,?,?,?)",
            (fac_id, started, "running", trigger)
        )
        log_id = cur.lastrowid
        db.commit()

    cmd = build_cmd(fac_id, fac)
    output_lines = []

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=build_env(fac_id))
        for line in proc.stdout:
            output_lines.append(line.rstrip())
        proc.wait()
        rc = proc.returncode
    except Exception as e:
        output_lines.append(f"ERROR launching script: {e}")
        rc = -1

    duration = (datetime.datetime.utcnow() - t0).total_seconds()
    full_log = "\n".join(output_lines)
    status = "ok" if rc == 0 else "error"

    row_count = None
    for line in reversed(output_lines):
        m = re.search(r"(\d[\d,]*)\s+rows?", line.replace(",", ""))
        if m:
            row_count = int(m.group(1))
            break

    if rc != 0 and any(kw in full_log.lower() for kw in ["cookie", "401", "403", "expired", "invalid"]):
        status = "cookie_error"

    with get_db() as db:
        db.execute(
            "UPDATE sync_logs SET finished_at=?,status=?,rows=?,duration_s=?,log_output=? WHERE id=?",
            (datetime.datetime.utcnow().isoformat(), status, row_count, duration, full_log, log_id)
        )
        db.commit()

    if rc == 0:
        csv_files = sorted(SCRIPTS_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        for csv_path in csv_files:
            age = datetime.datetime.now().timestamp() - csv_path.stat().st_mtime
            if age < 600:
                store_csv(fac_id, csv_path, log_id, row_count or 0)
                break

    return log_id

scheduler = AsyncIOScheduler()

def schedule_all(facilities: dict):
    scheduler.remove_all_jobs()
    for fac_id, fac in facilities.items():
        if not fac.get("enabled"):
            continue
        for cron in fac.get("schedules", []):
            parts = cron.split()
            if len(parts) == 5:
                mn, hr, dm, mo, dw = parts
                scheduler.add_job(
                    lambda fid=fac_id, f=fac: threading.Thread(target=run_sync_blocking, args=(fid, f, "scheduled"), daemon=True).start(),
                    CronTrigger(minute=mn, hour=hr, day=dm, month=mo, day_of_week=dw),
                    id=f"{fac_id}_{cron.replace(' ','_')}",
                    replace_existing=True,
                    misfire_grace_time=300,
                )
    # 11pm Miami = 3am UTC
    scheduler.add_job(cleanup_csvs_db, CronTrigger(hour=3, minute=0), id="csv_cleanup_daily", replace_existing=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _loop
    _loop = asyncio.get_event_loop()
    init_db()
    facs = load_facilities()
    schedule_all(facs)
    scheduler.start()
    yield
    scheduler.shutdown()

_loop = None
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/facilities", dependencies=[Depends(verify_key)])
def get_facilities():
    facs = load_facilities()
    result = {}
    for fac_id, fac in facs.items():
        with get_db() as db:
            last = db.execute(
                "SELECT id, status, rows, duration_s, started_at FROM sync_logs WHERE facility_id=? ORDER BY id DESC LIMIT 1",
                (fac_id,)
            ).fetchone()
        result[fac_id] = {
            **fac,
            "cookie_age_hours": cookie_age_hours(fac_id) if fac.get("has_cookie") else None,
            "has_cookie_stored": get_cookie(fac_id) is not None,
            "last_sync": dict(last) if last else None,
        }
    return result

@app.post("/api/facilities/{fac_id}/run", dependencies=[Depends(verify_key)])
def run_facility(fac_id: str):
    facs = load_facilities()
    if fac_id not in facs:
        raise HTTPException(404, "Facility not found")
    thread = threading.Thread(target=run_sync_blocking, args=(fac_id, facs[fac_id], "manual"), daemon=True)
    thread.start()
    return {"status": "started"}

class CookieBody(BaseModel):
    value: str

@app.post("/api/facilities/{fac_id}/cookie", dependencies=[Depends(verify_key)])
def update_cookie(fac_id: str, body: CookieBody):
    facs = load_facilities()
    if fac_id not in facs:
        raise HTTPException(404)
    set_cookie(fac_id, body.value)
    return {"status": "ok"}

class ScheduleBody(BaseModel):
    schedules: list[str]
    enabled: bool

@app.put("/api/facilities/{fac_id}/schedule", dependencies=[Depends(verify_key)])
def update_schedule(fac_id: str, body: ScheduleBody):
    facs = load_facilities()
    if fac_id not in facs:
        raise HTTPException(404)
    facs[fac_id]["schedules"] = body.schedules
    facs[fac_id]["enabled"] = body.enabled
    save_facilities(facs)
    schedule_all(facs)
    return {"status": "ok"}

@app.get("/api/logs", dependencies=[Depends(verify_key)])
def get_logs(limit: int = 200, facility_id: Optional[str] = None):
    with get_db() as db:
        if facility_id:
            rows = db.execute("SELECT * FROM sync_logs WHERE facility_id=? ORDER BY id DESC LIMIT ?", (facility_id, limit)).fetchall()
        else:
            rows = db.execute("SELECT * FROM sync_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/logs/{log_id}", dependencies=[Depends(verify_key)])
def get_log(log_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM sync_logs WHERE id=?", (log_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return dict(row)

@app.delete("/api/logs/{log_id}", dependencies=[Depends(verify_key)])
def delete_log(log_id: int):
    with get_db() as db:
        db.execute("DELETE FROM sync_logs WHERE id=?", (log_id,))
        db.commit()
    return {"status": "ok"}

@app.delete("/api/logs", dependencies=[Depends(verify_key)])
def delete_all_logs(facility_id: Optional[str] = None):
    with get_db() as db:
        if facility_id:
            db.execute("DELETE FROM sync_logs WHERE facility_id=?", (facility_id,))
        else:
            db.execute("DELETE FROM sync_logs")
        db.commit()
    return {"status": "ok"}

@app.get("/api/csvs", dependencies=[Depends(verify_key)])
def get_csvs(facility_id: Optional[str] = None):
    with get_db() as db:
        if facility_id:
            rows = db.execute("SELECT id, facility_id, filename, rows, size_bytes, created_at, log_id FROM csv_files WHERE facility_id=? ORDER BY id DESC", (facility_id,)).fetchall()
        else:
            rows = db.execute("SELECT id, facility_id, filename, rows, size_bytes, created_at, log_id FROM csv_files ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.get("/api/csvs/{csv_id}/download")
def download_csv(csv_id: int, key: str = ""):
    if API_KEY and key != API_KEY:
        raise HTTPException(403)
    with get_db() as db:
        row = db.execute("SELECT filename, content FROM csv_files WHERE id=?", (csv_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return Response(content=row["content"], media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{row["filename"]}"'})

@app.delete("/api/csvs/{csv_id}", dependencies=[Depends(verify_key)])
def delete_csv(csv_id: int):
    with get_db() as db:
        db.execute("DELETE FROM csv_files WHERE id=?", (csv_id,))
        db.commit()
    return {"status": "ok"}

@app.delete("/api/csvs", dependencies=[Depends(verify_key)])
def delete_all_csvs(facility_id: Optional[str] = None):
    with get_db() as db:
        if facility_id:
            db.execute("DELETE FROM csv_files WHERE facility_id=?", (facility_id,))
        else:
            db.execute("DELETE FROM csv_files")
        db.commit()
    return {"status": "ok"}

@app.get("/api/health")
def health():
    miami = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
    return {"status": "ok", "utc": datetime.datetime.utcnow().isoformat(), "miami": miami.isoformat()}

frontend_dist = BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(str(frontend_dist / "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")