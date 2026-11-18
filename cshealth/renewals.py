"""Renewal pipeline and playbook triggers."""
from datetime import date
from .data import NOW


def days_to_renewal(a):
    return (date.fromisoformat(a["renewal_date"]) - NOW.date()).days


def account_age_days(a):
    return (NOW.date() - date.fromisoformat(a["contract_start"])).days


def playbooks_for(a):
    """Return playbook names triggered for a scored account."""
    out = []
    d = days_to_renewal(a)
    if account_age_days(a) <= 60:
        out.append("onboarding")
    if d <= 120 and a["tier"] == "at_risk":
        out.append("at_risk_save")
    if d <= 90 and a["tier"] != "at_risk" and a["last_qbr_days_ago"] > 90:
        out.append("qbr")
    if a["days_past_due"] >= 30:
        out.append("billing_escalation")
    return out


def bucket(d):
    return "0-30" if d <= 30 else "31-60" if d <= 60 else "61-90" if d <= 90 else "91+"


def pipeline(scored):
    """Renewals within 90 days grouped by bucket with ARR and ARR at risk."""
    rows = {b: {"count": 0, "arr": 0, "arr_at_risk": 0} for b in ("0-30", "31-60", "61-90")}
    for a in scored:
        d = days_to_renewal(a)
        if d > 90:
            continue
        r = rows[bucket(d)]
        r["count"] += 1
        r["arr"] += a["arr"]
        if a["tier"] == "at_risk":
            r["arr_at_risk"] += a["arr"]
    return rows
