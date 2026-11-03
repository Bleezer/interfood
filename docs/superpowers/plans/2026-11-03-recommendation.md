# Ebédválogató megvalósítási terv

> Végrehajtás: saját munkamenetben, tesztvezérelten.

**Cél:** külön, offline futtatható ajánló és állandó heti kimeneti fájlok.
**Spec:** docs/superpowers/specs/2026-11-03-recommendation-design.md
**Technológia:** Python standard library, unittest; új függőség nélkül.

## Feladatok
- [x] Gyűjtő tesztje: ideiglenes mappában menu.json/raw.json, hibás adatnál megőrzés; RED, majd útvonalcsere, GREEN.
- [x] recommendation/profile.json: a felhasználó megadott értékei.
- [x] recommendation/selection.py: recommend(menu, profile) -> napi eredmények;
  tests/test_recommendation.py: határok, nulla zsír, hiányos számok, kizárások,
  szombat, vasárnap, szünnap, nincs jelölt, HTML és sorrend; RED -> GREEN.
- [x] recommendation/__main__.py: külön CLI, opcionális --menu/--profile;
  tests/test_recommendation.py: subprocess offline, hibás/bemenet nélküli futás.
- [x] README és AGENTS frissítése; teljes unittest, compileall, mentett étlap próba.
- [x] Diff ellenőrzés és commit.

## Ellenőrzési fókusz
Hiányos/negatív/nem véges számok; tengeri összetevők HTML-ben;
gyümölcsszósz és rántott zöldség; nincs megfelelő étel; szünnapok.

## Ellenőrzési eredmény

- 21 offline teszt sikeres; unittest, compileall és diff --check lefutott.
- A tesztek először elbuktak az új fájlnevek, az új ajánló,
  a szünnapos hétfő, a szombati teljes adag, a Karcsúsító rangsor,
  a hibás profil és a változó küszöbök indoklása esetén, majd javítás után sikeresek.
- Külön kódreview: a Karcsúsító csoport rangsorolása és a nem véges
  profilértékek javítva, regressziós tesztekkel. Az indoklások is a profilt követik.
- A korábbi mentett nyers étlap normalizálása megegyezik a mentett feldolgozott
  étlappal; ebből készültek el az aktuális menu.json/raw.json fájlok.
- A külön CLI a mentett étlap hat kínált napjára offline ajánlást készített.
- Élő gyűjtést és hálózati kérést nem indítottunk.
- Döntés: az első változat helyi szöveges szabályokat használ, nem AI-t.
  Ritka ételnevek felismerése ezért ellenőrzést igényelhet.
- A fájlcserék külön-külön atomikusak; közös kétfájlos tranzakció nincs.
