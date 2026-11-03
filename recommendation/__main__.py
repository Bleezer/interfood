"""Futtatás: python -m recommendation [--menu útvonal] [--profile útvonal]."""

import argparse
import json
from pathlib import Path

from .selection import recommend

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Ebédválogatás a mentett heti étlapból.")
    parser.add_argument("--menu", type=Path, default=ROOT / "data/menu.json")
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name("profile.json"))
    args = parser.parse_args()
    try:
        menu = json.loads(args.menu.read_text(encoding="utf-8"))
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
        results = recommend(menu, profile)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Nem sikerült a válogatás: {error}\n")
    print(f"Ebédajánlatok: {menu['week_start']} – {menu['week_end']}")
    print("Név és összetevők alapján, helyi szabályokkal; az összetevőket ellenőrizd.")
    for result in results:
        meal = result["meal"]
        if meal is None:
            print(f"{result['date']}: {result['reason']}")
            continue
        for index, option in enumerate([result] + result["alternatives"]):
            meal = option["meal"]
            label = "Fő ajánlat" if index == 0 else f"Alternatíva {index}"
            nutrition = meal["nutrition_per_portion"]
            print(f"{result['date']} – {label}: [{meal['code']}] {meal['name']} ({meal['category']})")
            print(f"  Fehérje: {nutrition['protein_g']:g} g; zsír: {nutrition['fat_g']:g} g.")
            print(f"  {option['reason']}")
            for warning in option["warnings"]:
                print(f"  Eltérés: {warning}")
    if not results:
        print("Nincs kínált hétfő–szombati nap az étlapban.")


if __name__ == "__main__":
    main()
