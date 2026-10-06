"""Rysuje `data/contributions.json` jako klasyczny kalendarz 53 tyg. × 7 dni.

Zaokrąglone kafelki w zielonej skali GitHuba (poziom 5 = neonowa góra skali)
„wyskakują” raz po skosie (CSS keyframes, bez pętli), pod spodem suma z roku.
Przezroczyste tło — wpasowuje się w ciemny i jasny motyw GitHuba.

    python scripts/render_heatmap_svg.py   # -> contrib-heatmap.svg
"""

import os
from datetime import date

from profile_data import FONT_SANS, MONTHS, ROOT, fmt, load, plural

OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          brak -> najjaśniejszy (poziom 5 to neonowy szczyt)
CELL = 13
GAP = 3
STEP = CELL + GAP
LEFT = 34
TOP = 26
LABEL = "#7d8590"
WEEKDAYS = {1: "pn", 3: "śr", 5: "pt"}  # wiersze: 0 = niedziela (jak na GitHubie)
DIAG_DELAY = 0.02  # s na krok przekątnej


def levels(days: list[dict]) -> list[int]:
    """Poziomy GitHuba 0–4, plus 5 dla najmocniejszych ~5% aktywnych dni."""
    nonzero = sorted(d["count"] for d in days if d["count"] > 0)
    neon = nonzero[int(len(nonzero) * 0.95)] if len(nonzero) >= 20 else None
    return [5 if neon is not None and d.get("level", 0) == 4 and d["count"] >= neon else d.get("level", 0)
            for d in days]


def main() -> None:
    data = load()
    static = os.environ.get("STATIC") == "1"
    days = data["days"]
    offset = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7  # niedziela = 0
    weeks = (offset + len(days) + 6) // 7
    width = LEFT + weeks * STEP - GAP + 6
    grid_bottom = TOP + 7 * STEP - GAP
    height = grid_bottom + 34

    css = (
        "text{font-family:" + FONT_SANS + "}"
        f".l{{fill:{LABEL};font-size:13px;font-weight:600}}"
        ".tot{fill:#8b949e;font-size:15px;font-weight:700}"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both}"
        "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:scale(1)}}"
        ".f{opacity:0;animation:fade .6s ease-out both}@keyframes fade{to{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.c,.f{opacity:1;animation:none}}"
    )
    if static:
        css = css.replace("opacity:0;", "opacity:1;").replace("animation:", "x-animation:")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Kalendarz kontrybucji GitHub {data.get("user", "")}">',
        f"<style>{css}</style>",
    ]

    # etykiety miesięcy: nad pierwszym tygodniem, w którym zaczyna się miesiąc
    seen, last_x = None, -100.0
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        if (dt.day == 1 or i == 0) and (dt.year, dt.month) != seen:
            seen = (dt.year, dt.month)
            x = LEFT + ((offset + i) // 7) * STEP
            if x - last_x >= 3 * STEP:
                out.append(f'<text class="l" x="{x}" y="{TOP - 10}">{MONTHS[dt.month - 1]}</text>')
                last_x = x
    for row, label in WEEKDAYS.items():
        out.append(f'<text class="l" x="0" y="{TOP + row * STEP + CELL - 2}">{label}</text>')

    for i, (d, lv) in enumerate(zip(days, levels(days))):
        col, row = divmod(offset + i, 7)
        n = d["count"]
        tip = f"{n} {plural(n, 'kontrybucja', 'kontrybucje', 'kontrybucji')} · {d['date']}"
        out.append(
            f'<rect class="c" x="{LEFT + col * STEP}" y="{TOP + row * STEP}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{PALETTE[lv]}" style="animation-delay:{(col + row) * DIAG_DELAY:.2f}s">'
            f"<title>{tip}</title></rect>"
        )

    total = data["total"]
    if data.get("placeholder"):
        caption = "dane pojawią się po pierwszym uruchomieniu GitHub Actions"
    else:
        caption = f"{fmt(total)} {plural(total, 'kontrybucja', 'kontrybucje', 'kontrybucji')} w ostatnim roku"
    reveal_end = (weeks + 6) * DIAG_DELAY
    out.append(f'<text class="tot f" x="{LEFT}" y="{grid_bottom + 24}" '
               f'style="animation-delay:{reveal_end:.2f}s">{caption}</text>')
    out.append("</svg>")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({weeks} tyg., {width}x{height})")


if __name__ == "__main__":
    main()
