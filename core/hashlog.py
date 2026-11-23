"""A hash-chained decision log. The browser version in web/src/hashlog.ts computes the same hashes."""
import hashlib, json

GENESIS = "0" * 64

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def entry_hash(prev_hash, entry):
    body = {k: entry[k] for k in ("at", "actor", "kind", "subject", "decision", "reason", "payload")}
    return hashlib.sha256((prev_hash + "|" + canonical(body)).encode()).hexdigest()

def verify(entries):
    """Returns the 1-based position of the first broken entry, or None if the chain holds."""
    prev = GENESIS
    for i, e in enumerate(entries, 1):
        if e["prev_hash"] != prev or e["hash"] != entry_hash(prev, e): return i
        prev = e["hash"]
    return None
