"""Build the evidence for every run at plant A: detection, first movers, unit ranking, library matches."""
from .analyze import load, normal_stats, analyze, rank_units, FAULT_START, MIN_PER_SAMPLE
from .library import signature, match
from .rollout import library, WIN
from .plant import FAULTS, SIGNALS

def evidence_all():
    a_stats = normal_stats(load("d00.dat", transpose=True)); lib = library(a_stats)
    out = {}
    for f in range(1, 22):
        rows = load(f"d{f:02d}_te.dat")
        on = analyze(rows, a_stats, 6.0, 4)
        ev = {"run": f"run-{f:02d}", "detected": bool(on)}
        if on:
            st = on[0]["onset"]
            end = min(st + WIN, len(rows))
            m = match(signature(rows, a_stats, st, end - st), lib)
            for x in m:
                k = FAULTS.get(x["fault"])
                x["cause"] = k[0] if k else "cause not recorded"; x["unit"] = k[1] if k else None
            ev.update(detected_minutes_after_fault=on[0]["minutes_after_start"],
                      signals=[{"id": o["id"], "name": o["name"], "area": o["area"], "direction": o["direction"],
                               "minutes_after_fault_start": o["minutes_after_start"], "max_deviation_in_std": o["peak"]} for o in on[:6]],
                      units=rank_units(on)[:3], library=m, window_hours=round((end - st) * MIN_PER_SAMPLE / 60, 1))
        out[f] = ev
    return out, a_stats
