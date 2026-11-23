"""Check a proposed tag mapping against how the signals actually behave, and suggest fixes.
Uses plant B's normal run and plant A's normal statistics. Nothing is applied without approval."""
import math
from .analyze import load, normal_stats
from .plant import SIGNALS
from .plant_b import to_plant_b, tag_list

CONV = {"none": lambda v: v, "degF_to_degC": lambda v: (v - 32) * 5 / 9,
        "bar_to_kPa": lambda v: v * 100.0, "t/h_to_kg/h": lambda v: v * 1000.0}
IDS = [s["id"] for s in SIGNALS]
SIG_NAME = {s["id"]: s["name"] for s in SIGNALS}

def col_stats(vals):
    m = sum(vals) / len(vals)
    s = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
    return m, s

def fit(vals, conv, a_mean, a_std):
    """How well converted values sit in plant A's normal band: |mean shift| in std units, and spread ratio."""
    if a_std == 0: return float("inf"), 0
    m, s = col_stats([CONV[conv](v) for v in vals])
    return abs(m - a_mean) / a_std, (s / a_std if a_std else 0)

def ok(shift, ratio): return shift < 4 and 0.4 < ratio < 2.5

def best_fits(vals, a_stats, top=1):
    cands = []
    for j, sid in enumerate(IDS):
        am, asd = a_stats[j]
        if asd == 0: continue
        for c in CONV:
            sh, r = fit(vals, c, am, asd)
            if ok(sh, r): cands.append((sh + abs(math.log(max(r, 1e-9))), sid, c))
    return sorted(cands)[:top]

def review(proposal):
    """Assign every plant B tag to one plant A signal using the data, with the model's proposal as a
    tie-breaker, then explain each line. Each plant A signal is used once."""
    a_stats = normal_stats(load("d00.dat", transpose=True))
    b_rows = to_plant_b(load("d00_te.dat"))
    tags = {t["tag"]: t for t in tag_list()}
    prop = {m["tag"]: m for m in proposal["mapping"]}
    cols = {tag: [r[tag] for r in b_rows] for tag in tags}
    frozen = {tag for tag, v in cols.items() if col_stats(v)[1] == 0}
    cands = []
    for tag, vals in cols.items():
        if tag in frozen: continue
        p = prop.get(tag)
        for j, sid in enumerate(IDS):
            am, asd = a_stats[j]
            if asd == 0: continue
            for c in CONV:
                sh, r = fit(vals, c, am, asd)
                if not ok(sh, r): continue
                cost = sh + abs(math.log(max(r, 1e-9)))
                if p and p.get("signal") == sid: cost -= 2.0      # trust the names when the data agrees
                cands.append((cost, tag, sid, c, sh, r))
    cands.sort()
    assigned, used = {}, set()
    for cost, tag, sid, c, sh, r in cands:
        if tag in assigned or sid in used: continue
        assigned[tag] = (sid, c, sh, r); used.add(sid)
    items = []
    for tag, meta in tags.items():
        p = prop.get(tag) or {}
        item = {"tag": tag, "description": meta["description"], "unit": meta["unit"],
                "proposed": p.get("signal"), "conversion": p.get("conversion"), "confidence": p.get("confidence")}
        if tag in frozen:
            item.update(status="frozen", suggested=None, suggested_conversion=None,
                        reason="The value never changes in the normal run. The transmitter looks stuck; keep it away from the agent until it is repaired.")
        elif tag not in assigned:
            item.update(status="unknown", suggested=None, suggested_conversion=None,
                        reason="No plant A signal fits this data. A person has to look at it.")
        else:
            sid, c, sh, r = assigned[tag]
            item.update(suggested=sid, suggested_conversion=c)
            if sid == item["proposed"] and c == item["conversion"]:
                item.update(status="ok", reason=f"Name and data agree: converted values sit in plant A's normal band (shift {sh:.1f} std, spread x{r:.2f}).")
            elif sid == item["proposed"]:
                item.update(status="unit", reason=f"Right signal, but the data fits only with '{c}', not '{item['conversion']}'. The unit label is wrong.")
            elif item["proposed"] is None:
                item.update(status="remap", reason=f"The model left it open. The data behaves like {sid} ({SIG_NAME[sid]}).")
            else:
                item.update(status="remap", reason=f"Named like {item['proposed']} ({SIG_NAME[item['proposed']]}), but the data behaves like {sid} ({SIG_NAME[sid]}).")
        items.append(item)
    return items

def data_truth():
    from .plant_b import truth, TAGS, SWAPPED
    t = truth()
    a, b = TAGS[SWAPPED[0]][0], TAGS[SWAPPED[1]][0]
    t[a], t[b] = t[b], t[a]
    return t

if __name__ == "__main__":
    from collections import Counter
    from .mapper import propose
    items = review(propose())
    t = data_truth()
    print(Counter(i["status"] for i in items))
    blind = sum(1 for i in items if i["proposed"] == t[i["tag"]])
    checked = sum(1 for i in items if i["suggested"] == t[i["tag"]])
    print(f"blind: {blind}/52 right; checked: {checked}/51 usable right (+1 frozen held back)")
    for i in items:
        if i["status"] != "ok" or i["suggested"] != t[i["tag"]]:
            flag = "" if i["suggested"] == t[i["tag"]] else "  <-- STILL WRONG"
            print(i["status"], i["tag"], "|", i["proposed"], "->", i["suggested"], i["suggested_conversion"], "| data truth", t[i["tag"]], i.get("note",""), flag)
