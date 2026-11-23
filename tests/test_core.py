from core.hashlog import GENESIS, entry_hash, verify
from core.agent import validate
from core.checks import review, data_truth
from core.mapper import propose
from core.plant_b import TAGS, FROZEN, MISLABELED

def chain(n):
    out, prev = [], GENESIS
    for i in range(n):
        e = {"at": f"2026-11-23T10:0{i}:00+00:00", "actor": "a", "kind": "mapping", "subject": f"T{i}", "decision": "accept", "reason": "", "payload": {"signal": "XMEAS(1)"}}
        e["prev_hash"] = prev; e["hash"] = entry_hash(prev, e); prev = e["hash"]; out.append(e)
    return out

def test_chain_holds_and_breaks_at_the_edited_entry():
    log = chain(4)
    assert verify(log) is None
    log[1]["reason"] = "edited later"
    assert verify(log) == 2

def test_checks_hold_back_the_frozen_transmitter_and_fix_the_unit_label():
    items = {i["tag"]: i for i in review(propose())}
    assert items[TAGS[FROZEN][0]]["status"] == "frozen"
    assert items[TAGS[FROZEN][0]]["suggested"] is None
    m = items[TAGS[MISLABELED][0]]
    assert m["status"] == "unit" and m["suggested_conversion"] == "none"

def test_every_usable_tag_ends_on_the_signal_its_data_carries():
    truth = data_truth()
    for i in review(propose()):
        if i["status"] != "frozen":
            assert i["suggested"] == truth[i["tag"]], i["tag"]

EV = {"signals": [{"id": "XMV(10)"}, {"id": "XMEAS(21)"}], "units": [{"area": "Reactor cooling"}],
      "library": [{"fault": 4, "similarity": 0.8}, {"fault": 11, "similarity": 0.4}, {"fault": 17, "similarity": 0.2}]}
GOOD = {"summary": "s", "matched_incident": 4, "unit": "Reactor cooling", "signals": ["XMV(10)"], "would_prove_wrong": "w", "next_check": "n"}

def test_a_note_that_follows_the_evidence_passes():
    assert validate(GOOD, EV) == []

def test_a_note_citing_a_signal_outside_the_evidence_is_rejected():
    assert validate({**GOOD, "signals": ["XMEAS(9)"]}, EV)

def test_a_note_naming_an_incident_outside_the_top_three_is_rejected():
    assert validate({**GOOD, "matched_incident": 6}, EV)

def test_a_weak_match_must_stay_unnamed():
    weak = {**EV, "library": [{"fault": 4, "similarity": 0.5}] + EV["library"][1:]}
    assert validate(GOOD, weak)
    assert validate({**GOOD, "matched_incident": None, "unit": "Reactor cooling"}, weak) == []
