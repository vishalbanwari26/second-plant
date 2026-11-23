"""Every number the demo shows, computed from the data. Writes data/results.json."""
import json
from pathlib import Path
from .analyze import load, normal_stats, analyze
from .library import signature, match
from .rollout import library, evaluate, WIN
from .checks import review, data_truth
from .mapper import propose

ROOT = Path(__file__).resolve().parents[1]

def compute():
    a_stats = normal_stats(load("d00.dat", transpose=True)); lib = library(a_stats)
    clean = analyze(load("d00_te.dat"), a_stats, 6.0, 4, start=0)
    det, curve = {}, []
    for f in range(1, 22): det[f] = analyze(load(f"d{f:02d}_te.dat"), a_stats, 6.0, 4)
    for hours in (1, 2, 4, 8):
        win = hours * 20
        lib_w = {}
        for g in range(1, 22):
            r = load(f"d{g:02d}.dat"); on = analyze(r, a_stats, 6.0, 4, start=0)
            lib_w[g] = signature(r, a_stats, min(on[0]["onset"] if on else 0, len(r) - win), win)
        top1 = top3 = n = 0
        for f in range(1, 22):
            if not det[f]: continue
            rows = load(f"d{f:02d}_te.dat"); st = det[f][0]["onset"]
            if st + win > len(rows): continue
            m = match(signature(rows, a_stats, st, win), lib_w); n += 1
            top1 += m[0]["fault"] == f; top3 += f in [x["fault"] for x in m]
        curve.append({"hours_after_detection": hours, "top1": top1, "top3": top3, "runs": n})
    proposal = propose(); items = review(proposal); truth = data_truth()
    checked = [{"tag": i["tag"], "signal": i["suggested"], "conversion": i["suggested_conversion"]} for i in items if i["suggested"]]
    blind = evaluate(proposal["mapping"], a_stats, lib); approved = evaluate(checked, a_stats, lib)
    return {
        "plant_a": {"runs": 21, "detected": sum(1 for f in det if det[f]), "missed": [f for f in det if not det[f]],
                    "false_alarms_normal_run": len(clean), "cause_curve": curve,
                    "median_detection_minutes": sorted(d[0]["minutes_after_start"] for d in det.values() if d)[len([1 for d in det.values() if d]) // 2]},
        "mapping": {"tags": len(items), "model_right": sum(1 for i in items if i["proposed"] == truth[i["tag"]]),
                    "model_proposed": sum(1 for i in items if i["proposed"]),
                    "checked_right": sum(1 for i in items if i["suggested"] == truth[i["tag"]]),
                    "held_back": sum(1 for i in items if i["status"] == "frozen"),
                    "status_counts": {s: sum(1 for i in items if i["status"] == s) for s in sorted({i["status"] for i in items})},
                    "model": proposal.get("model")},
        "rollout": {"blind": {k: blind[k] for k in ("signals_fed", "runs_with_false_alarm_before_fault", "named_right", "named_total")},
                    "approved": {k: approved[k] for k in ("signals_fed", "runs_with_false_alarm_before_fault", "named_right", "named_total")}},
    }

if __name__ == "__main__":
    r = compute(); (ROOT / "data" / "results.json").write_text(json.dumps(r, indent=1)); print(json.dumps(r, indent=1))
