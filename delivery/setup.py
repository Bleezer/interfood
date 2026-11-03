"""Célazonosító lekérése: python -m delivery.setup. Nem küld üzenetet."""

import argparse
from getpass import getpass

from .telegram import find_private_chats


def main():
    parser = argparse.ArgumentParser(description="Telegram privát célazonosítók lekérése a saját botból.")
    parser.parse_args()
    try:
        token = getpass("BotFather token (bevitel rejtett): ").strip()
        chats = find_private_chats(token)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Nem sikerült a beállítás: {error}\n")
    if not chats:
        parser.exit(1, "Előbb írj /start üzenetet az új botodnak, majd próbáld újra.\n")
    print("TELEGRAM_CHAT_ID lehetséges értékei:")
    print("\n".join(chats))


if __name__ == "__main__":
    main()
