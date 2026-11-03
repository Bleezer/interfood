# Projektutasítások

## Cél

A program a következő hét nyilvános Interfood-étlapját gyűjti helyi JSON-ba.
A feldolgozott adat későbbi, több családtag számára készülő ajánlások bemenete.

## Modulhatárok

- `interfood/collector.py`: Playwright és a nyilvános oldal ellenőrzése.
- `interfood/normalization.py`: tiszta feldolgozás és adatellenőrzés.
- `interfood/dates.py`: dátumszámítás.
- `interfood/storage.py`: atomikus UTF-8 JSON-mentés.
- `interfood/cli.py`: a futás összehangolása; `__main__.py`: modulbelépés.
- `collect_menu.py`: a korábbi parancs és publikus nevek kompatibilitása.
- `tests/`: offline tesztek.

## Működési korlátok

- A gyűjtő nem jelentkezik be, nem módosít kosarat és nem rendel.
- A dátumszámítás időzónája `Europe/Budapest`.
- A gyűjtés minden nyilvánosan kínált tételt megőriz; nincs személyes szűrés.
- A hiányzó tápérték nem nulla; a nulla tömegű helykitöltők kezelése maradjon meg.
- Hibás vagy üres étlap esetén ne írjuk felül a korábbi heti eredményt.
- A JSON formátumát és a `data/` kimeneti helyét csak külön feladat keretében változtasd.
- A meglévő `data/` és `inspection/` adatokat ne töröld vagy írd át rendezéskor.
- Az offline tesztek ne indítsanak valódi gyűjtést és ne módosítsák a mentett adatokat.

## Ellenőrzés és futtatás

A projekt gyökeréből, PowerShellben:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest -v
.\.venv\Scripts\python.exe -m compileall -q interfood recommendation delivery tests collect_menu.py
```

Gyűjtés: `.\.venv\Scripts\python.exe -X utf8 -m interfood`.
A korábbi `collect_menu.py` belépési pont is maradjon működőképes.
Új függőséget csak indokolt esetben adj hozzá; a verziók a `requirements.txt` fájlban vannak.
Superpowers tervek: `docs/superpowers/plans/`; specifikációk: `docs/superpowers/specs/`.

## Ebédválogatás

- `recommendation/`: offline válogatás a `data/menu.json` fájlból; nem importál gyűjtőt vagy Playwrightot.
- `recommendation/profile.json`: személyes tápértékhatárok és sorpreferenciák.
- A gyűjtő a `data/menu.json` és `data/raw.json` fájlokat cseréli; a régi dátumos adatokat rendezéskor megőrizzük.
- Kínálat nélküli napra és vasárnapra nincs ajánlás; szombaton csak a tápértékhatárok lazulnak.

## Kézbesítés

- `delivery/`: Telegram-kézbesítés; nem jelentkezik be az Interfood oldalára és nem rendel.
- `recommendation/report.py`: a CLI és a Telegram közös szöveges riportja.
- Token és chat-azonosító kizárólag Actions Secrets-be kerülhet, kódba vagy naplóba nem.
- Az offline tesztek a HTTP-hívásokat helyettesítik; valódi értesítést nem küldhetnek.
