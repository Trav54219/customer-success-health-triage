# Customer Success Health and Support Triage

A small Python project modeling the core workflows of a customer success and support operations team: health scoring, churn-risk tiers, renewal playbooks, ticket triage with SLA timers, and a CSM book-of-business report.

**All data is synthetic** (seeded random generator, fixed clock of 2026-11-17). The objects (accounts, health scores, playbooks, tickets, macros, SLAs) are modeled on concepts common to tools like Gainsight, Zendesk and Intercom. This project is **not connected to, and does not use any API of, those products**. No real customers or people appear anywhere.

## What it does
- `health.py`: score 0-100 from usage (35%), support load (25%), NPS (20%), billing (20%). Tiers: healthy >= 75, watch 50-74, at_risk < 50. Accounts 45+ days past due or with an open urgent ticket cannot be tiered healthy. Missing NPS is scored neutral and flagged.
- `renewals.py`: renewal pipeline for the next 90 days with ARR at risk, and playbook triggers (onboarding, QBR, at-risk save, billing escalation).
- `triage.py`: keyword categorization, priority (bumped for enterprise or at-risk accounts), SLA due times (urgent 1h, high 4h, normal 8h, low 24h), at-risk state at 75% of the window, escalation rules, queue routing, reply macros.
- `report.py`: per-CSM accounts, ARR, ARR at risk, average score, tier mix.
- `dashboard.py`: writes `docs/index.html`, a static page.

## Run
```
python3 -m pip install pytest
python3 -m pytest
python3 -m cshealth.dashboard   # regenerates docs/index.html
```

## Limits
Weights, thresholds and keyword rules are illustrative choices, not tuned on real outcomes. Scores here say nothing about real churn.
