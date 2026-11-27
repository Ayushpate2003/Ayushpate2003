#!/usr/bin/env python3
"""
make_ascii_svg.py  –  Monochrome ASCII-art portrait that types itself in.

Reads  : source-prepped.png  (512×512 RGBA, transparent bg)
Writes : avi-ascii.svg

Preview final frame (no animation):
    STATIC=1 python scripts/make_ascii_svg.py
"""
import os, sys, pathlib, numpy as np
from PIL import Image, ImageEnhance

# ── CONFIG ──────────────────────────────────────────────────────────────
INPUT        = "source-prepped.png"
OUTPUT       = "avi-ascii.svg"

COLS         = 120         # character columns
FONT_W       = 4.2         # monospace glyph width  (px in SVG)
FONT_H       = 7.8         # monospace glyph height (px in SVG)
FONT_SIZE    = 7.0         # CSS font-size (px)
FONT_FAMILY  = "'Courier New', Courier, monospace"

CONTRAST     = 1.85        # PIL contrast multiplier  (1.0 = off)
GAMMA        = 0.82        # pixel gamma (<1.0 = more midtone detail in face)
WHITE_FLOOR  = 15          # luminance below this → treat as bg (skip char)
FG_COLOR     = "#c9d1d9"   # GitHub dark text colour
BG_COLOR     = "none"      # transparent

# Animation
STATIC       = os.environ.get("STATIC", "0") == "1"
CHAR_DELAY   = 0.004       # seconds between characters typing in
# ── END CONFIG ──────────────────────────────────────────────────────────

ASCII_RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

def luminance(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def gamma_lut(pixels: np.ndarray, g: float) -> np.ndarray:
    lut = ((np.arange(256) / 255.0) ** (1.0 / g) * 255).astype(np.uint8)
    return lut[pixels]

def img_to_ascii(path: str):
    img = Image.open(path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img_rgb = Image.new("RGB", img.size, (0, 0, 0))
    img_rgb.paste(img.convert("RGB"), mask=img.split()[3])

    # contrast boost
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(CONTRAST)

    rows = int(COLS * (FONT_W / FONT_H) * (img.height / img.width))
    img_small = img_rgb.resize((COLS, rows), Image.LANCZOS)
    alpha_small = img.split()[3].resize((COLS, rows), Image.LANCZOS)

    pix  = np.array(img_small)
    alph = np.array(alpha_small)

    if GAMMA != 1.0:
        pix = gamma_lut(pix, GAMMA)

    lum = luminance(pix)
    result = []
    for r in range(rows):
        row_chars = []
        for c in range(COLS):
            if alph[r, c] < 30:          # transparent → skip
                row_chars.append(" ")
                continue
            l = lum[r, c]
            if l < WHITE_FLOOR:          # very dark → skip
                row_chars.append(" ")
                continue
            idx = int(l / 255.0 * (len(ASCII_RAMP) - 1))
            row_chars.append(ASCII_RAMP[idx])
        result.append(row_chars)
    return result

def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def build_svg(chars):
    rows = len(chars)
    cols = max(len(r) for r in chars)
    W = cols * FONT_W
    H = rows * FONT_H

    all_chars = [(r, c, ch)
                 for r, row in enumerate(chars)
                 for c, ch in enumerate(row)
                 if ch.strip()]
    n = len(all_chars)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">',
        f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>',
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}px" fill="{FG_COLOR}" '
        f'xml:space="preserve" letter-spacing="0">',
    ]

    for idx, (r, c, ch) in enumerate(all_chars):
        x = c * FONT_W
        y = r * FONT_H + FONT_H * 0.85   # baseline

        if STATIC:
            lines.append(f'  <text x="{x:.1f}" y="{y:.1f}">{xml_escape(ch)}</text>')
        else:
            delay = idx * CHAR_DELAY
            lines.append(
                f'  <text x="{x:.1f}" y="{y:.1f}" opacity="0">'
                f'{xml_escape(ch)}'
                f'<animate attributeName="opacity" values="0;1" dur="0.05s" '
                f'begin="{delay:.3f}s" fill="freeze"/>'
                f'</text>'
            )

    lines += ["</g>", "</svg>"]
    return "\n".join(lines)

def main():
    base = pathlib.Path(__file__).parent.parent
    inp  = base / INPUT
    out  = base / OUTPUT
    if not inp.exists():
        sys.exit(f"[error] {inp} not found. Run prep_photo.py first.")
    print(f"[ascii] Processing {inp} …  (STATIC={STATIC})")
    chars = img_to_ascii(str(inp))
    svg = build_svg(chars)
    out.write_text(svg, encoding="utf-8")
    rows = len(chars)
    H = rows * FONT_H
    print(f"[ascii] {len(chars)} rows × {max(len(r) for r in chars)} cols  →  height ≈ {H:.0f}px")
    print(f"[ascii] Saved → {out}")

if __name__ == "__main__":
    main()
