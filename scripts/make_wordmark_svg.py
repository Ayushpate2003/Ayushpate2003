#!/usr/bin/env python3
"""
make_wordmark_svg.py  –  3-D block-letter ASCII wordmark.

Usage:
    python scripts/make_wordmark_svg.py --mode rock --out wordmark.svg
"""
import argparse, pathlib, math, textwrap

# ── CONFIG ──────────────────────────────────────────────────────────────
TEXT         = "AYUSH"       # ← wordmark text

FONT_SIZE    = 20            # monospace font size (pt)
FONT_W       = 12.0          # glyph width  (px)
FONT_H       = 22.0          # glyph height (px)
FONT_FAMILY  = "'Courier New', Courier, monospace"

FG_COLOR     = "#c9d1d9"     # face colour
SHADOW_COLOR = "#444c56"     # 3-D depth colour
DEPTH        = 3             # 3-D extrusion depth (chars)
ROW_MARGIN   = 85            # px top/bottom padding to match portrait rendered height (~441px at width=490)
# ── END CONFIG ──────────────────────────────────────────────────────────

# 5×7 pixel font for A-Z 0-9 + space
GLYPHS = {
    'A': [" ### ",
          "#   #",
          "#   #",
          "#####",
          "#   #",
          "#   #",
          "#   #"],
    'Y': ["#   #",
          "#   #",
          " # # ",
          "  #  ",
          "  #  ",
          "  #  ",
          "  #  "],
    'U': ["#   #",
          "#   #",
          "#   #",
          "#   #",
          "#   #",
          "#   #",
          " ### "],
    'S': [" ####",
          "#    ",
          "#    ",
          " ### ",
          "    #",
          "    #",
          "#### "],
    'H': ["#   #",
          "#   #",
          "#   #",
          "#####",
          "#   #",
          "#   #",
          "#   #"],
    ' ': ["     "] * 7,
    # Fallback for unknown characters
    '?': [" ### ",
          "#   #",
          "   # ",
          "  #  ",
          "  #  ",
          "     ",
          "  #  "],
}

def render_text(text: str):
    """Return list-of-rows where each row is a string."""
    glyph_rows = []
    for ch in text.upper():
        g = GLYPHS.get(ch, GLYPHS['?'])
        glyph_rows.append(g)

    rows = []
    for line_idx in range(7):
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
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}pt" xml:space="preserve">',
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
