#!/usr/bin/env python3
"""Generates the neon GitHub dashboard cards in assets/generated/ from LIVE GitHub data.

Runs daily in .github/workflows/profile.yml. Needs GITHUB_TOKEN (provided by Actions).
Nothing here is hard-coded: every number comes from the GitHub GraphQL API.
Set DASHBOARD_FIXTURE=path.json to render from a saved API response (for local testing).
"""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_cards import BG2, CYAN, GOLD, MUTED, PANEL, PURPLE, TEXT, P, card, x  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "generated"
CARD_H = 376  # stats + languages share a height so they line up side by side

QUERY = """query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    contributionsCollection {
      totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def fetch(login):
    fixture = os.environ.get("DASHBOARD_FIXTURE")
    if fixture:
        return json.loads(pathlib.Path(fixture).read_text(encoding="utf-8"))
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required (it is provided automatically inside GitHub Actions).")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today not counted yet
        i -= 1
    while i >= 0 and counts[i]:
        cur += 1
        i -= 1
    return cur, longest


# ------------------------------------------------------------------------ cards
def stat_card(u, cc):
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    rows = [
        ("★", "Total stars", stars, GOLD),
        ("◆", "Commits (last 12 months)", cc["totalCommitContributions"], PURPLE),
        ("⇄", "Pull requests", u["pullRequests"]["totalCount"], CYAN),
        ("!", "Issues", u["issues"]["totalCount"], PURPLE),
        ("▣", "Public repositories", u["repositories"]["totalCount"], CYAN),
        ("☺", "Followers", u["followers"]["totalCount"], GOLD),
    ]
    out, y = [], 140
    for i, (g, label, val, col) in enumerate(rows):
        out.append(f'<text x="40" y="{y}" class="mono" font-size="16" fill="{col}" filter="url(#glow)">{g}</text>'
                   f'<text x="70" y="{y}" class="mono" font-size="15" fill="{TEXT}">{x(label)}</text>'
                   f'<text x="540" y="{y}" text-anchor="end" class="sans" font-size="20" fill="{col}">{val:,}'
                   f'<animate attributeName="opacity" values="0;1" dur="0.8s" begin="{i * 0.25:.2f}s" fill="freeze"/></text>'
                   f'<rect x="70" y="{y + 10}" width="470" height="1" fill="{PURPLE}" opacity=".18"/>')
        y += 38
    return card(CARD_H, "github stats", "Stats", "\n".join(out), w=580)


def lang_card(u):
    totals, colors = {}, {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            totals[n] = totals.get(n, 0) + e["size"]
            colors[n] = e["node"]["color"] or PURPLE
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in top) or 1
    out, bx, bw = [], 40, 500
    clip = f'<clipPath id="bar"><rect x="{bx}" y="128" width="{bw}" height="12" rx="6"/></clipPath><g clip-path="url(#bar)"><rect x="{bx}" y="128" width="{bw}" height="12" fill="{PANEL}"/>'
    cx = bx
    for n, v in top:
        w = bw * v / total
        clip += f'<rect x="{cx:.1f}" y="128" width="{w:.1f}" height="12" fill="{colors[n]}"/>'
        cx += w
    out.append(clip + "</g>")
    for i, (n, v) in enumerate(top):
        ly = 176 + i * 36
        pct = v / total
        out.append(f'<circle cx="46" cy="{ly - 5}" r="6" fill="{colors[n]}" filter="url(#glow)"/>'
                   f'<text x="62" y="{ly}" class="mono" font-size="14" fill="{TEXT}">{x(n)}</text>'
                   f'<text x="540" y="{ly}" text-anchor="end" class="mono" font-size="14" fill="{MUTED}">{100 * pct:.1f}%</text>'
                   f'<rect x="62" y="{ly + 8}" width="0" height="3" rx="1.5" fill="{colors[n]}" opacity=".8">'
                   f'<animate attributeName="width" values="0;{478 * pct:.1f}" dur="1.5s" begin="{i * 0.2:.1f}s" fill="freeze"/></rect>')
    if not top:
        out.append(f'<text x="40" y="180" class="mono" font-size="14" fill="{MUTED}">No language data yet.</text>')
    return card(CARD_H, "top languages", "Top Languages", "\n".join(out), w=580)


def contrib_card(cal):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    mx = max([d["contributionCount"] for d in days] + [1])
    scale = ["#161B2E", "#2E2366", "#4D3AA3", "#6E52D6", PURPLE]
    cell, gap = 15, 4
    gx0, gy0 = (1200 + 40 - len(weeks) * (cell + gap)) // 2, 150
    out = []
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            wd = dt.date.fromisoformat(d["date"]).isoweekday() % 7
            c = d["contributionCount"]
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / mx))
            glow = ' filter="url(#glow)"' if lvl == 4 else ""
            out.append(f'<rect x="{gx0 + wi * (cell + gap)}" y="{gy0 + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="3" '
                       f'fill="{scale[lvl]}"{glow}><title>{c} on {d["date"]}</title></rect>')
    for wd, lab in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        out.append(f'<text x="{gx0 - 36}" y="{gy0 + wd * (cell + gap) + 12}" class="mono" font-size="11" fill="{MUTED}">{lab}</text>')
    last_month = None
    for wi, w in enumerate(weeks):
        m = dt.date.fromisoformat(w["contributionDays"][0]["date"]).strftime("%b")
        if m != last_month and wi < len(weeks) - 2:
            out.append(f'<text x="{gx0 + wi * (cell + gap)}" y="{gy0 - 10}" class="mono" font-size="11" fill="{MUTED}">{m}</text>')
            last_month = m
    cur, longest = streaks(days)
    stats = [("CONTRIBUTIONS · 12 MO", cal["totalContributions"], CYAN), ("CURRENT STREAK", f"{cur} d", GOLD),
             ("LONGEST STREAK", f"{longest} d", PURPLE)]
    for i, (lab, val, col) in enumerate(stats):
        sx = 1164 - (2 - i) * 210
        out.append(f'<text x="{sx}" y="56" text-anchor="end" class="mono" font-size="11" letter-spacing="2" fill="{MUTED}">{lab}</text>'
                   f'<text x="{sx}" y="88" text-anchor="end" class="sans" font-size="26" fill="{col}" filter="url(#glow)">{val}</text>')
    sweep = (f'<rect x="{gx0 - 60}" y="{gy0}" width="60" height="{7 * (cell + gap)}" fill="{CYAN}" opacity=".08">'
             f'<animate attributeName="x" values="{gx0 - 60};{gx0 + len(weeks) * (cell + gap)}" dur="9s" repeatCount="indefinite"/></rect>')
    legend_y = gy0 + 7 * (cell + gap) + 20
    legend = f'<text x="1040" y="{legend_y + 11}" text-anchor="end" class="mono" font-size="11" fill="{MUTED}">less</text>'
    legend += "".join(f'<rect x="{1050 + i * 19}" y="{legend_y}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(scale))
    legend += f'<text x="1150" y="{legend_y + 11}" class="mono" font-size="11" fill="{MUTED}">more</text>'
    return card(legend_y + 36, "contributions", "Contributions", "\n".join(out) + sweep + legend)


def activity_card(cal):
    days = [d for w in cal["weeks"] for d in w["contributionDays"]][-31:]
    vals = [d["contributionCount"] for d in days]
    mx = max(vals + [1])
    x0, x1, y0, y1 = 80, 1160, 130, 330
    step = (x1 - x0) / max(len(vals) - 1, 1)
    pts = [(x0 + i * step, y1 - (y1 - y0) * v / mx) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = line + f" L{pts[-1][0]:.1f},{y1} L{pts[0][0]:.1f},{y1} Z"
    out = [f"""<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".45"/>
<stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></linearGradient></defs>"""]
    ticks = sorted({round(mx * k / 4) for k in range(5)})
    for t in ticks:
        gy = y1 - (y1 - y0) * t / mx
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{gy:.1f}" y2="{gy:.1f}" stroke="{PURPLE}" stroke-opacity=".12"/>'
                   f'<text x="{x0 - 14}" y="{gy + 4:.1f}" text-anchor="end" class="mono" font-size="11" fill="{MUTED}">{t}</text>')
    for i, d in enumerate(days):
        if i % 5 == 0 or i == len(days) - 1:
            lab = dt.date.fromisoformat(d["date"]).strftime("%d %b")
            out.append(f'<text x="{pts[i][0]:.1f}" y="{y1 + 24}" text-anchor="middle" class="mono" font-size="11" fill="{MUTED}">{lab}</text>')
    out.append(f'<path d="{area}" fill="url(#area)"/>')
    out.append(f'<path d="{line}" fill="none" stroke="{CYAN}" stroke-width="2.5" stroke-linejoin="round" filter="url(#glow)" '
               f'stroke-dasharray="4000" stroke-dashoffset="4000"><animate attributeName="stroke-dashoffset" values="4000;0" dur="3s" fill="freeze"/></path>')
    for i, (px, py) in enumerate(pts):
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{BG2}" stroke="{GOLD if vals[i] == mx and mx > 0 else PURPLE}" stroke-width="2">'
                   f'<title>{vals[i]} on {days[i]["date"]}</title></circle>')
    out.append(f'<text x="1164" y="56" text-anchor="end" class="mono" font-size="11" letter-spacing="2" fill="{MUTED}">LAST 31 DAYS</text>'
               f'<text x="1164" y="88" text-anchor="end" class="sans" font-size="26" fill="{CYAN}" filter="url(#glow)">{sum(vals)}</text>')
    return card(y1 + 50, "activity", "Activity Graph", "\n".join(out))


def main():
    data = fetch(P["username"])
    u = data["data"]["user"]
    cc = u["contributionsCollection"]
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"stats.svg": stat_card(u, cc), "languages.svg": lang_card(u),
             "contributions.svg": contrib_card(cc["contributionCalendar"]),
             "activity.svg": activity_card(cc["contributionCalendar"])}
    for n, c in files.items():
        (OUT / n).write_text(c, encoding="utf-8", newline="\n")
    print("dashboard built:", ", ".join(files))


if __name__ == "__main__":
    main()
