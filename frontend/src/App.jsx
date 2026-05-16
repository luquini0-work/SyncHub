import { useState, useEffect, useCallback, useRef } from "react"

const API = import.meta.env.VITE_API_URL || ""
const SESSION_KEY = "synchub_token"

// ── Platform colors ───────────────────────────────────────────
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
      hour: "2-digit", minute: "2-digit", second: "2-digit",
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

// ── Login Screen ──────────────────────────────────────────────
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
      } else {
        setErr("Contraseña incorrecta")
      }
    } catch { setErr("Error de conexión") }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: "100dvh", background: "#0A0A0F", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 360 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ width: 64, height: 64, margin: "0 auto 16px", background: "rgba(99,102,241,0.15)", borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid rgba(99,102,241,0.3)" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14l-4-4 1.41-1.41L11 13.17l6.59-6.59L19 8l-8 8z" fill="none"/>
              <path d="M12 4V2M12 22v-2M4 12H2M22 12h-2M6.34 6.34L4.93 4.93M19.07 19.07l-1.41-1.41M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" stroke="rgba(99,102,241,0.5)" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="12" cy="12" r="3" fill="none" stroke="#6366F1" strokeWidth="2"/>
              <path d="M12 9V5M15 12h4M12 15v4M9 12H5" stroke="#6366F1" strokeWidth="2" strokeLinecap="round"/>
              <path d="M17 7l-1 1M7 7l1 1M7 17l1-1M17 17l-1-1" stroke="rgba(99,102,241,0.6)" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#F9FAFB", letterSpacing: "-0.5px" }}>SyncHub</div>
          <div style={{ fontSize: 13, color: "#6B7280", marginTop: 4 }}>Facility Sync Dashboard</div>
        </div>

        <form onSubmit={submit}>
          <input
            type="password"
            value={pw}
            onChange={e => setPw(e.target.value)}
            placeholder="Contraseña"
            autoFocus
            style={{
              width: "100%", padding: "14px 16px", fontSize: 15,
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12, color: "#F9FAFB", outline: "none",
              boxSizing: "border-box", marginBottom: 12,
              fontFamily: "inherit"
            }}
          />
          {err && <div style={{ color: "#F87171", fontSize: 13, marginBottom: 10, textAlign: "center" }}>{err}</div>}
          <button type="submit" disabled={loading || !pw} style={{
            width: "100%", padding: "14px", fontSize: 15, fontWeight: 600,
            background: pw ? "#6366F1" : "rgba(99,102,241,0.3)",
            color: pw ? "#fff" : "rgba(255,255,255,0.3)",
            border: "none", borderRadius: 12, cursor: pw ? "pointer" : "default",
            transition: "all 0.2s", fontFamily: "inherit"
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
  const isToken = fac.platform === "finnly" || fac.platform === "upperhand" || fac.platform === "glofox"

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
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "flex-end", justifyContent: "center", zIndex: 100, backdropFilter: "blur(4px)" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#1C1C27", borderRadius: "20px 20px 0 0", padding: "24px 20px 32px", width: "100%", maxWidth: 480, border: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ width: 36, height: 4, background: "rgba(255,255,255,0.15)", borderRadius: 2, margin: "0 auto 20px" }} />
        <div style={{ fontSize: 15, fontWeight: 600, color: "#F9FAFB", marginBottom: 4 }}>{fac.name}</div>
        <div style={{ fontSize: 12, color: "#6B7280", marginBottom: 16 }}>
          {isToken ? "Actualizá el token" : "Pegá la cookie de sesión"}
          {fac.cookie_age_hours !== null && fac.cookie_updated_at && (
            <span style={{ marginLeft: 8, color: fac.cookie_age_hours > 20 ? "#F87171" : "#34D399" }}>
              · Última: {timeAgo(fac.cookie_updated_at)}
            </span>
          )}
        </div>
        <textarea
          autoFocus value={val} onChange={e => setVal(e.target.value)}
          placeholder={isToken ? "eyJhbGci..." : "ASP.NET_SessionId=...; __cf_bm=..."}
          style={{ width: "100%", height: 90, fontSize: 11, fontFamily: "monospace", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, padding: "10px 12px", resize: "none", color: "#E5E7EB", outline: "none", boxSizing: "border-box" }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button onClick={onClose} style={{ flex: 1, padding: "12px", fontSize: 14, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, color: "#9CA3AF", cursor: "pointer" }}>Cancelar</button>
          <button onClick={save} disabled={!val.trim() || saving} style={{ flex: 2, padding: "12px", fontSize: 14, fontWeight: 600, background: val.trim() ? "#6366F1" : "rgba(99,102,241,0.3)", border: "none", borderRadius: 10, color: val.trim() ? "#fff" : "rgba(255,255,255,0.3)", cursor: val.trim() ? "pointer" : "default" }}>
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
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", alignItems: "flex-end", justifyContent: "center", zIndex: 100, backdropFilter: "blur(4px)" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0D0D14", borderRadius: "20px 20px 0 0", width: "100%", maxWidth: 600, maxHeight: "80dvh", display: "flex", flexDirection: "column", border: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ padding: "16px 20px 12px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ width: 36, height: 4, background: "rgba(255,255,255,0.15)", borderRadius: 2, margin: "0 auto 12px" }} />
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#F9FAFB" }}>{facName}</div>
              {log && <div style={{ fontSize: 11, color: "#6B7280", marginTop: 2 }}>
                {log.rows ? `${log.rows.toLocaleString()} filas · ` : ""}{log.duration_s ? `${Math.round(log.duration_s)}s · ` : ""}{log.trigger}
              </div>}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {log?.log_output && (
                <button onClick={() => {
                  const a = document.createElement("a")
                  a.href = URL.createObjectURL(new Blob([log.log_output], { type: "text/plain" }))
                  a.download = `log-${logId}.txt`; a.click()
                }} style={{ padding: "6px 10px", fontSize: 11, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#9CA3AF", cursor: "pointer" }}>⬇</button>
              )}
              <button onClick={onClose} style={{ padding: "6px 10px", fontSize: 11, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#9CA3AF", cursor: "pointer" }}>✕</button>
            </div>
          </div>
        </div>
        <pre style={{ flex: 1, overflow: "auto", padding: "16px 20px", fontSize: 11, fontFamily: "monospace", color: "#9CA3AF", whiteSpace: "pre-wrap", wordBreak: "break-all", lineHeight: 1.7, margin: 0 }}>
          {log?.log_output || "Cargando..."}
        </pre>
      </div>
    </div>
  )
}

// ── Facility Row ──────────────────────────────────────────────
function FacRow({ fac, token, onCookie, onRun, onLog }) {
  const p = platInfo(fac.platform)
  const ckS = fac.has_cookie ? cookieStatus(fac.cookie_age_hours) : null
  const ckColor = ckS === "ok" ? "#34D399" : ckS === "warn" ? "#FBBF24" : ckS === "expired" ? "#F87171" : "#4B5563"
  const status = fac.running ? "run" : fac.last_sync?.status || "none"

  // Count syncs today
  const today = new Date().toISOString().slice(0, 10)
  const lastTime = fac.last_sync?.started_at
  const lastMiami = lastTime ? miamiTime(lastTime) : null

  return (
    <div style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", padding: "12px 16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* Platform dot */}
        <div style={{ width: 28, height: 28, borderRadius: "50%", background: p.color + "22", border: `1.5px solid ${p.color}55`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: p.color, flexShrink: 0 }}>
          {p.label}
        </div>

        {/* Name + time */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: "#F1F5F9", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{fac.name}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
            {lastMiami && <span style={{ fontSize: 10, color: "#6B7280" }}>{lastMiami}</span>}
            {fac.has_cookie && (
              <span style={{ fontSize: 9, color: ckColor, fontWeight: 600 }}>
                {ckS === "ok" ? `🍪 ${timeAgo(fac.cookie_updated_at)}` : ckS === "warn" ? "⚠ pronto" : ckS === "expired" ? "✕ expirada" : ""}
              </span>
            )}
          </div>
        </div>

        {/* Status tick/cross */}
        <div style={{ fontSize: 14, color: status === "ok" ? "#34D399" : status === "error" || status === "cookie_error" ? "#F87171" : status === "run" || status === "running" ? "#818CF8" : "#374151", flexShrink: 0 }}>
          {status === "ok" ? "✓" : status === "error" || status === "cookie_error" ? "✕" : status === "run" || status === "running" ? "↻" : "–"}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
          {fac.has_cookie && (
            <button onClick={() => onCookie(fac)} style={{ width: 32, height: 32, borderRadius: 8, background: ckS === "expired" ? "rgba(248,113,113,0.15)" : "rgba(255,255,255,0.05)", border: `1px solid ${ckS === "expired" ? "rgba(248,113,113,0.3)" : "rgba(255,255,255,0.08)"}`, fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              {fac.platform === "finnly" || fac.platform === "upperhand" || fac.platform === "glofox" ? "🔑" : "🍪"}
            </button>
          )}
          <button onClick={() => onRun(fac.id)} disabled={fac.running} style={{ height: 32, paddingInline: 14, borderRadius: 8, background: fac.running ? "rgba(99,102,241,0.2)" : "rgba(99,102,241,0.8)", border: "none", fontSize: 12, fontWeight: 600, color: fac.running ? "#818CF8" : "#fff", cursor: fac.running ? "not-allowed" : "pointer" }}>
            {fac.running ? "↻" : "▶"}
          </button>
          {fac.last_sync && (
            <button onClick={() => onLog(fac.last_sync.id, fac.name)} style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", fontSize: 12, cursor: "pointer", color: "#6B7280", display: "flex", alignItems: "center", justifyContent: "center" }}>
              ≡
            </button>
          )}
        </div>
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
  const [view, setView] = useState("dashboard")
  const [menuOpen, setMenuOpen] = useState(false)
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

  if (!token) return <LoginScreen onLogin={setToken} />

  const facList = Object.values(facilities)
  const today = new Date().toISOString().slice(0, 10)
  const syncsToday = logs.filter(l => l.started_at?.startsWith(today)).length
  const cookieAlerts = facList.filter(f => f.has_cookie && cookieStatus(f.cookie_age_hours) === "expired").length
  const errors = logs.filter(l => l.status === "error" || l.status === "cookie_error").length

  // Sort: running first, then errors, then pending, then done
  const sorted = [...facList].sort((a, b) => {
    const score = f => f.running ? 0 : (f.last_sync?.status === "error" ? 1 : f.has_cookie && cookieStatus(f.cookie_age_hours) === "expired" ? 2 : f.last_sync?.started_at?.startsWith(today) ? 4 : 3)
    return score(a) - score(b)
  })

  const filteredLogs = filterFac ? logs.filter(l => l.facility_id === filterFac) : logs
  const filteredCsvs = filterFac ? csvs.filter(c => c.facility_id === filterFac) : csvs

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body { font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', sans-serif; background: #0A0A0F; color: #F1F5F9; }
        button { font-family: inherit; transition: opacity 0.15s; }
        button:active { opacity: 0.7; }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
      `}</style>

      {/* Header */}
      <div style={{ position: "sticky", top: 0, zIndex: 50, background: "rgba(10,10,15,0.95)", backdropFilter: "blur(12px)", borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
          <div style={{ width: 28, height: 28, background: "rgba(99,102,241,0.2)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="3" fill="none" stroke="#6366F1" strokeWidth="2.5"/>
              <path d="M12 9V5M15 12h4M12 15v4M9 12H5" stroke="#6366F1" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <span style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.3px" }}>SyncHub</span>
        </div>

        {/* Nav tabs */}
        <div style={{ display: "flex", gap: 4 }}>
          {[
            { id: "dashboard", label: "Home" },
            { id: "logs", label: `Historial${errors > 0 ? ` (${errors})` : ""}` },
            { id: "csvs", label: `CSVs${csvs.length > 0 ? ` (${csvs.length})` : ""}` },
          ].map(tab => (
            <button key={tab.id} onClick={() => { setView(tab.id); setFilterFac(null) }} style={{
              padding: "6px 12px", fontSize: 12, fontWeight: view === tab.id ? 600 : 400,
              background: view === tab.id ? "rgba(99,102,241,0.2)" : "transparent",
              border: view === tab.id ? "1px solid rgba(99,102,241,0.3)" : "1px solid transparent",
              borderRadius: 8, color: view === tab.id ? "#A5B4FC" : "#6B7280", cursor: "pointer"
            }}>{tab.label}</button>
          ))}
        </div>

        <button onClick={() => { sessionStorage.removeItem(SESSION_KEY); setToken("") }} style={{ padding: "6px 10px", fontSize: 11, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, color: "#6B7280", cursor: "pointer" }}>
          ↩
        </button>
      </div>

      <div style={{ maxWidth: 640, margin: "0 auto", padding: "0 0 80px" }}>

        {/* DASHBOARD */}
        {view === "dashboard" && (
          <>
            {/* Stats */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, padding: "16px 16px 12px" }}>
              {[
                { label: "Syncs hoy", value: syncsToday, color: "#6366F1" },
                { label: "Facilities", value: facList.length, color: "#34D399" },
                { label: "⚠ Cookies", value: cookieAlerts, color: cookieAlerts > 0 ? "#F87171" : "#4B5563" },
              ].map((s, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12, padding: "12px 14px" }}>
                  <div style={{ fontSize: 10, color: "#6B7280", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{s.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Schedule info */}
            <div style={{ margin: "0 16px 12px", padding: "10px 14px", background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: 10, fontSize: 11, color: "#818CF8" }}>
              ⏱ 8:00am · 10:30am · 1:00pm · 3:30pm Miami · actualiza cada 15s
            </div>

            {/* Facility list */}
            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 16, margin: "0 16px", overflow: "hidden" }}>
              {sorted.map(fac => (
                <FacRow key={fac.id} fac={fac} token={token}
                  onCookie={f => setCookieFac(f)}
                  onRun={id => runFac(id)}
                  onLog={(id, name) => setLogModal({ id, name })}
                />
              ))}
            </div>
          </>
        )}

        {/* HISTORIAL */}
        {view === "logs" && (
          <div style={{ padding: "16px" }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 12, overflowX: "auto", paddingBottom: 4 }}>
              <button onClick={() => setFilterFac(null)} style={{ padding: "6px 12px", fontSize: 12, background: !filterFac ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.05)", border: !filterFac ? "1px solid rgba(99,102,241,0.3)" : "1px solid rgba(255,255,255,0.08)", borderRadius: 8, color: !filterFac ? "#A5B4FC" : "#6B7280", cursor: "pointer", whiteSpace: "nowrap" }}>
                Todos ({logs.length})
              </button>
              {Object.values(facilities).map(f => (
                <button key={f.id} onClick={() => setFilterFac(f.id)} style={{ padding: "6px 12px", fontSize: 12, background: filterFac === f.id ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.05)", border: filterFac === f.id ? "1px solid rgba(99,102,241,0.3)" : "1px solid rgba(255,255,255,0.08)", borderRadius: 8, color: filterFac === f.id ? "#A5B4FC" : "#6B7280", cursor: "pointer", whiteSpace: "nowrap" }}>
                  {f.name.split(" ").slice(0, 2).join(" ")}
                </button>
              ))}
            </div>

            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 16, overflow: "hidden" }}>
              {filteredLogs.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "#4B5563", fontSize: 13 }}>Sin registros</div>}
              {filteredLogs.map(log => {
                const fac = facilities[log.facility_id]
                const p = platInfo(fac?.platform)
                const st = log.status
                const stColor = st === "ok" ? "#34D399" : st === "error" || st === "cookie_error" ? "#F87171" : "#818CF8"
                const stIcon = st === "ok" ? "✓" : st === "error" || st === "cookie_error" ? "✕" : "↻"
                return (
                  <div key={log.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 24, height: 24, borderRadius: "50%", background: p.color + "22", border: `1.5px solid ${p.color}55`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: p.color, flexShrink: 0 }}>{p.label}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{fac?.name || log.facility_id}</div>
                      <div style={{ fontSize: 10, color: "#6B7280", marginTop: 2 }}>
                        {miamiTime(log.started_at)} · {log.rows ? `${log.rows.toLocaleString()} filas` : "–"} · {log.trigger}
                      </div>
                    </div>
                    <div style={{ fontSize: 14, color: stColor }}>{stIcon}</div>
                    {log.log_output && (
                      <button onClick={() => setLogModal({ id: log.id, name: fac?.name })} style={{ width: 28, height: 28, borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", fontSize: 12, cursor: "pointer", color: "#6B7280" }}>≡</button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* CSVs */}
        {view === "csvs" && (
          <div style={{ padding: "16px" }}>
            <div style={{ fontSize: 11, color: "#6B7280", marginBottom: 12 }}>
              {csvs.length} archivos · auto-borrado 11pm Miami
            </div>
            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 16, overflow: "hidden" }}>
              {filteredCsvs.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "#4B5563", fontSize: 13 }}>Sin CSVs</div>}
              {filteredCsvs.map(csv => {
                const fac = facilities[csv.facility_id]
                return (
                  <div key={csv.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#A5B4FC" }}>📄 {csv.filename}</div>
                      <div style={{ fontSize: 10, color: "#6B7280", marginTop: 2 }}>
                        {fac?.name} · {csv.rows?.toLocaleString()} filas · {csv.size_bytes ? `${(csv.size_bytes / 1024).toFixed(1)}KB` : ""}
                      </div>
                    </div>
                    <button onClick={() => { const a = document.createElement("a"); a.href = `${API}/api/csvs/${csv.id}/download?key=${token}`; a.download = csv.filename; a.click() }} style={{ padding: "6px 12px", fontSize: 11, background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 8, color: "#A5B4FC", cursor: "pointer" }}>⬇</button>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {cookieFac && <CookieModal fac={cookieFac} token={token} onClose={() => setCookieFac(null)} onSaved={fetchFacs} />}
      {logModal && <LogModal logId={logModal.id} facName={logModal.name} token={token} onClose={() => setLogModal(null)} />}
    </>
  )
}