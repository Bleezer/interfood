# Kézi családi kosárfeltöltés terve

Spec: docs/superpowers/specs/2026-11-05-manual-family-cart-design.md

- [x] Profillista és szigorú betöltés; saját profil + két inaktív családtag.
- [x] Natív profiles/parancs és explicit profilú kosárterv; Python RED → GREEN.
- [x] Profil szerinti terv/tétel/heti műveleti kulcsok, régi saját ledger migrációja.
- [x] Node-tesztek: heti egyszeri start, személyek külön indítása, közös adagok,
  több fül, bizonytalan művelet és régi adatok megőrzése; RED → GREEN.
- [x] Sarokpanel gombbal és személyválasztóval; automatikus indítás eltávolítása.
- [x] Izolált DOM-próba: belépéskor 0 kattintás, kattintásra feltölt,
  második kattintás/frissítés nem tölt, második személy plusz adagot ad,
  fiók- és kilépésvédelem megmarad.
- [x] CLI --person, dokumentáció és popup frissítése.
- [x] Kódreview, teljes offline teszt, compileall, natív próba, commit és push.

## Ellenőrzési eredmény

- 50 Python- és 16 Node-teszt sikeres, compileall és diff --check sikeres.
- A profillista és a heti személyes zárolás tesztjei megvalósítás előtt elbuktak.
- Valódi háttérkóddal, izolált böngészőoldalon igazolt: nincs automatikus indítás,
  a gomb egyszer tölt, frissítés után is tiltja az ismétlést, három személy külön
  adagokat kap, korábbi eltávolított adagot nem állít vissza, kilépés leállít.
- Kódreview: a régi saját kosár migrációját feleség/fiú első kiválasztásakor is
  végre kell hajtani. Külön wife-first teszttel RED → GREEN javítva.
- A kikapcsolt állapot gombon való megjelenítése DOM-regresszióval javítva.
- Csak a self profil konfigurált. A wife és son helye előkészítve, nincs
  hozzájuk kitalált vagy saját profilból másolt preferencia.
- Telegram továbbra is a saját profile.json fájllal fut; családi riport nincs bekapcsolva.
- A Chrome-bővítmény környilas frissítése és a valódi kosárpróba felhasználói lépés.
- A manifest key és a host útvonala változatlan; újratelepítés nem szükséges.

- A kizárások nem maradnak globálisak: exclude_seafood, exclude_fruity_meat
  és prefer_breaded_saturday személyenként állítható. A saját profil mindhármat
  true értékkel őrzi meg. Eltérő profil és hibás típus regresszióval ellenőrizve.
