"""Zamienia `source-prepped.png` w monochromatyczny ASCII-art, który „pisze się” sam.

Każdy wiersz jest odsłaniany od lewej do prawej przez animowany clipPath
(po krawędzi jedzie mały kursor-blok), wiersze startują kolejno z góry na dół.
Całość drukuje się raz i zamarza — bez pętli. Animacja to SMIL wewnątrz SVG,
więc GitHub ją odtwarza.

    python scripts/make_ascii_svg.py                 # -> jhit-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py        # zamrożona klatka (podgląd)
"""

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "jhit-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # jasne (rzadkie) -> ciemne (gęste); spacja czyści tło
COLS = 72
BG_CUTOFF = 48  # 0-255; jaśniejsze piksele źródła traktuj jako tło
CHAR_ASPECT = 0.55  # szerokość / wysokość znaku monospace
CELL_W = 7.2
CELL_H = CELL_W / CHAR_ASPECT * 0.5 * 2  # = 13.09: kwadratowe piksele obrazu
FONT_SIZE = 12
PAD = 18
MIN_HEIGHT = 533  # = wysokość info-card.svg, żeby kolumny w README się zrównały
BG = "#0d1117"
BORDER = "#30363d"
FG = "#c9d1d9"
CURSOR = "#398E4A"
ROW_DELAY = 0.07  # s między startami kolejnych wierszy
ROW_DUR = 0.45  # s na „wydrukowanie” jednego wiersza
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def to_grid(img: Image.Image) -> list[str]:
    gray = ImageOps.invert(img.convert("L"))
    # Prawie-białe tło (szum, kompresja) -> czysta spacja.
    gray = gray.point(lambda v: 0 if v < BG_CUTOFF else round((v - BG_CUTOFF) * 255 / (255 - BG_CUTOFF)))
    bbox = gray.point(lambda v: 255 if v > 32 else 0).getbbox()
    if bbox:  # przytnij do obiektu z marginesem
        m = int(max(img.size) * 0.03)
        l, t, r, b = bbox
        gray = gray.crop((max(l - m, 0), max(t - m, 0), min(r + m, img.width), min(b + m, img.height)))
    w, h = gray.size
    rows = max(1, round(COLS * (h / w) * CHAR_ASPECT))
    small = np.asarray(gray.resize((COLS, rows), Image.LANCZOS), dtype=float) / 255.0
    idx = np.clip((small * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def render(lines: list[str], static: bool) -> str:
    width = round(COLS * CELL_W + 2 * PAD)
    height = max(MIN_HEIGHT, round(len(lines) * CELL_H + 2 * PAD))
    top = (height - len(lines) * CELL_H) / 2
    inner_w = COLS * CELL_W
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Logo Jakub Hyziak IT w ASCII">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        "<defs>",
    ]
    body = []
    for i, line in enumerate(lines):
        y = top + i * CELL_H
        baseline = y + CELL_H * 0.78
        text = (
            f'<text x="{PAD}" y="{baseline:.2f}" xml:space="preserve" '
            f'textLength="{len(line) * CELL_W:.2f}" lengthAdjust="spacingAndGlyphs">{escape(line)}</text>'
        )
        if static or not line.strip():
            body.append(text)
            continue
        begin = i * ROW_DELAY
        x0 = PAD + (len(line) - len(line.lstrip())) * CELL_W  # pierwszy widoczny znak
        line_w = PAD + len(line) * CELL_W - x0
        dur = max(0.12, ROW_DUR * line_w / inner_w)
        out.append(
            f'<clipPath id="r{i}"><rect x="{x0:.2f}" y="{y:.2f}" width="0" height="{CELL_H + 1:.2f}">'
            f'<animate attributeName="width" from="0" to="{line_w:.2f}" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        body.append(
            f'<rect x="{x0:.2f}" y="{y + 1:.2f}" width="{CELL_W:.1f}" height="{CELL_H - 2:.2f}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{x0:.2f}" to="{x0 + line_w:.2f}" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.2f}s"/></rect>'
        )
    out.append("</defs>")
    out.append(f'<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{FG}">')
    out.extend(body)
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    lines = to_grid(Image.open(src))
    OUT.write_text(render(lines, static=os.environ.get("STATIC") == "1"), encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({COLS}x{len(lines)} znaków)")


if __name__ == "__main__":
    main()
