"""The Tennessee Eastman plant: what each of the 52 columns is, and which unit it belongs to."""

XMEAS = [
    ("A feed (stream 1)", "kscmh"), ("D feed (stream 2)", "kg/h"), ("E feed (stream 3)", "kg/h"),
    ("A and C feed (stream 4)", "kscmh"), ("Recycle flow (stream 8)", "kscmh"), ("Reactor feed rate (stream 6)", "kscmh"),
    ("Reactor pressure", "kPa"), ("Reactor level", "%"), ("Reactor temperature", "°C"),
    ("Purge rate (stream 9)", "kscmh"), ("Separator temperature", "°C"), ("Separator level", "%"),
    ("Separator pressure", "kPa"), ("Separator underflow (stream 10)", "m3/h"), ("Stripper level", "%"),
    ("Stripper pressure", "kPa"), ("Stripper underflow (stream 11)", "m3/h"), ("Stripper temperature", "°C"),
    ("Stripper steam flow", "kg/h"), ("Compressor work", "kW"), ("Reactor cooling water outlet temp", "°C"),
    ("Condenser cooling water outlet temp", "°C"),
] + [(f"Reactor feed analysis, component {c}", "mol%") for c in "ABCDEF"] \
  + [(f"Purge gas analysis, component {c}", "mol%") for c in "ABCDEFGH"] \
  + [(f"Product analysis, component {c}", "mol%") for c in "DEFGH"]

XMV = [
    "D feed flow valve", "E feed flow valve", "A feed flow valve", "A and C feed flow valve",
    "Compressor recycle valve", "Purge valve", "Separator liquid flow valve", "Stripper product flow valve",
    "Stripper steam valve", "Reactor cooling water flow", "Condenser cooling water flow",
]

FEEDS, REACTOR, R_COOL, SEP, STRIP, RECYCLE = (
    "Feeds", "Reactor", "Reactor cooling", "Separator and condenser", "Stripper", "Recycle, compressor and purge")

def unit_of_meas(i):  # i is 1-based XMEAS index
    if i in (1, 2, 3, 4): return FEEDS
    if i in (6, 7, 8, 9): return REACTOR
    if i == 21: return R_COOL
    if i in (11, 12, 13, 14, 22): return SEP
    if i in (15, 16, 17, 18, 19): return STRIP
    if i in (5, 10, 20): return RECYCLE
    if 23 <= i <= 28: return FEEDS      # analysis of the reactor feed
    if 29 <= i <= 36: return RECYCLE    # purge gas analysis
    return STRIP                         # product analysis

MV_UNIT = [FEEDS, FEEDS, FEEDS, FEEDS, RECYCLE, RECYCLE, SEP, STRIP, STRIP, R_COOL, SEP]

SIGNALS = (
    [{"id": f"XMEAS({i+1})", "name": n, "unit": u, "area": unit_of_meas(i + 1), "sampled": i >= 22}
     for i, (n, u) in enumerate(XMEAS)]
    + [{"id": f"XMV({i+1})", "name": n, "unit": "%", "area": MV_UNIT[i], "sampled": False}
       for i, n in enumerate(XMV)]
)

# Known disturbances (Downs and Vogel; README of the Braatz data set). 16-21 have no stated cause.
FAULTS = {
    1: ("A/C feed ratio step, B composition constant (stream 4)", FEEDS),
    2: ("B composition step, A/C ratio constant (stream 4)", FEEDS),
    3: ("D feed temperature step (stream 2)", FEEDS),
    4: ("Reactor cooling water inlet temperature step", R_COOL),
    5: ("Condenser cooling water inlet temperature step", SEP),
    6: ("A feed loss (stream 1)", FEEDS),
    7: ("C header pressure loss (stream 4)", FEEDS),
    8: ("A, B, C feed composition random variation (stream 4)", FEEDS),
    9: ("D feed temperature random variation (stream 2)", FEEDS),
    10: ("C feed temperature random variation (stream 4)", FEEDS),
    11: ("Reactor cooling water inlet temperature random variation", R_COOL),
    12: ("Condenser cooling water inlet temperature random variation", SEP),
    13: ("Reaction kinetics slow drift", REACTOR),
    14: ("Reactor cooling water valve sticking", R_COOL),
    15: ("Condenser cooling water valve sticking", SEP),
}
