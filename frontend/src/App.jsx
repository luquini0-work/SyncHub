import { useState, useEffect, useCallback, useRef } from "react"

const API = import.meta.env.VITE_API_URL || ""
const SESSION_KEY = "synchub_token"

// ── Platform config ───────────────────────────────────────────
const PLAT = {
  mindbody:     { color: "#3B82F6", label: "M" },
  finnly:       { color: "#10B981", label: "F" },
  opencourt:    { color: "#8B5CF6", label: "O" },
  rectimes:     { color: "#EF4444", label: "R" },
  albaplay:     { color: "#F59E0B", label: "A" },
  dserec:       { color: "#06B6D4", label: "D" },
  crestwood:    { color: "#EC4899", label: "C" },
  gymmaster:    { color: "#22C55E", label: "G" },
  setmore:      { color: "#A855F7", label: "S" },
  tripleseat:   { color: "#D97706", label: "T" },
  upperhand:    { color: "#14B8A6", label: "U" },
  glofox:       { color: "#60A5FA", label: "G" },
  sportskey:    { color: "#84CC16", label: "K" },
  perfectvenue: { color: "#F472B6", label: "P" },
  calengoo:     { color: "#C084FC", label: "C" },
  acuity:       { color: "#FB923C", label: "J" },
}
const platInfo = p => PLAT[p] || { color: "#94A3B8", label: "?" }

function miamiTime(iso) {
  if (!iso) return null
  try {
    return new Date(iso + "Z").toLocaleString("en-US", {
      timeZone: "America/New_York",
      hour: "2-digit", minute: "2-digit", hour12: true,
      month: "numeric", day: "numeric"
    })
  } catch { return iso }
}

function timeAgo(iso) {
  if (!iso) return null
  const diff = (Date.now() - new Date(iso + "Z").getTime()) / 1000
  if (diff < 60) return "now"
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

function cookieSt(ageH) {
  if (ageH === null || ageH === undefined) return "none"
  if (ageH > 20) return "expired"
  if (ageH > 12) return "warn"
  return "ok"
}

// ── CSS ───────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  :root {
    --bg:        #F0EDE8;
    --bg2:       #E8E4DE;
    --bg3:       #DEDAD3;
    --surface:   #FAFAF8;
    --border:    #D6D1CA;
    --border2:   #C8C2BA;
    --text1:     #1C1A18;
    --text2:     #5C5751;
    --text3:     #9C9690;
    --accent:    #2D6A4F;
    --accent2:   #40916C;
    --gold:      #C67C1A;
    --red:       #C0392B;
    --blue:      #1B4F8A;
    --radius:    14px;
    --shadow:    0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
    --shadow-md: 0 2px 8px rgba(0,0,0,0.10), 0 8px 24px rgba(0,0,0,0.07);
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text1);
    min-height: 100dvh;
  }

  button { font-family: inherit; cursor: pointer; border: none; background: none; }
  button:active { opacity: 0.75; }
  input, textarea { font-family: inherit; }

  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

  @keyframes spin { to { transform: rotate(360deg) } }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px) } to { opacity: 1; transform: translateY(0) } }
  @keyframes slideUp { from { transform: translateY(100%) } to { transform: translateY(0) } }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .fade-in { animation: fadeIn 0.25s ease both; }

  /* Login */
  .login-wrap {
    min-height: 100dvh;
    background: var(--bg);
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
    background-image: radial-gradient(circle at 20% 80%, rgba(45,106,79,0.06) 0%, transparent 50%),
                      radial-gradient(circle at 80% 20%, rgba(198,124,26,0.06) 0%, transparent 50%);
  }
  .login-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 40px 32px;
    width: 100%; max-width: 340px;
    box-shadow: var(--shadow-md);
  }
  .login-logo {
    width: 48px; height: 48px;
    background: var(--text1);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 20px;
  }
  .login-title { font-size: 20px; font-weight: 600; text-align: center; color: var(--text1); }
  .login-sub { font-size: 13px; color: var(--text3); text-align: center; margin-top: 4px; margin-bottom: 28px; }
  .login-input {
    width: 100%; padding: 13px 16px; font-size: 15px;
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: 10px; color: var(--text1);
    outline: none; transition: border-color 0.15s;
    margin-bottom: 12px;
  }
  .login-input:focus { border-color: var(--accent); }
  .login-btn {
    width: 100%; padding: 13px; font-size: 15px; font-weight: 600;
    background: var(--text1); color: var(--bg);
    border-radius: 10px; transition: opacity 0.15s;
  }
  .login-btn:disabled { opacity: 0.4; cursor: default; }
  .login-err { font-size: 12px; color: var(--red); text-align: center; margin-bottom: 8px; }

  /* Header */
  .header {
    position: sticky; top: 0; z-index: 40;
    background: rgba(240,237,232,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 16px;
    height: 52px;
    display: flex; align-items: center; gap: 12px;
  }
  .header-logo { width: 28px; height: 28px; background: var(--text1); border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .header-title { font-size: 15px; font-weight: 600; color: var(--text1); flex: 1; }
  .tab-btn {
    padding: 5px 12px; font-size: 12px; font-weight: 500;
    border-radius: 7px; color: var(--text2);
    transition: all 0.15s;
  }
  .tab-btn.active { background: var(--text1); color: var(--bg); }
  .logout-btn {
    width: 30px; height: 30px; border-radius: 7px;
    background: var(--bg2); border: 1px solid var(--border);
    font-size: 14px; display: flex; align-items: center; justify-content: center;
    color: var(--text2);
  }

  /* Stats */
  .stats-row {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 8px; padding: 14px 16px 10px;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px;
  }
  .stat-label { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500; margin-bottom: 4px; }
  .stat-value { font-size: 22px; font-weight: 600; color: var(--text1); font-family: 'DM Mono', monospace; }
  .stat-value.warn { color: var(--red); }

  /* Facility list */
  .fac-list {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    margin: 0 16px 16px;
    overflow: hidden;
    box-shadow: var(--shadow);
  }
  .fac-row {
    border-bottom: 1px solid var(--border);
    padding: 11px 14px;
    display: flex; align-items: center; gap: 10px;
    transition: background 0.15s;
  }
  .fac-row:last-child { border-bottom: none; }
  .fac-row.done { opacity: 0.45; }
  .fac-row:active { background: var(--bg); }

  /* Platform dot */
  .plat-dot {
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 700;
    flex-shrink: 0; font-family: 'DM Mono', monospace;
  }

  /* Fac info */
  .fac-info { flex: 1; min-width: 0; }
  .fac-name { font-size: 13px; font-weight: 500; color: var(--text1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .fac-meta { display: flex; align-items: center; gap: 8px; margin-top: 2px; }
  .meta-pill {
    display: flex; align-items: center; gap: 3px;
    font-size: 10px; font-weight: 500;
    padding: 2px 6px; border-radius: 5px;
    white-space: nowrap;
  }

  /* Status indicator */
  .status-icon { font-size: 13px; flex-shrink: 0; font-family: 'DM Mono', monospace; font-weight: 600; }

  /* Actions */
  .actions { display: flex; gap: 5px; flex-shrink: 0; align-items: center; }
  .icon-btn {
    height: 30px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600;
    transition: all 0.15s; flex-shrink: 0;
  }
  .cookie-btn {
    padding: 0 8px; gap: 3px;
    background: var(--bg2); border: 1px solid var(--border);
    color: var(--text2);
  }
  .cookie-btn.expired { background: rgba(192,57,43,0.08); border-color: rgba(192,57,43,0.25); color: var(--red); }
  .cookie-btn.warn { background: rgba(198,124,26,0.08); border-color: rgba(198,124,26,0.25); color: var(--gold); }
  .run-btn {
    width: 56px;
    background: var(--text1); color: var(--bg);
    font-size: 12px; font-weight: 600;
  }
  .run-btn:disabled { opacity: 0.35; cursor: default; }
  .run-btn.running { background: var(--bg2); color: var(--text2); border: 1px solid var(--border); }

  /* Modal overlay */
  .modal-overlay {
    position: fixed; inset: 0; z-index: 100;
    background: rgba(28,26,24,0.5);
    backdrop-filter: blur(4px);
    display: flex; align-items: flex-end; justify-content: center;
  }
  .modal-sheet {
    background: var(--surface);
    border-radius: 20px 20px 0 0;
    border-top: 1px solid var(--border);
    padding: 20px 20px 32px;
    width: 100%; max-width: 480px;
    animation: slideUp 0.25s cubic-bezier(0.34,1.56,0.64,1) both;
    box-shadow: 0 -8px 32px rgba(0,0,0,0.12);
  }
  .sheet-handle { width: 36px; height: 4px; background: var(--border2); border-radius: 2px; margin: 0 auto 18px; }
  .sheet-title { font-size: 15px; font-weight: 600; color: var(--text1); }
  .sheet-sub { font-size: 12px; color: var(--text3); margin-top: 3px; margin-bottom: 16px; }
  .sheet-textarea {
    width: 100%; height: 86px; font-size: 11px;
    font-family: 'DM Mono', monospace; line-height: 1.6;
    background: var(--bg); border: 1.5px solid var(--border);
    border-radius: 10px; padding: 10px 12px; resize: none;
    color: var(--text1); outline: none; transition: border-color 0.15s;
  }
  .sheet-textarea:focus { border-color: var(--accent); }
  .sheet-btns { display: flex; gap: 8px; margin-top: 12px; }
  .sheet-cancel { flex: 1; padding: 12px; font-size: 14px; font-weight: 500; background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; color: var(--text2); }
  .sheet-save { flex: 2; padding: 12px; font-size: 14px; font-weight: 600; background: var(--text1); border-radius: 10px; color: var(--bg); }
  .sheet-save:disabled { opacity: 0.35; cursor: default; }

  /* Log modal */
  .log-sheet {
    background: var(--surface);
    border-radius: 20px 20px 0 0;
    border-top: 1px solid var(--border);
    width: 100%; max-width: 600px;
    max-height: 80dvh; display: flex; flex-direction: column;
    animation: slideUp 0.22s ease both;
    box-shadow: 0 -8px 32px rgba(0,0,0,0.12);
  }
  .log-header { padding: 16px 18px 12px; border-bottom: 1px solid var(--border); }
  .log-pre { flex: 1; overflow: auto; padding: 16px 18px; font-size: 11px; font-family: 'DM Mono', monospace; color: var(--text2); white-space: pre-wrap; word-break: break-all; line-height: 1.7; margin: 0; background: var(--bg); }

  /* Historial */
  .list-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; margin: 0 16px 16px; overflow: hidden; box-shadow: var(--shadow); }
  .list-row { border-bottom: 1px solid var(--border); padding: 10px 14px; display: flex; align-items: center; gap: 10px; }
  .list-row:last-child { border-bottom: none; }

  /* Filter chips */
  .filter-row { display: flex; gap: 6px; padding: 10px 16px 8px; overflow-x: auto; scrollbar-width: none; }
  .filter-row::-webkit-scrollbar { display: none; }
  .chip { padding: 5px 12px; font-size: 11px; font-weight: 500; border-radius: 20px; white-space: nowrap; background: var(--surface); border: 1px solid var(--border); color: var(--text2); transition: all 0.15s; }
  .chip.active { background: var(--text1); border-color: var(--text1); color: var(--bg); }

  /* Empty state */
  .empty { padding: 40px 20px; text-align: center; color: var(--text3); font-size: 13px; }

  /* CSVs */
  .csv-row { border-bottom: 1px solid var(--border); padding: 10px 14px; display: flex; align-items: center; gap: 10px; }
  .csv-row:last-child { border-bottom: none; }
  .dl-btn { padding: 6px 12px; font-size: 11px; font-weight: 600; background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; color: var(--text2); white-space: nowrap; }

  @media (min-width: 640px) {
    .header { padding: 0 24px; }
    .stats-row { padding: 16px 24px 12px; }
    .fac-list { margin: 0 24px 16px; }
    .list-card { margin: 0 24px 16px; }
    .filter-row { padding: 10px 24px 8px; }
  }
`

// ── Login ─────────────────────────────────────────────────────
function Login({ onLogin }) {
  const [pw, setPw] = useState("")
  const [err, setErr] = useState("")
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setLoading(true); setErr("")
    try {
      const r = await fetch(`${API}/api/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: pw }) })
      if (r.ok) { const d = await r.json(); sessionStorage.setItem(SESSION_KEY, d.token); onLogin(d.token) }
      else setErr("Contraseña incorrecta")
    } catch { setErr("Sin conexión") }
    setLoading(false)
  }

  return (
    <div className="login-wrap">
      <div className="login-card fade-in">
        <div className="login-logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="#F0EDE8" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="12" cy="12" r="3" stroke="#F0EDE8" strokeWidth="2"/>
          </svg>
        </div>
        <div className="login-title">SyncHub</div>
        <div className="login-sub">Facility sync dashboard</div>
        <form onSubmit={submit}>
          <input className="login-input" type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="Contraseña" autoFocus />
          {err && <div className="login-err">{err}</div>}
          <button className="login-btn" type="submit" disabled={loading || !pw}>{loading ? "Entrando..." : "Entrar"}</button>
        </form>
      </div>
    </div>
  )
}

// ── Cookie modal ──────────────────────────────────────────────
function CookieModal({ fac, token, onClose, onSaved }) {
  const [val, setVal] = useState("")
  const [saving, setSaving] = useState(false)
  const isToken = ["finnly","upperhand","glofox"].includes(fac.platform)

  async function save() {
    if (!val.trim()) return
    setSaving(true)
    await fetch(`${API}/api/facilities/${fac.id}/cookie`, { method: "POST", headers: { "X-API-Key": token, "Content-Type": "application/json" }, body: JSON.stringify({ value: val }) })
    setSaving(false); onSaved(); onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="sheet-handle" />
        <div className="sheet-title">{fac.name}</div>
        <div className="sheet-sub">{isToken ? "Token de autenticación" : "Cookie de sesión"}{fac.cookie_updated_at ? ` · Actualizada ${timeAgo(fac.cookie_updated_at)}` : ""}</div>
        <textarea className="sheet-textarea" value={val} onChange={e => setVal(e.target.value)} placeholder={isToken ? "eyJhbGci..." : "_session=..."} autoFocus />
        <div className="sheet-btns">
          <button className="sheet-cancel" onClick={onClose}>Cancelar</button>
          <button className="sheet-save" onClick={save} disabled={!val.trim() || saving}>{saving ? "Guardando..." : "Guardar"}</button>
        </div>
      </div>
    </div>
  )
}

// ── Log modal ─────────────────────────────────────────────────
function LogModal({ logId, facName, token, onClose }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    fetch(`${API}/api/logs/${logId}`, { headers: { "X-API-Key": token } }).then(r => r.json()).then(setLog)
  }, [logId])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="log-sheet" onClick={e => e.stopPropagation()}>
        <div className="log-header">
          <div className="sheet-handle" />
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{facName}</div>
              {log && <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 2 }}>
                {log.rows ? `${log.rows.toLocaleString()} filas · ` : ""}{log.duration_s ? `${Math.round(log.duration_s)}s · ` : ""}{log.trigger}
              </div>}
            </div>
            <button onClick={onClose} className="icon-btn cookie-btn" style={{ width: 30 }}>✕</button>
          </div>
        </div>
        <pre className="log-pre">{log?.log_output || "Cargando..."}</pre>
      </div>
    </div>
  )
}

// ── Facility row ──────────────────────────────────────────────
function FacRow({ fac, token, onCookie, onRun, done }) {
  const p = platInfo(fac.platform)
  const ckS = fac.has_cookie ? cookieSt(fac.cookie_age_hours) : null
  const status = fac.running ? "running" : fac.last_sync?.status || "none"
  const lastTime = fac.last_sync?.started_at
  const rows = fac.last_sync?.rows

  const statusColor = status === "ok" ? "var(--accent)" : status === "error" || status === "cookie_error" ? "var(--red)" : status === "running" ? "var(--gold)" : "var(--border2)"
  const statusIcon = status === "ok" ? "✓" : status === "error" || status === "cookie_error" ? "✕" : status === "running" ? "↻" : "–"

  // Cookie button label
  const ckLabel = ckS === "ok" ? timeAgo(fac.cookie_updated_at) : ckS === "warn" ? "pronto" : ckS === "expired" ? "expiró" : null
  const ckIcon = fac.platform === "finnly" || fac.platform === "upperhand" || fac.platform === "glofox" ? "⚿" : "◉"

  return (
    <div className={`fac-row${done ? " done" : ""}`}>
      {/* Platform dot */}
      <div className="plat-dot" style={{ background: p.color + "18", border: `1.5px solid ${p.color}40`, color: p.color }}>
        {p.label}
      </div>

      {/* Info */}
      <div className="fac-info">
        <div className="fac-name">{fac.name}</div>
        <div className="fac-meta">
          {lastTime && (
            <span className="meta-pill" style={{ background: "rgba(45,106,79,0.08)", color: "var(--accent)" }}>
              <span style={{ fontSize: 10 }}>✓</span> {miamiTime(lastTime)}
            </span>
          )}
          {rows != null && (
            <span style={{ fontSize: 10, color: "var(--text3)", fontFamily: "'DM Mono', monospace" }}>
              {rows.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="status-icon" style={{ color: statusColor, animation: status === "running" ? "spin 1s linear infinite" : "none" }}>
        {statusIcon}
      </div>

      {/* Cookie btn (only if has_cookie) */}
      {fac.has_cookie && (
        <button
          className={`icon-btn cookie-btn${ckS === "expired" ? " expired" : ckS === "warn" ? " warn" : ""}`}
          onClick={() => onCookie(fac)}
          style={{ minWidth: 30, padding: ckLabel ? "0 7px" : "0 8px", gap: 4 }}
          title="Actualizar cookie"
        >
          <span style={{ fontSize: 12 }}>{ckIcon}</span>
          {ckLabel && <span style={{ fontSize: 9, fontFamily: "'DM Mono', monospace" }}>{ckLabel}</span>}
        </button>
      )}

      {/* Run btn */}
      <button
        className={`icon-btn run-btn${fac.running ? " running" : ""}`}
        onClick={() => onRun(fac.id)}
        disabled={fac.running}
        style={{ animation: fac.running ? "pulse 1.2s ease infinite" : "none" }}
      >
        {fac.running ? "↻" : "Run"}
      </button>
    </div>
  )
}

// ── Main app ──────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(SESSION_KEY) || "")
  const [facilities, setFacilities] = useState({})
  const [logs, setLogs] = useState([])
  const [csvs, setCsvs] = useState([])
  const [view, setView] = useState("dashboard")
  const [cookieFac, setCookieFac] = useState(null)
  const [logModal, setLogModal] = useState(null)
  const [filterFac, setFilterFac] = useState(null)

  const H = { "X-API-Key": token }

  const fetchFacs = useCallback(async () => {
    if (!token) return
    try {
      const r = await fetch(`${API}/api/facilities`, { headers: H })
      const d = await r.json()
      setFacilities(prev => {
        const m = {}
        for (const id in d) m[id] = { ...d[id], id, running: prev[id]?.running || false }
        return m
      })
    } catch {}
  }, [token])

  const fetchLogs = useCallback(async () => {
    if (!token) return
    try { const r = await fetch(`${API}/api/logs?limit=200`, { headers: H }); setLogs(await r.json()) } catch {}
  }, [token])

  const fetchCsvs = useCallback(async () => {
    if (!token) return
    try { const r = await fetch(`${API}/api/csvs`, { headers: H }); setCsvs(await r.json()) } catch {}
  }, [token])

  useEffect(() => {
    if (!token) return
    fetchFacs(); fetchLogs(); fetchCsvs()
    const t = setInterval(() => { fetchFacs(); fetchLogs() }, 15000)
    return () => clearInterval(t)
  }, [token])

  async function runFac(id) {
    setFacilities(p => ({ ...p, [id]: { ...p[id], running: true } }))
    await fetch(`${API}/api/facilities/${id}/run`, { method: "POST", headers: H })
    const poll = setInterval(async () => {
      const r = await fetch(`${API}/api/facilities`, { headers: H })
      const d = await r.json()
      if (d[id]?.last_sync?.status !== "running") {
        clearInterval(poll)
        setFacilities(p => ({ ...p, [id]: { ...d[id], id, running: false } }))
        fetchLogs(); fetchCsvs()
      }
    }, 3000)
    setTimeout(() => clearInterval(poll), 300000)
  }

  if (!token) return <><style>{CSS}</style><Login onLogin={setToken} /></>

  const facList = Object.values(facilities)
  const today = new Date().toISOString().slice(0, 10)
  const syncsToday = logs.filter(l => l.started_at?.startsWith(today)).length
  const cookieAlerts = facList.filter(f => f.has_cookie && cookieSt(f.cookie_age_hours) === "expired").length

  // "Done" logic: facility had a successful sync today
  const doneToday = new Set(
    logs.filter(l => l.started_at?.startsWith(today) && l.status === "ok").map(l => l.facility_id)
  )
  // All done = all enabled facilities synced ok today
  const enabledFacs = facList.filter(f => f.enabled !== false)
  const allDone = enabledFacs.length > 0 && enabledFacs.every(f => doneToday.has(f.id))

  // Sort: running first, then errors, then pending, then done
  const sorted = [...facList].sort((a, b) => {
    const score = f => {
      if (f.running) return 0
      if (f.last_sync?.status === "error" || f.last_sync?.status === "cookie_error") return 1
      if (!doneToday.has(f.id)) return 2
      return 3
    }
    return score(a) - score(b)
  })

  const filteredLogs = filterFac ? logs.filter(l => l.facility_id === filterFac) : logs
  const filteredCsvs = filterFac ? csvs.filter(c => c.facility_id === filterFac) : csvs

  return (
    <>
      <style>{CSS}</style>

      {/* Header */}
      <div className="header">
        <div className="header-logo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="#F0EDE8" strokeWidth="2.5" strokeLinecap="round"/>
            <circle cx="12" cy="12" r="3" stroke="#F0EDE8" strokeWidth="2.5"/>
          </svg>
        </div>
        <div className="header-title">SyncHub</div>
        {["dashboard","logs","csvs"].map(v => (
          <button key={v} className={`tab-btn${view === v ? " active" : ""}`} onClick={() => { setView(v); setFilterFac(null) }}>
            {v === "dashboard" ? "Home" : v === "logs" ? "Historial" : "CSVs"}
          </button>
        ))}
        <button className="logout-btn" onClick={() => { sessionStorage.removeItem(SESSION_KEY); setToken("") }} title="Salir">↩</button>
      </div>

      <div style={{ maxWidth: 640, margin: "0 auto", paddingBottom: 80 }}>

        {/* DASHBOARD */}
        {view === "dashboard" && <>
          <div className="stats-row">
            <div className="stat-card"><div className="stat-label">Syncs hoy</div><div className="stat-value">{syncsToday}</div></div>
            <div className="stat-card"><div className="stat-label">Facilities</div><div className="stat-value">{facList.length}</div></div>
            <div className="stat-card"><div className="stat-label">Cookies</div><div className={`stat-value${cookieAlerts > 0 ? " warn" : ""}`}>{cookieAlerts > 0 ? `${cookieAlerts} ⚠` : "OK"}</div></div>
          </div>

          {/* All-done banner */}
          {allDone && (
            <div style={{ margin: "0 16px 10px", padding: "10px 14px", background: "rgba(45,106,79,0.08)", border: "1px solid rgba(45,106,79,0.2)", borderRadius: 10, fontSize: 12, color: "var(--accent)", fontWeight: 500, display: "flex", alignItems: "center", gap: 6 }}>
              <span>✓</span> Todas las facilities sincronizadas hoy
            </div>
          )}

          <div className="fac-list">
            {sorted.map(fac => (
              <FacRow
                key={fac.id} fac={fac} token={token}
                done={!allDone && doneToday.has(fac.id)}
                onCookie={f => setCookieFac(f)}
                onRun={id => runFac(id)}
              />
            ))}
          </div>
        </>}

        {/* HISTORIAL */}
        {view === "logs" && <>
          <div className="filter-row">
            <button className={`chip${!filterFac ? " active" : ""}`} onClick={() => setFilterFac(null)}>Todos</button>
            {Object.values(facilities).map(f => (
              <button key={f.id} className={`chip${filterFac === f.id ? " active" : ""}`} onClick={() => setFilterFac(f.id)}>
                {f.name.split(" ").slice(0, 2).join(" ")}
              </button>
            ))}
          </div>
          <div className="list-card">
            {filteredLogs.length === 0 && <div className="empty">Sin registros</div>}
            {filteredLogs.map(log => {
              const fac = facilities[log.facility_id]
              const p = platInfo(fac?.platform)
              const st = log.status
              const stColor = st === "ok" ? "var(--accent)" : st === "error" || st === "cookie_error" ? "var(--red)" : "var(--gold)"
              const stIcon = st === "ok" ? "✓" : st === "error" || st === "cookie_error" ? "✕" : "↻"
              return (
                <div key={log.id} className="list-row" style={{ cursor: log.log_output ? "pointer" : "default" }} onClick={() => log.log_output && setLogModal({ id: log.id, name: fac?.name })}>
                  <div className="plat-dot" style={{ background: p.color + "18", border: `1.5px solid ${p.color}40`, color: p.color, width: 24, height: 24, fontSize: 8 }}>{p.label}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{fac?.name || log.facility_id}</div>
                    <div style={{ fontSize: 10, color: "var(--text3)", marginTop: 2, fontFamily: "'DM Mono', monospace" }}>
                      {miamiTime(log.started_at)}{log.rows ? ` · ${log.rows.toLocaleString()} filas` : ""}{log.duration_s ? ` · ${Math.round(log.duration_s)}s` : ""}
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: stColor, fontWeight: 600, fontFamily: "'DM Mono', monospace" }}>{stIcon}</div>
                </div>
              )
            })}
          </div>
        </>}

        {/* CSVs */}
        {view === "csvs" && <>
          <div style={{ padding: "10px 16px 6px", fontSize: 11, color: "var(--text3)" }}>
            {csvs.length} archivos · limpieza automática 11pm Miami
          </div>
          <div className="list-card">
            {filteredCsvs.length === 0 && <div className="empty">Sin CSVs</div>}
            {filteredCsvs.map(csv => (
              <div key={csv.id} className="csv-row">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontFamily: "'DM Mono', monospace", color: "var(--blue)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {csv.filename}
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text3)", marginTop: 2 }}>
                    {facilities[csv.facility_id]?.name} · {csv.rows?.toLocaleString()} filas · {csv.size_bytes ? `${(csv.size_bytes/1024).toFixed(1)}KB` : ""}
                  </div>
                </div>
                <button className="dl-btn" onClick={() => { const a = document.createElement("a"); a.href = `${API}/api/csvs/${csv.id}/download?key=${token}`; a.download = csv.filename; a.click() }}>
                  ↓ Descargar
                </button>
              </div>
            ))}
          </div>
        </>}
      </div>

      {cookieFac && <CookieModal fac={cookieFac} token={token} onClose={() => setCookieFac(null)} onSaved={fetchFacs} />}
      {logModal && <LogModal logId={logModal.id} facName={logModal.name} token={token} onClose={() => setLogModal(null)} />}
    </>
  )
}