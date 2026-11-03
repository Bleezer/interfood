import re
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from interfood.collector import API, fetch_menu


class CollectorTests(unittest.TestCase):
    def test_week_with_monday_closed(self):
        monday = date(2026, 11, 9)
        payload = {"data": {}}
        page = MagicMock()
        captured = {}

        def on(event, callback):
            captured[event] = callback

        def goto(*args, **kwargs):
            for endpoint, data in [("weeks", {"data": [{"year": 2026, "week": 46, "disabled": False}]}), ("menu", payload)]:
                response = MagicMock()
                response.url = API + endpoint
                response.request.method = "GET"
                response.ok = True
                response.json.return_value = data
                captured["response"](response)

        page.on.side_effect = on
        page.goto.side_effect = goto
        page.get_by_role.return_value.is_visible.return_value = False
        page.get_by_role.return_value.get_attribute.return_value = "Hét kiválasztása, jelenleg kiválasztott hét: 46"
        tabs = page.locator.return_value
        tabs.all_text_contents.return_value = ["2026.11.10.", "2026.11.11."]

        def filter_tabs(*, has_text):
            if isinstance(has_text, str) and has_text == "2026.11.09.":
                raise TimeoutError("A hétfő szünnap.")
            self.assertTrue(any(re.search(has_text, day) for day in tabs.all_text_contents()))
            return MagicMock()

        tabs.filter.side_effect = filter_tabs
        with patch("interfood.collector.sync_playwright") as playwright, patch("interfood.collector.normalize_menu", return_value=[{"date": "2026-11-10"}, {"date": "2026-11-11"}]):
            playwright.return_value.__enter__.return_value.chromium.launch.return_value.new_page.return_value = page
            self.assertEqual(fetch_menu(monday), payload)
