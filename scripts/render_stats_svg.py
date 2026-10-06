"""Karta ze statystykami (serie, suma, aktywne dni, rekord, średnia + wykres miesięczny).

Okno terminala o tym samym płótnie co `jhit-ascii.svg` (840 × 880), więc w README
oba panele przy równych szerokościach mają równe wysokości. Kafelki wjeżdżają
po kolei, liczby „odliczają” do prawdziwej wartości (stos klatek przełączanych
SMIL-owym <set> — GitHub nie uruchamia JS), na końcu rosną słupki miesięcy.

    python scripts/render_stats_svg.py   # -> stats.svg
"""

import os
from xml.sax.saxutils import escape

from profile_data import FONT_MONO, MONTHS, PROMPT, ROOT, fmt, load, short_date

OUT = ROOT / "stats.svg"

W, H = 840, 880  # == jhit-ascii.svg
PAD = 20
BAR_H = 30  # pasek tytułu
COLS, ROWS = 2, 3
GAP = 16
TILE_W = (W - 2 * PAD - GAP) / COLS
TILE_H = 150
TILES_TOP = BAR_H + PAD + 4
CHART_TOP = TILES_TOP + ROWS * (TILE_H + GAP)

BG, BG_TOP, TILE, FRAME = "#0d1117", "#111722", "#161b22", "#30363d"
MUTED, INK, GREEN, BAR = "#7d8590", "#e6edf3", "#39d353", "#26a641"

STAGGER = 0.15  # s między kafelkami
SLIDE = 0.45
COUNT = 1.2
FRAMES = 16
BARS_AT = STAGGER * COLS * ROWS + 0.4
BAR_STAGGER = 0.06
BAR_GROW = 0.6


def span(s: dict) -> str:
    return f"{short_date(s['start'])} – {short_date(s['end'])}" if s["length"] else "—"


def days_word(n: int) -> str:
    return " dzień" if n == 1 else " dni"


def tiles(data: dict) -> list[tuple]:
    cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
    n_days = len(data["days"])
    active = data["active_days"]
    # (etykieta, wartość, sufiks, podpis, kolor)
    return [
        ("obecna seria", cur["length"], days_word(cur["length"]), span(cur), GREEN),
        ("najdłuższa seria", lng["length"], days_word(lng["length"]), span(lng), INK),
        ("kontrybucje", data["total"], "", "w ostatnim roku", INK),
        ("aktywne dni", active, f" / {n_days}", f"{active / n_days:.0%} roku", INK),
        ("najlepszy dzień", best["count"] if best else 0, "", short_date(best["date"]) if best else "—", INK),
        ("średnio / aktywny dzień", float(data["avg_per_active_day"]), "", "kontrybucji", INK),
    ]


def main() -> None:
    data = load()
    static = os.environ.get("STATIC") == "1"
    empty = bool(data.get("placeholder"))

    css = (
        f".t{{opacity:0;animation:in {SLIDE}s ease-out both}}"
        "@keyframes in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
        f".b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_GROW}s ease-out both}}"
        "@keyframes grow{to{transform:scaleY(1)}}"
        "@media (prefers-reduced-motion:reduce){.t,.b{opacity:1;transform:none;animation:none}}"
    )
    if static:
        css = ".t{opacity:1}"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT_MONO}" role="img" aria-label="Statystyki kontrybucji GitHub">',
        f"<style>{css}</style>",
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{PAD + i * 16}" cy="{BAR_H / 2}" r="5" fill="{dot}"/>')
    out.append(f'<text x="{W / 2}" y="{BAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
               f'text-anchor="middle">{PROMPT}: ~$ ./stats.sh</text>')

    for i, (label, value, suffix, caption, color) in enumerate(tiles(data)):
        col, row = i % COLS, i // COLS
        x = PAD + col * (TILE_W + GAP)
        y = TILES_TOP + row * (TILE_H + GAP)
        start = i * STAGGER
        out.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                   f'fill="{TILE}" stroke="{FRAME}"/>')
        out.append(f'<text x="{x + 24:.1f}" y="{y + 40}" fill="{MUTED}" font-size="22">$ {escape(label)}</text>')
        num_y = y + 100
        if empty or static:
            shown = "—" if empty else fmt(value)
            out.append(f'<text x="{x + 24:.1f}" y="{num_y}" font-size="54" font-weight="700" fill="{color}">{shown}'
                       f'<tspan font-size="24" font-weight="400" fill="{MUTED}">{"" if empty else suffix}</tspan></text>')
        else:
            # klatki odliczania z ease-out: zwalnia przy dojściu do prawdziwej liczby
            t0 = start + SLIDE * 0.6
            for k in range(1, FRAMES + 1):
                v = value * (1 - (1 - k / FRAMES) ** 3)
                v = round(v, 1) if isinstance(value, float) else round(v)
                anim = f'<set attributeName="opacity" to="1" begin="{t0 + COUNT * (k - 1) / FRAMES:.3f}s"/>'
                if k < FRAMES:
                    anim += f'<set attributeName="opacity" to="0" begin="{t0 + COUNT * k / FRAMES:.3f}s"/>'
                out.append(f'<text x="{x + 24:.1f}" y="{num_y}" opacity="0" font-size="54" font-weight="700" '
                           f'fill="{color}">{fmt(v)}<tspan font-size="24" font-weight="400" fill="{MUTED}">'
                           f"{escape(suffix)}</tspan>{anim}</text>")
        out.append(f'<text x="{x + 24:.1f}" y="{y + 132}" fill="{MUTED}" font-size="20">{escape(caption)}</text>')
        out.append("</g>")

    # wykres miesięczny
    monthly = data["monthly"][-13:]
    cw, ch = W - 2 * PAD, H - PAD - CHART_TOP
    out.append(f'<g class="t" style="animation-delay:{BARS_AT - 0.3:.2f}s">')
    out.append(f'<rect x="{PAD}" y="{CHART_TOP}" width="{cw}" height="{ch}" rx="10" fill="{TILE}" stroke="{FRAME}"/>')
    out.append(f'<text x="{PAD + 24}" y="{CHART_TOP + 40}" fill="{MUTED}" font-size="22">$ kontrybucje / miesiąc</text>')
    out.append("</g>")
    top, bottom = CHART_TOP + 66, CHART_TOP + ch - 40
    left, right = PAD + 24, PAD + cw - 24
    slot = (right - left) / len(monthly)
    bw = slot * 0.62
    peak = max(m["total"] for m in monthly)
    for i, m in enumerate(monthly):
        h = max(2.0, (bottom - top) * m["total"] / peak) if peak else 2.0
        bx = left + i * slot + (slot - bw) / 2
        is_peak = peak and m["total"] == peak
        delay = BARS_AT + i * BAR_STAGGER
        cls = '' if static else ' class="b"'
        out.append(f'<rect{cls} x="{bx:.1f}" y="{bottom - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" '
                   f'fill="{GREEN if is_peak else BAR}" style="animation-delay:{delay:.2f}s">'
                   f'<title>{m["month"]}: {fmt(m["total"])}</title></rect>')
        mon = MONTHS[int(m["month"][5:7]) - 1]
        out.append(f'<text x="{bx + bw / 2:.1f}" y="{bottom + 28}" fill="{MUTED}" font-size="16" '
                   f'text-anchor="middle">{mon}</text>')
        if is_peak:
            out.append(f'<text class="t" style="animation-delay:{delay + BAR_GROW:.2f}s" x="{bx + bw / 2:.1f}" '
                       f'y="{bottom - h - 10:.1f}" fill="{INK}" font-size="18" text-anchor="middle">{fmt(peak)}</text>')

    out.append("</svg>")
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({W}x{H})")


if __name__ == "__main__":
    main()
