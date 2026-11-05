"""Chrome native messaging host: csak tervet számol, kosarat nem módosít."""

import base64
import hashlib
import json
import struct
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from interfood.dates import next_monday
from interfood.normalization import normalize_menu
from recommendation.selection import recommend

ROOT = Path(__file__).resolve().parents[1]
HOST_NAME = "hu.interfood.menu_helper"
MAX_INPUT = 8 * 1024 * 1024


def extension_id():
    manifest = json.loads((ROOT / "extension/manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(base64.b64decode(manifest["key"])).hexdigest()[:32]
    return "".join(chr(ord("a") + int(char, 16)) for char in digest)


def read_message(stream):
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError("Hiányos üzenetfejléc.")
    size = struct.unpack("=I", header)[0]
    if not 0 < size <= MAX_INPUT:
        raise ValueError("Érvénytelen üzenetméret.")
    data = bytearray()
    while len(data) < size:
        part = stream.read(size - len(data))
        if not part:
            raise ValueError("Hiányos üzenet.")
        data.extend(part)
    return json.loads(data)


def write_message(stream, message):
    data = json.dumps(message, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(data) > 1024 * 1024:
        raise ValueError("Túl hosszú válasz.")
    stream.write(struct.pack("=I", len(data)))
    stream.write(data)
    stream.flush()


def handle_request(request, today=None):
    try:
        if not isinstance(request, dict) or request.get("type") != "plan":
            raise ValueError("Ismeretlen művelet.")
        if not isinstance(request.get("payload"), dict):
            raise ValueError("Invalid menu payload.")
        monday = next_monday(today or datetime.now(ZoneInfo("Europe/Budapest")).date())
        meals = normalize_menu(request["payload"], monday)
        menu = {"schema_version": 1, "week_start": monday.isoformat(),
                "week_end": (monday + timedelta(days=6)).isoformat(), "meals": meals}
        profile = json.loads((ROOT / "recommendation/profile.json").read_text(encoding="utf-8"))
        items = []
        for day in recommend(menu, profile):
            for option in [day] + day["alternatives"]:
                meal = option["meal"]
                if meal is None:
                    continue
                if type(meal["id"]) is not int or meal["id"] <= 0:
                    raise ValueError("Hibás ételazonosító.")
                items.append({key: meal[key] for key in ("id", "date", "code", "name")})
                items[-1]["quantity"] = 1
        return {"ok": True, "plan": {"version": 1, "week_start": menu["week_start"],
                                    "week_end": menu["week_end"], "items": items}}
    except (OSError, KeyError, ValueError, TypeError, AttributeError):
        return {"ok": False, "error": "A betöltött étlapból nem készült érvényes következő heti kosárterv."}


def main():
    if len(sys.argv) < 2 or sys.argv[1] != f"chrome-extension://{extension_id()}/":
        return 1
    if sys.platform == "win32":
        import msvcrt
        import os
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    try:
        request = read_message(sys.stdin.buffer)
        if request is not None:
            write_message(sys.stdout.buffer, handle_request(request))
    except (OSError, ValueError):
        write_message(sys.stdout.buffer, {"ok": False, "error": "Hibás helyi üzenet."})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
