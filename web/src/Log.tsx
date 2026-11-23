import { useEffect, useState } from 'react'
import { api, STATIC } from './data'
import type { LogEntry } from './types'

export function Log() {
  const [log, setLog] = useState<{ entries: LogEntry[]; broken_at: number | null } | null>(null); const [hand, setHand] = useState<string[]>([])
  useEffect(() => { api.log().then(setLog); api.handover().then(setHand) }, [])
  if (!log) return null
  return (
    <>
      <h1>Decision log</h1>
      <p className="lead">Every accept, override, hold and defer, with who and why. Each entry's hash covers the one before it, so changing any old entry breaks the chain from that point.
        {STATIC ? ' In this demo the log lives in your browser.' : ' In PostgreSQL the table also refuses updates and deletes.'}</p>
      <div className="grid g2" style={{ marginBottom: 14 }}>
        <div className="card"><h3>Chain</h3>{log.entries.length === 0 ? <p className="muted small" style={{ margin: 0 }}>No decisions yet.</p> :
          log.broken_at ? <p className="err" style={{ margin: 0 }}>Broken at entry {log.broken_at}.</p> : <p style={{ margin: 0 }}><span className="badge b-ok">intact</span> {log.entries.length} entries verified</p>}</div>
        <div className="card"><h3>Shift handover</h3>{hand.map((l, i) => <div key={i} className="small">{l}</div>)}</div>
      </div>
      <div className="card tablewrap"><table className="small"><thead><tr><th>#</th><th>When</th><th>Who</th><th>What</th><th>Decision</th><th>Reason</th><th>Hash</th></tr></thead>
        <tbody>{log.entries.map((e, i) => <tr key={e.hash}><td>{i + 1}</td><td className="mono">{e.at.replace('T', ' ').slice(0, 16)}</td><td>{e.actor}</td><td>{e.kind}: <span className="mono">{e.subject}</span></td><td>{e.decision}</td><td>{e.reason || <span className="muted">—</span>}</td><td className="mono muted">{e.hash.slice(0, 10)}…</td></tr>)}</tbody></table></div>
      {STATIC && <p className="small"><button onClick={() => { api.reset(); location.reload() }}>Reset this demo</button></p>}
    </>
  )
}
