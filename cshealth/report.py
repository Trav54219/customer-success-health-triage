"""CSM book-of-business report."""
from collections import defaultdict
from .renewals import days_to_renewal, playbooks_for


def book_of_business(scored):
    book = defaultdict(lambda: {"accounts": 0, "arr": 0, "arr_at_risk": 0, "avg_score": 0.0,
                                "tiers": {"healthy": 0, "watch": 0, "at_risk": 0}, "renewals_90d": 0, "playbooks": 0})
    for a in scored:
        b = book[a["csm"]]
        b["accounts"] += 1
        b["arr"] += a["arr"]
        b["avg_score"] += a["score"]
        b["tiers"][a["tier"]] += 1
        if a["tier"] == "at_risk":
            b["arr_at_risk"] += a["arr"]
        if days_to_renewal(a) <= 90:
            b["renewals_90d"] += 1
        b["playbooks"] += len(playbooks_for(a))
    for b in book.values():
        b["avg_score"] = round(b["avg_score"] / b["accounts"], 1)
    return dict(sorted(book.items()))
