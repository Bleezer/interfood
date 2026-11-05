"""Névvel azonosítható családi profilok; nincs más személyre való fallback."""

import json
import re
from pathlib import Path

CATALOG = Path(__file__).with_name("profiles.json")


def _path(filename):
    if filename is None:
        return None
    if not isinstance(filename, str) or not filename:
        raise ValueError("Hibás profilfájlnév.")
    root = CATALOG.parent.resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or path.suffix != ".json":
        raise ValueError("A profilfájl a profilkönyvtáron belül legyen.")
    return path


def _catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid profile catalog.")
    entries = data.get("profiles")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Hibás profillista.")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", entry["id"]):
            raise ValueError("Hibás profilazonosító.")
        if entry["id"] in seen or not isinstance(entry.get("name"), str) or not entry["name"].strip():
            raise ValueError("Ismétlődő vagy név nélküli profil.")
        seen.add(entry["id"])
        _path(entry.get("file"))
    if data.get("default_profile_id") not in seen:
        raise ValueError("Hiányzó alapértelmezett profil.")
    return data


def list_profiles():
    return [{"id": entry["id"], "name": entry["name"],
             "configured": entry.get("file") is not None and _path(entry["file"]).is_file()}
            for entry in _catalog()["profiles"]]


def load_profile(profile_id=None):
    catalog = _catalog()
    identity = catalog["default_profile_id"] if profile_id is None else profile_id
    entry = next((entry for entry in catalog["profiles"] if entry["id"] == identity), None)
    if entry is None:
        raise ValueError("Ismeretlen személyes profil.")
    path = _path(entry.get("file"))
    if path is None or not path.is_file():
        raise ValueError(f"{entry['name']}: a preferenciák még nincsenek megadva.")
    profile = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Hibás személyes profilfájl.")
    return profile
