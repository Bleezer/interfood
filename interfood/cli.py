"""A heti étlapgyűjtés futtatása."""

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .collector import SITE, fetch_menu
from .dates import next_monday
from .normalization import normalize_menu
from .storage import save_json

OUTPUT = Path(__file__).resolve().parent.parent / "data"


def main():
    now = datetime.now(ZoneInfo("Europe/Budapest"))
    monday = next_monday(now.date())
    print(f"Gyűjtés: {monday} – {monday + timedelta(days=6)}", flush=True)
    raw = fetch_menu(monday)
    meals = normalize_menu(raw, monday)
    result = {
        "schema_version": 1,
        "source_url": SITE,
        "collected_at": datetime.now(ZoneInfo("Europe/Budapest")).isoformat(timespec="seconds"),
        "timezone": "Europe/Budapest",
        "week_start": monday.isoformat(),
        "week_end": (monday + timedelta(days=6)).isoformat(),
        "available_dates": sorted({meal["date"] for meal in meals}),
        "meal_count": len(meals),
        "meals": meals,
    }
    # Ellenőrzés után mentünk; hiba esetén a korábbi heti fájl megmarad.
    save_json(OUTPUT / "raw.json", raw)
    target = OUTPUT / "menu.json"
    save_json(target, result)
    print(f"Mentve: {target}")
    for day, count in sorted(Counter(meal["date"] for meal in meals).items()):
        print(f"  {day}: {count} tétel")
    missing = sum(any(v is None for v in m["nutrition_per_portion"].values()) for m in meals)
    print(f"Összesen {len(meals)} tétel; hiányos tápérték: {missing}.")
