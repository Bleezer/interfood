"""Futtatás: python -m recommendation [--menu útvonal] [--profile útvonal]."""

import argparse
import json
from pathlib import Path

from .selection import recommend
from .report import format_report

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
    print(format_report(menu, results), end="")


if __name__ == "__main__":
    main()
