import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]

import sys

sys.path.insert(0, str(ROOT))

from extract_maps import extract_maps
from viewer.maps import Maps


class ExtractMapsTest(unittest.TestCase):
    def test_extracts_map_geometry_and_region_links(self):
        source = """
        unrelated = { [1] = { "wrong.png" } }
        sQuowMapfiles = {
          [23] = { "djb.png", "Djelibeybi", 14, 14, 438, 369, "DJB", false, 16777215, 949, 652, true, },
          [24] = { "djb_wizards.png", "IIL - DJB Wizards", 28, 28, 210, 210, "DJB", false, 16777215, 426, 433, false, },
          [61] = { "am_fools.png", "AM Fools' Guild", 28, 28, 135, 101, "AM", false, 16777215, 260, 210, false, },
          [99] = { "discwhole.png", "Whole Disc", 1, 1, 1175, 3726, "Terrains", false, 0, 5809, 5000, true, },
        }
        sRegionLinkGroups = {
          [23] = {[23] = true, [24] = true,},
        }
        """

        extracted = extract_maps(source)

        self.assertEqual(extracted["maps"]["24"]["filename"], "djb_wizards.png")
        self.assertEqual(extracted["maps"]["61"]["title"], "AM Fools' Guild")
        self.assertEqual(extracted["maps"]["99"]["background"], 0)
        self.assertEqual(extracted["regions"]["23"], [23, 24])


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
