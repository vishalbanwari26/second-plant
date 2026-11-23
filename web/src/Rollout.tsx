import { useEffect, useMemo, useState } from 'react'
import { api, STATIC } from './data'
import type { MappingItem, RolloutScore, Signal, Summary } from './types'

const LABEL: Record<string, string> = { ok: 'name and data agree', remap: 'data disagrees', unit: 'unit label wrong', frozen: 'stuck transmitter', unknown: 'no fit' }
const CONVS = ['none', 'degF_to_degC', 'bar_to_kPa', 't/h_to_kg/h']

function Row({ m, sig, actor, onDone }: { m: MappingItem; sig: Record<string, Signal>; actor: string; onDone: () => void }) {
  const [reason, setReason] = useState(''); const [err, setErr] = useState(''); const [ov, setOv] = useState(false)
  const [signal, setSignal] = useState(m.suggested_signal ?? ''); const [conv, setConv] = useState(m.suggested_conversion ?? 'none')
  const go = async (decision: string) => {
    setErr('')
    try { await api.decideMapping(m, { decision, actor, reason, signal, conversion: conv }); onDone() } catch (e) { setErr((e as Error).message) }
  }
  const name = (id: string | null) => (id ? `${id} ${sig[id]?.name ?? ''}` : '—')
  return (
    <tr>
      <td className="mono">{m.tag}<div className="muted small">{m.description} · {m.unit_label}</div></td>
      <td className="small">{name(m.proposed_signal)}{m.proposed_conversion && m.proposed_conversion !== 'none' ? <div className="muted">{m.proposed_conversion}</div> : null}</td>
      <td className="small">{name(m.suggested_signal)}{m.suggested_conversion && m.suggested_conversion !== 'none' ? <div className="muted">{m.suggested_conversion}</div> : null}</td>
      <td><span className={`badge b-${m.status}`}>{m.status === 'remap' && !m.proposed_signal ? 'no proposal' : LABEL[m.status]}</span><div className="small muted" style={{ marginTop: 4, maxWidth: 360 }}>{m.reason}</div></td>
      <td style={{ minWidth: 250 }}>
        {m.decision ? <span className="badge b-done">{m.decision} by {m.decided_by}</span> : (
          <div className="grid" style={{ gap: 6 }}>
            <div className="row">
              <button className="primary" disabled={!m.suggested_signal} onClick={() => go('accept')}>Accept</button>
              <button onClick={() => setOv(!ov)}>Override</button>
              <button onClick={() => go('hold')}>Hold</button>
            </div>
            {ov && <div className="row">
              <select value={signal} onChange={e => setSignal(e.target.value)}>{Object.values(sig).map(s => <option key={s.id} value={s.id}>{s.id} {s.name}</option>)}</select>
              <select value={conv} onChange={e => setConv(e.target.value)}>{CONVS.map(c => <option key={c}>{c}</option>)}</select>
              <button onClick={() => go('override')}>Save override</button></div>}
            {m.status !== 'ok' && <input className="reason" placeholder="Reason (needed to override or hold)" value={reason} onChange={e => setReason(e.target.value)} />}
            {err && <div className="err">{err}</div>}
          </div>)}
      </td>
    </tr>
  )
}

export function Rollout({ actor, summary }: { actor: string; summary: Summary }) {
  const [items, setItems] = useState<MappingItem[]>([]); const [sig, setSig] = useState<Record<string, Signal>>({})
  const [filter, setFilter] = useState('flagged'); const [score, setScore] = useState<RolloutScore | null>(null); const [busy, setBusy] = useState(false)
  const load = () => api.rollout().then(setItems)
  useEffect(() => { load(); api.signals().then(s => setSig(Object.fromEntries(s.map(x => [x.id, x])))) }, [])
  const shown = useMemo(() => items.filter(i => filter === 'all' || (filter === 'flagged' ? i.status !== 'ok' : i.status === 'ok')), [items, filter])
  const open = items.filter(i => !i.decision)
  const okOpen = open.filter(i => i.status === 'ok')
  const acceptAgreeing = async () => { for (const m of okOpen) await api.decideMapping(m, { decision: 'accept', actor, reason: '' }); load() }
  const run = async () => { setBusy(true); try { setScore(await api.evaluate()) } finally { setBusy(false) } }
  const all = open.length === 0
  return (
    <>
      <h1>Rollout to plant B</h1>
      <p className="lead">Plant B handed over {items.length} tags with names, descriptions and unit labels. A model proposed where each one goes in plant A's model.
        The data checks below compare every tag's behaviour with plant A's normal band. Lines where name and data agree can be accepted together; every flagged line needs a person.</p>
      <div className="row" style={{ marginBottom: 12 }}>
        <div className="filter">{[['flagged', `Flagged (${items.filter(i => i.status !== 'ok').length})`], ['ok', `Agree (${items.filter(i => i.status === 'ok').length})`], ['all', 'All']].map(([k, l]) =>
          <button key={k} className={filter === k ? 'on' : ''} onClick={() => setFilter(k)}>{l}</button>)}</div>
        <div className="right">
          <button disabled={!okOpen.length} onClick={acceptAgreeing}>Accept {okOpen.length} agreeing lines</button>
          <span className="small muted">{open.length} lines open</span>
        </div>
      </div>
      <div className="card tablewrap"><table>
        <thead><tr><th>Plant B tag</th><th>Model proposed (names)</th><th>Data says</th><th>Check</th><th>Decision</th></tr></thead>
        <tbody>{shown.map(m => <Row key={m.tag} m={m} sig={sig} actor={actor} onDone={load} />)}</tbody>
      </table></div>
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Run plant A's agent on plant B</h2>
        {STATIC ? (
          <p className="small">{all ? 'All lines decided. ' : `${open.length} lines are still open. `}In the live app this replays plant B's 21 fault runs through your decided mapping. Results computed for this demo:
            with the model's mapping used blindly, <b>{summary.rollout.blind.runs_with_false_alarm_before_fault} of 21</b> runs alarm before any fault and <b>{summary.rollout.blind.named_right}</b> faults are named right;
            with every suggestion accepted and the stuck transmitter held, <b>{summary.rollout.approved.runs_with_false_alarm_before_fault}</b> false alarms and <b>{summary.rollout.approved.named_right} of {summary.rollout.approved.named_total}</b> named right.</p>
        ) : (
          <div className="row"><button className="primary" disabled={busy} onClick={run}>{busy ? 'Replaying 21 runs…' : 'Replay plant B through the decided mapping'}</button>
            {score && <span>{score.signals_fed} signals fed · <b>{score.runs_with_false_alarm_before_fault}</b> of 21 runs alarm before the fault · <b>{score.named_right} of {score.named_total}</b> faults named right</span>}</div>
        )}
      </div>
    </>
  )
}
