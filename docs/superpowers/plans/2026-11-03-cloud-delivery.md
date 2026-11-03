# Felhős kézbesítés megvalósítási terve

**Cél:** számítógéptől független heti étlap és Telegram-értesítés.
**Spec:** docs/superpowers/specs/2026-11-03-cloud-delivery-design.md
**Technológia:** Python standard library, GitHub Actions, Telegram Bot API.

- [x] tests/test_delivery.py: közös riport, hosszkorlát, üzenetsorrend, HTTP és API hiba,
  titok nélküli hibaszöveg, hiányzó hitelesítés és elavult étlap; RED.
- [x] recommendation/report.py: format_report(menu, results) -> str; a CLI ezt használja.
- [x] delivery/telegram.py: split_message(text), send_report(text, token, chat_id);
  urllib JSON POST, timeout, véges darabok, hibáknál leállás, titkok nélkül.
- [x] delivery/__main__.py: dry-run, tesztértesítés, hibajelzés és heti riport;
  frissesség ellenőrzés Budapest szerinti következő hétre; GREEN.
- [x] .github/workflows/weekly-menu.yml: kézi és heti futás, offline tesztek,
  Playwright Chromium, gyűjtés, kézbesítés; titkok kizárólag a kézbesítési lépésben.
- [x] docs/cloud-setup.md, README és AGENTS frissítése.
- [x] Teljes offline teszt, compileall, diff és külön kódreview.
- [x] Commit. Éles telepítés csak a még hiányzó fiók/tárhely/célpont megadásával.

## Ellenőrzési fókusz

Hibás/üres étlap nem küldhető; régi hét nem küldhető új ajánlatként.
Telegram hibaszöveg ne tartalmazzon bot tokent. Hosszú és Unicode szöveg
ne lépje túl az üzenetkorlátot. Hibánál ne menjen tovább a küldés.
A dry-run nem kér titkot és nem küld hálózati kérést.

## Ellenőrzési eredmény

- 37 offline teszt sikeres; új funkciók előtt a kézbesítési tesztek elbuktak,
  implementáció után sikeresek. A chat-azonosító lekérdezése külön RED → GREEN.
- A közös formázó megtartja az eredeti CLI-kimenet tartalmát.
- Külön read-only kódreview: nincs blokkoló helyességi vagy titokkezelési hiba.
- A dry-run a meglévő heti étlapból előnézetet készített, küldés nélkül.
- A workflow kapott külön, étlapgyűjtés nélküli telefonos tesztüzemmódot.
- Még nem igazolt: valódi Telegram-küldés, Ubuntu alatti élő gyűjtés,
  az ütemezett GitHub-futás. Ehhez a két titkos beállítás szükséges.
- A felhasználó megadta a repositoryt: https://github.com/Bleezer/interfood.git.
- Az első éles telefonos próba és a végleges időpont továbbra is bekötési feladat.
