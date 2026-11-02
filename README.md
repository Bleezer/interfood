# Interfood étlapgyűjtő

A program a Europe/Budapest szerinti következő hétfőtől vasárnapig tartó
időszak teljes, nyilvánosan megjelenő ételválasztékát menti. Nem jelentkezik
be, nem módosít kosarat és nem rendel. Nincsenek személyes ízlési szűrők:
ugyanazt az adatot később több családtag ajánlója is használhatja.

## Telepítés és futtatás Windows PowerShellben

A parancsokat a projekt gyökérmappájából futtasd. Első telepítéskor hozz létre
virtuális környezetet (a már meglévőt nem kell újra létrehozni).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -X utf8 -m interfood
```

A virtuális környezet aktiválása nem szükséges, mert közvetlenül annak
Pythonját indítjuk. A gyűjtő látható ablak nélkül fut.

A korábbi indítás is használható:

```powershell
.\.venv\Scripts\python.exe -X utf8 collect_menu.py
```

## Projektfelépítés

```text
interfood/
    __init__.py          # Python-csomag
    __main__.py          # python -m interfood
    cli.py               # Heti futtatás és összefoglaló
    collector.py         # Böngészős gyűjtés és oldalellenőrzés
    dates.py             # Következő hétfő számítása
    normalization.py     # Étlapellenőrzés és tápérték-feldolgozás
    storage.py           # Atomikus JSON-mentés
tests/                   # Offline unittest tesztek
scripts/try_interfood.py # Kézi böngészőpróba
data/                    # Feldolgozott és nyers heti adatok
inspection/              # Helyi vizsgálati adatok (Gitből kizárva)
docs/superpowers/        # Specifikációk és végrehajtási tervek
collect_menu.py          # Korábbi belépési és importálási felület
AGENTS.md                # Projektutasítások
requirements.txt         # Rögzített függőségek
```

## Eredmény

- `data/menu-YYYY-MM-DD.json`: feldolgozott heti étlap, a hétfő dátumával.
- `data/raw/YYYY-MM-DD.json`: eredeti étlapválasz, későbbi ellenőrzéshez.

A `meals` lista egy eleme egy dátumhoz és ételkódhoz tartozó ajánlat.
A kis adagok külön tételek, a levesek, desszertek és pékáruk is megmaradnak.
Azonos nevű étel több napon is szerepelhet; ezek nem duplikátumok.
A `available_dates` az oldal által ténylegesen kínált napokat tartalmazza,
nem feltételezünk minden napra választékot.

A `nutrition_per_portion` adagonkénti kcal- és grammértékeket tartalmaz.
A `components` megőrzi a fogások bontását. Többfogásos menünél összeadjuk
az értékeket. A forrás néha a köret nevét nulla tömeggel és teljesen nullás
tápértékkel külön is felsorolja, miközben az első sor a teljes adagot adja meg.
Ezeket `zero_weight_placeholder` jelöli; az összegbe nem számítanak bele.
A ténylegesen hiányzó vagy teljesen nullás, pozitív tömegű fogásadat `null`.
A `source_icons` a forrás saját jelöléseit őrzi; nem jelent külön ellenőrzött
allergénbesorolást. Az összetevők eredeti HTML-je az `ingredients_html` mező.

Az adatokat a nem dokumentált, nyilvános webes felület háttérválaszaiból
olvassuk Playwrighttal. Az oldal változása esetén szükség lehet igazításra.
A dátumokat, az azonosítókat és a megjelenő napok egyezését ellenőrizzük;
ez nem bizonyítja, hogy a szolgáltató már minden jövő heti ételt feltöltött.
Ha a következő hét még nem elérhető, üres vagy hibás, a program hibával leáll,
és nem írja felül a korábbi heti eredményt. A JSON cseréje atomikus.

## Ellenőrzés

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

A tesztek hálózat és böngészőindítás nélkül futnak. A kézi böngészőpróba
külön indítható, látható Chromium-ablakkal:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/try_interfood.py
```

Az időzített felhős futás, a távoli tartós tárolás és a családtagonkénti
ajánlás még nincs bekötve. A helyi JSON ezek közös bemenete lesz.
