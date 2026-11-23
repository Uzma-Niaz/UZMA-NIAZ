#!/usr/bin/env python3
"""Builds every static neon SVG in assets/ and README.md from profile.json.

Edit profile.json, then run:  python scripts/build_cards.py
(The GitHub Action also runs this automatically when profile.json changes.)
"""
import json
import pathlib
import re
import textwrap
import urllib.parse
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
ASSETS = ROOT / "assets"

BG1, BG2 = "#10131F", "#0D1117"
PURPLE, CYAN, GOLD = "#8F6BFF", "#5AE0FF", "#F5B800"
TEXT, MUTED, PANEL = "#E6E8F2", "#9AA3C7", "#141829"
W = 1200

STYLE = """<style>
.mono{font-family:'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'Courier New',monospace}
.sans{font-family:'Space Grotesk','Segoe UI','Inter','Helvetica Neue',Arial,sans-serif;font-weight:800}
</style>"""


def x(s):
    return escape(str(s), {'"': "&quot;"})


def load_icon(name):
    raw = (ASSETS / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    return re.search(r'\sd="([^"]+)"', raw).group(1)


def icon(name, cx, cy, size, fill, extra=""):
    s = size / 24
    return (f'<path transform="translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({s:.4f})" '
            f'd="{load_icon(name)}" fill="{fill}" {extra}/>')


def tw(text, size):
    """Approximate width of monospace text."""
    return len(text) * size * 0.61


def common_defs(extra=""):
    return f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PURPLE}"/><stop offset=".55" stop-color="{CYAN}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>
<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="{PURPLE}" stroke-opacity=".07"/></pattern>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" fill-opacity=".022"/></pattern>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
{extra}
</defs>"""


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{x(title)}"><title>{x(title)}</title>{STYLE}{body}</svg>\n')


def card(h, label, title, body, extra_defs="", w=W):
    """Rounded neon card with grid + scanline texture and a softly pulsing glowing border."""
    return svg(w, h, f"""{common_defs(extra_defs)}
<clipPath id="cardclip"><rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="18"/></clipPath>
<g clip-path="url(#cardclip)">
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <rect width="{w}" height="{h}" fill="url(#scan)"/>
</g>
<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="18" fill="none" stroke="url(#edge)" stroke-width="3" filter="url(#blur8)" opacity=".45">
  <animate attributeName="opacity" values=".25;.6;.25" dur="6s" repeatCount="indefinite"/>
</rect>
<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="18" fill="none" stroke="url(#edge)" stroke-width="1.2" stroke-opacity=".85"/>
<text x="36" y="46" class="mono" font-size="13" letter-spacing="3" fill="{GOLD}">// {x(label.upper())}</text>
<text x="36" y="84" class="sans" font-size="30" fill="{TEXT}">{x(title)}</text>
<rect x="36" y="98" width="56" height="3" rx="1.5" fill="{PURPLE}" filter="url(#glow)">
  <animate attributeName="width" values="56;96;56" dur="5s" repeatCount="indefinite"/>
</rect>
{body}""", title)


# --------------------------------------------------------------------------- hero
def hero():
    h, horizon, cx = 400, 272, W / 2
    verticals = "".join(
        f'<line x1="{cx + k * 7:.1f}" y1="{horizon}" x2="{cx + k * 140:.1f}" y2="{h}"/>' for k in range(-24, 25))
    n = 14
    pos = [horizon + (h - horizon) * (i / n) ** 2.1 for i in range(n + 1)]
    horizontals = "".join(
        f'<line x1="0" x2="{W}" y1="{pos[i]:.1f}" y2="{pos[i]:.1f}">'
        f'<animate attributeName="y1" values="{pos[i]:.1f};{pos[i + 1]:.1f}" dur="3.2s" repeatCount="indefinite"/>'
        f'<animate attributeName="y2" values="{pos[i]:.1f};{pos[i + 1]:.1f}" dur="3.2s" repeatCount="indefinite"/></line>'
        for i in range(n))
    sun_stripes = "".join(
        f'<rect x="{cx - 130}" y="{horizon - 70 + i * 13}" width="260" height="{2 + i * 1.3:.1f}" fill="#000"/>'
        for i in range(6))
    stars = "".join(
        f'<circle cx="{sx}" cy="{sy}" r="{r}" fill="#fff"><animate attributeName="opacity" values=".15;.8;.15" '
        f'dur="{d}s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for sx, sy, r, d, b in [(90, 60, 1.2, 5, 0), (210, 120, 1, 7, 1), (340, 48, 1.4, 6, 2), (470, 96, .9, 8, 0),
                                (760, 54, 1.2, 6, 3), (880, 118, 1, 7, 1), (1010, 72, 1.4, 5, 2), (1120, 140, 1, 8, 0),
                                (150, 200, .9, 6, 4), (1060, 210, .9, 7, 2)])
    name, title, sub = x(P["name"].upper()), x(P["title"].upper()), x(P["subtitle"])
    glitch = 'values="0 0;0 0;-5 0;4 0;0 0;0 0" keyTimes="0;.86;.88;.9;.92;1" dur="8s" repeatCount="indefinite"'
    extra = f"""
<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD}"/><stop offset=".55" stop-color="#FF5FA2"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
<linearGradient id="namefill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#D9CCFF"/></linearGradient>
<mask id="gridmask"><rect y="{horizon}" width="{W}" height="{h - horizon}" fill="url(#fade)"/></mask>
<mask id="sunmask"><rect width="{W}" height="{horizon}" fill="#fff"/>{sun_stripes}</mask>
<clipPath id="slice"><rect x="0" y="112" width="{W}" height="12"><animate attributeName="y" values="112;150;126;112" dur="8s" repeatCount="indefinite"/></rect></clipPath>"""
    body = f"""{common_defs(extra)}
<clipPath id="cardclip"><rect x="2" y="2" width="{W - 4}" height="{h - 4}" rx="20"/></clipPath>
<g clip-path="url(#cardclip)">
  <rect width="{W}" height="{h}" fill="url(#bg)"/>
  {stars}
  <circle cx="{cx}" cy="{horizon}" r="150" fill="{PURPLE}" opacity=".35" filter="url(#blur8)">
    <animate attributeName="opacity" values=".25;.45;.25" dur="7s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{cx}" cy="{horizon}" r="128" fill="url(#sun)" mask="url(#sunmask)" opacity=".9"/>
  <rect y="{horizon}" width="{W}" height="{h - horizon}" fill="{BG2}"/>
  <g stroke="{PURPLE}" stroke-width="1.3" mask="url(#gridmask)">{verticals}{horizontals}</g>
  <line x1="0" x2="{W}" y1="{horizon}" y2="{horizon}" stroke="{CYAN}" stroke-width="2" filter="url(#glow)" opacity=".9"/>
  <rect width="{W}" height="{h}" fill="url(#scan)"/>
</g>
<rect x="2" y="2" width="{W - 4}" height="{h - 4}" rx="20" fill="none" stroke="url(#edge)" stroke-width="1.2"/>
<text x="34" y="40" class="mono" font-size="13" fill="{MUTED}">&gt; sys.profile <tspan fill="{PURPLE}">//</tspan> {x(P["username"])}</text>
<g transform="translate({W - 140} 35)">
  <circle r="5" fill="{CYAN}" filter="url(#glow)"><animate attributeName="opacity" values="1;.3;1" dur="2.6s" repeatCount="indefinite"/></circle>
  <text x="14" y="5" class="mono" font-size="13" fill="{CYAN}" letter-spacing="2">ONLINE</text>
</g>
<g text-anchor="middle" class="sans" font-size="92" letter-spacing="10">
  <text x="{cx}" y="150" fill="{PURPLE}" filter="url(#blur8)" opacity=".9">{name}
    <animate attributeName="opacity" values=".6;1;.6" dur="5s" repeatCount="indefinite"/></text>
  <text x="{cx}" y="150" fill="{CYAN}" opacity=".55"><animateTransform attributeName="transform" type="translate" {glitch}/>{name}</text>
  <text x="{cx}" y="150" fill="#FF5FA2" opacity=".45" transform="translate(2 0)"><animateTransform attributeName="transform" type="translate" values="2 0;2 0;5 0;-4 0;2 0;2 0" keyTimes="0;.86;.88;.9;.92;1" dur="8s" repeatCount="indefinite"/>{name}</text>
  <text x="{cx}" y="150" fill="url(#namefill)">{name}</text>
  <g clip-path="url(#slice)" opacity="0"><text x="{cx + 10}" y="150" fill="{CYAN}">{name}</text>
    <animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;.86;.89;.92;1" dur="8s" repeatCount="indefinite"/></g>
</g>
<text x="{cx}" y="204" text-anchor="middle" class="mono" font-size="22" font-weight="700" letter-spacing="9" fill="{CYAN}"
      stroke="{BG2}" stroke-width="5" paint-order="stroke" filter="url(#glow)">◆ {title} ◆</text>
<text x="{cx}" y="236" text-anchor="middle" class="mono" font-size="14" letter-spacing="2" fill="{TEXT}"
      stroke="{BG2}" stroke-width="4" paint-order="stroke" opacity=".85">{sub}</text>"""
    return svg(W, h, body, f'{P["name"]} — {P["title"]}')


# ------------------------------------------------------------------------ divider
def divider():
    h = 34
    return svg(W, h, f"""<defs>
<linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="{PURPLE}" stop-opacity="0"/><stop offset=".3" stop-color="{PURPLE}"/><stop offset=".5" stop-color="{CYAN}"/><stop offset=".7" stop-color="{PURPLE}"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></linearGradient>
<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-20%" y="-300%" width="140%" height="700%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<line x1="40" x2="{W - 40}" y1="17" y2="17" stroke="url(#ln)" stroke-width="1.6" filter="url(#glow)"/>
<rect x="-200" y="16" width="180" height="2" fill="url(#sw)">
  <animate attributeName="x" values="-200;{W + 20}" dur="7s" repeatCount="indefinite"/>
</rect>
<g transform="translate({W / 2} 17)">
  <rect x="-7" y="-7" width="14" height="14" transform="rotate(45)" fill="{BG2}" stroke="{GOLD}" stroke-width="1.6" filter="url(#glow)">
    <animate attributeName="stroke-opacity" values=".4;1;.4" dur="4s" repeatCount="indefinite"/>
  </rect>
  <circle r="2.4" fill="{GOLD}"/>
</g>
<circle cx="{W / 2 - 70}" cy="17" r="2" fill="{CYAN}"/><circle cx="{W / 2 + 70}" cy="17" r="2" fill="{CYAN}"/>""",
               "divider")


# -------------------------------------------------------------------------- about
def about():
    lines, y, out = [], 140, []
    for para in P["about"]:
        lines += textwrap.wrap(para, 66) + [""]
    lines = lines[:-1]
    t = 0.0
    for i, line in enumerate(lines):
        if not line:
            y += 12
            continue
        dur = max(0.6, len(line) * 0.035)
        out.append(f"""<clipPath id="ln{i}"><rect x="36" y="{y - 18}" height="26" width="0">
  <animate attributeName="width" values="0;{tw(line, 16) + 20:.0f}" begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>
<text x="40" y="{y}" class="mono" font-size="16" fill="{TEXT}" clip-path="url(#ln{i})">{x(line)}</text>""")
        t += dur + 0.15
        y += 28
    content_h = y
    px = 800
    side = [f'<rect x="{px - 24}" y="124" width="1" height="{max(content_h, 330) - 150}" fill="{PURPLE}" opacity=".35"/>',
            f'<text x="{px}" y="140" class="mono" font-size="12" letter-spacing="3" fill="{GOLD}">ROLE</text>',
            f'<text x="{px}" y="166" class="sans" font-size="20" fill="{CYAN}">{x(P["title"])}</text>',
            f'<text x="{px}" y="208" class="mono" font-size="12" letter-spacing="3" fill="{GOLD}">WORKING ON</text>']
    fy = 236
    for j, f in enumerate(P["focus"]):
        side.append(f'<g><circle cx="{px + 5}" cy="{fy - 5}" r="4" fill="{PURPLE}" filter="url(#glow)">'
                    f'<animate attributeName="opacity" values=".35;1;.35" dur="4s" begin="{j}s" repeatCount="indefinite"/></circle>'
                    f'<text x="{px + 20}" y="{fy}" class="mono" font-size="14" fill="{TEXT}">{x(f)}</text></g>')
        fy += 28
    h = max(content_h, fy) + 24
    return card(h, "about me", "About Me", "\n".join(out + side))


# ---------------------------------------------------------------- automation demo
def keyframes(points):
    """points: [(t, v)] -> (values, keyTimes) with strictly increasing times in [0,1]."""
    pts, last = [], -1.0
    for t, v in points:
        t = min(max(t, 0.0), 1.0)
        if t <= last:
            t = last + 0.0001
        if t > 1:
            continue
        pts.append((t, v))
        last = t
    pts[0] = (0.0, pts[0][1])
    if pts[-1][0] < 1:
        pts.append((1.0, pts[-1][1]))
    return ";".join(str(v) for _, v in pts), ";".join(f"{t:.4f}" for t, _ in pts)


def anim(attr, points, dur):
    v, k = keyframes(points)
    return f'<animate attributeName="{attr}" values="{v}" keyTimes="{k}" dur="{dur}s" repeatCount="indefinite"/>'


def machine():
    steps = [
        ("Webhook", "invoice.pdf arrives", "n8n"),
        ("Extract", "PDF → plain text", "doc"),
        ("OpenAI", "AI reads & parses", "openai"),
        ("Validate", "is it an invoice?", "check"),
        ("Sheets + DB", "row saved", "googlesheets"),
        ("Gmail", "reply goes out", "gmail"),
    ]
    logs = [
        '> POST /webhook/invoice   file: "INV-0042.pdf"',
        "> extract-from-file: PDF text extracted",
        '> openai: { vendor: "Acme Supplies", total: "$1,240.00", due: "2026-12-05" }',
        "> if: total > 0 ✓   vendor found ✓   → valid invoice",
        '> google sheets: row appended   ·   supabase: record upserted',
        '> gmail: "Invoice INV-0042 received" → accounts@example.com',
        "✓ workflow complete — looping the simulation…",
    ]
    n, slot = len(steps), 2.0
    T = slot * (n + 1)
    e = 0.012
    nw, nh, top = 150, 118, 136
    gap = (W - 72 - n * nw) / (n - 1)
    xs = [36 + i * (nw + gap) for i in range(n)]
    out = []
    # simulation badge
    badge = "SIMULATION · SAMPLE DATA"
    bw = tw(badge, 12) + len(badge) * 1.5 + 44
    out.append(f'<g transform="translate({W - 36 - bw:.0f} 30)"><rect width="{bw:.0f}" height="30" rx="15" fill="{GOLD}" fill-opacity=".08" '
               f'stroke="{GOLD}" stroke-opacity=".8"/><circle cx="16" cy="15" r="4" fill="{GOLD}">'
               f'<animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>'
               f'<text x="28" y="19.5" class="mono" font-size="12" letter-spacing="1.5" fill="{GOLD}">{badge}</text></g>')
    out.append(f'<text x="{W - 36}" y="84" text-anchor="end" class="mono" font-size="12" fill="{MUTED}">'
               f'modelled on my n8n “Invoice Agent” workflow</text>')
    # connectors
    cy = top + nh / 2
    for i in range(n - 1):
        x1, x2 = xs[i] + nw + 4, xs[i + 1] - 4
        a = (i + 0.72) * slot / T
        b = (i + 1.0) * slot / T
        out.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{cy}" y2="{cy}" stroke="{PURPLE}" stroke-opacity=".55" stroke-width="2" '
                   f'stroke-dasharray="5 7"><animate attributeName="stroke-dashoffset" values="24;0" dur="1.6s" repeatCount="indefinite"/></line>')
        out.append(f'<circle cy="{cy}" r="5" fill="{CYAN}" filter="url(#glow)" cx="{x1:.1f}">'
                   + anim("cx", [(0, round(x1, 1)), (a, round(x1, 1)), (b, round(x2, 1)), (b + e, round(x1, 1))], T)
                   + anim("opacity", [(0, 0), (a - e, 0), (a, 1), (b, 1), (b + e, 0)], T) + "</circle>")
    # nodes
    for i, (name, sub, ic) in enumerate(steps):
        nx = xs[i]
        a, b = i * slot / T, (i + 1) * slot / T
        end = n * slot / T
        mid = nx + nw / 2
        if ic == "doc":
            glyph = (f'<g transform="translate({mid - 11} {top + 22})" fill="none" stroke="{TEXT}" stroke-width="1.8" stroke-linejoin="round">'
                     f'<path d="M0 0h14l8 8v20H0z"/><path d="M14 0v8h8M5 15h12M5 20h12"/></g>')
        elif ic == "check":
            glyph = (f'<g transform="translate({mid} {top + 36})" fill="none" stroke="{TEXT}" stroke-width="1.8">'
                     f'<rect x="-11" y="-11" width="22" height="22" transform="rotate(45)"/><path d="M-6 0l4 4 8-8"/></g>')
        else:
            col = {"n8n": "#EA4B71", "openai": "#FFFFFF", "googlesheets": "#34A853", "gmail": "#EA4335"}[ic]
            glyph = icon(ic, mid, top + 36, 28, col)
        out.append(f"""<g>
<rect x="{nx:.1f}" y="{top}" width="{nw}" height="{nh}" rx="14" fill="{PANEL}" stroke="{PURPLE}" stroke-opacity=".35"/>
<rect x="{nx:.1f}" y="{top}" width="{nw}" height="{nh}" rx="14" fill="{PURPLE}" fill-opacity=".06" stroke="{PURPLE}" stroke-opacity=".9" opacity="0">
  {anim("opacity", [(0, 0), (b, 0), (b + e, 1), (end, 1), (end + e * 3, 0)], T)}</rect>
<rect x="{nx:.1f}" y="{top}" width="{nw}" height="{nh}" rx="14" fill="{CYAN}" fill-opacity=".10" stroke="{CYAN}" stroke-width="2" filter="url(#glow)" opacity="0">
  {anim("opacity", [(0, 0), (a, 0), (a + e * 2, 1), (b, 1), (b + e * 2, 0)], T)}</rect>
<text x="{nx + 12:.1f}" y="{top + 20}" class="mono" font-size="11" fill="{GOLD}">0{i + 1}</text>
{glyph}
<text x="{mid:.1f}" y="{top + 82}" text-anchor="middle" class="sans" font-size="17" fill="{TEXT}">{x(name)}</text>
<text x="{mid:.1f}" y="{top + 102}" text-anchor="middle" class="mono" font-size="11" fill="{MUTED}">{x(sub)}</text>
</g>""")
    # console
    ctop = top + nh + 34
    out.append(f'<rect x="36" y="{ctop}" width="{W - 72}" height="62" rx="12" fill="#0A0D16" stroke="{PURPLE}" stroke-opacity=".3"/>')
    out.append(f'<text x="54" y="{ctop + 22}" class="mono" font-size="11" letter-spacing="2" fill="{MUTED}">EXECUTION LOG · sample data</text>')
    for j, line in enumerate(logs):
        a, b = j * slot / T, (j + 1) * slot / T
        col = CYAN if j == len(logs) - 1 else TEXT
        out.append(f'<text x="54" y="{ctop + 46}" class="mono" font-size="14" fill="{col}" opacity="0">{x(line)}'
                   + anim("opacity", [(0, 0), (a, 0), (a + e, 1), (b - e, 1), (b, 0)], T) + "</text>")
    out.append(f'<rect x="36" y="{ctop + 60}" width="0" height="2" rx="1" fill="{CYAN}" filter="url(#glow)">'
               f'<animate attributeName="width" values="0;{W - 72}" dur="{T}s" repeatCount="indefinite"/></rect>')
    return card(ctop + 96, "live demo", "The Automation Machine", "\n".join(out))


# ------------------------------------------------------------------------ project
def chip(cx, cy, label, color, size=13, delay=0.0, pulse=True):
    w = tw(label, size) + 26
    anim_ = (f'<animate attributeName="stroke-opacity" values=".45;1;.45" dur="5s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
             if pulse else "")
    return w, (f'<g><rect x="{cx:.1f}" y="{cy}" width="{w:.1f}" height="32" rx="16" fill="{color}" fill-opacity=".08" '
               f'stroke="{color}" stroke-opacity=".7" stroke-width="1.2">{anim_}</rect>'
               f'<text x="{cx + w / 2:.1f}" y="{cy + 21}" text-anchor="middle" class="mono" font-size="{size}" fill="{TEXT}">{x(label)}</text></g>')


def project():
    pr = P["project"]
    out = [f'<text x="36" y="140" class="sans" font-size="26" fill="{CYAN}" filter="url(#glow)">{x(pr["name"])}</text>']
    y = 174
    for line in textwrap.wrap(pr["description"], 70):
        out.append(f'<text x="36" y="{y}" class="mono" font-size="15" fill="{TEXT}">{x(line)}</text>')
        y += 24
    y += 12
    cx = 36
    for i, wf in enumerate(pr["workflows"]):
        w = tw(wf, 12) + 26
        if cx + w > 860:
            cx, y = 36, y + 42
        _, c = chip(cx, y, wf, PURPLE, 12, i * 0.8)
        out.append(c)
        cx += w + 10
    y += 66
    url = pr["url"].replace("https://", "")
    out.append(f'<text x="36" y="{y}" class="mono" font-size="14" fill="{GOLD}">→ {x(url)}</text>')
    # decorative mini flow on the right
    gx, gy = 1000, 200
    nodes = [(gx - 70, gy - 40), (gx + 60, gy - 60), (gx - 30, gy + 50), (gx + 80, gy + 40)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
    for k, (p, q) in enumerate(edges):
        (x1, y1), (x2, y2) = nodes[p], nodes[q]
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{PURPLE}" stroke-opacity=".6" stroke-width="1.6" stroke-dasharray="4 6">'
                   f'<animate attributeName="stroke-dashoffset" values="20;0" dur="1.8s" repeatCount="indefinite"/></line>')
        out.append(f'<circle r="3.5" fill="{CYAN}" filter="url(#glow)"><animate attributeName="cx" values="{x1};{x2}" dur="3s" begin="{k * .7}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="cy" values="{y1};{y2}" dur="3s" begin="{k * .7}s" repeatCount="indefinite"/></circle>')
    for k, (nx, ny) in enumerate(nodes):
        out.append(f'<rect x="{nx - 22}" y="{ny - 22}" width="44" height="44" rx="12" fill="{PANEL}" stroke="{CYAN if k % 3 == 0 else PURPLE}" stroke-width="1.4">'
                   f'<animate attributeName="stroke-opacity" values=".4;1;.4" dur="4s" begin="{k}s" repeatCount="indefinite"/></rect>')
    out.append(icon("n8n", nodes[0][0], nodes[0][1], 24, "#EA4B71"))
    out.append(icon("openai", nodes[1][0], nodes[1][1], 22, "#FFFFFF"))
    out.append(icon("supabase", nodes[2][0], nodes[2][1], 22, "#3FCF8E"))
    out.append(icon("gmail", nodes[3][0], nodes[3][1], 22, "#EA4335"))
    return card(y + 36, "featured project", "Featured Project", "\n".join(out))


# -------------------------------------------------------------------- tech stack
def stack():
    colors = [PURPLE, CYAN, GOLD, "#C39BFF", CYAN, PURPLE]
    out, y, d = [], 136, 0.0
    for gi, (group, items) in enumerate(P["stack"].items()):
        col = colors[gi % len(colors)]
        out.append(f'<text x="36" y="{y + 21}" class="mono" font-size="13" letter-spacing="3" fill="{col}">{x(group.upper())}</text>')
        cx = 200
        for it in items:
            w = tw(it, 14) + 26
            if cx + w > W - 36:
                cx, y = 200, y + 44
            _, c = chip(cx, y, it, col, 14, d)
            out.append(c)
            cx += w + 12
            d = (d + 0.6) % 5
        y += 56
    return card(y + 14, "tech stack", "Tech Stack", "\n".join(out))


# ----------------------------------------------------------------------- toolkit
def toolkit():
    tools = P["toolkit"]
    n = len(tools)
    tw_, th, top, g = 160, 128, 128, 0
    g = (W - 72 - n * tw_) / max(n - 1, 1)
    out = []
    for i, t in enumerate(tools):
        tx = 36 + i * (tw_ + g)
        out.append(f"""<g>
<rect x="{tx:.1f}" y="{top}" width="{tw_}" height="{th}" rx="16" fill="{PANEL}" stroke="{PURPLE}" stroke-opacity=".45">
  <animate attributeName="stroke-opacity" values=".3;.9;.3" dur="6s" begin="{i * 0.8:.1f}s" repeatCount="indefinite"/></rect>
<circle cx="{tx + tw_ / 2:.1f}" cy="{top + 52}" r="30" fill="{t['color']}" opacity=".12" filter="url(#blur8)"/>
{icon(t['icon'], tx + tw_ / 2, top + 52, 44, t['color'])}
<text x="{tx + tw_ / 2:.1f}" y="{top + 108}" text-anchor="middle" class="mono" font-size="13" fill="{TEXT}">{x(t['name'])}</text>
</g>""")
    sweep = f"""<defs><linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset=".5" stop-color="{CYAN}" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g clip-path="url(#cardclip)"><rect x="-260" y="0" width="220" height="{top + th + 60}" fill="url(#sweep)" transform="skewX(-18)">
<animate attributeName="x" values="-300;{W + 300}" dur="8s" repeatCount="indefinite"/></rect></g>"""
    return card(top + th + 40, "automation toolkit", "Automation Toolkit", "\n".join(out) + sweep)


# ------------------------------------------------------------------------ footer
def footer():
    h = 190
    pts, xpos = [], 40
    pattern = [0, 0, 0, -6, 8, -40, 34, -10, 0, 0]
    while xpos < W - 40:
        for v in pattern:
            pts.append(f"{xpos},{132 + v}")
            xpos += 12
    path = "M" + " L".join(pts)
    plen = 3200
    body = f"""{common_defs(f'''<linearGradient id="word" x1="0" x2="1" gradientUnits="objectBoundingBox">
<stop offset="0" stop-color="{PURPLE}"/><stop offset=".5" stop-color="{CYAN}"/><stop offset="1" stop-color="{PURPLE}"/>
<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="9s" repeatCount="indefinite"/></linearGradient>''')}
<clipPath id="cardclip"><rect x="2" y="2" width="{W - 4}" height="{h - 4}" rx="18"/></clipPath>
<g clip-path="url(#cardclip)"><rect width="{W}" height="{h}" fill="url(#bg)"/><rect width="{W}" height="{h}" fill="url(#grid)"/><rect width="{W}" height="{h}" fill="url(#scan)"/></g>
<rect x="2" y="2" width="{W - 4}" height="{h - 4}" rx="18" fill="none" stroke="url(#edge)" stroke-width="1.2"/>
<path d="{path}" fill="none" stroke="{PURPLE}" stroke-opacity=".25" stroke-width="1.5"/>
<path d="{path}" fill="none" stroke="{CYAN}" stroke-width="2" filter="url(#glow)" stroke-dasharray="160 {plen}">
  <animate attributeName="stroke-dashoffset" values="160;-{plen}" dur="10s" repeatCount="indefinite"/></path>
<text x="{W / 2}" y="78" text-anchor="middle" class="sans" font-size="44" letter-spacing="12" fill="{PURPLE}" filter="url(#blur8)" opacity=".7">BUILT IN PUBLIC
  <animate attributeName="opacity" values=".4;.85;.4" dur="6s" repeatCount="indefinite"/></text>
<text x="{W / 2}" y="78" text-anchor="middle" class="sans" font-size="44" letter-spacing="12" fill="url(#word)">BUILT IN PUBLIC</text>
<text x="{W / 2}" y="174" text-anchor="middle" class="mono" font-size="13" letter-spacing="2" fill="{MUTED}">
  <tspan fill="{GOLD}">◆</tspan>  {x(P["name"])}  ·  learning &amp; building  ·  github.com/{x(P["username"])}  <tspan fill="{GOLD}">◆</tspan></text>"""
    return svg(W, h, body, "Built in public")


# ------------------------------------------------------------------------ README
def readme():
    u, repo, br, v = P["username"], P["repo"], P["branch"], P["version"]
    raw = f"https://raw.githubusercontent.com/{u}/{repo}/{br}/assets"

    def img(path, alt, width="100%"):
        return f'<img src="{raw}/{path}?v={v}" width="{width}" alt="{x(alt)}"/>'

    div = img("divider.svg", "divider")
    lines = ";".join(urllib.parse.quote(l, safe="") for l in P["typing_lines"])
    typing = ("https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=3200&pause=1000"
              f"&color=8F6BFF&center=true&vCenter=true&width=760&lines={lines}")
    sh = "style=for-the-badge&labelColor=10131F"
    L, pr = P["links"], P["project"]
    badges = []
    if L.get("website"):
        badges.append(f'<a href="{L["website"]}"><img src="https://img.shields.io/badge/Website-8F6BFF?{sh}&logo=googlechrome&logoColor=8F6BFF"/></a>')
    if L.get("linkedin"):
        badges.append(f'<a href="{L["linkedin"]}"><img src="https://img.shields.io/badge/LinkedIn-5AE0FF?{sh}&logo=linkedin&logoColor=5AE0FF"/></a>')
    if L.get("email"):
        badges.append(f'<a href="mailto:{L["email"]}"><img src="https://img.shields.io/badge/Email-F5B800?{sh}&logo=gmail&logoColor=F5B800"/></a>')
    badges.append(f'<a href="https://github.com/{u}"><img src="https://img.shields.io/badge/GitHub-8F6BFF?{sh}&logo=github&logoColor=8F6BFF"/></a>')
    badges.append(f'<a href="{pr["url"]}"><img src="https://img.shields.io/badge/{urllib.parse.quote(pr["name"].replace("-", "--"))}-5AE0FF?{sh}&logo=n8n&logoColor=5AE0FF"/></a>')
    counters = [
        f'<img src="https://komarev.com/ghpvc/?username={u}&color=8f6bff&style=for-the-badge&label=PROFILE+VIEWS"/>',
        f'<a href="https://github.com/{u}?tab=followers"><img src="https://img.shields.io/github/followers/{u}?{sh}&color=5AE0FF&logo=github&label=FOLLOWERS"/></a>',
        f'<a href="https://github.com/{u}?tab=repositories"><img src="https://img.shields.io/github/stars/{u}?{sh}&color=F5B800&logo=github&label=STARS"/></a>',
    ]
    gen = "generated"
    md = f"""<!-- Generated by scripts/build_cards.py from profile.json — edit profile.json, not this file. -->
<div align="center">

{img("hero.svg", P["name"] + " — " + P["title"])}

<a href="https://github.com/{u}"><img src="{typing}" alt="Typing SVG"/></a>

{" ".join(badges)}

{" ".join(counters)}

{div}

{img("about.svg", "About me")}

{div}

{img("machine.svg", "The Automation Machine — simulation with sample data")}

{div}

<a href="{pr["url"]}">{img("project.svg", "Featured project: " + pr["name"])}</a>

<code>{x(pr["command"])}</code>
<br/><sub>{x(pr.get("command_note", ""))}</sub>

{div}

{img("stack.svg", "Tech stack")}

{div}

{img("toolkit.svg", "Automation toolkit")}

{div}

{img(f"{gen}/contributions.svg", "Contributions")}

{img(f"{gen}/stats.svg", "GitHub stats", "49%")} {img(f"{gen}/languages.svg", "Top languages", "49%")}

{img(f"{gen}/activity.svg", "Activity graph")}

{img(f"{gen}/snake.svg", "Contribution snake")}

<sub>Dashboard refreshed daily from live GitHub data by a GitHub Action.</sub>

{div}

<i>“{x(P["quote"])}”</i>

{img("footer.svg", "Built in public")}

</div>
"""
    return md


def main():
    ASSETS.mkdir(exist_ok=True)
    out = {"hero.svg": hero(), "divider.svg": divider(), "about.svg": about(), "machine.svg": machine(),
           "project.svg": project(), "stack.svg": stack(), "toolkit.svg": toolkit(), "footer.svg": footer()}
    for name, content in out.items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    (ROOT / "README.md").write_text(readme(), encoding="utf-8", newline="\n")
    print("built:", ", ".join(out), "+ README.md")


if __name__ == "__main__":
    main()
