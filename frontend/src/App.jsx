import { useState, useEffect, useRef, useCallback } from "react"

const API = import.meta.env.VITE_API_URL || ""

const PLATFORM_COLORS = {
  mindbody: { bg: "#E6F1FB", text: "#0C447C", label: "Mindbody" },
  finnly:   { bg: "#E1F5EE", text: "#085041", label: "Finnly" },
  amelia:   { bg: "#FAEEDA", text: "#633806", label: "Amelia" },
}

function timeAgo(isoStr) {
  if (!isoStr) return "—"
  const diff = (Date.now() - new Date(isoStr + "Z").getTime()) / 1000
  if (diff < 60) return "hace un momento"
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}m`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`
  return `hace ${Math.floor(diff / 86400)}d`
}

function cookieStatus(ageHours) {
  if (ageHours === null || ageHours === undefined) return "unknown"
  if (ageHours > 20) return "expired"
  if (ageHours > 12) return "warning"
  return "ok"
}

function StatusBadge({ status }) {
  const styles = {
    ok:           { bg: "#EAF3DE", color: "#27500A", icon: "✓", label: "OK" },
    warning:      { bg: "#FAEEDA", color: "#633806", icon: "⚡", label: "Cookie pronto" },
    expired:      { bg: "#FCEBEB", color: "#791F1F", icon: "✕", label: "Cookie expirada" },
    cookie_error: { bg: "#FCEBEB", color: "#791F1F", icon: "✕", label: "Cookie expirada" },
    error:        { bg: "#FCEBEB", color: "#791F1F", icon: "✕", label: "Error" },
    running:      { bg: "#E6F1FB", color: "#0C447C", icon: "↻", label: "Corriendo..." },
    unknown:      { bg: "#F1EFE8", color: "#5F5E5A", icon: "?", label: "Sin cookie" },
  }
  const s = styles[status] || styles.unknown
  return (
    <span style={{
      background: s.bg, color: s.color,
      fontSize: 11, padding: "3px 8px", borderRadius: 4,
      display: "inline-flex", alignItems: "center", gap: 4, fontWeight: 500
    }}>
      {s.icon} {s.label}
    </span>
  )
}

function CookieModal({ facility, fac_id, onClose, onSaved }) {
  const [value, setValue] = useState("")
  const isToken = fac_id === "honey_barry_arena"

  async function save() {
    const endpoint = isToken
      ? `${API}/api/facilities/${fac_id}/token`
      : `${API}/api/facilities/${fac_id}/cookie`
    await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value })
    })
    onSaved()
    onClose()
  }

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "var(--bg-primary, #fff)", borderRadius: 12,
        border: "0.5px solid rgba(0,0,0,0.12)", padding: 20, width: 440,
        boxShadow: "0 4px 24px rgba(0,0,0,0.12)"
      }}>
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>{facility?.name}</div>
        <div style={{ fontSize: 12, color: "#888", marginBottom: 14 }}>
          {isToken
            ? "Pegá el Bearer token de Finnly (Authorization header de DevTools)."
            : "Pegá la cookie de DevTools → GetTokens. Solo actualizá si el sync falla."}
        </div>
        <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>
          {isToken ? "Bearer token" : "Cookie string"}
        </div>
        <textarea
          value={value} onChange={e => setValue(e.target.value)}
          placeholder={isToken ? "Bearer eyJhbGci..." : "ASP.NET_SessionId=...; __cf_bm=..."}
          style={{
            width: "100%", height: 90, fontSize: 11, fontFamily: "monospace",
            border: "0.5px solid rgba(0,0,0,0.2)", borderRadius: 8, padding: 8,
            resize: "none", boxSizing: "border-box"
          }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{
            background: "transparent", border: "0.5px solid rgba(0,0,0,0.2)",
            borderRadius: 8, padding: "7px 14px", fontSize: 12, cursor: "pointer"
          }}>Cancelar</button>
          <button onClick={save} disabled={!value.trim()} style={{
            background: "#534AB7", color: "#fff", border: "none",
            borderRadius: 8, padding: "7px 16px", fontSize: 12, cursor: "pointer"
          }}>Guardar</button>
        </div>
      </div>
    </div>
  )
}

function LogModal({ logId, onClose }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    if (!logId) return
    fetch(`${API}/api/logs/${logId}`).then(r => r.json()).then(setLog)
  }, [logId])

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#1a1a2e", color: "#e2e2e2", borderRadius: 12,
        padding: 20, width: 600, maxHeight: "80vh", display: "flex", flexDirection: "column"
      }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12, color: "#fff" }}>
          Log #{logId}
        </div>
        <pre style={{
          fontSize: 11, fontFamily: "monospace", overflow: "auto",
          flex: 1, margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all"
        }}>
          {log?.log_output || "Cargando..."}
        </pre>
        <button onClick={onClose} style={{
          marginTop: 12, background: "#534AB7", color: "#fff", border: "none",
          borderRadius: 8, padding: "7px 16px", fontSize: 12, cursor: "pointer", alignSelf: "flex-end"
        }}>Cerrar</button>
      </div>
    </div>
  )
}

function FacilityCard({ fac_id, fac, onCookieClick, onRun }) {
  const plat = PLATFORM_COLORS[fac.platform] || PLATFORM_COLORS.mindbody
  const ckStatus = fac.cookie_file
    ? cookieStatus(fac.cookie_age_hours)
    : (fac.platform === "finnly" ? "ok" : "unknown")
  const lastStatus = fac.last_sync?.status
  const displayStatus = fac.running ? "running"
    : (lastStatus === "cookie_error" || ckStatus === "expired") ? "expired"
    : ckStatus === "warning" ? "warning"
    : lastStatus === "error" ? "error"
    : lastStatus === "ok" ? "ok" : "unknown"

  const scheduleText = fac.schedules?.length
    ? `${fac.schedules.length}× día`
    : "Sin schedule"

  return (
    <div style={{
      background: "#fff", border: displayStatus === "expired"
        ? "1px solid #E24B4A" : "0.5px solid rgba(0,0,0,0.1)",
      borderRadius: 12, padding: 14,
      transition: "border-color 0.2s"
    }}>
      {fac.running && (
        <div style={{
          height: 3, borderRadius: 2, marginBottom: 10,
          background: "linear-gradient(90deg,#534AB7,#AFA9EC,#534AB7)",
          backgroundSize: "200%",
          animation: "slide 1.5s linear infinite"
        }} />
      )}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500 }}>{fac.name}</div>
          <span style={{
            fontSize: 10, padding: "2px 7px", borderRadius: 4,
            background: plat.bg, color: plat.text
          }}>{plat.label}</span>
        </div>
        <StatusBadge status={displayStatus} />
      </div>
      <div style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>
        🕐 {scheduleText}
      </div>
      <div style={{ fontSize: 11, color: "#aaa", marginBottom: 12 }}>
        ⟳ {fac.last_sync
          ? `${timeAgo(fac.last_sync.started_at)} · ${fac.last_sync.rows ?? "—"} filas`
          : "Nunca sincronizado"}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => onRun(fac_id)}
          disabled={fac.running}
          style={{
            background: fac.running ? "#888" : "#534AB7", color: "#fff", border: "none",
            borderRadius: 8, padding: "6px 12px", fontSize: 12, cursor: fac.running ? "not-allowed" : "pointer",
            display: "flex", alignItems: "center", gap: 4
          }}
        >
          {fac.running ? "↻ Corriendo..." : "▶ Run now"}
        </button>
        <button
          onClick={() => onCookieClick(fac_id)}
          style={{
            background: "transparent", border: "0.5px solid rgba(0,0,0,0.2)",
            borderRadius: 8, padding: "6px 10px", fontSize: 12, cursor: "pointer",
            color: "#555"
          }}
        >
          {fac.platform === "finnly" ? "🔑 Token" : "🍪 Cookie"}
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [facilities, setFacilities] = useState({})
  const [logs, setLogs] = useState([])
  const [cookieModal, setCookieModal] = useState(null)
  const [logModal, setLogModal] = useState(null)
  const [view, setView] = useState("dashboard")
  const [runningFacs, setRunningFacs] = useState({})

  const fetchFacilities = useCallback(async () => {
    const r = await fetch(`${API}/api/facilities`)
    const data = await r.json()
    setFacilities(prev => {
      const merged = {}
      for (const id in data) {
        merged[id] = { ...data[id], running: prev[id]?.running || false }
      }
      return merged
    })
  }, [])

  const fetchLogs = useCallback(async () => {
    const r = await fetch(`${API}/api/logs?limit=50`)
    setLogs(await r.json())
  }, [])

  useEffect(() => {
    fetchFacilities()
    fetchLogs()
    const t = setInterval(() => { fetchFacilities(); fetchLogs() }, 15000)
    return () => clearInterval(t)
  }, [])

  async function runFacility(fac_id) {
    setFacilities(prev => ({ ...prev, [fac_id]: { ...prev[fac_id], running: true } }))
    await fetch(`${API}/api/facilities/${fac_id}/run`, { method: "POST" })
    // Poll until done
    const poll = setInterval(async () => {
      const r = await fetch(`${API}/api/facilities`)
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

  const byPlatform = {}
  for (const [id, fac] of Object.entries(facilities)) {
    const p = fac.platform || "mindbody"
    if (!byPlatform[p]) byPlatform[p] = {}
    byPlatform[p][id] = fac
  }

  const totalToday = logs.filter(l => l.started_at?.startsWith(new Date().toISOString().slice(0, 10))).length
  const totalRows = logs.filter(l => l.rows).reduce((s, l) => s + (l.rows || 0), 0)
  const errorCount = logs.filter(l => l.status === "error" || l.status === "cookie_error").length
  const cookieAlerts = Object.values(facilities).filter(f => cookieStatus(f.cookie_age_hours) !== "ok" && f.cookie_file).length

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #f5f4f1; color: #1a1a1a; }
        @keyframes slide { 0%{background-position:100%} 100%{background-position:-100%} }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <div style={{
          width: 200, background: "#fff", borderRight: "0.5px solid rgba(0,0,0,0.08)",
          padding: 16, flexShrink: 0, display: "flex", flexDirection: "column", gap: 2
        }}>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 18 }}>↻</span> SyncHub
          </div>
          {[
            { id: "dashboard", label: "Dashboard", icon: "⊞" },
            { id: "logs", label: "Historial", icon: "☰" },
          ].map(item => (
            <div key={item.id} onClick={() => setView(item.id)} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "7px 8px",
              borderRadius: 8, fontSize: 13, cursor: "pointer",
              background: view === item.id ? "#f0eff7" : "transparent",
              color: view === item.id ? "#534AB7" : "#666",
              fontWeight: view === item.id ? 500 : 400
            }}>
              {item.icon} {item.label}
            </div>
          ))}
          <div style={{ fontSize: 11, color: "#aaa", textTransform: "uppercase", letterSpacing: "0.06em", margin: "12px 0 4px", paddingLeft: 8 }}>Plataformas</div>
          {Object.entries(PLATFORM_COLORS).map(([p, c]) => {
            const count = Object.values(facilities).filter(f => f.platform === p).length
            return (
              <div key={p} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", fontSize: 13, color: "#666" }}>
                · {c.label}
                {count > 0 && (
                  <span style={{ marginLeft: "auto", background: c.bg, color: c.text, fontSize: 10, padding: "2px 6px", borderRadius: 4 }}>{count}</span>
                )}
              </div>
            )
          })}
        </div>

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {/* Topbar */}
          <div style={{
            background: "#fff", borderBottom: "0.5px solid rgba(0,0,0,0.08)",
            padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <div style={{ fontSize: 15, fontWeight: 500 }}>
              {view === "dashboard" ? "Dashboard" : "Historial de syncs"}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12, color: "#888" }}>
              {cookieAlerts > 0 && (
                <span style={{ color: "#A32D2D", fontWeight: 500 }}>⚠ {cookieAlerts} cookie{cookieAlerts > 1 ? "s" : ""} por renovar</span>
              )}
              <span>● Activo</span>
              <span style={{ color: "#aaa" }}>{new Date().toLocaleString("es-AR", { hour12: false })}</span>
            </div>
          </div>

          <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
            {view === "dashboard" && (
              <>
                {/* Metrics */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
                  {[
                    { label: "Syncs hoy", value: totalToday },
                    { label: "Registros (total)", value: totalRows.toLocaleString() },
                    { label: "Facilities activas", value: Object.keys(facilities).length },
                    { label: "Errores (últimos 50)", value: errorCount, warn: errorCount > 0 },
                  ].map((m, i) => (
                    <div key={i} style={{ background: "#ebebeb", borderRadius: 8, padding: "12px 14px" }}>
                      <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>{m.label}</div>
                      <div style={{ fontSize: 22, fontWeight: 500, color: m.warn ? "#A32D2D" : "inherit" }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Facilities by platform */}
                {Object.entries(byPlatform).map(([platform, facs]) => (
                  <div key={platform} style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                      {PLATFORM_COLORS[platform]?.label || platform}
                      <span style={{ fontSize: 12, color: "#aaa", fontWeight: 400 }}>· {Object.keys(facs).length} facilities</span>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                      {Object.entries(facs).map(([fac_id, fac]) => (
                        <FacilityCard
                          key={fac_id}
                          fac_id={fac_id}
                          fac={fac}
                          onCookieClick={id => setCookieModal(id)}
                          onRun={runFacility}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </>
            )}

            {view === "logs" && (
              <div style={{ background: "#fff", border: "0.5px solid rgba(0,0,0,0.08)", borderRadius: 12, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: "#f5f4f1" }}>
                      {["Hora", "Facility", "Plataforma", "Filas", "Duración", "Trigger", "Estado", ""].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#666", fontWeight: 500, borderBottom: "0.5px solid rgba(0,0,0,0.08)" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map(log => {
                      const fac = facilities[log.facility_id]
                      const plat = PLATFORM_COLORS[fac?.platform] || PLATFORM_COLORS.mindbody
                      const time = log.started_at ? new Date(log.started_at + "Z").toLocaleString("es-AR", { hour12: false }) : "—"
                      const dur = log.duration_s ? (log.duration_s > 60 ? `${Math.floor(log.duration_s / 60)}m ${Math.floor(log.duration_s % 60)}s` : `${Math.round(log.duration_s)}s`) : "—"
                      return (
                        <tr key={log.id} style={{ borderBottom: "0.5px solid rgba(0,0,0,0.06)" }}>
                          <td style={{ padding: "8px 12px", color: "#555" }}>{time}</td>
                          <td style={{ padding: "8px 12px", fontWeight: 500 }}>{fac?.name || log.facility_id}</td>
                          <td style={{ padding: "8px 12px" }}>
                            <span style={{ background: plat.bg, color: plat.text, fontSize: 10, padding: "2px 6px", borderRadius: 4 }}>{plat.label}</span>
                          </td>
                          <td style={{ padding: "8px 12px" }}>{log.rows?.toLocaleString() ?? "—"}</td>
                          <td style={{ padding: "8px 12px", color: "#888" }}>{dur}</td>
                          <td style={{ padding: "8px 12px", color: "#aaa" }}>{log.trigger || "manual"}</td>
                          <td style={{ padding: "8px 12px" }}><StatusBadge status={log.status} /></td>
                          <td style={{ padding: "8px 12px" }}>
                            {log.log_output && (
                              <button onClick={() => setLogModal(log.id)} style={{
                                background: "transparent", border: "0.5px solid rgba(0,0,0,0.15)",
                                borderRadius: 6, padding: "3px 8px", fontSize: 11, cursor: "pointer", color: "#555"
                              }}>Ver log</button>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {cookieModal && (
        <CookieModal
          fac_id={cookieModal}
          facility={facilities[cookieModal]}
          onClose={() => setCookieModal(null)}
          onSaved={fetchFacilities}
        />
      )}
      {logModal && <LogModal logId={logModal} onClose={() => setLogModal(null)} />}
    </>
  )
}
