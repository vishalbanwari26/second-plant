"""second-plant API: the rollout review, incidents, decisions and the decision log."""
import json, os
from datetime import datetime, timezone
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.hashlog import GENESIS, entry_hash, verify
from core.handover import handover
from core.checks import CONV, review
from core.mapper import propose
from core.rollout import evaluate, library
from core.analyze import load, normal_stats

ROOT = Path(__file__).resolve().parents[1]
DB = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5435/secondplant")
app = FastAPI(title="second-plant")

def conn(): return psycopg.connect(DB, row_factory=dict_row)

class MappingDecision(BaseModel):
    decision: str = Field(pattern="^(accept|override|hold)$")
    actor: str = Field(min_length=2)
    reason: str = ""
    signal: str | None = None
    conversion: str | None = None

class IncidentDecision(BaseModel):
    decision: str = Field(pattern="^(accept|override|defer)$")
    actor: str = Field(min_length=2)
    reason: str = ""

def append_log(c, actor, kind, subject, decision, reason, payload):
    prev = c.execute("SELECT hash FROM decision_log ORDER BY seq DESC LIMIT 1").fetchone()
    e = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "actor": actor, "kind": kind,
         "subject": subject, "decision": decision, "reason": reason, "payload": payload}
    e["prev_hash"] = prev["hash"] if prev else GENESIS
    e["hash"] = entry_hash(e["prev_hash"], e)
    c.execute("""INSERT INTO decision_log (at, actor, kind, subject, decision, reason, payload, prev_hash, hash)
                 VALUES (%(at)s, %(actor)s, %(kind)s, %(subject)s, %(decision)s, %(reason)s, %(payload)s, %(prev_hash)s, %(hash)s)""",
              {**e, "payload": Json(payload)})
    return e

@app.get("/api/summary")
def summary():
    return json.loads((ROOT / "data" / "results.json").read_text())

@app.get("/api/signals")
def signals():
    with conn() as c: return c.execute("SELECT id, name, unit, area FROM signals WHERE plant_id='A' ORDER BY id").fetchall()

@app.get("/api/rollout")
def rollout_items():
    with conn() as c:
        return c.execute("""SELECT m.*, t.description, t.unit_label FROM mappings m JOIN plant_tags t USING (plant_id, tag)
                            WHERE m.plant_id='B' ORDER BY CASE m.status WHEN 'frozen' THEN 0 WHEN 'unit' THEN 1 WHEN 'unknown' THEN 2 WHEN 'remap' THEN CASE WHEN m.proposed_signal IS NULL THEN 4 ELSE 3 END ELSE 5 END, m.tag""").fetchall()

@app.post("/api/rollout/{tag}/decide")
def decide_mapping(tag: str, d: MappingDecision):
    if d.decision in ("override", "hold") and len(d.reason.strip()) < 10:
        raise HTTPException(400, "Overriding or holding a line needs a reason of at least 10 characters.")
    with conn() as c:
        m = c.execute("SELECT * FROM mappings WHERE plant_id='B' AND tag=%s", (tag,)).fetchone()
        if not m: raise HTTPException(404, "unknown tag")
        if d.decision == "accept":
            if not m["suggested_signal"]: raise HTTPException(400, "Nothing to accept for this tag; hold it or override it.")
            sig, conv = m["suggested_signal"], m["suggested_conversion"]
        elif d.decision == "override":
            if not d.signal or d.conversion not in CONV: raise HTTPException(400, "An override needs a signal and a known conversion.")
            sig, conv = d.signal, d.conversion
        else:
            sig, conv = None, None
        c.execute("""UPDATE mappings SET decision=%s, final_signal=%s, final_conversion=%s, decided_by=%s, decision_reason=%s, decided_at=now()
                     WHERE plant_id='B' AND tag=%s""", (d.decision, sig, conv, d.actor, d.reason, tag))
        return append_log(c, d.actor, "mapping", tag, d.decision, d.reason, {"signal": sig, "conversion": conv, "status": m["status"]})

@app.post("/api/rollout/evaluate")
def evaluate_rollout():
    """Run the agent learned at plant A on plant B through the mapping as decided so far."""
    with conn() as c:
        rows = c.execute("SELECT tag, final_signal, final_conversion FROM mappings WHERE plant_id='B' AND decision IN ('accept','override')").fetchall()
    mapping = [{"tag": r["tag"], "signal": r["final_signal"], "conversion": r["final_conversion"]} for r in rows]
    a_stats = normal_stats(load("d00.dat", transpose=True))
    r = evaluate(mapping, a_stats, library(a_stats))
    return {k: r[k] for k in ("signals_fed", "runs_with_false_alarm_before_fault", "named_right", "named_total")}

@app.get("/api/incidents")
def incidents():
    with conn() as c:
        return c.execute("SELECT id, fault, state, decision, evidence->'detected_minutes_after_fault' AS detected_after, note->>'unit' AS unit, note->>'summary' AS summary FROM incidents ORDER BY fault").fetchall()

@app.get("/api/incidents/{iid}")
def incident(iid: str):
    with conn() as c:
        r = c.execute("SELECT * FROM incidents WHERE id=%s", (iid,)).fetchone()
        if not r: raise HTTPException(404, "unknown incident")
        return r

@app.post("/api/incidents/{iid}/decide")
def decide_incident(iid: str, d: IncidentDecision):
    if d.decision in ("override", "defer") and len(d.reason.strip()) < 10:
        raise HTTPException(400, "Overriding or deferring needs a reason of at least 10 characters.")
    with conn() as c:
        r = c.execute("SELECT note FROM incidents WHERE id=%s", (iid,)).fetchone()
        if not r: raise HTTPException(404, "unknown incident")
        state = "open" if d.decision == "defer" else "closed"
        c.execute("UPDATE incidents SET state=%s, decision=%s, decided_by=%s, decision_reason=%s WHERE id=%s", (state, d.decision, d.actor, d.reason, iid))
        n = r["note"] or {}
        return append_log(c, d.actor, "incident", iid, d.decision, d.reason, {"matched_incident": n.get("matched_incident"), "unit": n.get("unit")})

@app.get("/api/log")
def log():
    with conn() as c:
        rows = c.execute("SELECT at, actor, kind, subject, decision, reason, payload, prev_hash, hash FROM decision_log ORDER BY seq").fetchall()
    return {"entries": rows, "broken_at": verify(rows)}

@app.get("/api/handover")
def shift_handover():
    with conn() as c:
        inc = c.execute("SELECT id, state, note FROM incidents ORDER BY fault").fetchall()
        lg = c.execute("SELECT kind, subject, decision, actor, reason FROM decision_log ORDER BY seq").fetchall()
    return {"lines": handover(inc, lg)}
