"""Kompatibilis belépési pont; az új parancs: python -m interfood."""

from interfood.cli import OUTPUT, main
from interfood.collector import API, SITE, fetch_menu
from interfood.dates import next_monday
from interfood.normalization import NUTRIENTS, normalize_item, normalize_menu, number
from interfood.storage import save_json

__all__ = [
    "API", "NUTRIENTS", "OUTPUT", "SITE", "fetch_menu", "main",
    "next_monday", "normalize_item", "normalize_menu", "number", "save_json",
]


if __name__ == "__main__":
    main()
