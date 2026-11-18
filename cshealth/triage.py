"""Support ticket triage: category, priority, SLA timers, escalation, macros."""
from datetime import datetime, timedelta
from .data import NOW

CATEGORY_KEYWORDS = [  # first match wins, order matters
    ("security", ["breach", "suspicious", "unauthorized", "compromised"]),
    ("outage", ["down for", "outage", "unavailable", "cannot log in"]),
    ("billing", ["invoice", "refund", "charge", "card"]),
    ("bug", ["error", "broken", "not firing", "fails"]),
    ("feature_request", ["feature request", "would love"]),
    ("how_to", ["how do i", "question about", "where can i"]),
]
BASE_PRIORITY = {"security": "urgent", "outage": "urgent", "bug": "high",
                 "billing": "normal", "how_to": "low", "feature_request": "low", "other": "normal"}
SLA_HOURS = {"urgent": 1, "high": 4, "normal": 8, "low": 24}
ROUTES = {"security": "security-team", "outage": "tier2-engineering", "bug": "tier2-engineering",
          "billing": "billing-ops", "how_to": "tier1-support", "feature_request": "product-feedback", "other": "tier1-support"}
MACROS = {
    "security": "Thanks for flagging this. We have opened a security review and will update you within the hour.",
    "outage": "We are investigating a service issue and will post updates every 30 minutes.",
    "billing": "We have passed this to billing and will confirm the correction in writing.",
    "bug": "Thanks for the report. Please send the steps to reproduce and a timestamp so we can trace it.",
    "how_to": "Here is the guide for this. Reply if it does not cover your case.",
    "feature_request": "Logged with the product team. We will tell you if it is scheduled.",
    "other": "Thanks for reaching out. A support agent will follow up shortly.",
}
PRIORITY_RANK = {"low": 0, "normal": 1, "high": 2, "urgent": 3}


def categorize(subject):
    s = subject.lower()
    for cat, words in CATEGORY_KEYWORDS:
        if any(w in s for w in words):
            return cat
    return "other"


def prioritize(category, plan, account_tier=None):
    p = BASE_PRIORITY[category]
    bump = plan == "enterprise" or account_tier == "at_risk"
    if bump and PRIORITY_RANK[p] < 3:
        p = {"low": "normal", "normal": "high", "high": "urgent"}[p]
    return p


def sla_state(created_at, priority, now=NOW):
    due = created_at + timedelta(hours=SLA_HOURS[priority])
    total = (due - created_at).total_seconds()
    elapsed = (now - created_at).total_seconds()
    state = "breached" if elapsed >= total else "at_risk" if elapsed >= 0.75 * total else "ok"
    return due, state


def escalation(category, priority, plan, state):
    """Return escalation target or None."""
    if category == "security":
        return "head-of-security"
    if state == "breached" and priority in ("urgent", "high"):
        return "support-manager"
    if plan == "enterprise" and priority in ("urgent", "high") and state != "ok":
        return "csm-on-call"
    return None


def triage(ticket, account_tiers=None, now=NOW):
    cat = categorize(ticket["subject"])
    tier = (account_tiers or {}).get(ticket["account_id"])
    pri = prioritize(cat, ticket["plan"], tier)
    created = datetime.fromisoformat(ticket["created_at"])
    due, state = sla_state(created, pri, now)
    out = dict(ticket)
    out.update(category=cat, priority=pri, queue=ROUTES[cat], sla_due=due.isoformat(timespec="minutes"),
               sla_state=state, escalate_to=escalation(cat, pri, ticket["plan"], state), macro=MACROS[cat])
    return out


def triage_all(tickets, account_tiers=None):
    rows = [triage(t, account_tiers) for t in tickets]
    rank = {"breached": 0, "at_risk": 1, "ok": 2}
    return sorted(rows, key=lambda r: (rank[r["sla_state"]], -PRIORITY_RANK[r["priority"]], r["sla_due"]))
