"""Plant B: the same process run by another site. Different tag names and descriptions, some
signals in other units, and three problems that the tag list alone does not show:
two columns swapped in the export, one frozen transmitter, and one tag whose unit label is wrong."""
import json, random
from .analyze import load, ROOT
from .plant import SIGNALS

random.seed(7)

# (tag, description, unit label, conversion from plant A units to the unit actually in the data)
F = lambda c: c * 9 / 5 + 32          # °C -> °F
BAR = lambda kpa: kpa / 100.0         # kPa -> bar
TPH = lambda kgh: kgh / 1000.0        # kg/h -> t/h
SAME = lambda x: x
TAGS = {
 "XMEAS(1)": ("FI-1101", "Feed A to mixing zone", "kscmh", SAME),
 "XMEAS(2)": ("FI-1102", "Feed D, line 2", "t/h", TPH),
 "XMEAS(3)": ("FI-1103", "Feed E, line 3", "t/h", TPH),
 "XMEAS(4)": ("FI-1104", "Combined A+C feed, line 4", "kscmh", SAME),
 "XMEAS(5)": ("FI-1401", "Gas recycle to reactor", "kscmh", SAME),
 "XMEAS(6)": ("FI-1201", "R-100 total inlet flow", "kscmh", SAME),
 "XMEAS(7)": ("PI-1201", "R-100 head pressure", "bar", BAR),
 "XMEAS(8)": ("LI-1201", "R-100 liquid level", "%", SAME),
 "XMEAS(9)": ("TI-1201", "R-100 bed temperature", "degF", F),
 "XMEAS(10)": ("FI-1402", "Vent / purge flow", "kscmh", SAME),
 "XMEAS(11)": ("TI-1301", "V-300 flash drum temperature", "degF", F),
 "XMEAS(12)": ("LI-1301", "V-300 flash drum level", "%", SAME),
 "XMEAS(13)": ("PI-1301", "V-300 flash drum pressure", "bar", BAR),
 "XMEAS(14)": ("FI-1301", "V-300 bottoms to column", "m3/h", SAME),
 "XMEAS(15)": ("LI-1501", "C-500 sump level", "%", SAME),
 "XMEAS(16)": ("PI-1501", "C-500 top pressure", "bar", BAR),
 "XMEAS(17)": ("FI-1501", "C-500 product draw", "m3/h", SAME),
 "XMEAS(18)": ("TI-1501", "C-500 tray temperature", "degF", F),
 "XMEAS(19)": ("FI-1502", "C-500 reboiler steam", "t/h", TPH),
 "XMEAS(20)": ("JI-1401", "K-400 recycle compressor power", "kW", SAME),
 "XMEAS(21)": ("TI-1202", "R-100 jacket CW return temp", "degF", F),
 "XMEAS(22)": ("TI-1302", "E-310 condenser CW return temp", "degF", F),
}
for i, c in enumerate("ABCDEF"): TAGS[f"XMEAS({23+i})"] = (f"AI-12{10+i}", f"R-100 inlet GC, comp {c}", "mol%", SAME)
for i, c in enumerate("ABCDEFGH"): TAGS[f"XMEAS({29+i})"] = (f"AI-14{10+i}", f"Vent GC, comp {c}", "mol%", SAME)
for i, c in enumerate("DEFGH"): TAGS[f"XMEAS({37+i})"] = (f"AI-15{10+i}", f"Product GC, comp {c}", "mol%", SAME)
MV = ["FV-1102 Feed D valve", "FV-1103 Feed E valve", "FV-1101 Feed A valve", "FV-1104 Feed A+C valve",
      "HV-1401 compressor recycle valve", "FV-1402 vent valve", "FV-1301 flash drum bottoms valve",
      "FV-1501 column product valve", "FV-1502 reboiler steam valve", "TV-1202 R-100 jacket CW valve",
      "TV-1302 condenser CW valve"]
for i, d in enumerate(MV): TAGS[f"XMV({i+1})"] = (d.split()[0], " ".join(d.split()[1:]), "%", SAME)

# The three hidden problems. Each is invisible in the tag list.
SWAPPED = ("XMEAS(7)", "XMEAS(13)")   # reactor and separator pressure columns swapped in the export
FROZEN = "XMEAS(18)"                   # column tray temperature transmitter stuck
MISLABELED = "XMEAS(11)"               # labelled degF, but the data is still in degC

def to_plant_b(rows):
    ids = [s["id"] for s in SIGNALS]
    idx = {sid: i for i, sid in enumerate(ids)}
    out = []
    frozen_value = None
    for t, r in enumerate(rows):
        row = {}
        for sid in ids:
            tag, desc, unit, conv = TAGS[sid]
            v = r[idx[sid]]
            v = v if sid == MISLABELED else conv(v)
            row[tag] = round(v, 5)
        a, b = TAGS[SWAPPED[0]][0], TAGS[SWAPPED[1]][0]
        row[a], row[b] = row[b], row[a]
        ft = TAGS[FROZEN][0]
        if frozen_value is None: frozen_value = row[ft]
        row[ft] = frozen_value
        out.append(row)
    return out

def tag_list():
    """What plant B hands over: tag, description, unit label. Shuffled, like a real export."""
    lst = [{"tag": t[0], "description": t[1], "unit": t[2]} for t in TAGS.values()]
    random.shuffle(lst)
    return lst

def truth():
    return {TAGS[sid][0]: sid for sid in TAGS}

if __name__ == "__main__":
    print(len(tag_list()), tag_list()[:3])
    b = to_plant_b(load("d00_te.dat"))
    print(b[0][TAGS["XMEAS(9)"][0]], b[0][TAGS["XMEAS(7)"][0]], b[0][TAGS["XMEAS(18)"][0]], b[5][TAGS["XMEAS(18)"][0]])
