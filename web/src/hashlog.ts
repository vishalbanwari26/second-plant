// Same hash chain as core/hashlog.py: sha256(prev_hash + "|" + canonical JSON of the entry body).
import type { LogEntry } from './types'
export const GENESIS = '0'.repeat(64)

function canonical(v: unknown): string {
  if (v === null || typeof v !== 'object') return JSON.stringify(v)
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']'
  const o = v as Record<string, unknown>
  return '{' + Object.keys(o).sort().map(k => JSON.stringify(k) + ':' + canonical(o[k])).join(',') + '}'
}

async function sha256(s: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('')
}

export async function entryHash(prev: string, e: Omit<LogEntry, 'prev_hash' | 'hash'>) {
  const { at, actor, kind, subject, decision, reason, payload } = e
  return sha256(prev + '|' + canonical({ at, actor, kind, subject, decision, reason, payload }))
}

export async function verify(entries: LogEntry[]): Promise<number | null> {
  let prev = GENESIS
  for (let i = 0; i < entries.length; i++) {
    const e = entries[i]
    if (e.prev_hash !== prev || e.hash !== (await entryHash(prev, e))) return i + 1
    prev = e.hash
  }
  return null
}
