#!/usr/bin/env python3
"""
make_wordmark_svg.py  –  3-D block-letter ASCII wordmark.

Usage:
    python scripts/make_wordmark_svg.py --mode rock --out wordmark.svg
"""
import argparse, pathlib, math, textwrap

# ── CONFIG ──────────────────────────────────────────────────────────────
TEXT         = "Ayush"       # ← wordmark text

FONT_SIZE    = 18            # monospace font size (px)
FONT_W       = 11.0          # glyph width  (px)
FONT_H       = 20.0          # glyph height (px)
FONT_FAMILY  = "'Courier New', Courier, monospace"

FG_COLOR     = "#e6edf3"     # face colour
SHADOW_COLOR = "#3b434b"     # 3-D depth colour
DEPTH        = 4             # 3-D extrusion depth (layers)
ROW_MARGIN   = 75            # px top/bottom padding to match portrait rendered height (~441px at width=490)
# ── END CONFIG ──────────────────────────────────────────────────────────

# 6×9 pixel font for crisp, bold "Ayush"
GLYPHS = {
    'A': [
        "  ██  ",
        " ████ ",
        "██  ██",
        "██  ██",
        "██████",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
    ],
    'y': [
        "      ",
        "      ",
        "██  ██",
        "██  ██",
        "██  ██",
        " █████",
        "    ██",
        "██  ██",
        " ████ ",
    ],
    'u': [
        "      ",
        "      ",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        " ████ ",
    ],
    's': [
        "      ",
        "      ",
        " █████",
        "██    ",
        " ████ ",
        "    ██",
        "    ██",
        "█████ ",
        "      ",
    ],
    'h': [
        "██    ",
        "██    ",
        "█████ ",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
    ],
    ' ': ["      "] * 9,
    '?': [
        " ████ ",
        "██  ██",
        "   ██ ",
        "  ██  ",
        "  ██  ",
        "      ",
        "  ██  ",
        "      ",
        "      ",
    ],
}

def render_text(text: str):
    """Return list-of-rows where each row is a string."""
    glyph_rows = []
    for ch in text:
        g = GLYPHS.get(ch, GLYPHS.get(ch.upper(), GLYPHS['?']))
        glyph_rows.append(g)

    n_lines = len(glyph_rows[0]) if glyph_rows else 0
    rows = []
    for line_idx in range(n_lines):
        row = ""
        for gi, g in enumerate(glyph_rows):
            row += g[line_idx]
            if gi < len(glyph_rows) - 1:
                row += "  "    # letter spacing
        rows.append(row)
    return rows

def build_svg(rows, mode: str, out_path: pathlib.Path):
    n_cols = max(len(r) for r in rows)
    n_rows = len(rows)

    W = n_cols * FONT_W + DEPTH * FONT_W + 10
    H = n_rows * FONT_H + 2 * ROW_MARGIN + DEPTH * FONT_H + 10

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
        f'viewBox="0 0 {W:.0f} {H:.0f}">',
        '<rect width="100%" height="100%" fill="none"/>',
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}px" xml:space="preserve">',
    ]

    # Draw depth layers first (back to front)
    for d in range(DEPTH, 0, -1):
        alpha = 0.4 + 0.2 * (DEPTH - d) / max(DEPTH - 1, 1)
        for r, row in enumerate(rows):
            y = ROW_MARGIN + (r + d * 0.5) * FONT_H + FONT_H * 0.85
            x_off = d * FONT_W * 0.5
            safe = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(
                f'  <text x="{x_off:.1f}" y="{y:.1f}" '
                f'fill="{SHADOW_COLOR}" opacity="{alpha:.2f}">{safe}</text>'
            )

    # Draw face layer
    if mode == "rock":
        # Rock: pulse animation on each row
        for r, row in enumerate(rows):
            y  = ROW_MARGIN + r * FONT_H + FONT_H * 0.85
            delay = r * 0.08
            safe = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(
                f'  <text x="0" y="{y:.1f}" fill="{FG_COLOR}">'
                f'{safe}'
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0,0; 0,-2; 0,2; 0,0" dur="2.4s" begin="{delay:.2f}s" '
                f'repeatCount="indefinite"/>'
                f'</text>'
            )
    else:
        for r, row in enumerate(rows):
            y = ROW_MARGIN + r * FONT_H + FONT_H * 0.85
            safe = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f'  <text x="0" y="{y:.1f}" fill="{FG_COLOR}">{safe}</text>')

    lines += ["</g>", "</svg>"]
    svg = "\n".join(lines)
    out_path.write_text(svg, encoding="utf-8")
    print(f"[wordmark] Saved → {out_path}  (canvas {W:.0f}×{H:.0f}px)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="rock", choices=["rock", "static"])
    ap.add_argument("--out", default="wordmark.svg")
    args = ap.parse_args()

    rows = render_text(TEXT)
    out  = pathlib.Path(args.out)
    build_svg(rows, args.mode, out)

if __name__ == "__main__":
    main()
