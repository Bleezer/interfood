"""Közös, egyszerű szöveges ajánló terminálhoz és értesítéshez."""


def format_report(menu, results):
    lines = [f"Ebédajánlatok: {menu['week_start']} – {menu['week_end']}",
             "Név és összetevők alapján, helyi szabályokkal; az összetevőket ellenőrizd."]
    for result in results:
        if result["meal"] is None:
            lines.append(f"{result['date']}: {result['reason']}")
            continue
        for index, option in enumerate([result] + result["alternatives"]):
            meal = option["meal"]
            label = "Fő ajánlat" if index == 0 else f"Alternatíva {index}"
            nutrition = meal["nutrition_per_portion"]
            lines.append(f"{result['date']} – {label}: [{meal['code']}] {meal['name']} ({meal['category']})")
            lines.append(f"  Fehérje: {nutrition['protein_g']:g} g; zsír: {nutrition['fat_g']:g} g.")
            lines.append(f"  {option['reason']}")
            lines.extend(f"  Eltérés: {warning}" for warning in option["warnings"])
    if not results:
        lines.append("Nincs kínált hétfő–szombati nap az étlapban.")
    return "\n".join(lines) + "\n"
