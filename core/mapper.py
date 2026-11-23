"""Ask a model to map plant B's tags onto plant A's model, from tag names, descriptions and unit labels only.
The answer is cached in data/mapping_proposal.json so the demo builds offline."""
import json, os, sys, time, urllib.request
from pathlib import Path
from .plant import SIGNALS
from .plant_b import tag_list

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "mapping_proposal.json"
CONVERSIONS = ["none", "degF_to_degC", "bar_to_kPa", "t/h_to_kg/h"]

PROMPT = """You map instrument tags from a second plant onto the signal model of a first plant running the same process.
Plant A model (id, name, unit):
{model}

Plant B tag list (tag, description, unit label):
{tags}

For every plant B tag, return the plant A signal id it measures and the conversion needed to bring plant B's
unit label to plant A's unit. Allowed conversions: {conv}. Use each plant A id at most once.
Give a confidence between 0 and 1. Answer with JSON only:
{{"mapping": [{{"tag": "...", "signal": "XMEAS(n) or XMV(n)", "conversion": "...", "confidence": 0.0}}]}}"""

def call(prompt):
    body = {"model": "openai/gpt-oss-120b", "temperature": 0, "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json",
                                          "User-Agent": "deviation-tracer"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 5: time.sleep(2 ** attempt * 3); continue
            raise

def propose(refresh=False):
    if CACHE.exists() and not refresh: return json.loads(CACHE.read_text())
    model = "\n".join(f'{s["id"]} | {s["name"]} | {s["unit"]}' for s in SIGNALS)
    tags = "\n".join(f'{t["tag"]} | {t["description"]} | {t["unit"]}' for t in tag_list())
    out = call(PROMPT.format(model=model, tags=tags, conv=", ".join(CONVERSIONS)))
    out["model"] = "openai/gpt-oss-120b (Groq), temperature 0"
    CACHE.write_text(json.dumps(out, indent=1))
    return out

if __name__ == "__main__":
    from .plant_b import truth
    p = propose(refresh="--refresh" in sys.argv)
    t = truth()
    rows = p["mapping"]
    right = sum(1 for m in rows if t.get(m["tag"]) == m["signal"])
    print(f"{len(rows)} tags proposed, {right} map to the right signal")
    for m in rows:
        if t.get(m["tag"]) != m["signal"]: print("WRONG", m, "true:", t.get(m["tag"]))
