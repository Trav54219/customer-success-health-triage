"""Build the static HTML dashboard: python -m cshealth.dashboard"""
import html
from pathlib import Path
from .data import generate_accounts, generate_tickets
from .health import score_all
from .renewals import pipeline, playbooks_for, days_to_renewal
from .triage import triage_all
from .report import book_of_business


def money(n):
    return f"${n:,.0f}"


def build():
    scored = score_all(generate_accounts())
    tiers = {a["id"]: a["tier"] for a in scored}
    tickets = triage_all(generate_tickets(), tiers)
    pipe, book = pipeline(scored), book_of_business(scored)
    e = html.escape
    counts = {t: sum(a["tier"] == t for a in scored) for t in ("healthy", "watch", "at_risk")}
    rows = lambda items: "".join(f"<tr>{''.join(f'<td>{e(str(c))}</td>' for c in r)}</tr>" for r in items)
    risk = sorted([a for a in scored if a["tier"] == "at_risk"], key=lambda a: days_to_renewal(a))[:12]
    css = ("body{font:15px system-ui,sans-serif;margin:2rem auto;max-width:1000px;padding:0 1rem;color:#1c2330}"
           "table{border-collapse:collapse;width:100%;margin:.5rem 0 2rem}td,th{border-bottom:1px solid #dde;padding:.35rem .5rem;text-align:left}"
           ".k{display:inline-block;margin-right:1.5rem}.k b{font-size:1.6rem;display:block}.note{background:#fff7e0;padding:.6rem 1rem;border-radius:6px}")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CS Health and Triage Dashboard</title><style>{css}</style></head><body>
<h1>Customer Success Health and Support Triage</h1>
<p class="note">All data is synthetic and generated from a fixed seed. Objects are modeled on common CS and helpdesk concepts, not connected to any vendor product.</p>
<div><span class="k"><b>{len(scored)}</b>accounts</span><span class="k"><b>{counts['healthy']}</b>healthy</span>
<span class="k"><b>{counts['watch']}</b>watch</span><span class="k"><b>{counts['at_risk']}</b>at risk</span>
<span class="k"><b>{money(sum(a['arr'] for a in scored if a['tier']=='at_risk'))}</b>ARR at risk</span></div>
<h2>Renewal pipeline (next 90 days)</h2><table><tr><th>Window (days)</th><th>Renewals</th><th>ARR</th><th>ARR at risk</th></tr>
{rows((k, v['count'], money(v['arr']), money(v['arr_at_risk'])) for k, v in pipe.items())}</table>
<h2>At-risk accounts by renewal date</h2><table><tr><th>Account</th><th>CSM</th><th>Score</th><th>Days to renewal</th><th>ARR</th><th>Playbooks</th></tr>
{rows((a['name'], a['csm'], a['score'], days_to_renewal(a), money(a['arr']), ', '.join(playbooks_for(a)) or '-') for a in risk)}</table>
<h2>CSM book of business</h2><table><tr><th>CSM</th><th>Accounts</th><th>ARR</th><th>ARR at risk</th><th>Avg score</th><th>H / W / R</th><th>Renewals 90d</th></tr>
{rows((c, b['accounts'], money(b['arr']), money(b['arr_at_risk']), b['avg_score'], '/'.join(str(b['tiers'][t]) for t in ('healthy','watch','at_risk')), b['renewals_90d']) for c, b in book.items())}</table>
<h2>Ticket triage queue (worst SLA first)</h2><table><tr><th>Ticket</th><th>Subject</th><th>Category</th><th>Priority</th><th>Queue</th><th>SLA</th><th>Escalate to</th></tr>
{rows((t['id'], t['subject'], t['category'], t['priority'], t['queue'], t['sla_state'], t['escalate_to'] or '-') for t in tickets[:25])}</table>
</body></html>"""


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "index.html"
    out.write_text(build())
    print(f"wrote {out}")
