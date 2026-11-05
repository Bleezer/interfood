import io
import json
import struct
import unittest
from datetime import date

from cart_assistant.host import handle_request, read_message, write_message
from interfood.normalization import NUTRIENTS


def payload(day="2026-11-09"):
    item = {"id": 1, "date": day, "food": {"id": 2, "name": "Csirkemell, rizs"},
            "food_name_one": "Csirkemell", "weight_food_one": 400, "disabled": False}
    for source in NUTRIENTS.values():
        item[f"{source}_portion_food_one"] = 10
    item["protein_portion_food_one"] = 60
    item["fat_portion_food_one"] = 20
    return {"data": {"1": {"name": "Fitness", "categories": [
        {"code": "E1", "name": "Fitness", "items": [item]}]}}}


class CartHostTests(unittest.TestCase):
    def test_plan_uses_existing_rules_and_one_of_each(self):
        response = handle_request({"type": "plan", "payload": payload()}, date(2026, 11, 5))
        self.assertTrue(response["ok"])
        self.assertEqual(response["plan"]["week_start"], "2026-11-09")
        self.assertEqual([(x["id"], x["quantity"]) for x in response["plan"]["items"]], [(1, 1)])

    def test_stale_week_and_unknown_commands_rejected(self):
        for request in [{"type": "plan", "payload": payload("2026-11-02")},
                        {"type": "checkout"}, {"type": "plan", "payload": {"data": {}}}]:
            with self.subTest(request=request):
                self.assertFalse(handle_request(request, date(2026, 11, 5))["ok"])

    def test_protocol_roundtrip_utf8(self):
        stream = io.BytesIO()
        message = {"étel": "Tavaszi csirkemell rizottó"}
        write_message(stream, message)
        stream.seek(0)
        self.assertEqual(read_message(stream), message)

    def test_truncated_or_oversized_frames_rejected(self):
        self.assertIsNone(read_message(io.BytesIO()))
        for data in [b"x", struct.pack("=I", 100) + b"{}", struct.pack("=I", 10_000_000)]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                read_message(io.BytesIO(data))

    def test_invalid_payload_types_return_error_without_crashing(self):
        for value in [None, [], "menu", 123]:
            with self.subTest(value=value):
                self.assertFalse(handle_request({"type": "plan", "payload": value}, date(2026, 11, 5))["ok"])
