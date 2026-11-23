import { useEffect, useState } from 'react'
import { api } from './data'
import { Chart } from './Chart'
import type { Incident, IncidentRow } from './types'

function Detail({ id, actor, onDone }: { id: string; actor: string; onDone: () => void }) {
  const [inc, setInc] = useState<Incident | null>(null); const [reason, setReason] = useState(''); const [err, setErr] = useState('')
  const load = () => api.incident(id).then(setInc)
  useEffect(() => { setInc(null); setReason(''); setErr(''); load() }, [id])
  if (!inc) return <div className="card muted">Loading…</div>
  const ev = inc.evidence, n = inc.note
  const names = Object.fromEntries(ev.signals.map(s => [s.id, s.name]))
  const go = async (decision: string) => {
    setErr('')
    try { await api.decideIncident(inc, { decision, actor, reason }); await load(); onDone() } catch (e) { setErr((e as Error).message) }
  }
  return (
    <div className="grid">
      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between' }}><h2 style={{ margin: 0 }}>{inc.id} · detected {ev.detected_minutes_after_fault} min after the fault started</h2>
          <span className={`badge ${inc.state === 'open' ? 'b-remap' : 'b-done'}`}>{inc.decision ? `${inc.decision} by ${inc.decided_by}` : 'open'}</span></div>
        <div style={{ marginTop: 12 }}><Chart series={inc.series} names={names} /></div>
      </div>
      {n && <div className="card">
        <h3>Agent's shift note <span className="muted" style={{ textTransform: 'none', letterSpacing: 0 }}>· {n.source === 'model' ? `model, checks ${n.checks}` : n.checks}</span></h3>
        <div className="note"><p style={{ marginTop: 0 }}>{n.summary}</p>
          <p className="small"><b>Unit:</b> {n.unit} · <b>Matches past incident:</b> {n.matched_incident ?? 'none with confidence'}</p>
          <p className="small"><b>Would prove it wrong:</b> {n.would_prove_wrong}</p>
          <p className="small" style={{ marginBottom: 0 }}><b>Check first:</b> {n.next_check}</p></div>
        <div style={{ marginTop: 14 }}>
          {inc.state === 'open' && !inc.decision || inc.decision === 'defer' ? (
            <div className="grid" style={{ gap: 6 }}>
              <div className="row"><button className="primary" onClick={() => go('accept')}>Accept</button><button onClick={() => go('override')}>Override</button><button onClick={() => go('defer')}>Defer</button>
                <input className="reason" placeholder="Reason (needed to override or defer)" value={reason} onChange={e => setReason(e.target.value)} /></div>
              {err && <div className="err">{err}</div>}
            </div>) : <p className="small muted" style={{ margin: 0 }}>{inc.decision} by {inc.decided_by}{inc.decision_reason ? `: ${inc.decision_reason}` : ''}</p>}
        </div>
      </div>}
      <div className="grid g2">
        <div className="card"><h3>Signals that moved first</h3><table className="small"><tbody>
          {ev.signals.map(s => <tr key={s.id}><td className="mono">{s.id}</td><td>{s.name}<div className="muted">{s.area}</div></td><td>+{s.minutes_after_fault_start} min</td><td>{s.direction === 'up' ? '▲' : '▼'} {s.max_deviation_in_std}σ</td></tr>)}
        </tbody></table></div>
        <div className="card"><h3>Incident library, {ev.window_hours} h after detection</h3>
          {ev.library.map(m => <div key={m.fault} style={{ marginBottom: 10 }}>
            <div className="row small" style={{ justifyContent: 'space-between' }}><span>Incident {m.fault}: {m.cause}</span><b>{m.similarity}</b></div>
            <div className="bar"><i style={{ width: `${Math.max(0, m.similarity) * 100}%` }} /></div></div>)}
          <p className="small muted" style={{ marginBottom: 0 }}>Units in the order they moved: {ev.units.map(u => u.area).join(' → ')}</p></div>
      </div>
    </div>
  )
}

export function Incidents({ id, actor }: { id?: string; actor: string }) {
  const [rows, setRows] = useState<IncidentRow[]>([])
  const load = () => api.incidents().then(setRows)
  useEffect(() => { load() }, [])
  const current = id ?? rows[0]?.id
  return (
    <>
      <h1>Deviations at plant A</h1>
      <p className="lead">Each run is 48 hours of the plant with a disturbance switched on after 8 hours. The agent detects it, traces it, matches it to past incidents and writes a note. Nothing is acted on until a person accepts, overrides or defers it.</p>
      <div className="grid split">
        <div className="card list" style={{ padding: 8, alignSelf: 'start' }}>
          {rows.map(r => <a key={r.id} href={`#/incidents/${r.id}`} className={r.id === current ? 'on' : ''}>
            <div className="row" style={{ justifyContent: 'space-between' }}><b>{r.id}</b><span className={`badge ${r.state === 'open' ? 'b-remap' : 'b-done'}`}>{r.decision ?? 'open'}</span></div>
            <div className="small muted">{r.unit ?? '—'} · +{r.detected_after} min</div></a>)}
        </div>
        {current && <Detail id={current} actor={actor} onDone={load} />}
      </div>
    </>
  )
}
