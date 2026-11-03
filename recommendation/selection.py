"""Személyes ebédválasztás: tiszta, hálózat nélküli szabályok."""

import math
import re
import unicodedata
from datetime import date, timedelta
from html import unescape


def text(value):
    """HTML és ékezetek nélküli, kisbetűs szöveg."""
    plain = re.sub(r"<[^>]*>", "", unescape(value or ""))
    return "".join(c for c in unicodedata.normalize("NFKD", plain.casefold())
                   if not unicodedata.combining(c))


SEAFOOD = re.compile(
    r"\b(?:hal\w*|lazac\w*|tonhal\w*|hekk\w*|ponty\w*|harcsa\w*|"
    r"pisztrang\w*|sullo\w*|tokehal\w*|makrela\w*|szard\w*|szardella\w*|"
    r"pangasius\w*|tilapia\w*|tenger\w*|garnela\w*|kagylo\w*|"
    r"tintahal\w*|polip\w*|surimi\w*|scampi\w*|szepia\w*|"
    r"rak(?:ok|ot|kal|hus\w*|fele\w*|os)?)\b"
)
MEAT = re.compile(r"\b(?:csirke|pulyka|sertes|karaj|tarja|szuz|marha|borju|kacsa|liba|comb|mell|hus|sonka|bacon|nyul|szarvas|vaddiszno|oz|fasirt)\w*")
FRUIT = re.compile(r"\b(?:gyumolcs|ananasz|barack|oszibarack|sargabarack|szilva|meggy|cseresznye|alma(?!ecet)|korte|afonya|vorosafonya|mango|mazsola|szolo(?!mag)|narancs)\w*")
NOT_LUNCH = re.compile(r"leves|desszert|sutemeny|palacsinta|kenyer|kalacs|cipo|savanyusag")


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def recommend(menu, profile):
    """Fő ajánlat és legfeljebb két eltérő alternatíva naponta, módosítás nélkül."""
    if not isinstance(profile, dict):
        raise ValueError("Hibás személyes profil.")
    for key in ("min_protein_g", "max_fat_g", "min_protein_fat_ratio", "preferred_protein_fat_ratio"):
        if not valid_number(profile.get(key)):
            raise ValueError(f"Hibás profilérték: {key}")
    preferred = profile.get("preferred_categories")
    if not isinstance(preferred, list) or not all(isinstance(v, str) and v.strip() for v in preferred):
        raise ValueError("A sorpreferenciák szöveges listát igényelnek.")
    if not isinstance(profile.get("saturday_relaxed"), bool):
        raise ValueError("A szombati engedmény logikai érték legyen.")
    if profile["preferred_protein_fat_ratio"] < profile["min_protein_fat_ratio"]:
        raise ValueError("Az ideális arány nem lehet a minimum alatt.")
    if not isinstance(menu, dict) or menu.get("schema_version") != 1 or not isinstance(menu.get("meals"), list):
        raise ValueError("Nem támogatott vagy hibás étlapformátum.")
    start = date.fromisoformat(menu["week_start"])
    end = date.fromisoformat(menu["week_end"])
    if start.weekday() != 0 or end != start + timedelta(days=6):
        raise ValueError("Hibás heti dátumtartomány.")
    days = {}
    for meal in menu["meals"]:
        day = date.fromisoformat(meal["date"])
        if not start <= day <= end:
            raise ValueError("Az étel nem a megadott hétre esik.")
        if day.weekday() != 6:
            days.setdefault(day, []).append(meal)

    results = []
    for day, meals in sorted(days.items()):
        relaxed = day.weekday() == 5 and profile["saturday_relaxed"]
        candidates = []
        for meal in meals:
            name = text(meal["name"])
            ingredients = text(meal.get("ingredients_html"))
            components = " ".join(text(c.get("name")) for c in meal.get("components", []))
            category = text(meal.get("category"))
            group = text(meal.get("group"))
            description = " ".join((name, ingredients, components))
            if meal.get("order_disabled") or NOT_LUNCH.search(category + " " + group):
                continue
            if SEAFOOD.search(description):
                continue
            if MEAT.search(description) and (FRUIT.search(name + " " + components) or FRUIT.search(ingredients)):
                continue
            nutrition = meal.get("nutrition_per_portion") or {}
            protein, fat = nutrition.get("protein_g"), nutrition.get("fat_g")
            if not valid_number(protein) or not valid_number(fat):
                continue
            warnings = []
            if protein < profile["min_protein_g"]:
                warnings.append(f"A fehérje {profile['min_protein_g']:g} g alatt van.")
            if fat >= profile["max_fat_g"]:
                warnings.append(f"A zsír nem kevesebb {profile['max_fat_g']:g} g-nál.")
            if protein < profile["min_protein_fat_ratio"] * fat:
                warnings.append(f"A fehérje/zsír arány nem éri el a {profile['min_protein_fat_ratio']:g}:1 értéket.")
            if warnings and not relaxed:
                continue
            preferred = profile["preferred_categories"]
            rank = next((i for i, part in enumerate(preferred) if text(part) in category + " " + group), len(preferred))
            ideal = protein >= profile["preferred_protein_fat_ratio"] * fat
            fried_meat = bool(re.search(r"rantott|bunda|paniroz", name + " " + category)) and bool(MEAT.search(name))
            # Szombaton rántott hús; utána a sor, az ideális arány és a kisebb zsír.
            score = (0 if relaxed and fried_meat else 1,
                     protein < profile["min_protein_g"] if relaxed else False,
                     len(warnings), rank, not ideal, fat, -protein, str(meal["id"]))
            candidates.append((score, meal, warnings, ideal))
        if candidates:
            options = []
            seen_dishes = set()
            for _, selected, warnings, ideal in sorted(candidates, key=lambda candidate: candidate[0]):
                # A kis adag és a más körettel kínált azonos fogás nem új alternatíva.
                dish = next((text(part["name"]) for part in selected.get("components", [])
                             if part.get("name")), text(selected["name"]))
                dish = dish.split(",")[0].strip()
                if dish in seen_dishes:
                    continue
                seen_dishes.add(dish)
                reason = "Szombati, megengedőbb választás." if relaxed else "Megfelel a hétköznapi tápértékhatároknak."
                if ideal:
                    reason += f" A fehérje/zsír arány legalább {profile['preferred_protein_fat_ratio']:g}:1."
                options.append({"meal": selected, "reason": reason, "warnings": warnings})
                if len(options) == 3:
                    break
            results.append({"date": day.isoformat(), "relaxed": relaxed,
                            **options[0], "alternatives": options[1:]})
        else:
            results.append({"date": day.isoformat(), "meal": None, "relaxed": relaxed,
                            "reason": "Nincs a szabályoknak megfelelő, ismert tápértékű ebéd.",
                            "warnings": [], "alternatives": []})
    return results
