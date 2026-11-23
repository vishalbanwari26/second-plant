"""A shift handover note from the open incidents and the decisions made on this shift."""
def handover(incidents, log_entries):
    open_ = [i for i in incidents if i["state"] == "open"]
    decided = [e for e in log_entries if e["kind"] == "incident"]
    lines = [f"{len(open_)} open deviation(s), {len(decided)} decided this shift."]
    for i in open_[:5]:
        n = i.get("note") or {}
        lines.append(f"OPEN {i['id']}: {n.get('unit', '?')}. {n.get('next_check', '')}")
    for e in decided[-5:]:
        lines.append(f"{e['decision'].upper()} {e['subject']} by {e['actor']}: {e['reason']}")
    return lines
