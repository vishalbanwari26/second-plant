export type Status = 'ok' | 'remap' | 'unit' | 'frozen' | 'unknown'
export interface MappingItem {
  tag: string; description: string; unit_label: string
  proposed_signal: string | null; proposed_conversion: string | null; confidence: number | null
  status: Status; suggested_signal: string | null; suggested_conversion: string | null; reason: string; note?: string | null
  decision?: string | null; final_signal?: string | null; final_conversion?: string | null; decided_by?: string | null; decision_reason?: string | null
}
export interface Signal { id: string; name: string; unit: string; area: string }
export interface EvidenceSignal { id: string; name: string; area: string; direction: string; minutes_after_fault_start: number; max_deviation_in_std: number }
export interface LibraryMatch { fault: number; similarity: number; cause: string; unit: string | null }
export interface Evidence {
  run: string; detected: boolean; detected_minutes_after_fault: number; window_hours: number
  signals: EvidenceSignal[]; units: { area: string; onset: number; first_signal: string }[]; library: LibraryMatch[]
}
export interface Note { summary: string; matched_incident: number | null; unit: string; signals: string[]; would_prove_wrong: string; next_check: string; source: string; checks: string }
export interface Series { fault_start: number; minutes_per_sample: number; signals: { id: string; z: number[] }[] }
export interface Incident { id: string; fault: number; state: string; decision: string | null; decided_by?: string | null; decision_reason?: string | null; evidence: Evidence; note: Note | null; series: Series }
export interface IncidentRow { id: string; fault: number; state: string; decision: string | null; detected_after: number; unit: string | null; summary: string | null }
export interface LogEntry { at: string; actor: string; kind: string; subject: string; decision: string; reason: string; payload: Record<string, unknown>; prev_hash: string; hash: string }
export interface RolloutScore { signals_fed: number; runs_with_false_alarm_before_fault: number; named_right: number; named_total: number }
export interface Summary {
  plant_a: { runs: number; detected: number; missed: number[]; false_alarms_normal_run: number; median_detection_minutes: number
    cause_curve: { hours_after_detection: number; top1: number; top3: number; runs: number }[] }
  mapping: { tags: number; model_right: number; model_proposed: number; checked_right: number; held_back: number; status_counts: Record<string, number>; model: string }
  rollout: { blind: RolloutScore; approved: RolloutScore }
}
