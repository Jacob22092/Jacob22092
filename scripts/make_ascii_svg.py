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

from profile_data import FONT_MONO as FONT, PROMPT

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "jhit-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # jasne (rzadkie) -> ciemne (gęste); spacja czyści tło
W, H = 840, 880  # == stats.svg, żeby kolumny w README się zrównały
PAD = 20
BAR_H = 30  # pasek tytułu
FOOT_H = 30  # pasek z promptem na dole
COLS = 116
BG_CUTOFF = 48  # 0-255; jaśniejsze piksele źródła traktuj jako tło
CHAR_ASPECT = 0.55  # szerokość / wysokość znaku monospace
CELL_W = (W - 2 * PAD) / COLS
CELL_H = CELL_W / CHAR_ASPECT
FONT_SIZE = CELL_W / 0.6
BG, BG_TOP, FRAME = "#0d1117", "#111722", "#30363d"
FG = "#c9d1d9"
MUTED = "#7d8590"
CURSOR = "#39d353"
WHOAMI = "Jakub Hyziak"
ROW_DELAY = 0.045  # s między startami kolejnych wierszy
ROW_DUR = 0.4  # s na „wydrukowanie” pełnego wiersza


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
    area_top, area_bottom = BAR_H + 8, H - FOOT_H - 8
    top = area_top + max(0.0, (area_bottom - area_top - len(lines) * CELL_H) / 2)
    inner_w = COLS * CELL_W
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="Logo Jakub Hyziak IT w ASCII">',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{H - FOOT_H}" x2="{W}" y2="{H - FOOT_H}" stroke="{FRAME}"/>',
        *[f'<circle cx="{PAD + i * 16}" cy="{BAR_H / 2}" r="5" fill="{c}"/>'
          for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])],
        f'<text x="{W / 2}" y="{BAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
        f"{PROMPT}: ~$ ./portrait.sh</text>",
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG}"/></linearGradient>',
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
    out.append(f'<g font-size="{FONT_SIZE:.2f}" fill="{FG}">')
    out.extend(body)
    out.append("</g>")
    # prompt na dole: pojawia się, gdy portret się dopisze; kursor mruga kilka razy
    done = 0 if static else len(lines) * ROW_DELAY + ROW_DUR
    prompt = f"{PROMPT}:~$ whoami "
    fy = H - FOOT_H / 2 + 4
    reveal = "" if static else f'<set attributeName="opacity" to="1" begin="{done:.2f}s"/>'
    out.append(f'<g opacity="{1 if static else 0}">{reveal}'
               f'<text x="{PAD}" y="{fy}" font-size="12" fill="{MUTED}" xml:space="preserve">{prompt}'
               f'<tspan fill="{FG}">{escape(WHOAMI)}</tspan></text>'
               f'<rect x="{PAD + (len(prompt) + len(WHOAMI) + 1) * 7.2:.1f}" y="{fy - 10}" width="7" height="13" '
               f'fill="{CURSOR}">'
               + ("" if static else f'<animate attributeName="opacity" values="1;0" dur="1s" begin="{done:.2f}s" '
                  f'repeatCount="8" calcMode="discrete" fill="freeze"/>')
               + "</rect></g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    lines = to_grid(Image.open(src))
    OUT.write_text(render(lines, static=os.environ.get("STATIC") == "1"), encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({COLS}x{len(lines)} znaków)")


if __name__ == "__main__":
    main()
