"""Learn an incident library from the training runs, then name the cause of a new deviation by its signature."""
import math
from .analyze import load, normal_stats, FAULT_START
from .plant import SIGNALS, FAULTS

WINDOW = 80
WEIGHT_SWING = 2.0

def signature(rows, stats, start, length=WINDOW):
    """Two numbers per signal over the window: the mean shift (z, clipped) and how much more it
    swings than in normal operation (log of the std ratio). Random-variation faults show up in the second."""
    seg = rows[start:start + length]
    shift, swing = [], []
    for j, (m, s) in enumerate(stats):
        if s == 0: shift.append(0.0); swing.append(0.0); continue
        vals = [r[j] for r in seg]
        mu = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))
        shift.append(max(-10.0, min(10.0, (mu - m) / s)))
        swing.append(max(-3.0, min(3.0, math.log(max(sd, 1e-9) / s))))
    return shift + [WEIGHT_SWING * x for x in swing]

def cosine(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0

def build_library(stats):
    """One signature per training fault. In the training runs the fault is on from the start."""
    return {f: signature(load(f"d{f:02d}.dat"), stats, 0) for f in range(1, 22)}

def match(sig, library, top=3):
    scored = sorted(((cosine(sig, v), f) for f, v in library.items()), reverse=True)
    return [{"fault": f, "similarity": round(s, 2)} for s, f in scored[:top]]

if __name__ == "__main__":
    from .analyze import analyze
    stats = normal_stats(load("d00.dat", transpose=True))
    lib = build_library(stats)
    hits = top3 = n = 0
    for f in range(1, 22):
        rows = load(f"d{f:02d}_te.dat")
        on = analyze(rows, stats, 6.0, 4)
        start = on[0]["onset"] if on else FAULT_START
        m = match(signature(rows, stats, start), lib)
        ok = m[0]["fault"] == f; ok3 = f in [x["fault"] for x in m]
        n += 1; hits += ok; top3 += ok3
        print(f"{f:2d} detected={bool(on)!s:5} -> {m}  {'OK' if ok else ''}")
    print(f"cause top-1 {hits}/{n}, top-3 {top3}/{n}")
