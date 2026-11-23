"""The agent writes a shift note from the evidence; code checks it before anyone sees it.
Notes are cached in data/notes.json so the demo builds offline."""
import json, time
from pathlib import Path
from .plant import FAULTS
from .mapper import call

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "notes.json"
UNCERTAIN_BELOW = 0.6

PROMPT = """Deviation sizes are in standard deviations from normal operation, not sensor values.
You are the operations agent for a chemical plant. Write a short note for the shift team about one deviation.
Use only the evidence below. Do not invent signals, numbers or causes.

Evidence (JSON):
{evidence}

Rules:
- "signals": the ids of the signals you rely on, taken from evidence.signals.
- "matched_incident": the fault number of the past incident this matches, taken from evidence.library, or null if the best similarity is below {th}.
- "would_prove_wrong": one concrete observation that would show your conclusion is wrong.
- "next_check": one thing the shift should check first.
Answer with JSON only:
{{"summary": "2-3 sentences", "matched_incident": null, "unit": "process unit", "signals": [], "would_prove_wrong": "", "next_check": ""}}"""

def validate(note, ev):
    errs = []
    ids = {s["id"] for s in ev["signals"]}
    if not note.get("signals") or not set(note["signals"]) <= ids:
        errs.append(f"signals must be a non-empty subset of {sorted(ids)}")
    lib = ev["library"]
    allowed = {m["fault"] for m in lib}
    mi = note.get("matched_incident")
    if lib[0]["similarity"] < UNCERTAIN_BELOW:
        if mi is not None: errs.append(f"best similarity is {lib[0]['similarity']} < {UNCERTAIN_BELOW}: matched_incident must be null")
    elif mi not in allowed:
        errs.append(f"matched_incident must be one of {sorted(allowed)}")
    if mi in FAULTS and note.get("unit") != FAULTS[mi][1]:
        errs.append(f"unit must be '{FAULTS[mi][1]}' for incident {mi}")
    for k in ("summary", "would_prove_wrong", "next_check"):
        if not str(note.get(k, "")).strip(): errs.append(f"{k} is empty")
    return errs

def template(ev):
    top = ev["library"][0]
    known = FAULTS.get(top["fault"])
    s = ev["signals"][0]
    sure = top["similarity"] >= UNCERTAIN_BELOW
    return {"summary": f"{s['name']} moved first, {s['minutes_after_fault_start']} min after the fault started. "
                       + (f"The pattern matches past incident {top['fault']} (similarity {top['similarity']})." if sure else "No past incident matches well."),
            "matched_incident": top["fault"] if sure else None,
            "unit": known[1] if (sure and known) else ev["units"][0]["area"],
            "signals": [x["id"] for x in ev["signals"][:3]],
            "would_prove_wrong": "The first-moving signals return to normal while the others keep drifting.",
            "next_check": f"Check the instruments and equipment around {ev['units'][0]['area']}.",
            "source": "template"}

def write_note(ev):
    prompt = PROMPT.format(evidence=json.dumps(ev, indent=1), th=UNCERTAIN_BELOW)
    for attempt in range(2):
        note = call(prompt)
        errs = validate(note, ev)
        if not errs:
            note["source"] = "model"; note["checks"] = "passed" if attempt == 0 else "passed after one correction"
            return note
        prompt += "\n\nYour last answer was rejected: " + "; ".join(errs) + ". Fix it."
    t = template(ev); t["checks"] = "model failed twice: " + "; ".join(errs)
    return t

def notes_for(evidences, refresh=False):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for key, ev in evidences.items():
        if key in cache and not refresh: continue
        cache[key] = write_note(ev)
        CACHE.write_text(json.dumps(cache, indent=1))
        time.sleep(8)  # stay under the free tier's tokens per minute
    return cache
