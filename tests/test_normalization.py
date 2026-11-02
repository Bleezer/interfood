import unittest
from datetime import date

from interfood.dates import next_monday
from interfood.normalization import NUTRIENTS, normalize_item, normalize_menu


class MenuTests(unittest.TestCase):
    def test_next_week_at_year_boundary_and_on_sunday(self):
        self.assertEqual(next_monday(date(2026, 12, 31)), date(2027, 1, 4))
        self.assertEqual(next_monday(date(2026, 11, 8)), date(2026, 11, 9))
        self.assertEqual(next_monday(date(2026, 11, 9)), date(2026, 11, 16))

    def item(self):
        item = {"id": 1, "date": "2026-11-09", "food": {"id": 2, "name": "Menü"}}
        for suffix, value in (("one", 10), ("two", 20)):
            item[f"food_name_{suffix}"] = suffix
            item[f"weight_food_{suffix}"] = 200
            for source in NUTRIENTS.values():
                item[f"{source}_portion_food_{suffix}"] = value
        return item

    def normalize(self, item):
        return normalize_item(item, {"code": "M", "name": "Menü"}, {"name": "Menük"})

    def test_composite_portions_are_added(self):
        self.assertEqual(self.normalize(self.item())["nutrition_per_portion"]["protein_g"], 30)

    def test_zero_weight_side_dish_does_not_erase_total(self):
        item = self.item()
        item["weight_food_two"] = 0
        for source in NUTRIENTS.values():
            item[f"{source}_portion_food_two"] = 0
        result = self.normalize(item)
        self.assertEqual(result["nutrition_per_portion"]["protein_g"], 10)
        self.assertTrue(result["components"][1]["zero_weight_placeholder"])

    def test_missing_component_is_not_treated_as_zero(self):
        item = self.item()
        del item["protein_portion_food_two"]
        self.assertIsNone(self.normalize(item)["nutrition_per_portion"]["protein_g"])

    def test_empty_and_wrong_week_are_rejected(self):
        monday = date(2026, 11, 9)
        with self.assertRaises(ValueError):
            normalize_menu({"data": {}}, monday)
        item = self.item()
        item["date"] = "2026-11-02"
        payload = {"data": {"1": {"categories": [{"items": [item]}]}}}
        with self.assertRaises(ValueError):
            normalize_menu(payload, monday)


if __name__ == "__main__":
    unittest.main()
