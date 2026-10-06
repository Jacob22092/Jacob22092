"""Rysuje `data/contributions.json` jako klasyczny kalendarz 53 tyg. × 7 dni.

Zaokrąglone kafelki w zielonej skali GitHuba (poziom 5 = neonowa góra skali),
odsłaniane raz po skosie (CSS keyframes, bez zapętlonego „glow”), legenda
Mniej→Więcej i stopka ze statystykami.

    python scripts/render_heatmap_svg.py   # -> contrib-heatmap.svg
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          brak -> najjaśniejszy (poziom 5 to neonowy szczyt)
WIDTH = 1108  # = 554 + 554, tyle co logo + karta w README
CELL = 15
GAP = 4
STEP = CELL + GAP
LEFT = 58
TOP = 74
BG = "#0d1117"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
KEY = "#39d353"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
MONTHS = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
WEEKDAYS = {1: "pn", 3: "śr", 5: "pt"}  # wiersze: 0 = niedziela (jak na GitHubie)
DIAG_DELAY = 0.022  # s na krok przekątnej


def plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def placeholder() -> dict:
    """Pusta siatka, dopóki workflow nie pobierze prawdziwych danych."""
    end = date.today()
    start = end - timedelta(days=364 + (end.weekday() + 1) % 7)
    days = [{"date": (start + timedelta(i)).isoformat(), "count": 0, "level": 0}
            for i in range((end - start).days + 1)]
    return {"user": "Jacob22092", "days": days, "total": 0, "current_streak": 0,
            "longest_streak": 0, "best_day": None, "placeholder": True}


def levels(days: list[dict]) -> list[int]:
    """Poziomy GitHuba 0–4, plus 5 dla najmocniejszych ~5% aktywnych dni."""
    nonzero = sorted(d["count"] for d in days if d["count"] > 0)
    neon = nonzero[int(len(nonzero) * 0.95)] if len(nonzero) >= 20 else None
    out = []
    for d in days:
        lv = d.get("level", 0)
        if neon is not None and lv == 4 and d["count"] >= neon:
            lv = 5
        out.append(lv)
    return out


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8")) if SRC.exists() else placeholder()
    static = os.environ.get("STATIC") == "1"
    days = data["days"]
    lvls = levels(days)
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # niedziela = 0
    weeks = (offset + len(days) + 6) // 7

    grid_w = weeks * STEP - GAP
    x0 = LEFT + (WIDTH - LEFT - 24 - grid_w) / 2
    grid_bottom = TOP + 7 * STEP - GAP
    height = grid_bottom + 84

    css = (
        "@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}"
        ".c{opacity:0;transform-box:fill-box;animation:drop .5s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        ".f{opacity:0;animation:fade .6s ease-out forwards}"
    )
    if static:
        css = ".c,.f{opacity:1}"

    user = escape(data.get("user", ""))
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Kalendarz kontrybucji GitHub {user}">',
        f"<style>{css}</style>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<g font-family="{FONT}">',
        f'<text x="24" y="34" font-size="15" fill="{FG}"><tspan fill="{KEY}" font-weight="bold">{user}</tspan>'
        f'<tspan fill="{MUTED}"> · </tspan>aktywność na GitHubie</text>',
    ]

    # etykiety miesięcy: nad pierwszym tygodniem, w którym zaczyna się miesiąc
    seen = None
    last_x = -100
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        if dt.day == 1 or i == 0:
            if (dt.year, dt.month) != seen:
                seen = (dt.year, dt.month)
                x = x0 + ((offset + i) // 7) * STEP
                if x - last_x >= 3 * STEP:
                    out.append(f'<text x="{x:.1f}" y="{TOP - 10}" font-size="12" fill="{MUTED}">{MONTHS[dt.month - 1]}</text>')
                    last_x = x
    for row, label in WEEKDAYS.items():
        out.append(f'<text x="{x0 - 10:.1f}" y="{TOP + row * STEP + CELL - 3}" font-size="12" '
                   f'text-anchor="end" fill="{MUTED}">{label}</text>')

    for i, (d, lv) in enumerate(zip(days, lvls)):
        col, row = divmod(offset + i, 7)
        x = x0 + col * STEP
        y = TOP + row * STEP
        tip = f"{d['count']} {plural(d['count'], 'kontrybucja', 'kontrybucje', 'kontrybucji')} · {fmt_date(d['date'])}"
        out.append(
            f'<rect class="c" x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="3.5" fill="{PALETTE[lv]}" '
            f'style="animation-delay:{(col + row) * DIAG_DELAY:.3f}s"><title>{tip}</title></rect>'
        )

    reveal_end = (weeks + 6) * DIAG_DELAY + 0.3
    # legenda
    ly = grid_bottom + 22  # linia statystyk
    ly2 = ly + 26  # linia legendy / podpisu
    lx = x0 + grid_w - (len(PALETTE) * STEP - GAP) - 52
    out.append(f'<g class="f" style="animation-delay:{reveal_end:.2f}s">')
    out.append(f'<text x="{lx - 10:.1f}" y="{ly2 + CELL - 3}" font-size="12" text-anchor="end" fill="{MUTED}">Mniej</text>')
    for j, color in enumerate(PALETTE):
        out.append(f'<rect x="{lx + j * STEP:.1f}" y="{ly2}" width="{CELL}" height="{CELL}" rx="3.5" fill="{color}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * STEP + 6:.1f}" y="{ly2 + CELL - 3}" font-size="12" fill="{MUTED}">Więcej</text>')
    out.append("</g>")

    # stopka
    if data.get("placeholder"):
        stats = "dane pojawią się po pierwszym uruchomieniu GitHub Actions"
    else:
        total = data["total"]
        cur, lng = data["current_streak"], data["longest_streak"]
        parts = [
            f'<tspan fill="{KEY}" font-weight="bold">{fmt(total)}</tspan> '
            f"{plural(total, 'kontrybucja', 'kontrybucje', 'kontrybucji')} w ostatnim roku",
            f'seria: <tspan fill="{FG}">{cur} {plural(cur, "dzień", "dni", "dni")}</tspan>',
            f'rekord: <tspan fill="{FG}">{lng} {plural(lng, "dzień", "dni", "dni")}</tspan>',
        ]
        best = data.get("best_day")
        if best and best["count"]:
            parts.append(f'najlepszy dzień: <tspan fill="{FG}">{best["count"]}</tspan> ({fmt_date(best["date"])})')
        stats = f'<tspan fill="{MUTED}"> · </tspan>'.join(parts)
    out.append(f'<text class="f" x="{x0:.1f}" y="{ly + CELL - 3}" font-size="13" fill="{MUTED}" '
               f'style="animation-delay:{reveal_end:.2f}s">{stats}</text>')
    out.append(f'<text class="f" x="{x0:.1f}" y="{ly2 + CELL - 3}" font-size="11" fill="#484f58" '
               f'style="animation-delay:{reveal_end + 0.2:.2f}s">odświeżane codziennie przez GitHub Actions</text>')
    out.append("</g></svg>")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)} ({weeks} tyg., {WIDTH}x{height})")


if __name__ == "__main__":
    main()
