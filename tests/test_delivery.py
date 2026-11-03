import contextlib
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from delivery.__main__ import main, validate_week
from delivery.telegram import send_report, split_message
from recommendation.report import format_report

from tests.test_recommendation import PROFILE, meal, menu
from recommendation.selection import recommend


class DeliveryTests(unittest.TestCase):
    def response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    def test_report_contains_main_alternatives_and_warnings(self):
        source = menu(meal(1, name="Rizottó"), meal(2, name="Parajfőzelék"),
                      meal(3, day="2026-11-14", protein=35, fat=45))
        report = format_report(source, recommend(source, PROFILE))
        for expected in ["2026-11-09", "Fő ajánlat", "Alternatíva 1",
                         "Rizottó", "Parajfőzelék", "Fehérje:", "Eltérés:"]:
            self.assertIn(expected, report)

    def test_split_preserves_text_and_utf16_bound(self):
        message = ("Árvíztűrő tükörfúrógép 😀\n" * 1000) + "vége"
        parts = split_message(message)
        self.assertEqual("".join(parts), message)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(0 < len(part.encode("utf-16-le")) // 2 <= 3500 for part in parts))
        self.assertEqual(split_message("rövid"), ["rövid"])
        with self.assertRaises(ValueError):
            split_message(" ")

    def test_send_uses_json_and_preserves_message_order(self):
        report = "egy nap\n" * 1200
        with patch("delivery.telegram.urlopen", return_value=self.response({"ok": True} )) as opener, patch("delivery.telegram.time.sleep"):
            count = send_report(report, "123:secret", "456")
        self.assertEqual(count, len(split_message(report)))
        payloads = [json.loads(call.args[0].data) for call in opener.call_args_list]
        self.assertEqual([p["text"] for p in payloads], split_message(report))
        self.assertTrue(all(p["chat_id"] == "456" and "parse_mode" not in p for p in payloads))
        self.assertTrue(all(call.kwargs["timeout"] == 30 for call in opener.call_args_list))

    def test_failure_stops_and_does_not_leak_bot_token(self):
        token = "123:SECRET"
        errors = [HTTPError(f"https://api.telegram.org/bot{token}/sendMessage", 403, token, {}, None),
                  URLError(token)]
        for error in errors:
            with self.subTest(error=type(error)), patch("delivery.telegram.urlopen", side_effect=error) as opener:
                with self.assertRaises(RuntimeError) as caught:
                    send_report("szöveg" * 2000, token, "456")
                self.assertNotIn(token, str(caught.exception))
                self.assertEqual(opener.call_count, 1)
        with patch("delivery.telegram.urlopen", return_value=self.response({"ok": False, "description": token})):
            with self.assertRaises(RuntimeError) as caught:
                send_report("szöveg", token, "456")
            self.assertNotIn(token, str(caught.exception))

    def test_missing_credentials_do_not_call_network(self):
        with patch("delivery.telegram.urlopen") as opener:
            with self.assertRaises(ValueError):
                send_report("szöveg", "", "456")
            opener.assert_not_called()

    def test_week_validation_rejects_stale_menu(self):
        validate_week(menu(meal()), date(2026, 11, 3))
        with self.assertRaises(ValueError):
            validate_week(menu(meal()), date(2026, 11, 10))

    def test_dry_run_needs_no_secrets_and_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu.json"
            path.write_text(json.dumps(menu(meal()), ensure_ascii=False), encoding="utf-8")
            with patch.dict("os.environ", {}, clear=True), patch("delivery.__main__.validate_week"), patch("delivery.__main__.send_report") as send, contextlib.redirect_stdout(io.StringIO()) as output:
                main(["--dry-run", "--menu", str(path)])
            self.assertIn("Fő ajánlat", output.getvalue())
            send.assert_not_called()

    def test_test_notification_needs_no_menu(self):
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "123:secret", "TELEGRAM_CHAT_ID": "456"}, clear=True), patch("delivery.__main__.send_report", return_value=1) as send:
            main(["--test"])
        self.assertEqual(send.call_count, 1)

    def test_stale_menu_is_not_sent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu.json"
            path.write_text(json.dumps(menu(meal())), encoding="utf-8")
            with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "123:secret", "TELEGRAM_CHAT_ID": "456"}, clear=True), patch("delivery.__main__.validate_week", side_effect=ValueError("régi hét")), patch("delivery.__main__.send_report") as send, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(["--menu", str(path)])
            send.assert_not_called()

    def test_private_chat_discovery_uses_only_own_bot_updates(self):
        from delivery.telegram import find_private_chats
        updates = {"ok": True, "result": [
            {"message": {"chat": {"id": 123, "type": "private"}}},
            {"message": {"chat": {"id": 123, "type": "private"}}},
            {"message": {"chat": {"id": -456, "type": "group"}}},
            {"message": {"chat": {"id": 789, "type": "private"}}},
            {"edited_message": {"chat": {"id": 111, "type": "private"}}}
        ]}
        with patch("delivery.telegram.urlopen", return_value=self.response(updates)) as opener:
            self.assertEqual(find_private_chats("123:secret"), ["123", "789"])
        self.assertTrue(opener.call_args.args[0].full_url.endswith("/getUpdates"))
        self.assertNotIn("offset", json.loads(opener.call_args.args[0].data))
