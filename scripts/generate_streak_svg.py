#!/usr/bin/env python3
"""
generate_streak_svg.py  –  Animated GitHub contribution heat-map.

Fetches the public contributions graph from github.com/<username> and
renders it as an SVG with pop-and-flash animation.

Usage:
    python scripts/generate_streak_svg.py <github_username> <output.svg>
"""
import sys, math, re, datetime, pathlib
import requests
from bs4 import BeautifulSoup

# ── CONFIG ──────────────────────────────────────────────────────────────
CELL_SIZE   = 11       # contribution square size (px)
CELL_GAP    = 3        # gap between squares (px)
CORNER_R    = 2        # square corner radius (px)
TOP_MARGIN  = 24       # space for month labels
LEFT_MARGIN = 32       # space for day labels
FONT        = "'Segoe UI', Helvetica, Arial, sans-serif"
FONT_SIZE   = 10

# Monochrome palette (GitHub dark-ish)
COLORS = {
    0: "#161b22",   # empty
    1: "#0d4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}
LABEL_COLOR  = "#8b949e"
BORDER_COLOR = "#21262d"
BG_COLOR     = "#0d1117"
TEXT_COLOR   = "#c9d1d9"

# Animation
POP_DUR      = 0.18    # duration of pop scale animation (s)
FLASH_DUR    = 0.35    # duration of flash opacity animation (s)
STAGGER      = 0.004   # seconds between each cell's animation start
# ── END CONFIG ──────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "Mozilla/5.0 (GitHub Profile README generator)"}

def fetch_contributions(username: str):
    url = f"https://github.com/users/{username}/contributions"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[warn] Could not fetch live data: {e}. Using synthetic fallback.")
        return synthetic_data()

    soup = BeautifulSoup(resp.text, "html.parser")
    days = []
    for td in soup.find_all("td", {"class": re.compile(r"ContributionCalendar-day")}):
        date_str = td.get("data-date", "")
        count    = int(td.get("data-count", 0) or 0)
        level    = int(td.get("data-level", 0) or 0)
        if date_str:
            days.append({"date": date_str, "count": count, "level": level})
    if not days:
        print("[warn] Parsed 0 days from GitHub. Using synthetic fallback.")
        return synthetic_data()
    return days

def synthetic_data():
    """Generate ~1 year of fake contribution data for offline / fallback use."""
    import random
    today = datetime.date.today()
    start = today - datetime.timedelta(weeks=53)
    days  = []
    for i in range(371):
        d = start + datetime.timedelta(days=i)
        if d > today:
            break
        c = max(0, int(random.gauss(2, 2.5)))
        lv = 0 if c == 0 else min(4, 1 + c // 3)
        days.append({"date": str(d), "count": c, "level": lv})
    return days

def arrange_weeks(days):
    """Return list-of-weeks, each week a list of day dicts (Mon–Sun, 7 items)."""
    if not days:
        return []
    # find first Sunday on-or-before first day
    first = datetime.date.fromisoformat(days[0]["date"])
    offset = first.weekday() + 1   # days since Sunday (Mon=0 → offset 1)
    if offset == 7:
        offset = 0
    start_sunday = first - datetime.timedelta(days=offset)

    day_map = {d["date"]: d for d in days}
    weeks, week = [], []
    cur = start_sunday
    while True:
        ds = str(cur)
        week.append(day_map.get(ds, {"date": ds, "count": 0, "level": 0}))
        if cur.weekday() == 5:   # Saturday → end of week
            weeks.append(week)
            week = []
            # check if past last day
            if cur > datetime.date.fromisoformat(days[-1]["date"]):
                break
        cur += datetime.timedelta(days=1)
    if week:
        weeks.append(week)
    return weeks

def build_svg(username: str, days, out_path: pathlib.Path):
    weeks = arrange_weeks(days)
    nw    = len(weeks)
    step  = CELL_SIZE + CELL_GAP

    W = LEFT_MARGIN + nw * step + 10
    H = TOP_MARGIN  + 7 * step  + 20

    total_contribs = sum(d["count"] for d in days)

    idx = 0  # animation index

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'  <rect width="100%" height="100%" fill="{BG_COLOR}" rx="8"/>',
        # Title
        f'  <text x="{LEFT_MARGIN}" y="15" font-family="{FONT}" font-size="{FONT_SIZE}" '
        f'fill="{TEXT_COLOR}" font-weight="600">'
        f'{total_contribs:,} contributions – {username}</text>',
        f'  <g>',
    ]

    # Month labels
    prev_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            d = datetime.date.fromisoformat(day["date"])
            if d.day <= 7 and d.month != prev_month:
                x = LEFT_MARGIN + wi * step
                lines.append(
                    f'  <text x="{x}" y="{TOP_MARGIN - 4}" font-family="{FONT}" '
                    f'font-size="9" fill="{LABEL_COLOR}">'
                    f'{d.strftime("%b")}</text>'
                )
                prev_month = d.month

    # Day labels (Mon Wed Fri)
    for di, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = TOP_MARGIN + di * step + CELL_SIZE * 0.75
        lines.append(
            f'  <text x="{LEFT_MARGIN - 4}" y="{y:.1f}" font-family="{FONT}" '
            f'font-size="9" fill="{LABEL_COLOR}" text-anchor="end">{label}</text>'
        )

    # Cells
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_MARGIN + wi * step
            y = TOP_MARGIN  + di * step
            color = COLORS[day["level"]]
            begin = idx * STAGGER

            cell = (
                f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CORNER_R}" fill="{color}" stroke="{BORDER_COLOR}" '
                f'stroke-width="0.5" transform-origin="{x + CELL_SIZE/2} {y + CELL_SIZE/2}">'
            )
            if day["level"] > 0:
                cell += (
                    f'<animateTransform attributeName="transform" type="scale" '
                    f'values="0;1.3;1" dur="{POP_DUR}s" begin="{begin:.3f}s" fill="freeze" calcMode="spline" '
                    f'keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>'
                    f'<animate attributeName="opacity" values="0;1;0.7;1" dur="{FLASH_DUR}s" '
                    f'begin="{begin:.3f}s" fill="freeze"/>'
                )
            else:
                cell += (
                    f'<animateTransform attributeName="transform" type="scale" '
                    f'values="0;1" dur="{POP_DUR}s" begin="{begin:.3f}s" fill="freeze"/>'
                )
            cell += '</rect>'

            # Tooltip
            tooltip = f'<title>{day["date"]}: {day["count"]} contributions</title>'
            lines.append(f'  <g>{cell}{tooltip}</g>')
            idx += 1

    lines += ['  </g>', '</svg>']
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[streak] {len(days)} days  →  {out_path}")

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: generate_streak_svg.py <github_username> <output.svg>")
    username = sys.argv[1]
    out_path = pathlib.Path(sys.argv[2])
    print(f"[streak] Fetching contributions for {username} …")
    days = fetch_contributions(username)
    build_svg(username, days, out_path)

if __name__ == "__main__":
    main()
