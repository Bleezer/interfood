import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from interfood.cli import main


class CollectionTests(unittest.TestCase):
    def test_current_paths_and_invalid_menu_preserves_previous_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            meal = {"date": "2026-11-09", "nutrition_per_portion": {"protein_g": 40}}
            with patch("interfood.cli.OUTPUT", output), patch("interfood.cli.fetch_menu", return_value={"data": {}}), patch("interfood.cli.normalize_menu", return_value=[meal]):
                main()
            self.assertTrue((output / "menu.json").exists())
            self.assertTrue((output / "raw.json").exists())
            self.assertEqual(json.loads((output / "menu.json").read_text(encoding="utf-8"))["meal_count"], 1)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            with patch("interfood.cli.OUTPUT", output), patch("interfood.cli.fetch_menu", return_value={"data": {}}):
                with self.assertRaises(ValueError):
                    main()
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
