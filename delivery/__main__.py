"""Heti jelentés: python -m delivery; offline előnézet: --dry-run."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from interfood.dates import next_monday
from recommendation.report import format_report
from recommendation.selection import recommend
from .telegram import send_report

ROOT = Path(__file__).resolve().parents[1]


def validate_week(menu, today):
    if not isinstance(menu, dict) or not menu.get("meals"):
        raise ValueError("Hiányzó vagy üres heti étlap.")
    if menu.get("week_start") != next_monday(today).isoformat():
        raise ValueError("A mentett étlap nem a következő hétre szól; előbb gyűjts friss adatot.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Heti ebédajánló küldése Telegramra.")
    parser.add_argument("--menu", type=Path, default=ROOT / "data/menu.json")
    parser.add_argument("--profile", type=Path, default=ROOT / "recommendation/profile.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Csak előnézet; nincs küldés.")
    mode.add_argument("--test", action="store_true", help="Rövid tesztértesítés, étlap nélkül.")
    mode.add_argument("--failure", action="store_true", help="Hibajelzés az ütemezett futásból.")
    args = parser.parse_args(argv)
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not args.dry_run and (not token or not chat_id):
            raise ValueError("Állítsd be a TELEGRAM_BOT_TOKEN és TELEGRAM_CHAT_ID titkos értékeket.")
        if args.test:
            report = "Interfood: a telefonos értesítés működik."
        elif args.failure:
            report = "Interfood: a heti futás hibával leállt. Új teljes ajánló nem készült; ellenőrizd a GitHub Actions futását."
        else:
            menu = json.loads(args.menu.read_text(encoding="utf-8"))
            validate_week(menu, datetime.now(ZoneInfo("Europe/Budapest")).date())
            profile = json.loads(args.profile.read_text(encoding="utf-8"))
            report = format_report(menu, recommend(menu, profile))
        if args.dry_run:
            print(report, end="")
        else:
            count = send_report(report, token, chat_id)
            print(f"Telegram-értesítés elküldve: {count} üzenet.")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"Nem sikerült a kézbesítés: {error}\n")


if __name__ == "__main__":
    main()
