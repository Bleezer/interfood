import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from recommendation.selection import recommend

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "recommendation/profile.json").read_text(encoding="utf-8"))


def meal(identity=1, day="2026-11-09", name="Roston csirkemell, rizs", protein=60, fat=20, category="Fitness és alakbarát", **extra):
    return dict(id=identity, date=day, code=str(identity), name=name, category=category,
                group="Főétel", ingredients_html="csirkemell, rizs",
                components=[], order_disabled=False,
                nutrition_per_portion={"protein_g": protein, "fat_g": fat}, **extra)


def menu(*meals):
    return {"schema_version": 1, "week_start": "2026-11-09", "week_end": "2026-11-15",
            "available_dates": sorted({m["date"] for m in meals}), "meals": list(meals)}


class RecommendationTests(unittest.TestCase):
    def choose(self, *meals):
        return recommend(menu(*meals), PROFILE)

    def test_thresholds_and_missing_values(self):
        for protein, fat, allowed in [(40, 20, True), (39.9, 10, False),
                                      (60, 30, False), (40, 20.1, False),
                                      (40, 0, True), (None, 10, False),
                                      (40, None, False), (float("nan"), 10, False),
                                      (40, -1, False), (float("inf"), 10, False)]:
            with self.subTest(protein=protein, fat=fat):
                selected = self.choose(meal(protein=protein, fat=fat))[0]["meal"]
                self.assertEqual(selected is not None, allowed)

    def test_preferred_category_then_ideal_ratio(self):
        candidates = [meal(1, category="Sport és egészség", protein=80, fat=10),
                      meal(2, protein=40, fat=20), meal(3, protein=60, fat=20)]
        self.assertEqual(self.choose(*candidates)[0]["meal"]["id"], 3)
        self.assertEqual(self.choose(*reversed(candidates))[0]["meal"]["id"], 3)

    def test_exclusions_in_names_and_html(self):
        for name in ["Rántott hal", "Lazac", "Tonhal", "Garnélás rizs", "Kagyló",
                     "Ananászos csirkemell", "Barackos pulyka", "Csirkemell meggyszósszal"]:
            with self.subTest(name=name):
                self.assertIsNone(self.choose(meal(name=name))[0]["meal"])
        candidate = meal()
        candidate["ingredients_html"] = "rizs, <b>hal</b>szósz"
        self.assertIsNone(self.choose(candidate)[0]["meal"])
        self.assertIsNotNone(self.choose(meal(name="Mustáros csirkemell"))[0]["meal"])

    def test_saturday_relaxed_but_exclusions_remain(self):
        healthy = meal(1, day="2026-11-14")
        fried = meal(2, day="2026-11-14", name="Rántott sertéskaraj, rizs", protein=35, fat=45, category="Rántott")
        fish = meal(3, day="2026-11-14", name="Rántott hekk", category="Rántott")
        result = self.choose(healthy, fried, fish)[0]
        self.assertEqual(result["meal"]["id"], 2)
        self.assertTrue(result["relaxed"])
        self.assertEqual(len(result["warnings"]), 3)

    def test_only_available_days_and_no_sunday(self):
        result = self.choose(meal(day="2026-11-10"), meal(2, day="2026-11-15"))
        self.assertEqual([r["date"] for r in result], ["2026-11-10"])
        self.assertEqual(self.choose(), [])

    def test_no_candidate_and_non_lunch_categories(self):
        dessert = meal(category="Sport desszert", name="Protein sütemény")
        salad = meal(2, category="Friss saláták")
        salad["order_disabled"] = True
        self.assertIsNone(self.choose(dessert, salad)[0]["meal"])

    def test_input_is_not_modified(self):
        source = menu(meal())
        before = copy.deepcopy(source)
        recommend(source, PROFILE)
        self.assertEqual(source, before)

    def test_wrong_schema_or_dates_rejected(self):
        for source in [{"meals": []}, menu(meal(day="2026-11-16"))]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                recommend(source, PROFILE)

    def test_cli_offline_and_missing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu.json"
            path.write_text(json.dumps(menu(meal()), ensure_ascii=False), encoding="utf-8")
            run = subprocess.run([sys.executable, "-X", "utf8", "-m", "recommendation", "--menu", str(path)],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Roston csirkemell", run.stdout)
            self.assertIn("60", run.stdout)
            missing = subprocess.run([sys.executable, "-X", "utf8", "-m", "recommendation", "--menu", str(path.with_name("absent.json"))],
                                     cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(missing.returncode, 0)
            self.assertNotIn("Traceback", missing.stderr)

    def test_saturday_breaded_meat_prefers_full_portion(self):
        small = meal(1, day="2026-11-14", name="Pulykamell párizsi bundában", protein=29.4, fat=8.7, category="Kis rántott")
        full = meal(2, day="2026-11-14", name="Pulykamell párizsi bundában", protein=47, fat=14, category="Rántott")
        healthy = meal(3, day="2026-11-14", protein=70, fat=10)
        vegetable = meal(4, day="2026-11-14", name="Rántott sajt", category="Rántott")
        vegetable["ingredients_html"] = "sajt"
        self.assertEqual(self.choose(small, full, healthy, vegetable)[0]["meal"]["id"], 2)

    def test_karcsusito_group_precedes_sport_category(self):
        slimming = meal(1, category="Főétel")
        slimming["group"] = "Karcsúsító"
        sport = meal(2, category="Sport és egészség")
        self.assertEqual(self.choose(sport, slimming)[0]["meal"]["id"], 1)

    def test_fruit_derivatives_are_not_fruity_meat(self):
        candidate = meal()
        candidate["ingredients_html"] = "csirkemell, almaecet, szőlőmagolaj"
        self.assertIsNotNone(self.choose(candidate)[0]["meal"])

    def test_invalid_profile_thresholds_are_rejected(self):
        keys = ["min_protein_g", "max_fat_g", "min_protein_fat_ratio", "preferred_protein_fat_ratio"]
        for key in keys:
            for invalid in [float("nan"), float("inf"), -1, True, "40", None]:
                profile = dict(PROFILE, **{key: invalid})
                with self.subTest(key=key, invalid=invalid), self.assertRaises(ValueError):
                    recommend(menu(meal(protein=1, fat=100)), profile)
        for profile in [None, [], dict(PROFILE, preferred_categories="fitness"),
                        dict(PROFILE, saturday_relaxed="false")]:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                recommend(menu(meal()), profile)

    def test_custom_profile_warnings_match_thresholds(self):
        profile = dict(PROFILE, min_protein_g=50, max_fat_g=25, min_protein_fat_ratio=3)
        result = recommend(menu(meal(day="2026-11-14", protein=40, fat=30)), profile)[0]
        self.assertIn("50", result["warnings"][0])
        self.assertIn("25", result["warnings"][1])
        self.assertIn("3", result["warnings"][2])

    def test_two_alternatives_keep_primary_and_skip_repeated_dishes(self):
        first = meal(1, name="Roston csirkemell, zöldség", fat=10)
        same = meal(2, name="Roston csirkemell, rizs", fat=11)
        second = meal(3, name="Tavaszi csirkemell rizottó", fat=15)
        third = meal(4, name="Székelykáposzta csirkemellből", fat=16)
        fourth = meal(5, name="Fitt parajfőzelék, csirkefalatok", fat=17)
        source = [first, same, second, third, fourth]
        result = self.choose(*source)[0]
        self.assertEqual(result["meal"]["id"], 1)
        self.assertEqual([option["meal"]["id"] for option in result["alternatives"]], [3, 4])
        self.assertEqual(result, self.choose(*reversed(source))[0])

    def test_alternatives_obey_exclusions_and_numeric_limits(self):
        first = meal(1, name="Rizottó")
        second = meal(2, name="Székelykáposzta", fat=19)
        forbidden = meal(3, name="Lazac", fat=10)
        fatty = meal(4, name="Sült karaj", fat=35)
        result = self.choose(first, second, forbidden, fatty)[0]
        options = [result] + result["alternatives"]
        self.assertEqual({option["meal"]["id"] for option in options}, {1, 2})
        self.assertTrue(all(option["reason"] for option in options))

    def test_no_fabricated_alternatives(self):
        self.assertEqual(self.choose(meal())[0]["alternatives"], [])
        self.assertEqual(self.choose(meal(protein=10))[0]["alternatives"], [])

    def test_saturday_alternative_has_its_own_warnings(self):
        full = meal(1, day="2026-11-14", name="Rántott karaj", protein=60, fat=20)
        low = meal(2, day="2026-11-14", name="Rántott pulykamell", protein=35, fat=45)
        result = self.choose(full, low)[0]
        self.assertEqual(result["warnings"], [])
        self.assertEqual(len(result["alternatives"][0]["warnings"]), 3)

    def test_cli_prints_both_alternatives_and_their_nutrition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu.json"
            source = menu(meal(1, name="Rizottó", fat=10),
                          meal(2, name="Székelykáposzta", fat=15),
                          meal(3, name="Parajfőzelék", fat=19))
            path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
            run = subprocess.run([sys.executable, "-X", "utf8", "-m", "recommendation", "--menu", str(path)],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Alternatíva 1", run.stdout)
            self.assertIn("Alternatíva 2", run.stdout)
            self.assertIn("Székelykáposzta", run.stdout)
            self.assertIn("Parajfőzelék", run.stdout)
            self.assertEqual(run.stdout.count("Fehérje:"), 3)

    def test_bundled_component_and_missing_components_share_dish_identity(self):
        first = meal(1, name="Roston csirkemell, brokkoli", fat=10)
        first["components"] = [{"name": "Roston csirkemell, brokkoli"}]
        same = meal(2, name="Roston csirkemell, rizs", fat=11)
        same["components"] = [{"name": "Roston csirkemell"}]
        fallback = meal(3, name="Roston csirkemell, burgonya", fat=12)
        different = meal(4, name="Rizottó", fat=15)
        result = self.choose(first, same, fallback, different)[0]
        self.assertEqual([option["meal"]["id"] for option in result["alternatives"]], [4])
