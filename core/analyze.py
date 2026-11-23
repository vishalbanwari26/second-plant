"""Detect a deviation in each fault run and trace it to the process unit that moved first.
Plain Python, no dependencies. Writes docs/runs.json."""
import json, math, sys
from pathlib import Path
from .plant import SIGNALS, FAULTS

ROOT = Path(__file__).resolve().parents[1]
FAULT_START = 160          # the disturbance is switched on after 8 hours (3-minute samples)
MIN_PER_SAMPLE = 3

def load(name, transpose=False):
    rows = [[float(x) for x in line.split()] for line in open(ROOT / "data" / name) if line.strip()]
    return [list(c) for c in zip(*rows)] if transpose else rows

def normal_stats(rows):
    cols = list(zip(*rows))
    out = []
    for c in cols:
        m = sum(c) / len(c)
        s = math.sqrt(sum((x - m) ** 2 for x in c) / (len(c) - 1))
        out.append((m, s))
    return out

def onset(series, mean, std, start, k, hold):
    """First sample at or after `start` where |z| > k for `hold` samples in a row."""
    if std == 0: return None
    run = 0
    for t in range(start, len(series)):
        run = run + 1 if abs((series[t] - mean) / std) > k else 0
        if run == hold: return t - hold + 1
    return None

def rank_units(onsets):
    """A unit's time is the earliest onset of any of its signals; ties go to the bigger deviation."""
    best = {}
    for o in onsets:
        a = o["area"]
        key = (o["onset"], -o["peak"])
        if a not in best or key < best[a][0]: best[a] = (key, o["id"])
    return [{"area": a, "onset": k[0], "first_signal": sid} for a, (k, sid) in sorted(best.items(), key=lambda kv: kv[1][0])]

def analyze(rows, stats, k, hold, start=FAULT_START):
    cols = list(zip(*rows))
    onsets = []
    for j, sig in enumerate(SIGNALS):
        m, s = stats[j]
        t = onset(cols[j], m, s, start, k, hold)
        if t is None: continue
        z = [(x - m) / s for x in cols[j][start:]]
        peak = max(z, key=abs)
        onsets.append({"id": sig["id"], "name": sig["name"], "area": sig["area"], "sampled": sig["sampled"],
                       "onset": t, "minutes_after_start": (t - start) * MIN_PER_SAMPLE,
                       "peak": round(abs(peak), 1), "direction": "up" if peak > 0 else "down"})
    onsets.sort(key=lambda o: (o["onset"], -o["peak"]))
    return onsets

def main(k=6.0, hold=4):
    stats = normal_stats(load("d00.dat", transpose=True))
    # false alarms on the clean test run, counted from the same start
    clean = analyze(load("d00_te.dat"), stats, k, hold)
    runs = []
    for f in range(1, 22):
        rows = load(f"d{f:02d}_te.dat")
        early = analyze(rows, stats, k, hold, start=0)
        pre = [o for o in early if o["onset"] < FAULT_START]
        on = analyze(rows, stats, k, hold)
        units = rank_units(on)
        truth = FAULTS.get(f)
        runs.append({"fault": f, "cause": truth[0] if truth else None, "true_area": truth[1] if truth else None,
                     "detected": bool(on), "detect_minutes": on[0]["minutes_after_start"] if on else None,
                     "signals": on[:8], "units": units, "alarms_before_fault": len(pre)})
    known = [r for r in runs if r["true_area"]]
    det = [r for r in known if r["detected"]]
    top1 = [r for r in det if r["units"][0]["area"] == r["true_area"]]
    top2 = [r for r in det if r["true_area"] in [u["area"] for u in r["units"][:2]]]
    summary = {"k": k, "hold": hold, "clean_run_alarms": len(clean),
               "known_faults": len(known), "detected": len(det), "top1": len(top1), "top2": len(top2)}
    return runs, summary, stats

if __name__ == "__main__":
    k = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    hold = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    runs, summary, _ = main(k, hold)
    print(summary)
    for r in runs:
        u = [x["area"] for x in r["units"][:3]]
        print(f'{r["fault"]:2d} det={r["detected"]!s:5} t={r["detect_minutes"]} pre={r["alarms_before_fault"]} true={r["true_area"]} | {u}')
