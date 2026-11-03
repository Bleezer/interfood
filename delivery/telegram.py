"""Telegram-kézbesítés; a bot azonosítója nem kerül hibaszövegbe."""

import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MESSAGE_LIMIT = 3500


def split_message(message):
    """Sorhatáron darabol, hosszú sornál karakterhatáron; UTF-16-ban is korlátos."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Üres értesítés nem küldhető.")
    parts, current, units = [], "", 0
    for line in message.splitlines(keepends=True):
        line_units = len(line.encode("utf-16-le")) // 2
        if line_units <= MESSAGE_LIMIT:
            if current and units + line_units > MESSAGE_LIMIT:
                parts.append(current)
                current, units = "", 0
            current += line
            units += line_units
        else:
            for char in line:
                char_units = len(char.encode("utf-16-le")) // 2
                if units + char_units > MESSAGE_LIMIT:
                    parts.append(current)
                    current, units = "", 0
                current += char
                units += char_units
    if current:
        parts.append(current)
    return parts


def _api_request(method, payload, token):
    if not isinstance(token, str) or not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise ValueError("Hiányzó vagy hibás TELEGRAM_BOT_TOKEN.")
    request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        status = error.code
        error.close()
        raise RuntimeError(f"Telegram HTTP hiba ({status}); a kérés leállt.") from None
    except (URLError, OSError, ValueError):
        raise RuntimeError("Telegram hálózati vagy válaszhiba; a kérés leállt.") from None
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError("A Telegram elutasította a kérést.")
    return result.get("result")


def find_private_chats(token):
    """A saját bot legutóbbi üzeneteiből ad privát célazonosítókat; nem nyugtáz."""
    updates = _api_request("getUpdates", {"allowed_updates": ["message"], "timeout": 0}, token)
    if not isinstance(updates, list):
        raise RuntimeError("Hibás Telegram üzenetlista.")
    chats = []
    for update in updates:
        chat = update.get("message", {}).get("chat", {})
        if chat.get("type") == "private":
            identity = str(chat["id"])
            if identity not in chats:
                chats.append(identity)
    return chats


def send_report(report, token, chat_id):
    """Sorrendben elküldi a darabokat; hiba után nincs ismétlés vagy további küldés."""
    if not isinstance(chat_id, str) or not re.fullmatch(r"-?[0-9]+", chat_id):
        raise ValueError("Hiányzó vagy hibás TELEGRAM_CHAT_ID; számszerű azonosító szükséges.")
    chunks = split_message(report)
    for index, chunk in enumerate(chunks):
        if index:
            time.sleep(1.1)
        _api_request("sendMessage", {"chat_id": chat_id, "text": chunk}, token)
    return len(chunks)
