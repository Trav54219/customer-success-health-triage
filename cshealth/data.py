"""Seeded synthetic data generator. Every record is invented."""
import random
from datetime import datetime, timedelta

NOW = datetime(2026, 11, 17, 9, 0)  # fixed clock so output is reproducible
PLANS = {"starter": 12_000, "growth": 48_000, "enterprise": 180_000}
CSMS = ["CSM-A", "CSM-B", "CSM-C", "CSM-D", "CSM-E"]
TICKET_SNIPPETS = {
    "billing": ["Invoice shows a duplicate charge", "Need a refund for last month", "Update card on file"],
    "bug": ["Export fails with error 500", "Dashboard is broken after the update", "Webhook not firing"],
    "outage": ["Production is down for all our users", "Cannot log in, site unavailable", "API outage since 08:00"],
    "how_to": ["How do I add a new user?", "Question about setting up SSO", "Where can I find the audit report?"],
    "security": ["We saw a suspicious login on an admin account", "Possible data breach alert from our IT team"],
    "feature_request": ["Feature request: bulk edit", "Would love a Slack integration"],
}


def generate_accounts(n=60, seed=42):
    rng = random.Random(seed)
    accounts = []
    for i in range(n):
        plan = rng.choices(list(PLANS), weights=[5, 4, 1])[0]
        seats = {"starter": rng.randint(5, 25), "growth": rng.randint(30, 120), "enterprise": rng.randint(200, 800)}[plan]
        start = NOW - timedelta(days=rng.randint(10, 700))
        term = 365
        end = start + timedelta(days=term)
        while end < NOW:  # roll forward to next renewal
            end += timedelta(days=term)
        # a latent "true health" drives correlated signals so tiers are not random noise
        latent = rng.random()
        prev = rng.randint(80, 400)
        accounts.append({
            "id": f"ACC-{1000 + i}",
            "name": f"Demo Co {i + 1:02d}",
            "plan": plan,
            "arr": int(PLANS[plan] * rng.uniform(0.8, 1.3)),
            "seats": seats,
            "csm": CSMS[i % len(CSMS)],
            "contract_start": start.date().isoformat(),
            "renewal_date": end.date().isoformat(),
            "last_qbr_days_ago": rng.choice([20, 45, 80, 120, 200, 400]),
            "active_seats": max(1, int(seats * (0.15 + 0.8 * latent))),
            "logins_30d": int(prev * (0.3 + 1.0 * latent)),
            "logins_prev_30d": prev,
            "tickets_30d": int(round((1 - latent) * 8 + rng.random() * 2)),
            "open_urgent_tickets": 1 if (latent < 0.25 and rng.random() < 0.6) else 0,
            "nps": None if rng.random() < 0.15 else max(-100, min(100, int(-60 + 160 * latent + rng.randint(-20, 20)))) ,
            "days_past_due": 0 if latent > 0.3 or rng.random() < 0.6 else rng.choice([7, 20, 35, 50, 75]),
        })
    return accounts


def generate_tickets(n=40, seed=7):
    rng = random.Random(seed)
    tickets = []
    cats = list(TICKET_SNIPPETS)
    for i in range(n):
        cat = rng.choices(cats, weights=[3, 4, 1, 5, 1, 2])[0]
        text = rng.choice(TICKET_SNIPPETS[cat])
        tickets.append({
            "id": f"T-{5000 + i}",
            "account_id": f"ACC-{1000 + rng.randrange(60)}",
            "plan": rng.choices(list(PLANS), weights=[5, 4, 1])[0],
            "subject": text,
            "created_at": (NOW - timedelta(minutes=rng.randint(5, 60 * 30))).isoformat(timespec="minutes"),
            "status": "open",
        })
    return tickets
