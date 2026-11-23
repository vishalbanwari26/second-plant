"""Load the plant model, plant B's tags, the checked mapping and the incidents into PostgreSQL."""
import json, os
from pathlib import Path
import psycopg
from psycopg.types.json import Json
from .plant import SIGNALS, FAULTS
from .plant_b import tag_list
from .checks import review
from .mapper import propose
from .incidents import evidence_all
from .series import series

ROOT = Path(__file__).resolve().parents[1]

def seed(url):
    ev, a_stats = evidence_all()
    notes = json.loads((ROOT / "data" / "notes.json").read_text())
    items = review(propose())
    with psycopg.connect(url) as c:
        c.execute((ROOT / "db" / "schema.sql").read_text())
        c.execute("TRUNCATE decision_log, incidents, mappings, plant_tags, signals, plants RESTART IDENTITY CASCADE")
        c.execute("INSERT INTO plants VALUES ('A', 'Plant A (learned)'), ('B', 'Plant B (rollout)')")
        for s, (m, sd) in zip(SIGNALS, a_stats):
            c.execute("INSERT INTO signals VALUES ('A', %s, %s, %s, %s, %s, %s, %s)", (s["id"], s["name"], s["unit"], s["area"], s["sampled"], m, sd))
        for t in tag_list():
            c.execute("INSERT INTO plant_tags VALUES ('B', %s, %s, %s)", (t["tag"], t["description"], t["unit"]))
        for i in items:
            c.execute("""INSERT INTO mappings (plant_id, tag, proposed_signal, proposed_conversion, confidence, status,
                         suggested_signal, suggested_conversion, reason, note) VALUES ('B', %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                      (i["tag"], i["proposed"], i["conversion"], i["confidence"], i["status"], i["suggested"], i["suggested_conversion"], i["reason"], i.get("note")))
        for f, e in ev.items():
            if not e["detected"]: continue
            ids = [s["id"] for s in e["signals"][:4]]
            c.execute("INSERT INTO incidents (id, plant_id, fault, evidence, note, series) VALUES (%s, 'A', %s, %s, %s, %s)",
                      (e["run"], f, Json(e), Json(notes.get(str(f))), Json(series(f, ids, a_stats))))
    return len(items)

if __name__ == "__main__":
    print("seeded", seed(os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5435/secondplant")))
