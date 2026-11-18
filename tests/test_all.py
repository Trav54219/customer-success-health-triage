from datetime import datetime
from cshealth.data import generate_accounts, generate_tickets, NOW
from cshealth.health import score_account, score_all, tier_for
from cshealth.renewals import playbooks_for, pipeline
from cshealth.triage import categorize, prioritize, sla_state, escalation, triage
from cshealth.report import book_of_business
from cshealth.dashboard import build

BASE = dict(id="X", seats=100, active_seats=90, logins_30d=200, logins_prev_30d=200, tickets_30d=0,
            open_urgent_tickets=0, nps=70, days_past_due=0, arr=50000, csm="CSM-A", plan="growth",
            contract_start="2025-01-01", renewal_date="2027-06-01", last_qbr_days_ago=30)


def test_seeded_data_is_deterministic():
    assert generate_accounts() == generate_accounts()
    assert generate_tickets() == generate_tickets()


def test_healthy_account():
    s = score_account(BASE)
    assert s["tier"] == "healthy" and s["score"] >= 75


def test_unhealthy_account_is_at_risk():
    a = dict(BASE, active_seats=10, logins_30d=20, tickets_30d=7, nps=-40, days_past_due=50)
    assert score_account(a)["tier"] == "at_risk"


def test_past_due_caps_healthy_at_watch():
    assert tier_for(90, dict(BASE, days_past_due=50)) == "watch"


def test_missing_nps_is_neutral_and_flagged():
    s = score_account(dict(BASE, nps=None))
    assert s["parts"]["nps"] == 50.0 and s["nps_missing"]


def test_scores_in_range():
    for a in score_all(generate_accounts()):
        assert 0 <= a["score"] <= 100


def test_playbooks():
    risky = score_account(dict(BASE, active_seats=5, logins_30d=5, tickets_30d=8, nps=-60,
                               days_past_due=40, renewal_date="2026-12-20"))
    p = playbooks_for(risky)
    assert "at_risk_save" in p and "billing_escalation" in p
    qbr = score_account(dict(BASE, renewal_date="2026-12-30", last_qbr_days_ago=200))
    assert "qbr" in playbooks_for(qbr)
    new = score_account(dict(BASE, contract_start="2026-11-01"))
    assert "onboarding" in playbooks_for(new)


def test_pipeline_buckets_only_90_days():
    rows = pipeline(score_all(generate_accounts()))
    assert set(rows) == {"0-30", "31-60", "61-90"}


def test_categorize_and_priority():
    assert categorize("Production is down for all our users") == "outage"
    assert categorize("Possible data breach alert") == "security"
    assert categorize("hello") == "other"
    assert prioritize("how_to", "enterprise") == "normal"
    assert prioritize("outage", "starter") == "urgent"


def test_sla_states():
    c = datetime(2026, 11, 17, 8, 0)
    assert sla_state(c, "high", NOW)[1] == "ok"          # 1h of 4h
    assert sla_state(c, "urgent", NOW)[1] == "breached"  # 1h of 1h
    assert sla_state(datetime(2026, 11, 17, 5, 30), "high", NOW)[1] == "at_risk"  # 3.5h of 4h


def test_escalation_rules():
    assert escalation("security", "urgent", "starter", "ok") == "head-of-security"
    assert escalation("bug", "high", "starter", "breached") == "support-manager"
    assert escalation("bug", "high", "enterprise", "at_risk") == "csm-on-call"
    assert escalation("how_to", "low", "starter", "ok") is None


def test_triage_attaches_macro_and_queue():
    t = triage({"id": "T", "account_id": "A", "plan": "starter", "subject": "Invoice shows a duplicate charge",
                "created_at": "2026-11-17T08:30", "status": "open"})
    assert t["queue"] == "billing-ops" and t["macro"] and t["sla_state"] == "ok"


def test_book_of_business_totals():
    scored = score_all(generate_accounts())
    book = book_of_business(scored)
    assert sum(b["accounts"] for b in book.values()) == len(scored)
    assert sum(b["arr"] for b in book.values()) == sum(a["arr"] for a in scored)


def test_dashboard_states_synthetic():
    h = build()
    assert "synthetic" in h and "<table>" in h
