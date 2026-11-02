# A projekt rendezése

## Cél és elfogadott irány

A felhasználó a mappák és a kód rendezését kérte, és jóváhagyta az egyszerű
`interfood/` csomagszerkezetet. A kis, helyben futtatott gyűjtő számára ez
kevesebb beállítást igényel, mint egy telepíthető `src/` elrendezés.

## Megfontolt megoldások

- **Választott:** gyökérszintű Python-csomag, külön gyűjtő-, feldolgozó- és
  mentési modulokkal; `tests/`, `scripts/`, `docs/` mappákkal.
- **Alternatíva:** `src/interfood/` és telepíthető parancs `pyproject.toml`
  segítségével. Újrafelhasználható csomagnál előnyös, most indokolatlan többlet.

## Szerkezet és felelősségek

- `interfood/normalization.py`: tápértékek, számalakítás és étlapellenőrzés.
- `interfood/dates.py`: a következő hétfő kiszámítása.
- `interfood/collector.py`: Playwright, nyilvános végpontok és oldalellenőrzés.
- `interfood/storage.py`: atomikus JSON-mentés.
- `interfood/cli.py`: a gyűjtés összehangolása és az eredmény összefoglalása.
- `interfood/__main__.py`: `python -m interfood` belépési pont.
- `collect_menu.py`: a korábbi futtatási és importálási felület vékony továbbítója.
- `tests/`: automatikus tesztek; `scripts/`: kézi böngészőpróba.
- `data/`, `inspection/`: a meglévő adatok eredeti helye.
- `README.md`: telepítés, parancsok és mappatérkép.
- `AGENTS.md`: a projekt működési korlátai és ellenőrzési parancsai.

## Korlátok

A gyűjtés működése, a JSON formátuma és a mentett adatok helye változatlan.
Nincs új függőség, bejelentkezés, rendelés vagy kosármódosítás.
A régi `python collect_menu.py` parancs tovább működik.
Az offline ellenőrzések nem írják felül a meglévő adatokat.
A munkamenetben a Git nem ismeri fel tárolóként a `C:\private\interfood` mappát;
új tároló létrehozása nem része a rendezésnek.

## Ellenőrzés

Az öt meglévő teszt az átszervezés előtt sikeres. Áthelyezés után ezeket
újra futtatjuk; a mentett nyers étlap feldolgozását összevetjük a meglévő
eredménnyel. Ideiglenes könyvtárban ellenőrizzük a mentést, és ellenőrizzük,
hogy a két belépési pont ugyanazt a főfüggvényt használja. Élő gyűjtés
nem szükséges a szerkezeti átalakítás igazolásához.
