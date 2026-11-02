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
- `tests/`: offline tesztek; `scripts/`: kézi próbák.

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
.\.venv\Scripts\python.exe -m compileall -q interfood tests scripts collect_menu.py
```

Gyűjtés: `.\.venv\Scripts\python.exe -X utf8 -m interfood`.
A korábbi `collect_menu.py` belépési pont is maradjon működőképes.
Új függőséget csak indokolt esetben adj hozzá; a verziók a `requirements.txt` fájlban vannak.
Superpowers tervek: `docs/superpowers/plans/`; specifikációk: `docs/superpowers/specs/`.
