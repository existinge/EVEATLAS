"""Taste scores do not control whether a novel title is displayed."""
WEIGHTS={"romance_payoff":25,"acting_chemistry":20,"plot_stakes":20,"pursuit":15,"visual_fit":10,"pacing":10}
def score(criteria):
    if any(k not in criteria for k in WEIGHTS):return None
    if any(not isinstance(criteria[k],(int,float)) or not 0<=criteria[k]<=10 for k in WEIGHTS):raise ValueError("Score range 0..10")
    return round(sum(criteria[k]*w/10 for k,w in WEIGHTS.items()),1)
