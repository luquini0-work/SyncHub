import { useState, useEffect, useCallback } from "react"

const API = import.meta.env.VITE_API_URL || ""
const SESSION_KEY = "synchub_token"

const PLAT = {
  mindbody:     { color: "#2563EB", label: "M" },
  finnly:       { color: "#059669", label: "F" },
  opencourt:    { color: "#7C3AED", label: "O" },
  rectimes:     { color: "#DC2626", label: "R" },
  albaplay:     { color: "#D97706", label: "A" },
  dserec:       { color: "#0891B2", label: "D" },
  crestwood:    { color: "#BE185D", label: "C" },
  gymmaster:    { color: "#16A34A", label: "G" },
  setmore:      { color: "#9333EA", label: "S" },
  tripleseat:   { color: "#B45309", label: "T" },
  upperhand:    { color: "#0F766E", label: "U" },
  glofox:       { color: "#1D4ED8", label: "G" },
  sportskey:    { color: "#65A30D", label: "K" },
  perfectvenue: { color: "#DB2777", label: "P" },
  calengoo:     { color: "#7C3AED", label: "C" },
  acuity:       { color: "#EA580C", label: "J" },
}

function platInfo(p) { return PLAT[p] || { color: "#6B7280", label: "?" } }

function timeAgo(iso) {
  if (!iso) return null
  const diff = (Date.now() - new Date(iso + "Z").getTime()) / 1000
  if (diff < 60) return "ahora"
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

function miamiTime(iso) {
  if (!iso) return null
  try {
    return new Date(iso + "Z").toLocaleString("en-US", {
      timeZone: "America/New_York",
      hour: "2-digit", minute: "2-digit",
      hour12: true, month: "numeric", day: "numeric"
    })
  } catch { return iso }
}

function cookieStatus(ageH) {
  if (ageH === null || ageH === undefined) return "none"
  if (ageH > 20) return "expired"
  if (ageH > 12) return "warn"
  return "ok"
}

// ── CSS ───────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  body {
    font-family: 'Syne', sans-serif;
    background: #fff;
    color: #0A0A0A;
    min-height: 100dvh;
  }

  ::-webkit-scrollbar { width: 3px; }
  ::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 2px; }

  button { font-family: inherit; }
  button:active { opacity: 0.75; }

  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

  @keyframes shimmer {
    0%   { box-shadow: 0 0 0 0 rgba(0,0,0,0.06), inset 0 0 0 1px rgba(0,0,0,0.08); background: #fff; }
    50%  { box-shadow: 0 0 0 3px rgba(0,0,0,0.04), inset 0 0 0 1px rgba(0,0,0,0.15); background: #f9f9f9; }
    100% { box-shadow: 0 0 0 0 rgba(0,0,0,0.06), inset 0 0 0 1px rgba(0,0,0,0.08); background: #fff; }
  }

  .fac-row {
    border-bottom: 1px solid #F0F0F0;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: background 0.15s;
    animation: fadeIn 0.3s ease both;
    position: relative;
  }
  .fac-row:last-child { border-bottom: none; }
  .fac-row:hover { background: #FAFAFA; }
  .fac-row.running {
    animation: shimmer 1.6s ease-in-out infinite;
    border-left: 2px solid #0A0A0A;
  }
  .fac-row.error { border-left: 2px solid #E53E3E; }
  .fac-row.cookie-warn { border-left: 2px solid #D97706; }

  .run-btn {
    height: 30px;
    padding: 0 14px;
    border-radius: 4px;
    background: #0A0A0A;
    border: none;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    cursor: pointer;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    transition: background 0.15s;
  }
  .run-btn:hover { background: #333; }
  .run-btn:disabled {
    background: #F0F0F0;
    color: #999;
    cursor: not-allowed;
  }

  .icon-btn {
    width: 30px;
    height: 30px;
    border-radius: 4px;
    background: transparent;
    border: 1px solid #E8E8E8;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #888;
    transition: border-color 0.15s, color 0.15s;
  }
  .icon-btn:hover { border-color: #0A0A0A; color: #0A0A0A; }
  .icon-btn.warn { border-color: #F6AD55; color: #D97706; }
  .icon-btn.expired { border-color: #FC8181; color: #E53E3E; }

  .tab {
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: transparent;
    border: none;
    cursor: pointer;
    color: #AAAAAA;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab.active { color: #0A0A0A; border-bottom-color: #0A0A0A; }

  .chip {
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
    border: 1px solid #E8E8E8;
    border-radius: 20px;
    color: #888;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .chip.active { background: #0A0A0A; border-color: #0A0A0A; color: #fff; }

  .stat-block {
    padding: 16px 20px;
    border-right: 1px solid #F0F0F0;
  }
  .stat-block:last-child { border-right: none; }

  .log-row {
    border-bottom: 1px solid #F5F5F5;
    padding: 11px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    animation: fadeIn 0.2s ease both;
  }
  .log-row:last-child { border-bottom: none; }
  .log-row:hover { background: #FAFAFA; }

  .modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.4);
    display: flex; align-items: flex-end; justify-content: center;
    z-index: 100;
    backdrop-filter: blur(2px);
  }
  .modal-sheet {
    background: #fff;
    border-radius: 16px 16px 0 0;
    padding: 24px 20px 36px;
    width: 100%; max-width: 480px;
    border-top: 1px solid #E8E8E8;
  }
  .modal-handle {
    width: 32px; height: 3px;
    background: #E0E0E0;
    border-radius: 2px;
    margin: 0 auto 20px;
  }
`

// ── Login ─────────────────────────────────────────────────────
function LoginScreen({ onLogin }) {
  const [pw, setPw] = useState("")
  const [err, setErr] = useState("")
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setLoading(true); setErr("")
    try {
      const r = await fetch(`${API}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw })
      })
      if (r.ok) {
        const d = await r.json()
        sessionStorage.setItem(SESSION_KEY, d.token)
        onLogin(d.token)
      } else { setErr("Contraseña incorrecta") }
    } catch { setErr("Error de conexión") }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: "100dvh", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <style>{CSS}</style>
      <div style={{ width: "100%", maxWidth: 320 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <img
            src="https://i.imgur.com/858aa104a4eb27eb3d0e3a62964c103e.png"
            alt="SyncHub"
            style={{ width: 56, height: 56, objectFit: "contain", margin: "0 auto 14px", display: "block" }}
            onError={e => { e.target.style.display = "none" }}
          />
          <div style={{ fontSize: 22, fontWeight: 800, color: "#0A0A0A", letterSpacing: "-0.5px" }}>SyncHub</div>
          <div style={{ fontSize: 12, color: "#999", marginTop: 3, letterSpacing: "0.08em", textTransform: "uppercase" }}>Facility Sync Dashboard</div>
        </div>

        <form onSubmit={submit}>
          <input
            type="password" value={pw} onChange={e => setPw(e.target.value)}
            placeholder="Contraseña" autoFocus
            style={{
              width: "100%", padding: "13px 16px", fontSize: 14,
              background: "#F8F8F8", border: "1px solid #E8E8E8",
              borderRadius: 8, color: "#0A0A0A", outline: "none",
              boxSizing: "border-box", marginBottom: 10, fontFamily: "inherit"
            }}
          />
          {err && <div style={{ color: "#E53E3E", fontSize: 12, marginBottom: 10, textAlign: "center" }}>{err}</div>}
          <button type="submit" disabled={loading || !pw} style={{
            width: "100%", padding: 13, fontSize: 13, fontWeight: 700,
            letterSpacing: "0.06em", textTransform: "uppercase",
            background: pw ? "#0A0A0A" : "#F0F0F0",
            color: pw ? "#fff" : "#BBB",
            border: "none", borderRadius: 8,
            cursor: pw ? "pointer" : "default", fontFamily: "inherit"
          }}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Cookie Modal ──────────────────────────────────────────────
function CookieModal({ fac, token, onClose, onSaved }) {
  const [val, setVal] = useState("")
  const [saving, setSaving] = useState(false)
  const isToken = ["finnly","upperhand","glofox"].includes(fac.platform)

  async function save() {
    if (!val.trim()) return
    setSaving(true)
    await fetch(`${API}/api/facilities/${fac.id}/cookie`, {
      method: "POST",
      headers: { "X-API-Key": token, "Content-Type": "application/json" },
      body: JSON.stringify({ value: val })
    })
    setSaving(false); onSaved(); onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="modal-handle" />
        <div style={{ fontSize: 14, fontWeight: 700, color: "#0A0A0A", marginBottom: 3 }}>{fac.name}</div>
        <div style={{ fontSize: 12, color: "#999", marginBottom: 16 }}>
          {isToken ? "Actualizá el token de sesión" : "Pegá la cookie de sesión"}
          {fac.cookie_age_hours !== null && fac.cookie_updated_at && (
            <span style={{ marginLeft: 8, color: fac.cookie_age_hours > 20 ? "#E53E3E" : "#16A34A" }}>
              · Última: {timeAgo(fac.cookie_updated_at)}
            </span>
          )}
        </div>
        <textarea
          autoFocus value={val} onChange={e => setVal(e.target.value)}
          placeholder={isToken ? "eyJhbGci..." : "ASP.NET_SessionId=...; __cf_bm=..."}
          style={{ width: "100%", height: 88, fontSize: 11, fontFamily: "'JetBrains Mono', monospace", background: "#F8F8F8", border: "1px solid #E8E8E8", borderRadius: 8, padding: "10px 12px", resize: "none", color: "#0A0A0A", outline: "none", boxSizing: "border-box" }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button onClick={onClose} style={{ flex: 1, padding: 12, fontSize: 13, background: "#F8F8F8", border: "1px solid #E8E8E8", borderRadius: 8, color: "#666", cursor: "pointer", fontFamily: "inherit" }}>Cancelar</button>
          <button onClick={save} disabled={!val.trim() || saving} style={{ flex: 2, padding: 12, fontSize: 13, fontWeight: 700, background: val.trim() ? "#0A0A0A" : "#F0F0F0", border: "none", borderRadius: 8, color: val.trim() ? "#fff" : "#BBB", cursor: val.trim() ? "pointer" : "default", fontFamily: "inherit" }}>
            {saving ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Log Modal ─────────────────────────────────────────────────
function LogModal({ logId, facName, token, onClose }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    fetch(`${API}/api/logs/${logId}`, { headers: { "X-API-Key": token } })
      .then(r => r.json()).then(setLog)
  }, [logId])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#fff", borderRadius: "16px 16px 0 0", width: "100%", maxWidth: 600, maxHeight: "82dvh", display: "flex", flexDirection: "column", borderTop: "1px solid #E8E8E8" }}>
        <div style={{ padding: "20px 20px 14px", borderBottom: "1px solid #F0F0F0" }}>
          <div style={{ width: 32, height: 3, background: "#E0E0E0", borderRadius: 2, margin: "0 auto 16px" }} />
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#0A0A0A" }}>{facName}</div>
              {log && <div style={{ fontSize: 11, color: "#999", marginTop: 3, fontFamily: "'JetBrains Mono', monospace" }}>
                {log.rows ? `${log.rows.toLocaleString()} filas` : ""}{log.duration_s ? ` · ${Math.round(log.duration_s)}s` : ""}{log.trigger ? ` · ${log.trigger}` : ""}
              </div>}
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              {log?.log_output && (
                <button onClick={() => {
                  const a = document.createElement("a")
                  a.href = URL.createObjectURL(new Blob([log.log_output], { type: "text/plain" }))
                  a.download = `log-${logId}.txt`; a.click()
                }} className="icon-btn">⬇</button>
              )}
              <button onClick={onClose} className="icon-btn">✕</button>
            </div>
          </div>
        </div>
        <pre style={{ flex: 1, overflow: "auto", padding: "16px 20px", fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: "#555", whiteSpace: "pre-wrap", wordBreak: "break-all", lineHeight: 1.8, margin: 0, background: "#FAFAFA" }}>
          {log?.log_output || "Cargando..."}
        </pre>
      </div>
    </div>
  )
}

// ── Facility Row ──────────────────────────────────────────────
function FacRow({ fac, onCookie, onRun, onLog }) {
  const p = platInfo(fac.platform)
  const ckS = fac.has_cookie ? cookieStatus(fac.cookie_age_hours) : null
  const isRunning = fac.running || fac.last_sync?.status === "running"
  const status = isRunning ? "running" : fac.last_sync?.status || "none"

  const rowClass = `fac-row${isRunning ? " running" : status === "error" || status === "cookie_error" ? " error" : ckS === "expired" ? " cookie-warn" : ""}`

  return (
    <div className={rowClass}>
      {/* Platform badge */}
      <div style={{
        width: 30, height: 30, borderRadius: 6,
        background: p.color + "14",
        border: `1.5px solid ${p.color}40`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 10, fontWeight: 700, color: p.color, flexShrink: 0
      }}>
        {p.label}
      </div>

      {/* Name + subtitle */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "#0A0A0A", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {fac.name}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
          {fac.last_sync?.started_at && (
            <span style={{ fontSize: 10, color: "#AAA", fontFamily: "'JetBrains Mono', monospace" }}>
              {miamiTime(fac.last_sync.started_at)}
              {fac.last_sync?.rows ? ` · ${fac.last_sync.rows.toLocaleString()}` : ""}
            </span>
          )}
          {ckS === "expired" && <span style={{ fontSize: 9, fontWeight: 700, color: "#E53E3E", letterSpacing: "0.05em", textTransform: "uppercase" }}>cookie exp</span>}
          {ckS === "warn" && <span style={{ fontSize: 9, fontWeight: 700, color: "#D97706", letterSpacing: "0.05em", textTransform: "uppercase" }}>pronto</span>}
        </div>
      </div>

      {/* Status icon */}
      <div style={{
        fontSize: 13, fontWeight: 700, flexShrink: 0,
        color: isRunning ? "#0A0A0A"
          : status === "ok" ? "#16A34A"
          : status === "error" || status === "cookie_error" ? "#E53E3E"
          : "#D0D0D0",
        fontFamily: "'JetBrains Mono', monospace",
        animation: isRunning ? "spin 1s linear infinite" : "none",
        display: "inline-block"
      }}>
        {isRunning ? "↻" : status === "ok" ? "✓" : status === "error" || status === "cookie_error" ? "✕" : "–"}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {fac.has_cookie && (
          <button
            onClick={() => onCookie(fac)}
            className={`icon-btn${ckS === "expired" ? " expired" : ckS === "warn" ? " warn" : ""}`}
            title="Actualizar cookie"
          >
            {["finnly","upperhand","glofox"].includes(fac.platform) ? "🔑" : "🍪"}
          </button>
        )}
        {fac.last_sync && (
          <button onClick={() => onLog(fac.last_sync.id, fac.name)} className="icon-btn" title="Ver log">≡</button>
        )}
        <button onClick={() => onRun(fac.id)} disabled={isRunning} className="run-btn">
          {isRunning ? "..." : "Run"}
        </button>
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(SESSION_KEY) || "")
  const [facilities, setFacilities] = useState({})
  const [logs, setLogs] = useState([])
  const [csvs, setCsvs] = useState([])
  const [view, setView] = useState("home")
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
    try {
      const r = await fetch(`${API}/api/logs?limit=200`, { headers: H })
      setLogs(await r.json())
    } catch {}
  }, [token])

  const fetchCsvs = useCallback(async () => {
    if (!token) return
    try {
      const r = await fetch(`${API}/api/csvs`, { headers: H })
      setCsvs(await r.json())
    } catch {}
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

  if (!token) return <><style>{CSS}</style><LoginScreen onLogin={setToken} /></>

  const facList = Object.values(facilities)
  const today = new Date().toISOString().slice(0, 10)
  const syncsToday = logs.filter(l => l.started_at?.startsWith(today)).length
  const cookieAlerts = facList.filter(f => f.has_cookie && cookieStatus(f.cookie_age_hours) === "expired").length
  const totalRows = logs.filter(l => l.started_at?.startsWith(today)).reduce((s, l) => s + (l.rows || 0), 0)

  const sorted = [...facList].sort((a, b) => {
    const score = f => {
      if (f.running || f.last_sync?.status === "running") return 0
      if (f.last_sync?.status === "error" || f.last_sync?.status === "cookie_error") return 1
      if (f.has_cookie && cookieStatus(f.cookie_age_hours) === "expired") return 2
      if (!f.last_sync?.started_at?.startsWith(today)) return 3
      return 4
    }
    return score(a) - score(b)
  })

  const filteredLogs = filterFac ? logs.filter(l => l.facility_id === filterFac) : logs
  const filteredCsvs = filterFac ? csvs.filter(c => c.facility_id === filterFac) : csvs

  return (
    <>
      <style>{CSS}</style>

      {/* ── Header ── */}
      <div style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "#0A0A0A",
        padding: "0 20px",
        display: "flex", alignItems: "center", gap: 0,
        height: 52,
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 9, flex: 1 }}>
          <img
            src="/logo.png"
            alt="S"
            style={{ width: 22, height: 22, objectFit: "contain", filter: "invert(1)" }}
            onError={e => { e.target.style.display = "none" }}
          />
          <span style={{ fontSize: 15, fontWeight: 800, color: "#fff", letterSpacing: "-0.3px" }}>SyncHub</span>
          <span style={{ fontSize: 11, color: "#555", marginLeft: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block", marginRight: 5, verticalAlign: "middle" }}></span>
            {facList.length} activas
          </span>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 0, borderBottom: "none" }}>
          {[
            { id: "home", label: "Home" },
            { id: "logs", label: "Historial" },
            { id: "csvs", label: "CSV" },
          ].map(tab => (
            <button key={tab.id} onClick={() => { setView(tab.id); setFilterFac(null) }}
              style={{
                padding: "0 14px", height: 52, fontSize: 12, fontWeight: 600,
                letterSpacing: "0.04em", textTransform: "uppercase",
                background: "transparent", border: "none",
                borderBottom: view === tab.id ? "2px solid #fff" : "2px solid transparent",
                color: view === tab.id ? "#fff" : "#666",
                cursor: "pointer", transition: "color 0.15s, border-color 0.15s"
              }}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 640, margin: "0 auto", paddingBottom: 80 }}>

        {/* ── HOME ── */}
        {view === "home" && <>

          {/* Stats strip */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", borderBottom: "1px solid #F0F0F0" }}>
            {[
              { label: "Syncs", value: syncsToday },
              { label: "Facilities", value: facList.length },
              { label: "Cookies", value: cookieAlerts > 0 ? `${cookieAlerts} ⚠` : "OK", warn: cookieAlerts > 0 },
              { label: "Filas", value: totalRows > 1000 ? `${(totalRows/1000).toFixed(0)}k` : totalRows || "–" },
            ].map((s, i) => (
              <div key={i} className="stat-block">
                <div style={{ fontSize: 10, color: "#AAA", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: s.warn ? "#E53E3E" : "#0A0A0A", letterSpacing: "-0.5px" }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* Facility list */}
          <div>
            {sorted.map(fac => (
              <FacRow key={fac.id} fac={fac} token={token}
                onCookie={f => setCookieFac(f)}
                onRun={id => runFac(id)}
                onLog={(id, name) => setLogModal({ id, name })}
              />
            ))}
            {facList.length === 0 && (
              <div style={{ padding: 60, textAlign: "center", color: "#CCC", fontSize: 13 }}>Cargando...</div>
            )}
          </div>

          <div style={{ padding: "12px 20px", fontSize: 10, color: "#CCC", letterSpacing: "0.05em", textTransform: "uppercase" }}>
            C — Clean Editorial · actualiza cada 15s
          </div>
        </>}

        {/* ── HISTORIAL ── */}
        {view === "logs" && <>
          {/* Filter chips */}
          <div style={{ display: "flex", gap: 6, padding: "14px 20px 10px", overflowX: "auto", borderBottom: "1px solid #F0F0F0" }}>
            <button onClick={() => setFilterFac(null)} className={`chip${!filterFac ? " active" : ""}`}>
              Todos ({logs.length})
            </button>
            {Object.values(facilities).map(f => (
              <button key={f.id} onClick={() => setFilterFac(f.id)} className={`chip${filterFac === f.id ? " active" : ""}`}>
                {f.name.split(" ").slice(0, 2).join(" ")}
              </button>
            ))}
          </div>

          <div>
            {filteredLogs.length === 0 && (
              <div style={{ padding: 60, textAlign: "center", color: "#CCC", fontSize: 13 }}>Sin registros</div>
            )}
            {filteredLogs.map(log => {
              const fac = facilities[log.facility_id]
              const p = platInfo(fac?.platform)
              const st = log.status
              const stColor = st === "ok" ? "#16A34A" : st === "error" || st === "cookie_error" ? "#E53E3E" : "#0A0A0A"
              const stIcon = st === "ok" ? "✓" : st === "error" || st === "cookie_error" ? "✕" : "↻"
              return (
                <div key={log.id} className="log-row"
                  style={{ cursor: log.log_output ? "pointer" : "default" }}
                  onClick={() => log.log_output && setLogModal({ id: log.id, name: fac?.name })}>
                  <div style={{ width: 26, height: 26, borderRadius: 6, background: p.color + "14", border: `1.5px solid ${p.color}40`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: p.color, flexShrink: 0 }}>{p.label}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#0A0A0A" }}>{fac?.name || log.facility_id}</div>
                    <div style={{ fontSize: 10, color: "#AAA", marginTop: 2, fontFamily: "'JetBrains Mono', monospace" }}>
                      {miamiTime(log.started_at)}{log.rows ? ` · ${log.rows.toLocaleString()}` : ""}{log.duration_s ? ` · ${Math.round(log.duration_s)}s` : ""}{log.trigger ? ` · ${log.trigger}` : ""}
                    </div>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: stColor, fontFamily: "'JetBrains Mono', monospace" }}>{stIcon}</div>
                </div>
              )
            })}
          </div>
        </>}

        {/* ── CSV ── */}
        {view === "csvs" && <>
          <div style={{ padding: "14px 20px 10px", fontSize: 11, color: "#AAA", letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid #F0F0F0" }}>
            {csvs.length} archivos · auto-borrado 11pm Miami
          </div>

          {/* filter */}
          <div style={{ display: "flex", gap: 6, padding: "10px 20px 8px", overflowX: "auto", borderBottom: "1px solid #F5F5F5" }}>
            <button onClick={() => setFilterFac(null)} className={`chip${!filterFac ? " active" : ""}`}>Todos</button>
            {Object.values(facilities).map(f => (
              <button key={f.id} onClick={() => setFilterFac(f.id)} className={`chip${filterFac === f.id ? " active" : ""}`}>
                {f.name.split(" ").slice(0, 2).join(" ")}
              </button>
            ))}
          </div>

          <div>
            {filteredCsvs.length === 0 && (
              <div style={{ padding: 60, textAlign: "center", color: "#CCC", fontSize: 13 }}>Sin CSVs</div>
            )}
            {filteredCsvs.map(csv => {
              const fac = facilities[csv.facility_id]
              return (
                <div key={csv.id} style={{ borderBottom: "1px solid #F5F5F5", padding: "11px 20px", display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontFamily: "'JetBrains Mono', monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#0A0A0A" }}>
                      {csv.filename}
                    </div>
                    <div style={{ fontSize: 10, color: "#AAA", marginTop: 2 }}>
                      {fac?.name} · {csv.rows?.toLocaleString()} filas{csv.size_bytes ? ` · ${(csv.size_bytes/1024).toFixed(1)}KB` : ""}
                    </div>
                  </div>
                  <button onClick={() => { const a = document.createElement("a"); a.href = `${API}/api/csvs/${csv.id}/download?key=${token}`; a.download = csv.filename; a.click() }}
                    style={{ padding: "6px 12px", fontSize: 11, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase", background: "#0A0A0A", border: "none", borderRadius: 4, color: "#fff", cursor: "pointer", fontFamily: "inherit" }}>
                    ↓
                  </button>
                </div>
              )
            })}
          </div>
        </>}
      </div>

      {/* Modals */}
      {cookieFac && <CookieModal fac={cookieFac} token={token} onClose={() => setCookieFac(null)} onSaved={fetchFacs} />}
      {logModal && <LogModal logId={logModal.id} facName={logModal.name} token={token} onClose={() => setLogModal(null)} />}
    </>
  )
}