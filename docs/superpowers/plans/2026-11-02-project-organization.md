# Project Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Átlátható mappák és felelősségenként szétválasztott Python-modulok, az eddigi működés megőrzésével.

**Architecture:** Egyszerű gyökérszintű `interfood/` csomag. A régi indítófájl kompatibilitási továbbító marad, a tesztek és a kézi próbák saját mappába kerülnek.

**Tech Stack:** Python, unittest, Playwright; meglévő requirements.txt.

**Spec:** `docs/superpowers/specs/2026-11-02-project-organization-design.md`

## Global Constraints

- A gyűjtés működése, a JSON formátuma és a mentett adatok helye változatlan.
- Nincs új függőség, bejelentkezés, rendelés vagy kosármódosítás.
- A régi `python collect_menu.py` parancs tovább működik.
- Az offline ellenőrzések nem írják felül a meglévő adatokat.
- A munkamenetben a Git nem ismeri fel tárolóként a `C:\private\interfood` mappát; új tároló létrehozása nem része a rendezésnek.

## Review Focus

- A csomagból számított kimeneti útvonal továbbra is a gyökér `data/` mappája.
- A korábbi importálási felület és indítás használható marad.
- Az alapértelmezett unittest-felderítés megtalálja az áthelyezett teszteket.
- A mentett nyers étlap ugyanazokat a feldolgozott tételeket eredményezi.
- Az atomikus mentés és a magyar ékezetek megőrzése működik.

### Task 1: A gyűjtő modulokra bontása

**Files:** `interfood/__init__.py`, `interfood/__main__.py`, `interfood/dates.py`, `interfood/normalization.py`, `interfood/collector.py`, `interfood/storage.py`, `interfood/cli.py`, `collect_menu.py`.

**Interfaces:** A meglévő `next_monday(today)`, `number(value)`, `normalize_item(item, category, group)`, `normalize_menu(payload, monday)`, `fetch_menu(monday)`, `save_json(path, data)` és `main()` aláírások maradnak. A `NUTRIENTS`, `SITE`, `API`, `OUTPUT` értékek a felelős modulokban kapnak helyet; a régi modul újraexportálja őket.

- [x] Rögzítsük offline összehasonlítással, hogy a jelenlegi nyers és feldolgozott étlap tételei egyeznek; jegyezzük fel az adatfájlok SHA256 lenyomatát.
- [x] Mozgassuk át a függvényeket a specifikáció szerinti modulokba, logikai módosítás nélkül. Az `OUTPUT` a csomag szülőkönyvtárában levő `data/` legyen.
- [x] Készítsük el a csomagbelépést és a kompatibilitási továbbítót.
- [x] Futtassuk: `.\.venv\Scripts\python.exe -X utf8 -m unittest -v`; elvárt: öt sikeres teszt.
- [x] Offline ellenőrizzük az `OUTPUT` értékét, a belépési pontok azonosságát, a nyers adatok normalizálásának egyezését és a JSON-mentést ideiglenes könyvtárban.

### Task 2: Mappák és projektútmutató

**Files:** `tests/__init__.py`, `tests/test_normalization.py`, `scripts/try_interfood.py`, `README.md`, `AGENTS.md`, `.gitignore`.

**Interfaces:** A tesztek közvetlenül az `interfood.dates` és `interfood.normalization` modulokat használják. A kézi próba önálló script marad.

- [x] Helyezzük át a meglévő teszteket és a kézi böngészőpróbát; hozzuk létre a tesztcsomagot a felderítéshez.
- [x] Frissítsük a README-t a mappatérképpel, a virtuális környezet létrehozásával, az új és a régi indítóparanccsal, valamint az offline tesztparanccsal.
- [x] Írjuk le az AGENTS.md-ben a felelősségi határokat, a tesztparancsot, az adatmegőrzést és a gyűjtő működési korlátait; egészítsük ki a gitignore-t az ideiglenes mentésekkel.
- [x] Futtassuk újra az alapértelmezett unittest-felderítést és a modulok fordíthatósági ellenőrzését; elvárt: öt sikeres teszt és nulla fordítási hiba.
- [x] Ellenőrizzük a fájlfát, a mentett adatok változatlan lenyomatát és a specifikáció minden pontját.

## Végrehajtás

Javaslat: közvetlen végrehajtás ebben a munkamenetben. A két feladat szorosan
összefügg, a változás kis méretű, a meglévő offline adatokkal ellenőrizhető.
Commit nem készült, mert a munkamenetben a Git nem ismerte fel tárolóként a munkamappát.
