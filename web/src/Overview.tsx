import type { Summary } from './types'

export function Overview({ s }: { s: Summary }) {
  const four = s.plant_a.cause_curve.find(c => c.hours_after_detection === 4)!
  const { blind, approved } = s.rollout
  return (
    <>
      <h1>Roll a plant agent out to the next plant, without breaking it</h1>
      <p className="lead">An agent learns plant A: how normal looks, and what past incidents looked like. Plant B runs the same process,
        but its tags have other names, some readings come in other units, and its data has problems a tag list does not show.
        A model proposes the tag mapping, data checks catch what the names hide, and an engineer approves each flagged line before the agent acts at plant B.
        Every decision goes into a hash-chained log.</p>
      <div className="grid g3">
        <div className="card kpi"><h3>Plant B, mapping used blindly</h3>
          <div className="vs"><b className="bad">{blind.runs_with_false_alarm_before_fault}/21</b><small>runs alarm before any fault</small></div>
          <small>Faults named right: {blind.named_right} of 21. The frozen transmitter and wrong units set the alarms off on the first sample.</small></div>
        <div className="card kpi"><h3>Plant B, after checks and approval</h3>
          <div className="vs"><b className="good">{approved.runs_with_false_alarm_before_fault}/21</b><small>false alarms</small></div>
          <small>Faults named right: {approved.named_right} of {approved.named_total} detected, against {four.top1} of {four.runs} at plant A itself.</small></div>
        <div className="card kpi"><h3>Tag mapping</h3>
          <div className="vs"><b>{s.mapping.model_right} → {s.mapping.checked_right}</b><small>of {s.mapping.tags} tags right</small></div>
          <small>Names alone ({s.mapping.model}), then data checks; {s.mapping.held_back} stuck transmitter held back.</small></div>
      </div>
      <div className="grid g2" style={{ marginTop: 14 }}>
        <div className="card"><h2>How it works</h2>
          <ol className="steps">
            <li><b>Learn plant A.</b> Normal bands from a clean run, and an incident library: one signature per past incident, from how each signal shifts and how much it swings.</li>
            <li><b>Detect and trace.</b> A signal alarms when it leaves ±6σ for four samples in a row. The signals that moved first point to the process unit, and the incident library names the likely cause.</li>
            <li><b>Explain, checked.</b> A model writes the shift note. Code rejects it if it cites a signal outside the evidence, names an incident outside the library's top three, or names one when the match is weak.</li>
            <li><b>Roll out.</b> A model maps plant B's tags from names and units. Every line is then checked against plant A's normal band; swapped columns, a stuck transmitter and a wrong unit label are flagged with what the data says instead.</li>
            <li><b>People decide.</b> Accept, override with a reason, or hold. Every decision is chained into a log that shows if anyone edits an old entry.</li>
          </ol></div>
        <div className="card"><h2>Plant A, the learned agent</h2>
          <p className="small">Tennessee Eastman process, the public benchmark for plant-wide faults: 52 signals across feeds, reactor, separator, stripper and recycle; 21 fault runs with known disturbances.</p>
          <table className="small"><tbody>
            <tr><td>Runs with a fault detected</td><td><b>{s.plant_a.detected} of {s.plant_a.runs}</b></td></tr>
            <tr><td>False alarms on the clean run</td><td><b>{s.plant_a.false_alarms_normal_run}</b></td></tr>
            <tr><td>Median time to detection</td><td><b>{s.plant_a.median_detection_minutes} min</b></td></tr>
            {s.plant_a.cause_curve.map(c => <tr key={c.hours_after_detection}><td>Exact incident named, {c.hours_after_detection} h after detection</td><td><b>{c.top1} of {c.runs}</b> (top 3: {c.top3})</td></tr>)}
            <tr><td>Not detected</td><td>faults {s.plant_a.missed.join(', ')}; 3, 9 and 15 are known in the literature to be nearly invisible in this data</td></tr>
          </tbody></table></div>
      </div>
      <div className="card" style={{ marginTop: 14 }}><h2>What this is not</h2>
        <p className="small muted" style={{ margin: 0 }}>Plant B is the same simulated process with names, units and three data problems changed on purpose, so every answer is known. A real second plant also differs in equipment, operating points and control tuning. The incident library has one example per incident. The thresholds were fixed before scoring; the accuracy at 1, 2, 4 and 8 hours is reported as a curve, not picked.</p></div>
    </>
  )
}
