# Chrome kosársegéd

A segéd kizárólag **gombnyomásra** tölti a kosarat. Belépéskor és profilváltáskor
sem tesz be ételt. A sarokban személyválasztó és **Kosárba teszem** gomb van.
Egy személy egy hétre egyszer indíthat feltöltést, a közös Interfood-fiókon belül.

## Frissítés a korábbi verzióról

Chrome → `chrome://extensions` → Interfood kosársegéd → **Frissítés** (környíl).
Utána frissítsd az Interfood-lapot. A meglévő helyi kapcsolat újratelepítése
nem szükséges, mert a bővítmény azonosítója és a host útvonala ugyanaz.
A környilas frissítés megőrzi a korábbi heti nyilvántartást.

A korábbi automatikus feltöltés a saját profilhoz számít.
Az új gomb arra a hétre már csak jelzi, hogy volt feltöltés.

## Első telepítés

```powershell
.\.venv\Scripts\python.exe -X utf8 -m cart_assistant.install
```

A telepítő saját felhasználói HKCU-regisztrációt készít; nem kell adminjog.
Chrome-ban `chrome://extensions` → Fejlesztői mód → Kicsomagolt bővítmény betöltése.
Mappa: `C:\private\interfood\extension`. A projekt mappája maradjon meg.

## Használat

1. Nyisd meg az Interfood étlapját, és jelentkezz be.
2. A jobb alsó sarokban válaszd ki, kinek kérsz ebédet.
3. Nyomd meg a **Kosárba teszem** gombot.
4. A kiválasztott személy napi fő ajánlata és két alternatívája kerül a kosárba.
5. Vedd ki, ami nem kell, majd te véglegesítsd a rendelést.

Második gombnyomásnál ugyanarra a személyre és hétre jelzi, hogy a feltöltés
már megtörtént. Üres kosárral, rendelés után, másnap és új étlapjelöltekkel sem
tölti fel újra ugyanazt a személyt. Megszakadt/bizonytalan futás sem indul újra;
a maradékot kézzel ellenőrizd.

Ha másik családtagnak ugyanaz az étel kell, egy új adag kerül be.
A korábbi személy által kézzel kivett adagot nem állítja vissza.
Az első személyhez egy már kézzel betett adag elfogadható; a meglévő más
tételeket és adagszámokat nem csökkenti.

A bővítmény ikonjánál a **Kosársegéd bekapcsolva** kapcsolóval kikapcsolható.
A helyi adatok törlése vagy a bővítmény eltávolítása törli a heti emlékezetet.
Másik fülön történt fiókváltás megszakítja a futást; frissítsd az aktív lapot.

## Családi profilok

`recommendation/profiles.json` tartalmazza a személyek listáját:

- `self` — Én: a meglévő `profile.json` szabályai.
- `wife` — Feleségem: még nincs konfigurálva.
- `son` — Fiam: még nincs konfigurálva.

A nem konfigurált profil a legördülőben látszik, de nem választható.
A saját preferenciák meghatározása után külön JSON-fájlt kell rendelni a
személy `file` mezőjéhez. Nincs automatikus másolás vagy fallback a saját profilra.

Példa: `{"id":"wife","name":"Feleségem","file":"profiles/wife.json"}`.
A profilfájl a recommendation/ könyvtáron belül legyen, a jelenlegi profile.json
sémájában. A tényleges értékeket az adott személy igényei alapján kell megadni.
A fehérje/zsírhatárok, sorpreferenciák és szombati lazítás mellett az
exclude_seafood, exclude_fruity_meat és prefer_breaded_saturday logikai
mezőkkel a kizárások és a rántott hús előnye is személyenként állítható.
A saját profilban mindhárom true, a korábbi szabályok szerint.

CLI: `python -m recommendation --person self`; a régi `--profile útvonal` is működik.
A Telegram heti workflow egyelőre a korábbi saját profile.json-t használja;
ez a módosítás nem küld új címzettnek és nem állít elő automatikus családi riportot.

A kosárterv az éppen betöltött étlapból számol újra; ha a forrás változott,
eltérhet a korábban elküldött Telegram-jelöltektől.

## Fejlesztői ellenőrzés

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest -v
node --test extension/tests/*.test.cjs
.\.venv\Scripts\python.exe -X utf8 scripts/check_cart_dom.py
```

A DOM-próba minden URL-t helyi HTML-re cserél; nincs valódi kosárkérés.
A felhasználói Chrome-ban az első valódi próba külön ellenőrzés.
Rendelést és fizetést a segéd nem véglegesít.

## Eltávolítás

Chrome → Bővítmények → Interfood kosársegéd → Eltávolítás.
A host regisztrációja külön törölhető PowerShellből:

```powershell
Remove-Item -LiteralPath 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\hu.interfood.menu_helper'
```
