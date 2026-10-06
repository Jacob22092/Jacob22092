"""Wspólne pomocniki: wczytanie `data/contributions.json` i polskie formatowanie."""

import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
MONTHS = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
FONT_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
FONT_SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
PROMPT = "jakub@github"


def load(path: Path = SRC) -> dict:
    """Dane z JSON-a albo pusta siatka, dopóki workflow ich nie pobierze."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    end = date.today()
    start = end - timedelta(days=364 + (end.weekday() + 1) % 7)
    days = [{"date": (start + timedelta(i)).isoformat(), "count": 0, "level": 0}
            for i in range((end - start).days + 1)]
    months: dict[str, int] = {}
    for d in days:
        months.setdefault(d["date"][:7], 0)
    empty = {"length": 0, "start": None, "end": None}
    return {"user": "Jacob22092", "days": days, "total": 0, "current_streak": empty,
            "longest_streak": empty, "best_day": None, "active_days": 0, "avg_per_active_day": 0.0,
            "monthly": [{"month": m, "total": 0} for m in months], "placeholder": True}


def plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def fmt(n: float) -> str:
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.1f}".replace(",", " ").replace(".", ",")
    return f"{int(round(n)):,}".replace(",", " ")


def short_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]}"
