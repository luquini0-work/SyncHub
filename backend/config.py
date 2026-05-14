"""
Todas las credenciales vienen de variables de entorno.
En Railway: Settings → Variables → agregar cada una.
En local: crear un archivo .env (NO subir a GitHub).
"""
import os
from pathlib import Path

def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

# ── CatchCorner accounts ───────────────────────────────────────────────────────
CC_ACCOUNTS = {
    "cc_main": {
        "username": env("CC_MAIN_USER"),
        "password": env("CC_MAIN_PASS"),
    },
    "cc_breakaway": {
        "username": env("CC_BREAKAWAY_USER"),
        "password": env("CC_BREAKAWAY_PASS"),
    },
    "cc_jesse": {
        "username": env("CC_JESSE_USER"),
        "password": env("CC_JESSE_PASS"),
    },
    "cc_ctf": {
        "username": env("CC_CTF_USER"),
        "password": env("CC_CTF_PASS"),
    },
    "cc_pickleball": {
        "username": env("CC_PICKLEBALL_USER"),
        "password": env("CC_PICKLEBALL_PASS"),
    },
    "cc_badminton": {
        "username": env("CC_BADMINTON_USER"),
        "password": env("CC_BADMINTON_PASS"),
    },
    "cc_humble": {
        "username": env("CC_HUMBLE_USER"),
        "password": env("CC_HUMBLE_PASS"),
    },
    "cc_sugarland": {
        "username": env("CC_SUGARLAND_USER"),
        "password": env("CC_SUGARLAND_PASS"),
    },
    "cc_puresoccer": {
        "username": env("CC_PURESOCCER_USER"),
        "password": env("CC_PURESOCCER_PASS"),
    },
    "cc_honey": {
        "username": env("CC_HONEY_USER"),
        "password": env("CC_HONEY_PASS"),
    },
}

# ── Facilities ─────────────────────────────────────────────────────────────────
FACILITIES = {
    "create_the_finish": {
        "name": "Create The Finish",
        "platform": "mindbody",
        "script": "create_the_finish_sync.py",
        "cookie_file": "cookie_ctf.txt",
        "cc_account": "cc_ctf",
        "cc_facility": "2361",
        "schedules": ["0 6 * * *", "0 12 * * *", "0 18 * * *"],
        "enabled": True,
    },
    "houston_pickleball": {
        "name": "Houston Pickleball",
        "platform": "mindbody",
        "script": "houston_sync.py",
        "script_args": ["pickleball"],
        "cookie_file": "cookie_pickleball.txt",
        "cc_account": "cc_pickleball",
        "cc_facility": "2224",
        "schedules": ["0 7 * * *"],
        "enabled": True,
    },
    "houston_badminton": {
        "name": "Houston Badminton",
        "platform": "mindbody",
        "script": "houston_sync.py",
        "script_args": ["badminton"],
        "cookie_file": "cookie_badminton.txt",
        "cc_account": "cc_badminton",
        "cc_facility": "2225",
        "schedules": ["5 7 * * *"],
        "enabled": True,
    },
    "infinite_humble": {
        "name": "Infinite Hitting - Humble",
        "platform": "mindbody",
        "script": "infinite_hitting_sync.py",
        "script_args": ["humble"],
        "cookie_file": "cookie_humble.txt",
        "cc_account": "cc_humble",
        "cc_facility": "2246",
        "schedules": ["0 6 * * *"],
        "enabled": True,
    },
    "infinite_sugarland": {
        "name": "Infinite Hitting - Sugar Land",
        "platform": "mindbody",
        "script": "infinite_hitting_sync.py",
        "script_args": ["sugarland"],
        "cookie_file": "cookie_sugarland.txt",
        "cc_account": "cc_sugarland",
        "cc_facility": "2245",
        "schedules": ["0 6 * * *"],
        "enabled": True,
    },
    "pure_soccer_woodlands": {
        "name": "Pure Soccer - Woodlands",
        "platform": "mindbody",
        "script": "pure_soccer_woodlands_sync.py",
        "cookie_file": "cookie_puresoccer.txt",
        "cc_account": "cc_puresoccer",
        "cc_facility": "2858",
        "schedules": ["0 8 * * *", "0 17 * * *"],
        "enabled": True,
    },
    "honey_barry_arena": {
        "name": "Honey Barry Arena",
        "platform": "finnly",
        "script": "honey_barry_arena_sync.py",
        "cookie_file": None,
        "cc_account": "cc_honey",
        "cc_facility": "2354",
        "schedules": ["0 6,10,14,18,22 * * *"],
        "enabled": True,
    },
    "academy_usa": {
        "name": "Academy USA",
        "platform": "mindbody",
        "script": "academy_usa_sync.py",
        "cookie_file": None,
        "cc_account": "cc_main",
        "cc_facility": "2105",
        "schedules": ["0 7 * * *"],
        "enabled": True,
    },
    "breakaway": {
        "name": "BreakAway Speed Sports",
        "platform": "mindbody",
        "script": "breakaway_sync.py",
        "cookie_file": None,
        "cc_account": "cc_breakaway",
        "cc_facility": "2284",
        "schedules": ["0 7 * * *"],
        "enabled": True,
    },
}
