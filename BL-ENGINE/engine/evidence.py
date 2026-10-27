"""Facts and subjective taste must carry separate source support."""
REQUIRED_FACTS=("completed","real_bl","romance_progression","official_stream")
def evidence_gate(candidate):
    evidence=candidate.get("evidence",{})
    missing=[k for k in REQUIRED_FACTS if not evidence.get(k,{}).get("supported")]
    if candidate.get("hard_reject"):return {"approved":False,"reasons":["hard_reject"]}
    return {"approved":not missing,"reasons":["unverified:"+k for k in missing]}
