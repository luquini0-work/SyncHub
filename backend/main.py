"""
SyncHub Backend — FastAPI
Las credenciales vienen SOLO de variables de entorno (Railway → Variables).
Los scripts reciben las credenciales via env vars, no via archivos.
"""

import os, json, subprocess, threading, datetime, sqlite3, asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR    = BASE_DIR / "data"
DB_PATH     = DATA_DIR / "synchub.db"
COOKIES_DIR = DATA_DIR / "cookies"
FAC_CONFIG  = DATA_DIR / "facilities.json"

DATA_DIR.mkdir(exist_ok=True)
COOKIES_DIR.mkdir(exist_ok=True)
SCRIPTS_DIR.mkdir(exist_ok=True)

# ── Optional API key auth ──────────────────────────────────────────────────────

API_KEY = os.environ.get("SYNCHUB_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_key(key: str = Security(api_key_header)):
    if not API_KEY:
        return  # no key configured = open
    if key != API_KEY:
        raise HTTPException(403, "Invalid API key")

# ── Database ───────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT    NOT NULL,
                started_at  TEXT    NOT NULL,
                finished_at TEXT,
                status      TEXT    NOT NULL DEFAULT 'running',
                rows        INTEGER,
                duration_s  REAL,
                trigger     TEXT    DEFAULT 'manual',
                log_output  TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                facility_id TEXT PRIMARY KEY,
                value       TEXT,
                updated_at  TEXT
            )
        """)
        db.commit()

# ── Facilities config ──────────────────────────────────────────────────────────

DEFAULT_FACILITIES = {
    "create_the_finish": {
        "name": "Create The Finish", "platform": "mindbody",
        "script": "create_the_finish_sync.py", "has_cookie": True,
        "cc_facility": "2361", "schedules": ["0 6 * * *", "0 12 * * *", "0 18 * * *"], "enabled": True,
    },
    "houston_pickleball": {
        "name": "Houston Pickleball", "platform": "mindbody",
        "script": "houston_sync.py", "script_args": ["pickleball"], "has_cookie": True,
        "cc_facility": "2224", "schedules": ["0 7 * * *"], "enabled": True,
    },
    "houston_badminton": {
        "name": "Houston Badminton", "platform": "mindbody",
        "script": "houston_sync.py", "script_args": ["badminton"], "has_cookie": True,
        "cc_facility": "2225", "schedules": ["5 7 * * *"], "enabled": True,
    },
    "infinite_humble": {
        "name": "Infinite Hitting - Humble", "platform": "mindbody",
        "script": "infinite_hitting_sync.py", "script_args": ["humble"], "has_cookie": True,
        "cc_facility": "2246", "schedules": ["0 6 * * *"], "enabled": True,
    },
    "infinite_sugarland": {
        "name": "Infinite Hitting - Sugar Land", "platform": "mindbody",
        "script": "infinite_hitting_sync.py", "script_args": ["sugarland"], "has_cookie": True,
        "cc_facility": "2245", "schedules": ["0 6 * * *"], "enabled": True,
    },
    "pure_soccer_woodlands": {
        "name": "Pure Soccer - Woodlands", "platform": "mindbody",
        "script": "pure_soccer_woodlands_sync.py", "has_cookie": True,
        "cc_facility": "2858", "schedules": ["0 8 * * *", "0 17 * * *"], "enabled": True,
    },
    "honey_barry_arena": {
        "name": "Honey Barry Arena", "platform": "finnly",
        "script": "honey_barry_arena_sync.py", "has_cookie": False,
        "cc_facility": "2354", "schedules": ["0 6,10,14,18,22 * * *"], "enabled": True,
    },
    "academy_usa": {
        "name": "Academy USA", "platform": "mindbody",
        "script": "academy_usa_sync.py", "has_cookie": False,
        "cc_facility": "2105", "schedules": ["0 7 * * *"], "enabled": True,
    },
    "breakaway": {
        "name": "BreakAway Speed Sports", "platform": "mindbody",
        "script": "breakaway_sync.py", "has_cookie": False,
        "cc_facility": "2284", "schedules": ["0 7 * * *"], "enabled": True,
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

# ── Cookie management (stored in DB, not filesystem) ──────────────────────────

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

# ── Script runner ──────────────────────────────────────────────────────────────

_loop = None

def build_env(fac_id: str) -> dict:
    """Pass credentials as env vars to the subprocess — never as args."""
    env = os.environ.copy()
    # Cookie
    cookie = get_cookie(fac_id)
    if cookie:
        env["SYNC_COOKIE"] = cookie
    # Finnly token from env
    if fac_id == "honey_barry_arena":
        env["FINNLY_TOKEN"] = os.environ.get("FINNLY_TOKEN", "")
    return env

def build_cmd(fac_id: str, fac: dict) -> list:
    script = SCRIPTS_DIR / fac["script"]
    cmd = ["python", str(script)] + fac.get("script_args", [])
    # Pass cookie via env var SYNC_COOKIE (scripts must read it)
    # Cookie file fallback: write temp file if needed
    if fac.get("has_cookie"):
        cookie = get_cookie(fac_id)
        if cookie:
            # Write to temp cookie file for scripts that use --cookie-file
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
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=build_env(fac_id)
        )
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

    # Detect rows
    rows = None
    import re
    for line in reversed(output_lines):
        m = re.search(r"(\d[\d,]*)\s+rows", line.replace(",", ""))
        if m:
            rows = int(m.group(1))
            break

    # Detect cookie errors
    if any(kw in full_log.lower() for kw in ["cookie", "401", "403", "expired", "invalid"]):
        if rc != 0:
            status = "cookie_error"

    with get_db() as db:
        db.execute(
            "UPDATE sync_logs SET finished_at=?,status=?,rows=?,duration_s=?,log_output=? WHERE id=?",
            (datetime.datetime.utcnow().isoformat(), status, rows, duration, full_log, log_id)
        )
        db.commit()

    return log_id

# ── CSV cleanup ────────────────────────────────────────────────────────────────

def cleanup_csvs():
    cutoff = datetime.datetime.now().timestamp() - 86400
    deleted = 0
    for f in SCRIPTS_DIR.glob("*.csv"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted += 1
    # Also clean temp cookie files
    for f in COOKIES_DIR.glob("*.txt"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
    if deleted:
        print(f"[cleanup] {deleted} CSV files deleted")

# ── Scheduler ─────────────────────────────────────────────────────────────────

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
                    lambda fid=fac_id, f=fac: threading.Thread(
                        target=run_sync_blocking, args=(fid, f, "scheduled"), daemon=True
                    ).start(),
                    CronTrigger(minute=mn, hour=hr, day=dm, month=mo, day_of_week=dw),
                    id=f"{fac_id}_{cron.replace(' ','_')}",
                    replace_existing=True,
                    misfire_grace_time=300,
                )
    scheduler.add_job(cleanup_csvs, CronTrigger(hour=3, minute=0), id="csv_cleanup", replace_existing=True)

# ── App ────────────────────────────────────────────────────────────────────────

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

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)  # hide docs in prod

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/facilities", dependencies=[Depends(verify_key)])
def get_facilities():
    facs = load_facilities()
    result = {}
    for fac_id, fac in facs.items():
        with get_db() as db:
            last = db.execute(
                "SELECT status, rows, duration_s, started_at FROM sync_logs WHERE facility_id=? ORDER BY id DESC LIMIT 1",
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
    fac = facs[fac_id]
    thread = threading.Thread(target=run_sync_blocking, args=(fac_id, fac, "manual"), daemon=True)
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
def get_logs(limit: int = 100, facility_id: Optional[str] = None):
    with get_db() as db:
        if facility_id:
            rows = db.execute(
                "SELECT * FROM sync_logs WHERE facility_id=? ORDER BY id DESC LIMIT ?",
                (facility_id, limit)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM sync_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/logs/{log_id}", dependencies=[Depends(verify_key)])
def get_log(log_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM sync_logs WHERE id=?", (log_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return dict(row)

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat()}

# ── Serve React ────────────────────────────────────────────────────────────────

frontend_dist = BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(str(frontend_dist / "index.html"))
