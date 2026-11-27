#!/usr/bin/env python3
"""
prep_photo.py  –  Remove background + boost local contrast (CLAHE).
Usage:
    python scripts/prep_photo.py <input_image> <output_png>

Outputs a 512×512 RGBA PNG ready for make_ascii_svg.py.
"""
import sys, pathlib, numpy as np
from PIL import Image
import cv2

# ── CONFIG ──────────────────────────────────────────────────────────────
TARGET_SIZE   = (512, 512)   # output canvas size (px)
CLAHE_CLIP    = 2.5          # CLAHE clip limit  (1–8; higher = more contrast)
CLAHE_GRID    = (8, 8)       # CLAHE tile grid size
GAMMA         = 1.0          # pre-CLAHE gamma correction (1.0 = off)
FACE_BRIGHT   = 1.15         # mild luminance boost for face region
# ── END CONFIG ──────────────────────────────────────────────────────────

def gamma_correct(img_rgb: np.ndarray, g: float) -> np.ndarray:
    lut = np.array([((i / 255.0) ** (1.0 / g)) * 255 for i in range(256)],
                   dtype=np.uint8)
    return lut[img_rgb]

def apply_clahe(img_rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_GRID)
    lab[..., 0] = clahe.apply(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

def remove_bg(src: pathlib.Path) -> Image.Image:
    try:
        from rembg import remove
        with open(src, "rb") as f:
            data = f.read()
        out = remove(data)
        return Image.open(__import__("io").BytesIO(out)).convert("RGBA")
    except ImportError:
        print("[warn] rembg not installed; skipping background removal.")
        return Image.open(src).convert("RGBA")

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: prep_photo.py <input> <output.png>")
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])

    print(f"[prep] Loading {src} …")
    img_pil = remove_bg(src)

    # Resize keeping aspect, then centre-paste on square canvas
    img_pil.thumbnail(TARGET_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
    off = ((TARGET_SIZE[0] - img_pil.width) // 2,
           (TARGET_SIZE[1] - img_pil.height) // 2)
    canvas.paste(img_pil, off, mask=img_pil)

    rgb  = np.array(canvas.convert("RGB"))
    alpha = np.array(canvas.split()[3])

    if GAMMA != 1.0:
        rgb = gamma_correct(rgb, GAMMA)

    rgb = apply_clahe(rgb)

    # Mild face-region brightness boost
    rgb = np.clip(rgb.astype(np.float32) * FACE_BRIGHT, 0, 255).astype(np.uint8)

    # Recompose RGBA
    result = Image.fromarray(rgb).convert("RGBA")
    result.putalpha(Image.fromarray(alpha))
    result.save(dst, "PNG")
    print(f"[prep] Saved → {dst}")

if __name__ == "__main__":
    main()
