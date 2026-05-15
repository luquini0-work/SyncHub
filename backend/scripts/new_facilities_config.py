# ══════════════════════════════════════════════════════════════
# NEW FACILITIES — paste this into DEFAULT_FACILITIES in main.py
# after the existing 9 facilities
# ══════════════════════════════════════════════════════════════

NEW_FACILITIES = {
    # ── No cookie needed ──────────────────────────────────────
    "ctx_fieldhouse": {
        "name": "CTX Fieldhouse", "platform": "rectimes",
        "script": "ctx_fieldhouse_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "opencourt_fieldhouse": {
        "name": "OpenCourt - The Fieldhouse", "platform": "opencourt",
        "script": "opencourt_sync.py", "script_args": ["fieldhouse"], "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "capital_city_barton": {
        "name": "Capital City Pickleball - Barton Rooftop", "platform": "opencourt",
        "script": "opencourt_sync.py", "script_args": ["barton"], "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "capital_city_downtown": {
        "name": "Capital City Pickleball - Downtown", "platform": "opencourt",
        "script": "opencourt_sync.py", "script_args": ["downtown"], "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "brandeis_athletic": {
        "name": "Brandeis Athletic", "platform": "dserec",
        "script": "brandeis_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "crestwood_pickleball": {
        "name": "Crestwood Pickleball", "platform": "crestwood",
        "script": "crestwood_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "six_iron": {
        "name": "6ix Iron", "platform": "albaplay",
        "script": "six_iron_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "western_fair": {
        "name": "Western Fair", "platform": "finnly",
        "script": "western_fair_sync.py", "has_cookie": False,
        "cc_facility": "572", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "usports": {
        "name": "USports", "platform": "calengoo",
        "script": "usports_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "jump_shot_gym": {
        "name": "Jump Shot Gym", "platform": "acuity",
        "script": "jump_shot_gym_sync.py", "has_cookie": False,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },

    # ── Token/Cookie (manual update via SyncHub 🍪) ───────────
    "dbat": {
        "name": "D-BAT", "platform": "upperhand",
        "script": "dbat_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "neon_energy": {
        "name": "Neon Energy Sports", "platform": "upperhand",
        "script": "neon_energy_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "tjs_sports": {
        "name": "TJ's Sports Club", "platform": "glofox",
        "script": "tjs_sports_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "the_st_james": {
        "name": "The St. James", "platform": "tripleseat",
        "script": "the_st_james_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "home_court": {
        "name": "Home Court", "platform": "gymmaster",
        "script": "home_court_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "millworks": {
        "name": "MillWorks", "platform": "setmore",
        "script": "millworks_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "commish_field": {
        "name": "Commish Field / Soccer Post", "platform": "sportskey",
        "script": "commish_field_sync.py", "has_cookie": True,
        "cc_facility": "1591", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
    "christs_haven": {
        "name": "Christ's Haven", "platform": "perfectvenue",
        "script": "christs_haven_sync.py", "has_cookie": True,
        "cc_facility": "SET_CC_FAC", "schedules": MIAMI_SCHEDULES, "enabled": True,
    },
}

# ══════════════════════════════════════════════════════════════
# RAILWAY VARIABLES to add (CC credentials per facility)
# Format: CC_{FAC_ID_UPPER}_USER / CC_{FAC_ID_UPPER}_PASS / CC_{FAC_ID_UPPER}_FAC
# ══════════════════════════════════════════════════════════════
"""
CC_CTX_USER / CC_CTX_PASS / CC_CTX_FAC
CC_OPENCOURT_FIELDHOUSE_USER / CC_OPENCOURT_FIELDHOUSE_PASS / CC_OPENCOURT_FIELDHOUSE_FAC
CC_BARTON_USER / CC_BARTON_PASS / CC_BARTON_FAC
CC_DOWNTOWN_USER / CC_DOWNTOWN_PASS / CC_DOWNTOWN_FAC
CC_BRANDEIS_USER / CC_BRANDEIS_PASS / CC_BRANDEIS_FAC
CC_CRESTWOOD_USER / CC_CRESTWOOD_PASS / CC_CRESTWOOD_FAC
CC_SIX_IRON_USER / CC_SIX_IRON_PASS / CC_SIX_IRON_FAC
CC_WESTERN_FAIR_USER=catchcornersetup206@gmail.com / CC_WESTERN_FAIR_PASS=@SsU*BOr8$onh03&EiWc%$zuEh^qFt / CC_WESTERN_FAIR_FAC=572
CC_USPORTS_USER / CC_USPORTS_PASS / CC_USPORTS_FAC
CC_JUMP_SHOT_USER / CC_JUMP_SHOT_PASS / CC_JUMP_SHOT_FAC
CC_DBAT_USER / CC_DBAT_PASS / CC_DBAT_FAC
CC_NEON_USER / CC_NEON_PASS / CC_NEON_FAC
CC_TJS_USER / CC_TJS_PASS / CC_TJS_FAC
CC_ST_JAMES_USER / CC_ST_JAMES_PASS / CC_ST_JAMES_FAC
CC_HOME_COURT_USER / CC_HOME_COURT_PASS / CC_HOME_COURT_FAC
CC_MILLWORKS_USER / CC_MILLWORKS_PASS / CC_MILLWORKS_FAC
CC_COMMISH_USER=localloginformainte.n.anc.e.1.99.40@gmail.com / CC_COMMISH_PASS=H#r6v8npPgpuqXayO6x*nqKQJDU524 / CC_COMMISH_FAC=1591
CC_CHRISTS_HAVEN_USER / CC_CHRISTS_HAVEN_PASS / CC_CHRISTS_HAVEN_FAC
"""
