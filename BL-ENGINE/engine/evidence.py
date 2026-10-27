"""Evidence evaluation: approval needs attributable independent facts, not boolean assertions."""
REQUIRED_FACTS=("completed","real_bl","romance_progression","official_stream")

def evidence_gate(candidate):
    if candidate.get("hard_reject"):
        return {"approved":False,"reasons":["hard_reject"]}
    reasons=[]
    evidence=candidate.get("evidence",{})
    for key in REQUIRED_FACTS:
        claim=evidence.get(key,{})
        sources=claim.get("sources",[]) if isinstance(claim,dict) else []
        if not isinstance(claim,dict) or claim.get("supported") is not True:
            reasons.append("unsupported:"+key)
        elif not isinstance(sources,list) or not any(isinstance(s,str) and s.startswith(("https://","http://")) for s in sources):
            reasons.append("no_attributable_source:"+key)
    # Explicit user-specific veto is always separate from romance/identity evidence.
    return {"approved":not reasons,"reasons":reasons}
