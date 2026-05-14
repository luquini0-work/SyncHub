# SyncHub — Plataforma de Sync para CatchCorner

Dashboard web para correr y programar syncs de Mindbody/Finnly → CatchCorner.

## Estructura

```
synchub/
├── backend/
│   ├── main.py           ← FastAPI app
│   ├── requirements.txt
│   └── data/             ← SQLite DB + cookies (se crea automático)
│       ├── cookies/      ← archivos .txt de cookies
│       └── facilities.json
├── backend/scripts/      ← PEGAR AQUÍ todos los .py de sync
│   ├── create_the_finish_sync.py
│   ├── houston_sync.py
│   ├── infinite_hitting_sync.py
│   ├── pure_soccer_woodlands_sync.py
│   ├── honey_barry_arena_sync.py
│   ├── academy_usa_sync.py
│   ├── breakaway_sync.py
│   └── config.json       ← config original (para Honey Barry token)
├── frontend/             ← React dashboard
├── Procfile
└── railway.json
```

## Deploy en Railway (gratis)

1. Crear cuenta en https://railway.app (gratis con GitHub)

2. Clonar/subir este repo a GitHub

3. En Railway → New Project → Deploy from GitHub repo

4. Railway detecta automáticamente el railway.json

5. Una vez deployado, ir a Settings → Generate Domain → tenés tu URL pública

## Setup local (desarrollo)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5173

## Poner los scripts

Copiar todos los .py de sync a `backend/scripts/`:
- create_the_finish_sync.py
- houston_sync.py
- infinite_hitting_sync.py
- pure_soccer_woodlands_sync.py
- honey_barry_arena_sync.py
- academy_usa_sync.py
- breakaway_sync.py
- config.json (para Honey Barry token)

## Cookies

Las cookies se guardan en `backend/data/cookies/`.
Desde el dashboard: botón "Cookie" → pegar → Guardar.
No hay que tocar archivos .txt manualmente.

## Schedules

Configurables desde `backend/data/facilities.json` o próximamente desde la UI.
Formato cron: `"0 6 * * *"` = todos los días a las 6am.

## Variables de entorno Railway

No se necesitan. Todo funciona con las credenciales hardcodeadas en los scripts.
Si querés mayor seguridad, podés agregar:
- `SECRET_KEY` para proteger la API con autenticación básica

## Limpieza automática

Los CSVs generados se borran automáticamente todos los días a las 3am.
