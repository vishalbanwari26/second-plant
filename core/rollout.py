"""Run the agent learned at plant A on plant B's data, through a tag mapping.
Compares the model's mapping used blindly with the mapping after data checks and approval."""
from .analyze import load, normal_stats, analyze, FAULT_START
from .library import signature, match
from .plant import SIGNALS
from .plant_b import to_plant_b
from .checks import CONV, review, data_truth

IDS = [s["id"] for s in SIGNALS]
WIN = 80   # 4 hours

def to_plant_a(b_rows, mapping, a_stats):
    """Rebuild plant A columns from plant B tags. A signal with no tag reads as its normal mean (no information)."""
    src = {}
    for m in mapping:
        if m.get("signal") in IDS and m.get("conversion") in CONV and m["signal"] not in src:
            src[m["signal"]] = (m["tag"], CONV[m["conversion"]])
    out = []
    for r in b_rows:
        row = []
        for j, sid in enumerate(IDS):
            if sid in src: tag, f = src[sid]; row.append(f(r[tag]))
            else: row.append(a_stats[j][0])
        out.append(row)
    return out, len(src)

def library(a_stats):
    lib = {}
    for f in range(1, 22):
        r = load(f"d{f:02d}.dat")
        on = analyze(r, a_stats, 6.0, 4, start=0)
        st = min(on[0]["onset"] if on else 0, len(r) - WIN)
        lib[f] = signature(r, a_stats, st, WIN)
    return lib

def evaluate(mapping, a_stats, lib):
    clean, n_src = to_plant_a(to_plant_b(load("d00_te.dat")), mapping, a_stats)
    false_alarms = analyze(clean, a_stats, 6.0, 4, start=0)
    res = {"signals_fed": n_src, "false_alarm_signals_normal_run": [o["id"] for o in false_alarms], "runs": []}
    top1 = n = 0
    for f in range(1, 22):
        rows, _ = to_plant_a(to_plant_b(load(f"d{f:02d}_te.dat")), mapping, a_stats)
        pre = analyze(rows, a_stats, 6.0, 4, start=0)
        alarm_before_fault = any(o["onset"] < FAULT_START for o in pre)
        on = analyze(rows, a_stats, 6.0, 4)
        named = None
        if on and on[0]["onset"] + WIN <= len(rows):
            named = match(signature(rows, a_stats, on[0]["onset"], WIN), lib)[0]["fault"]
            n += 1; top1 += named == f
        res["runs"].append({"fault": f, "alarm_before_fault": alarm_before_fault, "named": named})
    res["named_right"] = top1; res["named_total"] = n
    res["runs_with_false_alarm_before_fault"] = sum(r["alarm_before_fault"] for r in res["runs"])
    return res

if __name__ == "__main__":
    from .mapper import propose
    a_stats = normal_stats(load("d00.dat", transpose=True)); lib = library(a_stats)
    prop = propose()["mapping"]
    items = review(propose())
    checked = [{"tag": i["tag"], "signal": i["suggested"], "conversion": i["suggested_conversion"]} for i in items if i["suggested"]]
    t = data_truth()
    perfect = [{"tag": tag, "signal": sid, "conversion": next(c for c in CONV if True)} for tag, sid in t.items()]
    for name, m in [("blind model mapping", prop), ("checked + approved", checked)]:
        r = evaluate(m, a_stats, lib)
        print(name, "| fed", r["signals_fed"], "| false-alarm signals on normal run:", r["false_alarm_signals_normal_run"][:6],
              "| runs alarmed before the fault:", r["runs_with_false_alarm_before_fault"], "/21 | cause named right", r["named_right"], "/", r["named_total"])
    # reference: the agent at plant A itself
    ref = {"fault": None}
