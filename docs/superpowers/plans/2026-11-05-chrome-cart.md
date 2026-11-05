# Chrome kosársegéd terve

**Cél:** a felhasználó által kért három napi jelölt kosárba tétele Chrome-ban.
**Spec:** docs/superpowers/specs/2026-11-05-chrome-cart-design.md
**Végrehajtás:** helyben, tesztvezérelten; a felhasználó önálló munkát kért.

- [x] Native Python-host: keretezett JSON, rögzített profillal, nyilvános étlapból
  dátumellenőrzött terv; tests/test_cart_assistant.py RED → GREEN.
- [x] extension/core.js és tests: Budapest szerinti dátum, tervellenőrzés,
  tartós fiók/heti/item ledger; Node beépített test.
- [x] extension/background.js: senderellenőrzés, natív kapcsolat, soros foglalás.
- [x] extension/bridge.js: csak menu payload, user ID és logout; token nélkül.
- [x] extension/content.js: hét és nap választása, egyenkénti pluszgomb,
  mennyiség-visszaellenőrzés, pending/done/uncertain, státusz és kikapcsolás.
- [x] extension/popup.* és manifest.json: helyi kapcsoló, minimális engedélyek.
- [x] cart_assistant/install.py: HKCU regisztráció, stabil extension ID, helyi launcher.
- [x] Offline protokoll- és DOM-ellenőrzés; valódi kosár nem része az offline tesztnek.
- [x] README, docs/chrome-cart-setup.md, AGENTS: külön engedély a kosársegédnek.
- [x] Kódreview, teljes unittest, compileall, Node-tesztek, commit és push.
- [ ] Kézi Chrome-bővítménytelepítés és első bejelentkezett próba a felhasználóval.

## Fókusz
Meglévő kosár és kézzel eltávolított ajánlatok; több lap; accountváltás;
hibás/régi terv; ünnepnap; félbeszakadt kattintás; személyes adatok elkülönítése.

## Ellenőrzés és állapot

- 42 Python-teszt és 11 Node-teszt sikeres; compileall és diff --check sikeres.
- A natív host és a duplázásvédelem tesztjei kezdetben elbuktak (hiányzó
  implementáció), majd a megvalósítás után sikeresek.
- A kódreview három versenyhelyzetet jelzett: aszinkron fiókellenőrzés,
  késői busy-zár és másik fül fiókváltása. Reprodukáló tesztek után javítva;
  a fiókjelzések az összes Interfood-fül között közösek, a másik fül
  helyi storage-változása is érvényteleníti a korábbi fiókállapotot.
- Az offline DOM-próba ellenőrzi: bejelentkezés nélkül nincs módosítás;
  meglévő mennyiség megmarad; kézzel kivett tétel nem kerül vissza;
  kilépés egy függő ellenőrzés alatt nem vezet kattintáshoz; párhuzamos
  indításból csak egy ajánlás/feltöltés indul.
- A mintaoldal UTF-8 hiánya javítva. Ez a tesztoldal hibája volt.
- A helyi Windows-host regisztrálva, stabil Chrome-ID:
  cendpfiifamlaefjehmahofgpbccnmon.
- A regisztrált .bat launcheren át 1 692 985 bájtos valódi nyers étlapból
  szabályos natív válasz érkezett 18 tétellel a 2026-11-09-i hétre.
- A Chrome-bővítmény felhasználói betöltése és az első valódi kosárpróba
  továbbra is hátravan. Valódi kosárkérést nem indítottunk.
- A közvetlen Chrome-vezérlő két belépési pontja Node runtime elérési
  hibával leállt; a végső betöltési lépést ezért a felhasználó végzi.
