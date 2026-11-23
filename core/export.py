"""Write the read-only data the static demo needs (no API, no database) to web/public/data."""
import json
from pathlib import Path
from .plant import SIGNALS
from .plant_b import tag_list
from .checks import review
from .mapper import propose
from .incidents import evidence_all
from .series import series

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "public" / "data"

def main():
    (OUT / "incidents").mkdir(parents=True, exist_ok=True)
    w = lambda name, obj: (OUT / f"{name}.json").write_text(json.dumps(obj, separators=(",", ":")))
    w("summary", json.loads((ROOT / "data" / "results.json").read_text()))
    w("signals", [{"id": s["id"], "name": s["name"], "unit": s["unit"], "area": s["area"]} for s in SIGNALS])
    tags = {t["tag"]: t for t in tag_list()}
    items = review(propose())
    rows = [{"tag": i["tag"], "description": tags[i["tag"]]["description"], "unit_label": tags[i["tag"]]["unit"],
             "proposed_signal": i["proposed"], "proposed_conversion": i["conversion"], "confidence": i["confidence"],
             "status": i["status"], "suggested_signal": i["suggested"], "suggested_conversion": i["suggested_conversion"],
             "reason": i["reason"], "note": i.get("note")} for i in items]
    PRI = {"frozen": 0, "unit": 1, "unknown": 2, "remap": 3, "ok": 5}
    rows.sort(key=lambda r: (PRI[r["status"]] + (1 if r["status"] == "remap" and not r["proposed_signal"] else 0), r["tag"]))
    w("rollout", rows)
    ev, a_stats = evidence_all()
    notes = json.loads((ROOT / "data" / "notes.json").read_text())
    lst = []
    for f, e in ev.items():
        if not e["detected"]: continue
        n = notes.get(str(f))
        inc = {"id": e["run"], "fault": f, "state": "open", "decision": None, "evidence": e, "note": n,
               "series": series(f, [s["id"] for s in e["signals"][:4]], a_stats)}
        w(f"incidents/{e['run']}", inc)
        lst.append({"id": e["run"], "fault": f, "state": "open", "decision": None, "detected_after": e["detected_minutes_after_fault"],
                    "unit": n.get("unit") if n else None, "summary": n.get("summary") if n else None})
    w("incidents", lst)
    print("exported", len(rows), "tags,", len(lst), "incidents")

if __name__ == "__main__":
    main()
