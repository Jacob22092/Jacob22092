"""Ręcznie złożona karta w stylu `neofetch`: pasek tytułu + kolorowe wiersze klucz/wartość.

Każdy wiersz pojawia się z krótkim opóźnieniem (fade + slide), więc panel
„drukuje się” obok ASCII-logo. `STATIC=1` generuje zamrożoną klatkę do podglądu.

    python scripts/make_info_card.py   # -> info-card.svg
"""

import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

USER_HOST = ("jakub", "jhyziak-it")

# (klucz, wartość) — None jako klucz = linia kontynuacji, ("", "") = odstęp
ROWS = [
    ("Firma", "Jakub Hyziak IT · jednoosobowa, bez pośredników"),
    ("Lokalizacja", "Kraków, PL · zdalnie PL/UE · on-site Małopolska"),
    ("Usługi", "Strony WWW · Sieci & VPN · Wsparcie IT · AI"),
    ("", ""),
    ("WWW", "React, Next.js, TypeScript, Tailwind"),
    ("Sieci", "MikroTik, UniFi, WireGuard, IPsec, VLAN"),
    ("Helpdesk", "Windows/Linux/macOS, MDM, backup 3-2-1"),
    ("AI / RAG", "Self-hosted LLM, Qdrant, LangChain"),
    ("", ""),
    ("PageSpeed", "Wydajność 83→98 · Dostępność 84→96"),
    (None, "Sprawdzone metody 100 · SEO 100"),
    ("Opinie", "★ 5.0 Google (10) · ★ 5.0 Oferteo (2)"),
    ("Model", "Fixed-Price lub abonament SLA"),
    (None, "umowa + NDA przed startem · zero vendor lock-in"),
    ("", ""),
    ("WWW", "jhyziak.eu"),
    ("Kontakt", "kontakt@jhyziak.eu · +48 797 589 367"),
]

WIDTH = 554
PAD_X = 24
TOP = 54  # pod paskiem tytułu
LINE_H = 22
MIN_HEIGHT = 533  # = wysokość jhit-ascii.svg, żeby kolumny w README się zrównały
FONT_SIZE = 13
KEY_COL = 13  # szerokość kolumny klucza w znakach
CHAR_W = FONT_SIZE * 0.6
BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
KEY = "#39d353"
ACCENT = "#398E4A"
SWATCHES = ["#0d1117", "#f85149", "#39d353", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
STAGGER = 0.12
START = 0.5


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    user, host = USER_HOST
    title = f"{user}@{host}"
    lines = []  # (svg_fragment)

    lines.append(
        f'<tspan fill="{KEY}" font-weight="bold">{user}</tspan><tspan fill="{FG}">@</tspan>'
        f'<tspan fill="{KEY}" font-weight="bold">{host}</tspan>'
    )
    lines.append(f'<tspan fill="{MUTED}">{"-" * len(title)}</tspan>')
    for key, val in ROWS:
        if key == "" and val == "":
            lines.append("")
        elif key is None:
            lines.append(f'<tspan fill="{FG}">{" " * KEY_COL}{escape(val)}</tspan>')
        else:
            pad = " " * max(1, KEY_COL - len(key) - 1)
            lines.append(
                f'<tspan fill="{KEY}" font-weight="bold">{escape(key)}</tspan>'
                f'<tspan fill="{MUTED}">:</tspan><tspan fill="{FG}">{pad}{escape(val)}</tspan>'
            )

    height = max(MIN_HEIGHT, TOP + len(lines) * LINE_H + 6 + 18 + 24)
    swatch_y = height - 18 - 24

    css = (
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".l{opacity:0;animation:in .45s ease-out forwards}"
    )
    if static:
        css = ".l{opacity:1}"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Jakub Hyziak IT — karta informacyjna">',
        f"<style>{css}</style>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M12.5 0.5h{WIDTH - 25}a12 12 0 0 1 12 12v19.5h-{WIDTH - 1}v-19.5a12 12 0 0 1 12-12z" fill="{BAR}"/>',
        f'<line x1="0.5" y1="32" x2="{WIDTH - 0.5}" y2="32" stroke="{BORDER}"/>',
        '<circle cx="20" cy="16" r="5.5" fill="#ff5f57"/>',
        '<circle cx="38" cy="16" r="5.5" fill="#febc2e"/>',
        '<circle cx="56" cy="16" r="5.5" fill="#28c840"/>',
        f'<text x="{WIDTH / 2}" y="20.5" text-anchor="middle" font-family="{FONT}" font-size="12" '
        f'fill="{MUTED}">{title} ~ $ neofetch</text>',
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}" xml:space="preserve">',
    ]
    for i, frag in enumerate(lines):
        if not frag:
            continue
        y = TOP + i * LINE_H
        out.append(
            f'<text class="l" x="{PAD_X}" y="{y}" style="animation-delay:{START + i * STAGGER:.2f}s">{frag}</text>'
        )
    out.append("</g>")

    delay = START + len(lines) * STAGGER
    for j, color in enumerate(SWATCHES):
        out.append(
            f'<rect class="l" x="{PAD_X + j * 26}" y="{swatch_y}" width="24" height="16" fill="{color}" '
            f'stroke="{BORDER}" style="animation-delay:{delay + j * 0.04:.2f}s"/>'
        )
    cursor_x = PAD_X + len(SWATCHES) * 26 + 10
    out.append(
        f'<rect class="l" x="{cursor_x}" y="{swatch_y + 1}" width="{CHAR_W:.1f}" height="14" fill="{ACCENT}" '
        f'style="animation-delay:{delay + 0.4:.2f}s"><animate attributeName="fill-opacity" values="1;0;1" '
        f'dur="1s" begin="{delay + 0.4:.2f}s" repeatCount="6" calcMode="discrete" fill="freeze"/></rect>'
    )
    out.append("</svg>")
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()
