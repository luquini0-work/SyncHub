import { useState, useEffect, useCallback } from "react"

const API = import.meta.env.VITE_API_URL || ""
const API_KEY = "synchub2026"
const H = { "X-API-Key": API_KEY, "Content-Type": "application/json" }

const PLATFORMS = {
  mindbody: { bg: "#EBF3FF", text: "#1A4FA0", label: "Mindbody" },
  finnly:   { bg: "#EDFAF4", text: "#0D6645", label: "Finnly" },
  amelia:   { bg: "#FFF7ED", text: "#92400E", label: "Amelia" },
}

const STATUS_STYLES = {
  ok:           { bg: "#F0FDF4", color: "#15803D", border: "#BBF7D0", icon: "✓", label: "OK" },
  warning:      { bg: "#FFFBEB", color: "#B45309", border: "#FDE68A", icon: "⚠", label: "Cookie pronto" },
  expired:      { bg: "#FEF2F2", color: "#DC2626", border: "#FECACA", icon: "✕", label: "Cookie expirada" },
  cookie_error: { bg: "#FEF2F2", color: "#DC2626", border: "#FECACA", icon: "✕", label: "Cookie expirada" },
  error:        { bg: "#FEF2F2", color: "#DC2626", border: "#FECACA", icon: "✕", label: "Error" },
  running:      { bg: "#EFF6FF", color: "#2563EB", border: "#BFDBFE", icon: "↻", label: "Corriendo..." },
  unknown:      { bg: "#F9FAFB", color: "#6B7280", border: "#E5E7EB", icon: "–", label: "Sin cookie" },
}

function timeAgo(isoStr) {
  if (!isoStr) return "—"
  const diff = (Date.now() - new Date(isoStr + "Z").getTime()) / 1000
  if (diff < 60) return "ahora"
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

function cookieStatus(ageHours) {
  if (ageHours === null || ageHours === undefined) return "unknown"
  if (ageHours > 20) return "expired"
  if (ageHours > 12) return "warning"
  return "ok"
}

function getFacilityStatus(fac) {
  if (fac.running) return "running"
  const ck = fac.has_cookie ? cookieStatus(fac.cookie_age_hours) : null
  if (ck === "expired" || fac.last_sync?.status === "cookie_error") return "expired"
  if (ck === "warning") return "warning"
  if (fac.last_sync?.status === "error") return "error"
  if (fac.last_sync?.status === "ok") return "ok"
  return "unknown"
}

function Badge({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.unknown
  return (
    <span style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}`, fontSize: 11, padding: "2px 8px", borderRadius: 20, display: "inline-flex", alignItems: "center", gap: 4, fontWeight: 600, whiteSpace: "nowrap" }}>
      <span style={{ animation: status === "running" ? "spin 1s linear infinite" : "none" }}>{s.icon}</span>
      {s.label}
    </span>
  )
}

function PlatBadge({ platform }) {
  const p = PLATFORMS[platform] || PLATFORMS.mindbody
  return <span style={{ background: p.bg, color: p.text, fontSize: 10, padding: "2px 7px", borderRadius: 4, fontWeight: 600 }}>{p.label}</span>
}

function fmtBytes(b) {
  if (!b) return "—"
  if (b < 1024) return `${b} B`
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1048576).toFixed(1)} MB`
}

function CookieBadge({ ageHours, updatedAt }) {
  const status = cookieStatus(ageHours)
  const colors = {
    ok:      { bg: "#F0FDF4", color: "#15803D", border: "#BBF7D0" },
    warning: { bg: "#FFFBEB", color: "#B45309", border: "#FDE68A" },
    expired: { bg: "#FEF2F2", color: "#DC2626", border: "#FECACA" },
    unknown: { bg: "#F9FAFB", color: "#9CA3AF", border: "#E5E7EB" },
  }
  const c = colors[status] || colors.unknown
  const label = status === "ok"
    ? `Cookie OK · ${timeAgo(updatedAt)}`
    : status === "warning"
    ? `Cookie pronto · ${timeAgo(updatedAt)}`
    : status === "expired"
    ? `Cookie expirada · ${timeAgo(updatedAt)}`
    : "Sin cookie"

  return (
    <span style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}`, fontSize: 10, padding: "2px 7px", borderRadius: 4, fontWeight: 500, whiteSpace: "nowrap" }}>
      🍪 {label}
    </span>
  )
}

function CookieModal({ fac_id, facility, onClose, onSaved }) {
  const [value, setValue] = useState("")
  const [saving, setSaving] = useState(false)
  const isToken = fac_id === "honey_barry_arena"

  async function save() {
    if (!value.trim()) return
    setSaving(true)
    await fetch(`${API}/api/facilities/${fac_id}/cookie`, { method: "POST", headers: H, body: JSON.stringify({ value }) })
    setSaving(false); onSaved(); onClose()
  }

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(2px)" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#fff", borderRadius: 16, padding: 24, width: 460, boxShadow: "0 20px 60px rgba(0,0,0,0.15)", border: "1px solid #E5E7EB" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{facility?.name}</div>
            <div style={{ fontSize: 12, color: "#9CA3AF", marginTop: 2 }}>
              {isToken ? "Actualizá el Bearer token de Finnly" : "Pegá la cookie de sesión de Mindbody"}
            </div>
            {facility?.cookie_age_hours !== null && facility?.cookie_age_hours !== undefined && (
              <div style={{ marginTop: 6 }}>
                <CookieBadge ageHours={facility.cookie_age_hours} updatedAt={facility.cookie_updated_at} />
              </div>
            )}
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#9CA3AF", fontSize: 18 }}>✕</button>
        </div>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#6B7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {isToken ? "Bearer token" : "Cookie string"}
        </div>
        <textarea autoFocus value={value} onChange={e => setValue(e.target.value)}
          placeholder={isToken ? "Bearer eyJhbGci..." : "ASP.NET_SessionId=...; __cf_bm=..."}
          style={{ width: "100%", height: 100, fontSize: 11, fontFamily: "monospace", border: "1px solid #D1D5DB", borderRadius: 8, padding: "10px 12px", resize: "none", boxSizing: "border-box", outline: "none", background: "#F9FAFB" }} />
        <div style={{ display: "flex", gap: 8, marginTop: 14, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ background: "#fff", border: "1px solid #D1D5DB", borderRadius: 8, padding: "8px 16px", fontSize: 13, cursor: "pointer" }}>Cancelar</button>
          <button onClick={save} disabled={!value.trim() || saving} style={{ background: saving ? "#818CF8" : "#4F46E5", color: "#fff", border: "none", borderRadius: 8, padding: "8px 18px", fontSize: 13, cursor: "pointer", fontWeight: 500 }}>{saving ? "Guardando..." : "Guardar"}</button>
        </div>
      </div>
    </div>
  )
}

function LogModal({ logId, facilityName, onClose }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    if (!logId) return
    fetch(`${API}/api/logs/${logId}`, { headers: H }).then(r => r.json()).then(setLog)
  }, [logId])

  function downloadLog() {
    if (!log?.log_output) return
    const blob = new Blob([log.log_output], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a"); a.href = url; a.download = `sync-log-${logId}.txt`; a.click()
    URL.revokeObjectURL(url)
  }

  const dur = log?.duration_s ? (log.duration_s > 60 ? `${Math.floor(log.duration_s / 60)}m ${Math.floor(log.duration_s % 60)}s` : `${Math.round(log.duration_s)}s`) : null

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(2px)" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0F172A", borderRadius: 16, width: 700, maxHeight: "85vh", display: "flex", flexDirection: "column", boxShadow: "0 25px 60px rgba(0,0,0,0.4)", border: "1px solid #1E293B", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid #1E293B", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#F1F5F9" }}>{facilityName || `Log #${logId}`}</div>
            {log && <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>{log.rows ? `${log.rows.toLocaleString()} filas` : "Sin filas"} · {dur || "—"} · {log.trigger}</div>}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {log?.log_output && <button onClick={downloadLog} style={{ background: "#1E293B", border: "1px solid #334155", color: "#94A3B8", borderRadius: 7, padding: "5px 12px", fontSize: 11, cursor: "pointer" }}>⬇ Log</button>}
            <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#475569", fontSize: 18 }}>✕</button>
          </div>
        </div>
        {log && (
          <div style={{ padding: "8px 20px", background: log.status === "ok" ? "#052E16" : "#450A0A", borderBottom: "1px solid #1E293B", display: "flex", alignItems: "center", gap: 8 }}>
            <Badge status={log.status} />
            <span style={{ fontSize: 11, color: "#94A3B8" }}>{log.started_at ? new Date(log.started_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"}</span>
          </div>
        )}
        <pre style={{ fontSize: 11, fontFamily: "monospace", overflow: "auto", flex: 1, margin: 0, padding: "16px 20px", whiteSpace: "pre-wrap", wordBreak: "break-all", color: "#CBD5E1", lineHeight: 1.7 }}>
          {log?.log_output || "Cargando..."}
        </pre>
      </div>
    </div>
  )
}

function Confirm({ message, onConfirm, onCancel }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000 }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: 24, width: 360, boxShadow: "0 10px 40px rgba(0,0,0,0.15)" }}>
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 20 }}>{message}</div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onCancel} style={{ border: "1px solid #D1D5DB", background: "#fff", borderRadius: 8, padding: "7px 16px", fontSize: 13, cursor: "pointer" }}>Cancelar</button>
          <button onClick={onConfirm} style={{ background: "#DC2626", color: "#fff", border: "none", borderRadius: 8, padding: "7px 16px", fontSize: 13, cursor: "pointer", fontWeight: 500 }}>Eliminar</button>
        </div>
      </div>
    </div>
  )
}

function FacilityRow({ fac_id, fac, done, onCookieClick, onRun, onLogClick }) {
  const status = getFacilityStatus(fac)
  const ckStatus = fac.has_cookie ? cookieStatus(fac.cookie_age_hours) : null
  const showCookieWarning = ckStatus === "expired" || ckStatus === "warning"

  return (
    <div style={{ borderBottom: "1px solid #F3F4F6", background: done ? "#FAFBFC" : "#fff" }}>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 90px 110px 130px 160px 100px", alignItems: "center", padding: "10px 16px" }}>
        {/* Name */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, background: status === "ok" ? "#22C55E" : status === "running" ? "#3B82F6" : status === "warning" ? "#F59E0B" : status === "expired" || status === "error" ? "#EF4444" : "#D1D5DB", animation: status === "running" ? "pulse 1.5s infinite" : "none" }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: done ? "#6B7280" : "#111827" }}>{fac.name}</div>
            <div style={{ display: "flex", gap: 6, marginTop: 3, flexWrap: "wrap" }}>
              <span style={{ fontSize: 10, color: "#9CA3AF" }}>{fac.schedules?.length ? `${fac.schedules.length}× día` : "Sin schedule"}</span>
              {fac.has_cookie && (
                <CookieBadge ageHours={fac.cookie_age_hours} updatedAt={fac.cookie_updated_at} />
              )}
            </div>
          </div>
        </div>

        <div><PlatBadge platform={fac.platform} /></div>

        <div style={{ fontSize: 12, color: "#6B7280" }}>
          {fac.last_sync
            ? <span>{timeAgo(fac.last_sync.started_at)}{fac.last_sync.rows != null && <span style={{ color: "#9CA3AF" }}> · {fac.last_sync.rows.toLocaleString()}</span>}</span>
            : <span style={{ color: "#D1D5DB" }}>Nunca</span>}
        </div>

        <div><Badge status={status} /></div>

        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => onRun(fac_id)} disabled={fac.running} style={{
            background: fac.running ? "#EEF2FF" : done ? "#F0FDF4" : "#4F46E5",
            color: fac.running ? "#818CF8" : done ? "#15803D" : "#fff",
            border: fac.running ? "1px solid #C7D2FE" : done ? "1px solid #BBF7D0" : "none",
            borderRadius: 7, padding: "5px 12px", fontSize: 11, cursor: fac.running ? "not-allowed" : "pointer", fontWeight: 500
          }}>
            {fac.running ? "↻ Corriendo" : done ? "↻ Re-run" : "▶ Run"}
          </button>
          <button onClick={() => onCookieClick(fac_id)} style={{
            background: showCookieWarning ? "#FEF2F2" : "#F9FAFB",
            border: showCookieWarning ? "1px solid #FECACA" : "1px solid #E5E7EB",
            borderRadius: 7, padding: "5px 8px", fontSize: 11, cursor: "pointer",
            color: showCookieWarning ? "#DC2626" : "#6B7280"
          }}>
            {fac.platform === "finnly" ? "🔑" : "🍪"}
          </button>
        </div>

        <div>
          {fac.last_sync && <button onClick={() => onLogClick(fac.last_sync?.id, fac.name)} style={{ background: "none", border: "1px solid #E5E7EB", borderRadius: 7, padding: "5px 10px", fontSize: 11, cursor: "pointer", color: "#6B7280" }}>Ver log</button>}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [facilities, setFacilities] = useState({})
  const [logs, setLogs] = useState([])
  const [csvs, setCsvs] = useState([])
  const [cookieModal, setCookieModal] = useState(null)
  const [logModal, setLogModal] = useState(null)
  const [confirm, setConfirm] = useState(null)
  const [view, setView] = useState("dashboard")
  const [filterFac, setFilterFac] = useState(null)
  const [filterStatus, setFilterStatus] = useState("all")

  const fetchFacilities = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/facilities`, { headers: H })
      const data = await r.json()
      setFacilities(prev => { const m = {}; for (const id in data) m[id] = { ...data[id], running: prev[id]?.running || false }; return m })
    } catch {}
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/logs?limit=200`, { headers: H })
      const data = await r.json()
      setLogs(Array.isArray(data) ? data : [])
    } catch {}
  }, [])

  const fetchCsvs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/csvs`, { headers: H })
      const data = await r.json()
      setCsvs(Array.isArray(data) ? data : [])
    } catch {}
  }, [])

  useEffect(() => {
    fetchFacilities(); fetchLogs(); fetchCsvs()
    const t = setInterval(() => { fetchFacilities(); fetchLogs(); fetchCsvs() }, 15000)
    return () => clearInterval(t)
  }, [])

  async function runFacility(fac_id) {
    setFacilities(prev => ({ ...prev, [fac_id]: { ...prev[fac_id], running: true } }))
    await fetch(`${API}/api/facilities/${fac_id}/run`, { method: "POST", headers: H })
    const poll = setInterval(async () => {
      const r = await fetch(`${API}/api/facilities`, { headers: H })
      const data = await r.json()
      const last = data[fac_id]?.last_sync
      if (last && last.status !== "running") {
        clearInterval(poll)
        setFacilities(prev => ({ ...prev, [fac_id]: { ...data[fac_id], running: false } }))
        fetchLogs(); fetchCsvs()
      }
    }, 3000)
    setTimeout(() => { clearInterval(poll); fetchFacilities() }, 300000)
  }

  async function deleteLog(id) { await fetch(`${API}/api/logs/${id}`, { method: "DELETE", headers: H }); fetchLogs() }
  async function deleteAllLogs(fid) { await fetch(`${API}/api/logs${fid ? `?facility_id=${fid}` : ""}`, { method: "DELETE", headers: H }); fetchLogs() }
  async function deleteCsv(id) { await fetch(`${API}/api/csvs/${id}`, { method: "DELETE", headers: H }); fetchCsvs() }
  async function deleteAllCsvs(fid) { await fetch(`${API}/api/csvs${fid ? `?facility_id=${fid}` : ""}`, { method: "DELETE", headers: H }); fetchCsvs() }
  function downloadCsv(id, filename) { const a = document.createElement("a"); a.href = `${API}/api/csvs/${id}/download?key=${API_KEY}`; a.download = filename; a.click() }

  const facList = Object.entries(facilities)
  const today = new Date().toISOString().slice(0, 10)
  const totalToday = logs.filter(l => l.started_at?.startsWith(today)).length
  const totalRows = logs.filter(l => l.rows).reduce((s, l) => s + (l.rows || 0), 0)
  const errorCount = logs.filter(l => l.status === "error" || l.status === "cookie_error").length
  const cookieAlerts = facList.filter(([, f]) => f.has_cookie && ["expired", "warning"].includes(cookieStatus(f.cookie_age_hours))).length

  const sortedFacs = [...facList].sort(([, a], [, b]) => {
    const p = s => s === "running" ? 0 : s === "expired" || s === "error" ? 1 : s === "warning" ? 2 : s === "unknown" ? 3 : 4
    return p(getFacilityStatus(a)) - p(getFacilityStatus(b))
  })

  const pendingFacs = sortedFacs.filter(([, f]) => { const s = getFacilityStatus(f); return s !== "ok" || !f.last_sync?.started_at?.startsWith(today) })
  const doneFacs = sortedFacs.filter(([, f]) => getFacilityStatus(f) === "ok" && f.last_sync?.started_at?.startsWith(today))

  const filteredLogs = logs.filter(l => {
    if (filterFac && l.facility_id !== filterFac) return false
    if (filterStatus === "error" && l.status !== "error" && l.status !== "cookie_error") return false
    if (filterStatus === "ok" && l.status !== "ok") return false
    return true
  })
  const filteredCsvs = filterFac ? csvs.filter(c => c.facility_id === filterFac) : csvs
  const sidebarFacs = sortedFacs.map(([id, f]) => ({ id, f, status: getFacilityStatus(f) }))

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, 'Helvetica Neue', sans-serif; background: #F8F9FA; color: #111827; }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        button { transition: filter 0.1s; }
        button:hover:not(:disabled) { filter: brightness(0.93); }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 3px; }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <div style={{ width: 220, background: "#fff", borderRight: "1px solid #F3F4F6", display: "flex", flexDirection: "column", flexShrink: 0, position: "sticky", top: 0, height: "100vh", overflowY: "auto" }}>
          <div style={{ padding: "18px 16px 12px", borderBottom: "1px solid #F3F4F6" }}>
            <div style={{ fontSize: 15, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 28, height: 28, background: "#4F46E5", borderRadius: 8, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 14, color: "#fff" }}>↻</span>
              SyncHub
            </div>
          </div>

          <div style={{ padding: "10px 8px" }}>
            {[
              { id: "dashboard", label: "Dashboard", icon: "⊞" },
              { id: "logs", label: "Historial", icon: "☰", badge: errorCount > 0 ? errorCount : null, bc: "#DC2626", bb: "#FEF2F2" },
              { id: "csvs", label: "CSVs", icon: "📄", badge: csvs.length > 0 ? csvs.length : null, bc: "#4F46E5", bb: "#EEF2FF" },
            ].map(item => (
              <div key={item.id} onClick={() => setView(item.id)} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", borderRadius: 8, fontSize: 13, cursor: "pointer", background: view === item.id ? "#EEF2FF" : "transparent", color: view === item.id ? "#4F46E5" : "#6B7280", fontWeight: view === item.id ? 600 : 400, marginBottom: 2 }}>
                <span>{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && <span style={{ background: item.bb, color: item.bc, fontSize: 10, padding: "1px 6px", borderRadius: 10, fontWeight: 600 }}>{item.badge}</span>}
              </div>
            ))}
          </div>

          <div style={{ padding: "0 8px 8px" }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.06em", padding: "8px 10px 4px" }}>Facilities</div>
            {sidebarFacs.map(({ id, f, status }) => (
              <div key={id} onClick={() => { setFilterFac(filterFac === id ? null : id); setView("logs") }} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", borderRadius: 8, fontSize: 12, cursor: "pointer", background: filterFac === id && view === "logs" ? "#EEF2FF" : "transparent", color: filterFac === id && view === "logs" ? "#4F46E5" : "#374151", marginBottom: 1 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", flexShrink: 0, background: status === "ok" ? "#22C55E" : status === "running" ? "#3B82F6" : status === "warning" ? "#F59E0B" : status === "expired" || status === "error" ? "#EF4444" : "#D1D5DB" }} />
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{f.name}</span>
                {f.has_cookie && cookieStatus(f.cookie_age_hours) === "expired" && (
                  <span style={{ fontSize: 9, background: "#FEF2F2", color: "#DC2626", padding: "1px 4px", borderRadius: 4, fontWeight: 600 }}>!</span>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: "auto", padding: "12px 16px", borderTop: "1px solid #F3F4F6" }}>
            <div style={{ fontSize: 11, color: "#9CA3AF", display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} /> Activo · cada 15s
            </div>
            <div style={{ fontSize: 10, color: "#A5B4FC", marginTop: 4 }}>⏱ 8am, 10:30, 1pm, 3:30pm Miami</div>
            {cookieAlerts > 0 && (
              <div style={{ fontSize: 11, color: "#DC2626", marginTop: 6, fontWeight: 500, background: "#FEF2F2", padding: "4px 8px", borderRadius: 6 }}>
                ⚠ {cookieAlerts} cookie{cookieAlerts > 1 ? "s" : ""} por renovar
                <div style={{ fontSize: 10, color: "#9CA3AF", marginTop: 2, fontWeight: 400 }}>Corré cookie_refresher.py</div>
              </div>
            )}
          </div>
        </div>

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          <div style={{ background: "#fff", borderBottom: "1px solid #F3F4F6", padding: "14px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 10 }}>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              {view === "dashboard" ? "Dashboard" : view === "csvs" ? "CSVs generados" : filterFac ? `Historial · ${facilities[filterFac]?.name || filterFac}` : "Historial de syncs"}
            </div>
            <div style={{ fontSize: 12, color: "#9CA3AF" }}>{new Date().toLocaleString("es-AR", { hour12: false })}</div>
          </div>

          <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>

            {/* DASHBOARD */}
            {view === "dashboard" && (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 24 }}>
                  {[
                    { label: "Syncs hoy", value: totalToday, icon: "↻" },
                    { label: "Filas procesadas", value: totalRows.toLocaleString(), icon: "⊞" },
                    { label: "Facilities activas", value: facList.length, icon: "◎" },
                    { label: "Cookies por renovar", value: cookieAlerts, icon: "🍪", warn: cookieAlerts > 0 },
                  ].map((m, i) => (
                    <div key={i} style={{ background: "#fff", borderRadius: 12, padding: "16px 18px", border: m.warn ? "1px solid #FECACA" : "1px solid #F3F4F6", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                      <div style={{ fontSize: 11, color: "#9CA3AF", fontWeight: 500, marginBottom: 8 }}>{m.icon} {m.label}</div>
                      <div style={{ fontSize: 26, fontWeight: 700, color: m.warn ? "#DC2626" : "#111827" }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "2fr 90px 110px 130px 160px 100px", padding: "8px 16px", marginBottom: 4 }}>
                  {["Facility", "Plat.", "Último sync", "Estado", "Acciones", "Log"].map(h => (
                    <div key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</div>
                  ))}
                </div>

                {pendingFacs.length > 0 && (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", marginBottom: 16, overflow: "hidden" }}>
                    <div style={{ padding: "9px 16px", borderBottom: "1px solid #F3F4F6", fontSize: 11, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.05em", background: "#FAFAFA" }}>Pendientes · {pendingFacs.length}</div>
                    {pendingFacs.map(([id, fac]) => <FacilityRow key={id} fac_id={id} fac={fac} done={false} onCookieClick={setCookieModal} onRun={runFacility} onLogClick={(logId, name) => setLogModal({ id: logId, name })} />)}
                  </div>
                )}

                {doneFacs.length > 0 && (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", overflow: "hidden" }}>
                    <div style={{ padding: "9px 16px", borderBottom: "1px solid #F3F4F6", fontSize: 11, fontWeight: 600, color: "#15803D", textTransform: "uppercase", letterSpacing: "0.05em", background: "#F0FDF4" }}>✓ Completados hoy · {doneFacs.length}</div>
                    {doneFacs.map(([id, fac]) => <FacilityRow key={id} fac_id={id} fac={fac} done={true} onCookieClick={setCookieModal} onRun={runFacility} onLogClick={(logId, name) => setLogModal({ id: logId, name })} />)}
                  </div>
                )}
              </>
            )}

            {/* HISTORIAL */}
            {view === "logs" && (
              <>
                <div style={{ display: "flex", gap: 10, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
                  <select value={filterFac || ""} onChange={e => setFilterFac(e.target.value || null)} style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: "7px 12px", fontSize: 13, background: "#fff", cursor: "pointer", outline: "none" }}>
                    <option value="">Todas las facilities</option>
                    {facList.map(([id, f]) => <option key={id} value={id}>{f.name}</option>)}
                  </select>
                  {["all", "ok", "error"].map(s => (
                    <button key={s} onClick={() => setFilterStatus(s)} style={{ border: filterStatus === s ? "1px solid #4F46E5" : "1px solid #E5E7EB", background: filterStatus === s ? "#EEF2FF" : "#fff", color: filterStatus === s ? "#4F46E5" : "#6B7280", borderRadius: 8, padding: "7px 14px", fontSize: 12, cursor: "pointer", fontWeight: filterStatus === s ? 600 : 400 }}>
                      {s === "all" ? "Todos" : s === "ok" ? "✓ OK" : "✕ Errores"}
                    </button>
                  ))}
                  <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: "#9CA3AF" }}>{filteredLogs.length} registros</span>
                    <button onClick={() => setConfirm({ message: filterFac ? `¿Borrar logs de ${facilities[filterFac]?.name}?` : "¿Borrar TODOS los logs?", onConfirm: () => { deleteAllLogs(filterFac); setConfirm(null) } })} style={{ border: "1px solid #FECACA", background: "#FEF2F2", color: "#DC2626", borderRadius: 8, padding: "6px 12px", fontSize: 12, cursor: "pointer" }}>
                      🗑 Borrar {filterFac ? "estos" : "todos"}
                    </button>
                  </div>
                </div>

                <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "150px 1fr 90px 70px 70px 70px 90px 120px", padding: "10px 16px", background: "#FAFAFA", borderBottom: "1px solid #F3F4F6" }}>
                    {["Hora", "Facility", "Plat.", "Filas", "Dur.", "Trigger", "Estado", "Acciones"].map(h => (
                      <div key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</div>
                    ))}
                  </div>
                  {filteredLogs.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "#9CA3AF", fontSize: 13 }}>No hay registros</div>}
                  {filteredLogs.map(log => {
                    const fac = facilities[log.facility_id]
                    const time = log.started_at ? new Date(log.started_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"
                    const dur = log.duration_s ? (log.duration_s > 60 ? `${Math.floor(log.duration_s / 60)}m ${Math.floor(log.duration_s % 60)}s` : `${Math.round(log.duration_s)}s`) : "—"
                    return (
                      <div key={log.id} style={{ display: "grid", gridTemplateColumns: "150px 1fr 90px 70px 70px 70px 90px 120px", padding: "9px 16px", borderBottom: "1px solid #F9FAFB", alignItems: "center", background: log.status === "error" || log.status === "cookie_error" ? "#FFF8F8" : "#fff" }}>
                        <div style={{ fontSize: 11, color: "#6B7280" }}>{time}</div>
                        <div style={{ fontSize: 12, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{fac?.name || log.facility_id}</div>
                        <div><PlatBadge platform={fac?.platform} /></div>
                        <div style={{ fontSize: 12 }}>{log.rows?.toLocaleString() ?? "—"}</div>
                        <div style={{ fontSize: 12, color: "#6B7280" }}>{dur}</div>
                        <div style={{ fontSize: 11, color: "#9CA3AF" }}>{log.trigger || "manual"}</div>
                        <div><Badge status={log.status} /></div>
                        <div style={{ display: "flex", gap: 5 }}>
                          {log.log_output && <button onClick={() => setLogModal({ id: log.id, name: fac?.name })} style={{ background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: 6, padding: "3px 8px", fontSize: 11, cursor: "pointer" }}>Log</button>}
                          <button onClick={() => setConfirm({ message: "¿Borrar este log?", onConfirm: () => { deleteLog(log.id); setConfirm(null) } })} style={{ background: "none", border: "1px solid #FECACA", borderRadius: 6, padding: "3px 7px", fontSize: 11, cursor: "pointer", color: "#DC2626" }}>🗑</button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}

            {/* CSVs */}
            {view === "csvs" && (
              <>
                <div style={{ display: "flex", gap: 10, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
                  <select value={filterFac || ""} onChange={e => setFilterFac(e.target.value || null)} style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: "7px 12px", fontSize: 13, background: "#fff", cursor: "pointer", outline: "none" }}>
                    <option value="">Todas las facilities</option>
                    {facList.map(([id, f]) => <option key={id} value={id}>{f.name}</option>)}
                  </select>
                  <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: "#9CA3AF" }}>{filteredCsvs.length} archivos · auto-borrado 11pm</span>
                    <button onClick={() => setConfirm({ message: filterFac ? `¿Borrar CSVs de ${facilities[filterFac]?.name}?` : "¿Borrar TODOS los CSVs?", onConfirm: () => { deleteAllCsvs(filterFac); setConfirm(null) } })} style={{ border: "1px solid #FECACA", background: "#FEF2F2", color: "#DC2626", borderRadius: 8, padding: "6px 12px", fontSize: 12, cursor: "pointer" }}>
                      🗑 Borrar {filterFac ? "estos" : "todos"}
                    </button>
                  </div>
                </div>
                {filteredCsvs.length === 0 ? (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", padding: 60, textAlign: "center" }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>📄</div>
                    <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 6 }}>No hay CSVs todavía</div>
                    <div style={{ fontSize: 13, color: "#9CA3AF" }}>Se guardan automáticamente al completar cada sync exitoso</div>
                  </div>
                ) : (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 120px 80px 80px 160px 180px", padding: "10px 16px", background: "#FAFAFA", borderBottom: "1px solid #F3F4F6" }}>
                      {["Archivo", "Facility", "Filas", "Tamaño", "Creado", "Acciones"].map(h => (
                        <div key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</div>
                      ))}
                    </div>
                    {filteredCsvs.map(csv => {
                      const fac = facilities[csv.facility_id]
                      const created = csv.created_at ? new Date(csv.created_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"
                      return (
                        <div key={csv.id} style={{ display: "grid", gridTemplateColumns: "1fr 120px 80px 80px 160px 180px", padding: "10px 16px", borderBottom: "1px solid #F9FAFB", alignItems: "center" }}>
                          <div style={{ fontSize: 11, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontFamily: "monospace" }}>📄 {csv.filename}</div>
                          <div><PlatBadge platform={fac?.platform} /></div>
                          <div style={{ fontSize: 12 }}>{csv.rows?.toLocaleString() ?? "—"}</div>
                          <div style={{ fontSize: 12, color: "#6B7280" }}>{fmtBytes(csv.size_bytes)}</div>
                          <div style={{ fontSize: 11, color: "#6B7280" }}>{created}</div>
                          <div style={{ display: "flex", gap: 6 }}>
                            <button onClick={() => downloadCsv(csv.id, csv.filename)} style={{ background: "#EEF2FF", border: "1px solid #C7D2FE", color: "#4F46E5", borderRadius: 7, padding: "5px 10px", fontSize: 11, cursor: "pointer", fontWeight: 500 }}>⬇ Descargar</button>
                            <button onClick={() => setConfirm({ message: `¿Borrar ${csv.filename}?`, onConfirm: () => { deleteCsv(csv.id); setConfirm(null) } })} style={{ background: "none", border: "1px solid #FECACA", borderRadius: 7, padding: "5px 8px", fontSize: 11, cursor: "pointer", color: "#DC2626" }}>🗑</button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {cookieModal && <CookieModal fac_id={cookieModal} facility={facilities[cookieModal]} onClose={() => setCookieModal(null)} onSaved={fetchFacilities} />}
      {logModal && <LogModal logId={logModal.id} facilityName={logModal.name} onClose={() => setLogModal(null)} />}
      {confirm && <Confirm message={confirm.message} onConfirm={confirm.onConfirm} onCancel={() => setConfirm(null)} />}
    </>
  )
}