import { useState, useEffect, useCallback } from "react"

const API = import.meta.env.VITE_API_URL || ""
const API_KEY = "synchub2026"
const H = { "X-API-Key": API_KEY, "Content-Type": "application/json" }

const PLATFORMS = {
  mindbody: { bg: "#EBF3FF", text: "#1A4FA0", dot: "#3B82F6", label: "Mindbody" },
  finnly:   { bg: "#EDFAF4", text: "#0D6645", dot: "#10B981", label: "Finnly" },
  amelia:   { bg: "#FFF7ED", text: "#92400E", dot: "#F59E0B", label: "Amelia" },
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
    <span style={{
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      fontSize: 11, padding: "2px 8px", borderRadius: 20,
      display: "inline-flex", alignItems: "center", gap: 4, fontWeight: 600,
      whiteSpace: "nowrap"
    }}>
      <span style={{ fontSize: status === "running" ? 12 : 10, animation: status === "running" ? "spin 1s linear infinite" : "none" }}>{s.icon}</span>
      {s.label}
    </span>
  )
}

function PlatBadge({ platform }) {
  const p = PLATFORMS[platform] || PLATFORMS.mindbody
  return (
    <span style={{
      background: p.bg, color: p.text, fontSize: 10, padding: "2px 7px",
      borderRadius: 4, fontWeight: 600, letterSpacing: "0.02em"
    }}>{p.label}</span>
  )
}

// ── Cookie / Token Modal ──────────────────────────────────────────────────────

function CookieModal({ fac_id, facility, onClose, onSaved }) {
  const [value, setValue] = useState("")
  const [saving, setSaving] = useState(false)
  const isToken = fac_id === "honey_barry_arena"

  async function save() {
    if (!value.trim()) return
    setSaving(true)
    await fetch(`${API}/api/facilities/${fac_id}/cookie`, {
      method: "POST", headers: H, body: JSON.stringify({ value })
    })
    setSaving(false)
    onSaved()
    onClose()
  }

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
      backdropFilter: "blur(2px)"
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 16, padding: 24, width: 460,
        boxShadow: "0 20px 60px rgba(0,0,0,0.15)", border: "1px solid #E5E7EB"
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#111" }}>{facility?.name}</div>
            <div style={{ fontSize: 12, color: "#9CA3AF", marginTop: 2 }}>
              {isToken ? "Actualizá el Bearer token de Finnly" : "Pegá la cookie de sesión de Mindbody"}
            </div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#9CA3AF", fontSize: 18 }}>✕</button>
        </div>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#6B7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {isToken ? "Bearer token" : "Cookie string"}
        </div>
        <textarea
          autoFocus
          value={value} onChange={e => setValue(e.target.value)}
          placeholder={isToken ? "Bearer eyJhbGci..." : "ASP.NET_SessionId=...; __cf_bm=..."}
          style={{
            width: "100%", height: 100, fontSize: 11, fontFamily: "monospace",
            border: "1px solid #D1D5DB", borderRadius: 8, padding: "10px 12px",
            resize: "none", boxSizing: "border-box", outline: "none",
            background: "#F9FAFB", color: "#111"
          }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 14, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{
            background: "#fff", border: "1px solid #D1D5DB", borderRadius: 8,
            padding: "8px 16px", fontSize: 13, cursor: "pointer", color: "#374151"
          }}>Cancelar</button>
          <button onClick={save} disabled={!value.trim() || saving} style={{
            background: saving ? "#818CF8" : "#4F46E5", color: "#fff", border: "none",
            borderRadius: 8, padding: "8px 18px", fontSize: 13, cursor: "pointer", fontWeight: 500
          }}>{saving ? "Guardando..." : "Guardar"}</button>
        </div>
      </div>
    </div>
  )
}

// ── Log Modal ─────────────────────────────────────────────────────────────────

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
    const a = document.createElement("a")
    a.href = url
    a.download = `sync-log-${logId}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  function downloadCSV() {
    if (!log?.log_output) return
    // Extract CSV-like lines from log
    const lines = log.log_output.split("\n").filter(l => l.includes(",") || l.includes("\t"))
    const blob = new Blob([lines.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `sync-data-${logId}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const dur = log?.duration_s
    ? (log.duration_s > 60 ? `${Math.floor(log.duration_s / 60)}m ${Math.floor(log.duration_s % 60)}s` : `${Math.round(log.duration_s)}s`)
    : null

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
      backdropFilter: "blur(2px)"
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#0F172A", borderRadius: 16, padding: 0, width: 680,
        maxHeight: "85vh", display: "flex", flexDirection: "column",
        boxShadow: "0 25px 60px rgba(0,0,0,0.4)", border: "1px solid #1E293B", overflow: "hidden"
      }}>
        {/* Header */}
        <div style={{
          padding: "16px 20px", borderBottom: "1px solid #1E293B",
          display: "flex", alignItems: "center", justifyContent: "space-between"
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#F1F5F9" }}>
              {facilityName || `Log #${logId}`}
            </div>
            {log && (
              <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                {log.rows ? `${log.rows.toLocaleString()} filas` : "Sin filas"} · {dur || "—"} · {log.trigger}
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {log?.log_output && (
              <>
                <button onClick={downloadCSV} style={{
                  background: "#1E293B", border: "1px solid #334155", color: "#94A3B8",
                  borderRadius: 7, padding: "5px 12px", fontSize: 11, cursor: "pointer"
                }}>⬇ CSV</button>
                <button onClick={downloadLog} style={{
                  background: "#1E293B", border: "1px solid #334155", color: "#94A3B8",
                  borderRadius: 7, padding: "5px 12px", fontSize: 11, cursor: "pointer"
                }}>⬇ Log</button>
              </>
            )}
            <button onClick={onClose} style={{
              background: "none", border: "none", cursor: "pointer", color: "#475569", fontSize: 18, lineHeight: 1
            }}>✕</button>
          </div>
        </div>

        {/* Status bar */}
        {log && (
          <div style={{
            padding: "8px 20px", background: log.status === "ok" ? "#052E16" : "#450A0A",
            borderBottom: "1px solid #1E293B", display: "flex", alignItems: "center", gap: 8
          }}>
            <Badge status={log.status} />
            <span style={{ fontSize: 11, color: "#94A3B8" }}>
              {log.started_at ? new Date(log.started_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"}
            </span>
          </div>
        )}

        {/* Log output */}
        <pre style={{
          fontSize: 11, fontFamily: "'JetBrains Mono', 'Fira Code', monospace", overflow: "auto",
          flex: 1, margin: 0, padding: "16px 20px", whiteSpace: "pre-wrap", wordBreak: "break-all",
          color: "#CBD5E1", lineHeight: 1.7, background: "#0F172A"
        }}>
          {log?.log_output || "Cargando..."}
        </pre>
      </div>
    </div>
  )
}

// ── Facility Row (dashboard list) ─────────────────────────────────────────────

function FacilityRow({ fac_id, fac, dim, onCookieClick, onRun, onLogClick }) {
  const status = getFacilityStatus(fac)
  const plat = PLATFORMS[fac.platform] || PLATFORMS.mindbody
  const syncedToday = fac.last_sync?.started_at?.startsWith(new Date().toISOString().slice(0, 10))

  return (
    <div style={{
      display: "grid", gridTemplateColumns: "2fr 100px 120px 140px 130px 120px",
      alignItems: "center", padding: "10px 16px",
      borderBottom: "1px solid #F3F4F6",
      background: dim ? "#FAFAFA" : "#fff",
      opacity: dim ? 0.55 : 1,
      transition: "opacity 0.2s",
    }}>
      {/* Name */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: status === "ok" ? "#22C55E"
            : status === "running" ? "#3B82F6"
            : status === "warning" ? "#F59E0B"
            : status === "expired" || status === "error" ? "#EF4444"
            : "#D1D5DB",
          flexShrink: 0,
          boxShadow: status === "running" ? "0 0 0 3px rgba(59,130,246,0.2)" : "none",
          animation: status === "running" ? "pulse 1.5s infinite" : "none"
        }} />
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: "#111827" }}>{fac.name}</div>
          <div style={{ fontSize: 11, color: "#9CA3AF", marginTop: 1 }}>
            {fac.schedules?.length ? `${fac.schedules.length}× al día` : "Sin schedule"}
          </div>
        </div>
      </div>

      {/* Platform */}
      <div><PlatBadge platform={fac.platform} /></div>

      {/* Last sync */}
      <div style={{ fontSize: 12, color: "#6B7280" }}>
        {fac.last_sync
          ? <span title={fac.last_sync.started_at}>
              {timeAgo(fac.last_sync.started_at)}
              {fac.last_sync.rows != null && <span style={{ color: "#9CA3AF" }}> · {fac.last_sync.rows.toLocaleString()}</span>}
            </span>
          : <span style={{ color: "#D1D5DB" }}>Nunca</span>}
      </div>

      {/* Status */}
      <div><Badge status={status} /></div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 6 }}>
        <button
          onClick={() => onRun(fac_id)}
          disabled={fac.running}
          style={{
            background: fac.running ? "#EEF2FF" : "#4F46E5",
            color: fac.running ? "#818CF8" : "#fff",
            border: fac.running ? "1px solid #C7D2FE" : "none",
            borderRadius: 7, padding: "5px 10px", fontSize: 11,
            cursor: fac.running ? "not-allowed" : "pointer", fontWeight: 500
          }}
        >
          {fac.running ? "↻" : "▶ Run"}
        </button>
        <button onClick={() => onCookieClick(fac_id)} style={{
          background: "#F9FAFB", border: "1px solid #E5E7EB",
          borderRadius: 7, padding: "5px 8px", fontSize: 11, cursor: "pointer", color: "#6B7280"
        }}>
          {fac.platform === "finnly" ? "🔑" : "🍪"}
        </button>
      </div>

      {/* Last log */}
      <div>
        {fac.last_sync && (
          <button onClick={() => onLogClick(fac.last_sync?.id || null, fac.name)} style={{
            background: "none", border: "1px solid #E5E7EB",
            borderRadius: 7, padding: "5px 10px", fontSize: 11, cursor: "pointer", color: "#6B7280"
          }}>Ver último log</button>
        )}
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [facilities, setFacilities] = useState({})
  const [logs, setLogs] = useState([])
  const [cookieModal, setCookieModal] = useState(null)
  const [logModal, setLogModal] = useState(null)   // { id, name }
  const [view, setView] = useState("dashboard")
  const [filterFac, setFilterFac] = useState(null) // facility_id filter for logs
  const [filterStatus, setFilterStatus] = useState("all") // all | pending | ok | error

  const fetchFacilities = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/facilities`, { headers: H })
      const data = await r.json()
      setFacilities(prev => {
        const merged = {}
        for (const id in data) merged[id] = { ...data[id], running: prev[id]?.running || false }
        return merged
      })
    } catch {}
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/logs?limit=100`, { headers: H })
      const data = await r.json()
      setLogs(Array.isArray(data) ? data : [])
    } catch {}
  }, [])

  useEffect(() => {
    fetchFacilities()
    fetchLogs()
    const t = setInterval(() => { fetchFacilities(); fetchLogs() }, 15000)
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
        fetchLogs()
      }
    }, 3000)
    setTimeout(() => { clearInterval(poll); fetchFacilities() }, 300000)
  }

  // ── Computed ──────────────────────────────────────────────────────────────

  const facList = Object.entries(facilities)
  const today = new Date().toISOString().slice(0, 10)

  const totalToday = logs.filter(l => l.started_at?.startsWith(today)).length
  const totalRows = logs.filter(l => l.rows).reduce((s, l) => s + (l.rows || 0), 0)
  const errorCount = logs.filter(l => l.status === "error" || l.status === "cookie_error").length
  const cookieAlerts = facList.filter(([, f]) => {
    if (!f.has_cookie) return false
    const s = cookieStatus(f.cookie_age_hours)
    return s === "expired" || s === "warning"
  }).length

  // Sort: pending/errors first, then by last sync (oldest first), then synced-ok at bottom
  const sortedFacs = [...facList].sort(([, a], [, b]) => {
    const sa = getFacilityStatus(a)
    const sb = getFacilityStatus(b)
    const priority = s => s === "running" ? 0 : s === "expired" || s === "error" ? 1 : s === "warning" ? 2 : s === "unknown" ? 3 : 4
    return priority(sa) - priority(sb)
  })

  const pendingFacs = sortedFacs.filter(([, f]) => {
    const s = getFacilityStatus(f)
    return s !== "ok" || !f.last_sync?.started_at?.startsWith(today)
  })
  const doneFacs = sortedFacs.filter(([, f]) => {
    const s = getFacilityStatus(f)
    return s === "ok" && f.last_sync?.started_at?.startsWith(today)
  })

  // Filter logs
  const filteredLogs = logs.filter(l => {
    if (filterFac && l.facility_id !== filterFac) return false
    if (filterStatus !== "all") {
      if (filterStatus === "error" && l.status !== "error" && l.status !== "cookie_error") return false
      if (filterStatus === "ok" && l.status !== "ok") return false
    }
    return true
  })

  // ── Sidebar items ─────────────────────────────────────────────────────────

  const sidebarFacs = sortedFacs.map(([id, f]) => ({ id, f, status: getFacilityStatus(f) }))

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, 'Helvetica Neue', sans-serif; background: #F8F9FA; color: #111827; }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        button:hover { filter: brightness(0.95); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 3px; }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>

        {/* ── Sidebar ──────────────────────────────────────────────────── */}
        <div style={{
          width: 220, background: "#fff", borderRight: "1px solid #F3F4F6",
          display: "flex", flexDirection: "column", flexShrink: 0,
          position: "sticky", top: 0, height: "100vh", overflowY: "auto"
        }}>
          {/* Logo */}
          <div style={{ padding: "18px 16px 12px", borderBottom: "1px solid #F3F4F6" }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#111827", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                width: 28, height: 28, background: "#4F46E5", borderRadius: 8,
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                fontSize: 14, color: "#fff"
              }}>↻</span>
              SyncHub
            </div>
          </div>

          {/* Nav */}
          <div style={{ padding: "10px 8px" }}>
            {[
              { id: "dashboard", label: "Dashboard", icon: "⊞" },
              { id: "logs", label: "Historial", icon: "☰" },
            ].map(item => (
              <div key={item.id} onClick={() => setView(item.id)} style={{
                display: "flex", alignItems: "center", gap: 8, padding: "7px 10px",
                borderRadius: 8, fontSize: 13, cursor: "pointer",
                background: view === item.id ? "#EEF2FF" : "transparent",
                color: view === item.id ? "#4F46E5" : "#6B7280",
                fontWeight: view === item.id ? 600 : 400, marginBottom: 2,
                transition: "background 0.15s"
              }}>
                <span style={{ fontSize: 14 }}>{item.icon}</span> {item.label}
              </div>
            ))}
          </div>

          {/* Facilities list in sidebar */}
          <div style={{ padding: "0 8px 8px" }}>
            <div style={{
              fontSize: 10, fontWeight: 600, color: "#9CA3AF",
              textTransform: "uppercase", letterSpacing: "0.06em",
              padding: "8px 10px 4px"
            }}>Facilities</div>
            {sidebarFacs.map(({ id, f, status }) => (
              <div key={id} onClick={() => {
                setFilterFac(filterFac === id ? null : id)
                setView("logs")
              }} style={{
                display: "flex", alignItems: "center", gap: 8, padding: "6px 10px",
                borderRadius: 8, fontSize: 12, cursor: "pointer",
                background: filterFac === id && view === "logs" ? "#EEF2FF" : "transparent",
                color: filterFac === id && view === "logs" ? "#4F46E5" : "#374151",
                marginBottom: 1, transition: "background 0.15s"
              }}>
                <div style={{
                  width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
                  background: status === "ok" ? "#22C55E"
                    : status === "running" ? "#3B82F6"
                    : status === "warning" ? "#F59E0B"
                    : status === "expired" || status === "error" ? "#EF4444"
                    : "#D1D5DB"
                }} />
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{f.name}</span>
              </div>
            ))}
          </div>

          {/* Bottom status */}
          <div style={{ marginTop: "auto", padding: "12px 16px", borderTop: "1px solid #F3F4F6" }}>
            <div style={{ fontSize: 11, color: "#9CA3AF", display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} />
              Activo · actualiza cada 15s
            </div>
            {cookieAlerts > 0 && (
              <div style={{ fontSize: 11, color: "#DC2626", marginTop: 6, fontWeight: 500 }}>
                ⚠ {cookieAlerts} cookie{cookieAlerts > 1 ? "s" : ""} por renovar
              </div>
            )}
          </div>
        </div>

        {/* ── Main ─────────────────────────────────────────────────────── */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

          {/* Topbar */}
          <div style={{
            background: "#fff", borderBottom: "1px solid #F3F4F6",
            padding: "14px 24px", display: "flex", alignItems: "center", justifyContent: "space-between",
            position: "sticky", top: 0, zIndex: 10
          }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#111827" }}>
              {view === "dashboard" ? "Dashboard" : filterFac ? `Historial · ${facilities[filterFac]?.name || filterFac}` : "Historial de syncs"}
            </div>
            <div style={{ fontSize: 12, color: "#9CA3AF" }}>
              {new Date().toLocaleString("es-AR", { hour12: false })}
            </div>
          </div>

          <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>

            {/* ── DASHBOARD ──────────────────────────────────────────────── */}
            {view === "dashboard" && (
              <>
                {/* Metrics */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 24 }}>
                  {[
                    { label: "Syncs hoy", value: totalToday, icon: "↻" },
                    { label: "Filas procesadas", value: totalRows.toLocaleString(), icon: "⊞" },
                    { label: "Facilities activas", value: facList.length, icon: "◎" },
                    { label: "Errores recientes", value: errorCount, icon: "⚠", warn: errorCount > 0 },
                  ].map((m, i) => (
                    <div key={i} style={{
                      background: "#fff", borderRadius: 12, padding: "16px 18px",
                      border: m.warn ? "1px solid #FECACA" : "1px solid #F3F4F6",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.04)"
                    }}>
                      <div style={{ fontSize: 11, color: "#9CA3AF", fontWeight: 500, marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
                        <span>{m.icon}</span> {m.label}
                      </div>
                      <div style={{ fontSize: 26, fontWeight: 700, color: m.warn ? "#DC2626" : "#111827" }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Table header */}
                <div style={{
                  display: "grid", gridTemplateColumns: "2fr 100px 120px 140px 130px 120px",
                  padding: "8px 16px", marginBottom: 4
                }}>
                  {["Facility", "Plataforma", "Último sync", "Estado", "Acciones", "Log"].map(h => (
                    <div key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</div>
                  ))}
                </div>

                {/* Pending / needs attention */}
                {pendingFacs.length > 0 && (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", marginBottom: 16, overflow: "hidden" }}>
                    <div style={{ padding: "10px 16px", borderBottom: "1px solid #F3F4F6", fontSize: 11, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.05em", background: "#FAFAFA" }}>
                      Pendientes · {pendingFacs.length}
                    </div>
                    {pendingFacs.map(([id, fac]) => (
                      <FacilityRow
                        key={id} fac_id={id} fac={fac} dim={false}
                        onCookieClick={setCookieModal}
                        onRun={runFacility}
                        onLogClick={(logId, name) => setLogModal({ id: logId, name })}
                      />
                    ))}
                  </div>
                )}

                {/* Done today */}
                {doneFacs.length > 0 && (
                  <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", boxShadow: "0 1px 3px rgba(0,0,0,0.04)", overflow: "hidden" }}>
                    <div style={{ padding: "10px 16px", borderBottom: "1px solid #F3F4F6", fontSize: 11, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.05em", background: "#FAFAFA" }}>
                      Completados hoy · {doneFacs.length}
                    </div>
                    {doneFacs.map(([id, fac]) => (
                      <FacilityRow
                        key={id} fac_id={id} fac={fac} dim={true}
                        onCookieClick={setCookieModal}
                        onRun={runFacility}
                        onLogClick={(logId, name) => setLogModal({ id: logId, name })}
                      />
                    ))}
                  </div>
                )}
              </>
            )}

            {/* ── LOGS ───────────────────────────────────────────────────── */}
            {view === "logs" && (
              <>
                {/* Filters */}
                <div style={{ display: "flex", gap: 10, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
                  {/* Facility selector */}
                  <select value={filterFac || ""} onChange={e => setFilterFac(e.target.value || null)} style={{
                    border: "1px solid #E5E7EB", borderRadius: 8, padding: "7px 12px", fontSize: 13,
                    background: "#fff", color: "#374151", cursor: "pointer", outline: "none"
                  }}>
                    <option value="">Todas las facilities</option>
                    {facList.map(([id, f]) => <option key={id} value={id}>{f.name}</option>)}
                  </select>

                  {/* Status filter */}
                  {["all", "ok", "error"].map(s => (
                    <button key={s} onClick={() => setFilterStatus(s)} style={{
                      border: filterStatus === s ? "1px solid #4F46E5" : "1px solid #E5E7EB",
                      background: filterStatus === s ? "#EEF2FF" : "#fff",
                      color: filterStatus === s ? "#4F46E5" : "#6B7280",
                      borderRadius: 8, padding: "7px 14px", fontSize: 12,
                      cursor: "pointer", fontWeight: filterStatus === s ? 600 : 400
                    }}>
                      {s === "all" ? "Todos" : s === "ok" ? "✓ OK" : "✕ Errores"}
                    </button>
                  ))}

                  <span style={{ fontSize: 12, color: "#9CA3AF", marginLeft: "auto" }}>
                    {filteredLogs.length} registros
                  </span>
                </div>

                {/* Table */}
                <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #F3F4F6", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
                  {/* Header */}
                  <div style={{
                    display: "grid", gridTemplateColumns: "150px 1fr 90px 80px 80px 80px 90px 110px",
                    padding: "10px 16px", background: "#FAFAFA", borderBottom: "1px solid #F3F4F6"
                  }}>
                    {["Hora", "Facility", "Plataforma", "Filas", "Duración", "Trigger", "Estado", "Acciones"].map(h => (
                      <div key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</div>
                    ))}
                  </div>

                  {filteredLogs.length === 0 && (
                    <div style={{ padding: 40, textAlign: "center", color: "#9CA3AF", fontSize: 13 }}>
                      No hay registros para este filtro
                    </div>
                  )}

                  {filteredLogs.map(log => {
                    const fac = facilities[log.facility_id]
                    const time = log.started_at ? new Date(log.started_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"
                    const dur = log.duration_s
                      ? (log.duration_s > 60 ? `${Math.floor(log.duration_s / 60)}m ${Math.floor(log.duration_s % 60)}s` : `${Math.round(log.duration_s)}s`)
                      : "—"
                    return (
                      <div key={log.id} style={{
                        display: "grid", gridTemplateColumns: "150px 1fr 90px 80px 80px 80px 90px 110px",
                        padding: "10px 16px", borderBottom: "1px solid #F9FAFB",
                        alignItems: "center",
                        background: log.status === "error" || log.status === "cookie_error" ? "#FFF8F8" : "#fff"
                      }}>
                        <div style={{ fontSize: 11, color: "#6B7280", fontVariantNumeric: "tabular-nums" }}>{time}</div>
                        <div style={{ fontSize: 12, fontWeight: 500, color: "#111827", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {fac?.name || log.facility_id}
                        </div>
                        <div><PlatBadge platform={fac?.platform} /></div>
                        <div style={{ fontSize: 12, color: "#374151" }}>{log.rows?.toLocaleString() ?? "—"}</div>
                        <div style={{ fontSize: 12, color: "#6B7280" }}>{dur}</div>
                        <div style={{ fontSize: 11, color: "#9CA3AF" }}>{log.trigger || "manual"}</div>
                        <div><Badge status={log.status} /></div>
                        <div style={{ display: "flex", gap: 5 }}>
                          {log.log_output && (
                            <button onClick={() => setLogModal({ id: log.id, name: fac?.name })} style={{
                              background: "#F9FAFB", border: "1px solid #E5E7EB",
                              borderRadius: 6, padding: "4px 8px", fontSize: 11, cursor: "pointer", color: "#374151"
                            }}>Log</button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {cookieModal && (
        <CookieModal
          fac_id={cookieModal}
          facility={facilities[cookieModal]}
          onClose={() => setCookieModal(null)}
          onSaved={fetchFacilities}
        />
      )}
      {logModal && (
        <LogModal
          logId={logModal.id}
          facilityName={logModal.name}
          onClose={() => setLogModal(null)}
        />
      )}
    </>
  )
}