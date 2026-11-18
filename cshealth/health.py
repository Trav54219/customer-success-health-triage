"""Customer health score from usage, support, NPS and billing signals.

Weights: usage 35, support 25, NPS 20, billing 20. Each sub-score is 0-100.
Tiers: healthy >= 75, watch 50-74, at_risk < 50. Hard override: 45+ days
past due or an open urgent ticket caps the tier at watch.
"""
WEIGHTS = {"usage": 0.35, "support": 0.25, "nps": 0.20, "billing": 0.20}


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def usage_score(a):
    seat_util = a["active_seats"] / a["seats"]
    trend = a["logins_30d"] / max(1, a["logins_prev_30d"])  # 1.0 = flat
    return clamp(60 * min(seat_util / 0.8, 1) + 40 * clamp(trend, 0, 1.2) / 1.2)


def support_score(a):
    # more tickets per 30d lowers score; urgent open ticket is a heavy penalty
    return clamp(100 - 9 * a["tickets_30d"] - 30 * a["open_urgent_tickets"])


def nps_score(a):
    if a["nps"] is None:
        return 50.0  # unknown is neutral, flagged separately
    return clamp((a["nps"] + 100) / 2)


def billing_score(a):
    d = a["days_past_due"]
    return 100.0 if d <= 0 else clamp(100 - 1.6 * d)


def tier_for(score, a):
    tier = "healthy" if score >= 75 else "watch" if score >= 50 else "at_risk"
    if tier == "healthy" and (a["days_past_due"] >= 45 or a["open_urgent_tickets"]):
        tier = "watch"
    return tier


def score_account(a):
    parts = {"usage": usage_score(a), "support": support_score(a),
             "nps": nps_score(a), "billing": billing_score(a)}
    total = sum(parts[k] * w for k, w in WEIGHTS.items())
    out = dict(a)
    out.update(parts={k: round(v, 1) for k, v in parts.items()}, score=round(total, 1),
               tier=tier_for(total, a), nps_missing=a["nps"] is None)
    return out


def score_all(accounts):
    return [score_account(a) for a in accounts]
