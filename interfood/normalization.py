"""A nyers étlap ellenőrzése és egységesítése."""

import math
from datetime import date, timedelta

NUTRIENTS = {
    "energy_kcal": "energy",
    "protein_g": "protein",
    "fat_g": "fat",
    "carbohydrate_g": "carb",
    "saturated_fat_g": "saturated_fat",
    "sugar_g": "sugar",
    "salt_g": "salt",
}


def number(value):
    if value is None or value == "":
        return None
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"Érvénytelen szám: {value!r}")
    return result


def normalize_item(item, category, group):
    components = []
    for suffix in ("one", "two", "three"):
        name = item.get(f"food_name_{suffix}")
        if not name:
            continue
        nutrition = {
            key: number(item.get(f"{source}_portion_food_{suffix}"))
            for key, source in NUTRIENTS.items()
        }
        weight = number(item.get(f"weight_food_{suffix}"))
        placeholder = suffix != "one" and weight == 0 and all(v == 0 for v in nutrition.values())
        # A teljesen nullás tápértéksor nem használható tápértékadatként.
        if all(value in (None, 0) for value in nutrition.values()):
            nutrition = dict.fromkeys(NUTRIENTS)
        components.append({
            "name": name,
            "weight_g": weight,
            "zero_weight_placeholder": placeholder,
            "nutrition_per_portion": nutrition,
        })
    totals = {}
    for key in NUTRIENTS:
        values = [part["nutrition_per_portion"][key] for part in components if not part["zero_weight_placeholder"]]
        totals[key] = round(sum(values), 3) if values and all(v is not None for v in values) else None
    food = item["food"]
    return {
        "id": item["id"],
        "food_id": food["id"],
        "date": item["date"],
        "code": category["code"],
        "category": category["name"],
        "group": group["name"],
        "name": food.get("display_name") or food["name"],
        "price_huf": number(item.get("price")),
        "order_disabled": item.get("disabled"),
        "order_deadline": item.get("order_disabled_at"),
        "ingredients_html": item.get("description"),
        "source_icons": item.get("menu_icons", []),
        "nutrition_per_portion": totals,
        "components": components,
    }


def normalize_menu(payload, monday):
    if payload.get("error") or not isinstance(payload.get("data"), dict):
        raise ValueError("Az étlapválasz hibás vagy megváltozott a szerkezete.")
    meals = []
    seen = set()
    for group in payload["data"].values():
        for category in group["categories"]:
            if category.get("weekly_menus"):
                raise ValueError("Új heti menüstruktúra jelent meg; előbb ellenőrizni kell.")
            for item in category["items"]:
                day = date.fromisoformat(item["date"])
                if not monday <= day <= monday + timedelta(days=6):
                    raise ValueError(f"Másik hét adata érkezett: {day}")
                if item["id"] in seen:
                    raise ValueError(f"Ismétlődő étlapazonosító: {item['id']}")
                seen.add(item["id"])
                meals.append(normalize_item(item, category, group))
    if not meals:
        raise ValueError("A következő heti étlap üres; nem mentünk üres eredményt.")
    return sorted(meals, key=lambda meal: (meal["date"], meal["code"], meal["id"]))
