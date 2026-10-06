"""Pobiera publiczny kalendarz kontrybucji z GitHuba — bez tokenu i bez GraphQL.

GitHub serwuje go jako HTML pod https://github.com/users/<user>/contributions
(ten sam fragment, którego używa strona profilu). Parsujemy komórki dni i
zapisujemy `data/contributions.json` z surowymi dniami + statystykami.

    python scripts/fetch_contributions.py [username]
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
DEFAULT_USER = "Jacob22092"
COUNT_RE = re.compile(r"^\s*([\d,]+)\s+contributions?\b", re.I)


def fetch_html(user: str) -> str:
    resp = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap (+https://github.com/" + user + ")"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        count = 0
        if cell.get("data-count") is not None:  # starszy format
            count = int(cell["data-count"])
        else:
            m = COUNT_RE.match(tips.get(cell.get("id"), "") or cell.get_text(" ", strip=True))
            count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": cell["data-date"], "count": count, "level": int(cell.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("nie znaleziono komórek kalendarza — GitHub zmienił HTML?")
    return days


def streaks(days: list[dict]) -> tuple[dict, dict]:
    """Zwraca (bieżąca, najdłuższa) seria jako {length, start, end}."""
    longest = {"length": 0, "start": None, "end": None}
    run_start = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            run_start = run_start if run_start is not None else i
            if i - run_start + 1 > longest["length"]:
                longest = {"length": i - run_start + 1, "start": days[run_start]["date"], "end": d["date"]}
        else:
            run_start = None
    # bieżąca seria: dzisiejsze 0 jej nie przerywa (dzień jeszcze trwa)
    end = len(days) - 1
    if end >= 0 and days[end]["count"] == 0:
        end -= 1
    start = end
    while start >= 0 and days[start]["count"] > 0:
        start -= 1
    length = end - start
    current = {"length": length, "start": days[start + 1]["date"] if length else None,
               "end": days[end]["date"] if length else None}
    return current, longest


def build(user: str, days: list[dict]) -> dict:
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "user": user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0.0,
        "monthly": [{"month": m, "total": t} for m, t in monthly.items()],
        "days": days,
    }


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", DEFAULT_USER)
    data = build(user, parse_days(fetch_html(user)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"zapisano {OUT.relative_to(ROOT)}: {data['total']} kontrybucji, {len(data['days'])} dni")


if __name__ == "__main__":
    main()
