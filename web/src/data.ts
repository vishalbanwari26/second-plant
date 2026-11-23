// One data layer, two backends: the live API (Docker) or static JSON with decisions kept in this browser.
import type { Incident, IncidentRow, LogEntry, MappingItem, RolloutScore, Signal, Summary } from './types'
import { entryHash, GENESIS, verify } from './hashlog'

export const STATIC = import.meta.env.VITE_STATIC === '1'
const base = import.meta.env.BASE_URL
const KEY = 'second-plant:v1'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(STATIC ? `${base}data/${path}.json` : `/api/${path}`)
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? r.statusText)
  return r.json()
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`/api/${path}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(j.detail ?? r.statusText)
  return j
}

interface Local { mappings: Record<string, Partial<MappingItem>>; incidents: Record<string, Partial<Incident>>; log: LogEntry[] }
function local(): Local {
  try { return JSON.parse(localStorage.getItem(KEY) ?? '') } catch { return { mappings: {}, incidents: {}, log: [] } }
}
function save(l: Local) { try { localStorage.setItem(KEY, JSON.stringify(l)) } catch { /* private mode */ } }
async function appendLocal(l: Local, e: Omit<LogEntry, 'prev_hash' | 'hash'>) {
  const prev = l.log.length ? l.log[l.log.length - 1].hash : GENESIS
  const full = { ...e, prev_hash: prev, hash: await entryHash(prev, e) }
  l.log.push(full); save(l); return full
}
function need(decision: string, reason: string) {
  if (decision !== 'accept' && reason.trim().length < 10) throw new Error('This decision needs a reason of at least 10 characters.')
}
const now = () => new Date().toISOString().slice(0, 19) + '+00:00'

export const api = {
  summary: () => get<Summary>('summary'),
  signals: () => get<Signal[]>('signals'),
  async rollout(): Promise<MappingItem[]> {
    const items = await get<MappingItem[]>('rollout')
    if (!STATIC) return items
    const l = local(); return items.map(i => ({ ...i, ...(l.mappings[i.tag] ?? {}) }))
  },
  async decideMapping(item: MappingItem, d: { decision: string; actor: string; reason: string; signal?: string; conversion?: string }) {
    if (!STATIC) return post<LogEntry>(`rollout/${item.tag}/decide`, d)
    need(d.decision, d.reason)
    const sig = d.decision === 'accept' ? item.suggested_signal : d.decision === 'override' ? d.signal ?? null : null
    const conv = d.decision === 'accept' ? item.suggested_conversion : d.decision === 'override' ? d.conversion ?? null : null
    if (d.decision === 'accept' && !sig) throw new Error('Nothing to accept for this tag; hold it or override it.')
    if (d.decision === 'override' && (!sig || !conv)) throw new Error('An override needs a signal and a conversion.')
    const l = local()
    l.mappings[item.tag] = { decision: d.decision, final_signal: sig, final_conversion: conv, decided_by: d.actor, decision_reason: d.reason }
    return appendLocal(l, { at: now(), actor: d.actor, kind: 'mapping', subject: item.tag, decision: d.decision, reason: d.reason, payload: { signal: sig, conversion: conv, status: item.status } })
  },
  async evaluate(): Promise<RolloutScore | null> {
    if (!STATIC) return post<RolloutScore>('rollout/evaluate', {})
    return null
  },
  async incidents(): Promise<IncidentRow[]> {
    const rows = await get<IncidentRow[]>('incidents')
    if (!STATIC) return rows
    const l = local(); return rows.map(r => ({ ...r, ...(l.incidents[r.id] ?? {}) }) as IncidentRow)
  },
  async incident(id: string): Promise<Incident> {
    const r = await get<Incident>(`incidents/${id}`)
    if (!STATIC) return r
    return { ...r, ...(local().incidents[id] ?? {}) }
  },
  async decideIncident(inc: Incident, d: { decision: string; actor: string; reason: string }) {
    if (!STATIC) return post<LogEntry>(`incidents/${inc.id}/decide`, d)
    need(d.decision, d.reason)
    const l = local()
    l.incidents[inc.id] = { state: d.decision === 'defer' ? 'open' : 'closed', decision: d.decision, decided_by: d.actor, decision_reason: d.reason }
    return appendLocal(l, { at: now(), actor: d.actor, kind: 'incident', subject: inc.id, decision: d.decision, reason: d.reason, payload: { matched_incident: inc.note?.matched_incident ?? null, unit: inc.note?.unit ?? null } })
  },
  async log(): Promise<{ entries: LogEntry[]; broken_at: number | null }> {
    if (!STATIC) return get('log')
    const entries = local().log; return { entries, broken_at: await verify(entries) }
  },
  async handover(): Promise<string[]> {
    if (!STATIC) return (await get<{ lines: string[] }>('handover')).lines
    const rows = await api.incidents(); const lg = local().log
    const open = rows.filter(r => r.state === 'open'); const decided = lg.filter(e => e.kind === 'incident')
    return [`${open.length} open deviation(s), ${decided.length} decided this shift.`,
      ...open.slice(0, 5).map(r => `OPEN ${r.id}: ${r.unit ?? '?'}.`),
      ...decided.slice(-5).map(e => `${e.decision.toUpperCase()} ${e.subject} by ${e.actor}: ${e.reason}`)]
  },
  reset() { try { localStorage.removeItem(KEY) } catch { /* ignore */ } },
}
