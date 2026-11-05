"""Egyszeri Windows-telepítés: python -m cart_assistant.install."""

import json
import sys
from pathlib import Path

from .host import HOST_NAME, ROOT, extension_id


def main():
    if sys.platform != "win32":
        raise SystemExit("Ez a telepítő Windows Chrome-hoz készült.")
    import winreg
    target = ROOT / ".local/chrome-native"
    target.mkdir(parents=True, exist_ok=True)
    launcher = target / "launch.bat"
    launcher.write_text(
        f'@echo off\ncd /d "{ROOT}"\n"{sys.executable}" -X utf8 -m cart_assistant.host %*\n',
        encoding="utf-8",
    )
    manifest = target / f"{HOST_NAME}.json"
    manifest.write_text(json.dumps({
        "name": HOST_NAME, "description": "Interfood helyi ebédválogató",
        "path": str(launcher), "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id()}/"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))
    print(f"Helyi kosársegéd regisztrálva. Chrome-bővítmény: {extension_id()}")
    print(f"Betöltendő mappa: {ROOT / 'extension'}")


if __name__ == "__main__":
    main()
