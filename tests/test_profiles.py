import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from recommendation.profiles import list_profiles, load_profile
from cart_assistant.host import handle_request
from tests.test_cart_assistant import payload
from datetime import date


class ProfileTests(unittest.TestCase):
    def test_only_self_configured_no_invented_family_preferences(self):
        profiles = {p["id"]: p for p in list_profiles()}
        self.assertTrue(profiles["self"]["configured"])
        self.assertFalse(profiles["wife"]["configured"])
        self.assertFalse(profiles["son"]["configured"])
        self.assertEqual(load_profile("self")["min_protein_g"], 40)
        for identity in ["wife", "son", "../profile", "missing"]:
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                load_profile(identity)

    def test_configured_person_uses_own_thresholds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"custom.json").write_text(json.dumps({"min_protein_g": 75}), encoding="utf-8")
            (root/"profiles.json").write_text(json.dumps({
                "default_profile_id":"custom",
                "profiles":[{"id":"custom","name":"Custom","file":"custom.json"}]}),encoding="utf-8")
            with patch("recommendation.profiles.CATALOG",root/"profiles.json"):
                self.assertEqual(load_profile("custom")["min_protein_g"],75)
                self.assertTrue(list_profiles()[0]["configured"])

    def test_native_lists_profiles_and_rejects_unconfigured_or_unspecified(self):
        self.assertTrue(handle_request({"type":"profiles"})["ok"])
        for identity in [None, "wife", "son", "missing"]:
            request={"type":"plan","payload":payload(),"profile_id":identity}
            with self.subTest(identity=identity):
                self.assertFalse(handle_request(request,date(2026,11,5))["ok"])

    def test_native_response_carries_selected_person(self):
        response=handle_request({"type":"plan","payload":payload(),"profile_id":"self"},date(2026,11,5))
        self.assertTrue(response["ok"])
        self.assertEqual(response["plan"]["profile_id"],"self")

    def test_native_recommends_with_selected_person_not_self_rules(self):
        own = load_profile("self")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"strict.json").write_text(json.dumps(dict(own, min_protein_g=75)),encoding="utf-8")
            (root/"profiles.json").write_text(json.dumps({
                "default_profile_id":"strict",
                "profiles":[{"id":"strict","name":"Strict","file":"strict.json"}]}),encoding="utf-8")
            with patch("recommendation.profiles.CATALOG",root/"profiles.json"):
                result=handle_request({"type":"plan","profile_id":"strict","payload":payload()},date(2026,11,5))
                self.assertTrue(result["ok"])
                self.assertEqual(result["plan"]["profile_id"],"strict")
                self.assertEqual(result["plan"]["items"],[])

    def test_profile_file_cannot_escape_profile_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"profiles.json").write_text(json.dumps({
                "default_profile_id":"bad",
                "profiles":[{"id":"bad","name":"Bad","file":"../outside.json"}]}),encoding="utf-8")
            with patch("recommendation.profiles.CATALOG",root/"profiles.json"):
                with self.assertRaises(ValueError):
                    list_profiles()

    def test_food_exclusions_can_differ_between_people(self):
        from recommendation.selection import recommend
        from tests.test_recommendation import meal, menu, PROFILE
        fish=menu(meal(name="Lazac", category="Főétel"))
        fruit=menu(meal(name="Ananászos csirkemell"))
        self.assertIsNone(recommend(fish,PROFILE)[0]["meal"])
        self.assertIsNone(recommend(fruit,PROFILE)[0]["meal"])
        other=dict(PROFILE,exclude_seafood=False,exclude_fruity_meat=False)
        self.assertIsNotNone(recommend(fish,other)[0]["meal"])
        self.assertIsNotNone(recommend(fruit,other)[0]["meal"])

    def test_optional_personal_preferences_reject_non_boolean_values(self):
        from recommendation.selection import recommend
        from tests.test_recommendation import meal, menu, PROFILE
        for key in ["exclude_seafood","exclude_fruity_meat","prefer_breaded_saturday"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                recommend(menu(meal()),dict(PROFILE,**{key:"false"}))
