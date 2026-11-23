import type { Series } from './types'

const COLORS = ['var(--accent)', 'var(--accent2)', 'var(--warn)', '#b483ff']

export function Chart({ series, names }: { series: Series; names: Record<string, string> }) {
  const W = 760, H = 240, P = { l: 40, r: 10, t: 12, b: 26 }
  const n = series.signals[0]?.z.length ?? 0
  const all = series.signals.flatMap(s => s.z)
  const lim = Math.min(40, Math.max(8, ...all.map(Math.abs)))
  const x = (i: number) => P.l + (i / Math.max(1, n - 1)) * (W - P.l - P.r)
  const y = (v: number) => P.t + (1 - (Math.max(-lim, Math.min(lim, v)) + lim) / (2 * lim)) * (H - P.t - P.b)
  const hours = (i: number) => ((i - series.fault_start) * series.minutes_per_sample) / 60
  const ticks = [] as number[]
  for (let h = Math.ceil(hours(0)); h <= hours(n - 1); h += 2) ticks.push(series.fault_start + (h * 60) / series.minutes_per_sample)
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Signals in standard deviations from normal, around the fault start">
        <rect x={P.l} y={y(6)} width={W - P.l - P.r} height={y(-6) - y(6)} fill="var(--chip)" />
        {[-lim, 0, lim].map(v => <g key={v}><line x1={P.l} x2={W - P.r} y1={y(v)} y2={y(v)} stroke="var(--line)" /><text x={P.l - 6} y={y(v) + 4} fontSize="10" textAnchor="end" fill="var(--muted)">{v.toFixed(0)}σ</text></g>)}
        <line x1={x(series.fault_start)} x2={x(series.fault_start)} y1={P.t} y2={H - P.b} stroke="var(--bad)" strokeDasharray="4 3" />
        <text x={x(series.fault_start) + 4} y={P.t + 10} fontSize="10" fill="var(--bad)">fault starts</text>
        {ticks.map(t => <text key={t} x={x(t)} y={H - 8} fontSize="10" textAnchor="middle" fill="var(--muted)">{hours(t) >= 0 ? '+' : ''}{hours(t).toFixed(0)} h</text>)}
        {series.signals.map((s, k) => <polyline key={s.id} fill="none" stroke={COLORS[k % 4]} strokeWidth="1.6" points={s.z.map((v, i) => `${x(i)},${y(v)}`).join(' ')} />)}
      </svg>
      <div className="row small" style={{ marginTop: 6 }}>
        <span className="muted">Shaded band: ±6σ, the alarm limit.</span>
        {series.signals.map((s, k) => <span key={s.id}><i style={{ display: 'inline-block', width: 10, height: 3, background: COLORS[k % 4], verticalAlign: 'middle', marginRight: 5 }} />{names[s.id] ?? s.id}</span>)}
      </div>
    </div>
  )
}
