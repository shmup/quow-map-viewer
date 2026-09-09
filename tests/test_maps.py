import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from viewer.maps import Maps


class MapsTest(unittest.TestCase):
    def test_loads_records_and_formats_background(self):
        data = {
            "maps": {
                "23": {
                    "filename": "djb.png",
                    "title": "Djelibeybi",
                    "background": 16777215,
                    "width": 949,
                    "height": 652,
                },
                "99": {
                    "filename": "discwhole.png",
                    "title": "Whole Disc",
                    "background": 0,
                    "width": 5809,
                    "height": 5000,
                },
            },
            "regions": {"23": [23, 24]},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "maps.json"
            path.write_text(json.dumps(data), encoding="utf-8")

            maps = Maps(path)

        self.assertEqual(maps.map_info(23).background, "#ffffff")
        self.assertEqual(maps.map_info(99).background, "#000000")
        self.assertEqual(maps.region_maps(23), (23, 24))
        self.assertIsNone(maps.map_info(65))


if __name__ == "__main__":
    unittest.main()
