"""Chart data for an incident: the first-moving signals around the fault, in std units from normal."""
from .analyze import load, FAULT_START
from .plant import SIGNALS

IDS = [s["id"] for s in SIGNALS]

def series(run, ids, a_stats, before=40, after=240):
    rows = load(f"d{run:02d}_te.dat")
    lo, hi = max(0, FAULT_START - before), min(len(rows), FAULT_START + after)
    out = {"fault_start": FAULT_START - lo, "minutes_per_sample": 3, "signals": []}
    for sid in ids:
        j = IDS.index(sid); m, s = a_stats[j]
        out["signals"].append({"id": sid, "z": [round((rows[t][j] - m) / s, 2) for t in range(lo, hi)]})
    return out
