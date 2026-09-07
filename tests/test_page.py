import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PAGE = ROOT / "page.html"


class PageBehaviourTest(unittest.TestCase):
    def run_javascript(self, expression):
        page = PAGE.read_text(encoding="utf-8")
        match = re.search(r"// fit-start\n(.*?)// fit-end", page, re.DOTALL)
        self.assertIsNotNone(match)
        script = f"{match.group(1)}\nconsole.log(JSON.stringify({expression}));"
        result = subprocess.run(
            ["bun", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_small_map_scales_up_to_cover_window(self):
        self.assertEqual(self.run_javascript("fitScale(800, 600, 240, 130)"), 4.615384615384615)

    def test_large_map_stays_at_native_scale(self):
        self.assertEqual(self.run_javascript("fitScale(800, 600, 1354, 1256)"), 1)

    def test_marker_is_centred_away_from_edges(self):
        self.assertEqual(
            self.run_javascript("viewport(400, 300, 1000, 800, 500, 400, 1)"),
            {"left": 300, "top": 250},
        )

    def test_viewport_clamps_at_each_edge(self):
        self.assertEqual(
            self.run_javascript("viewport(400, 300, 1000, 800, 10, 10, 1)"),
            {"left": 0, "top": 0},
        )
        self.assertEqual(
            self.run_javascript("viewport(400, 300, 1000, 800, 990, 790, 1)"),
            {"left": 600, "top": 500},
        )


if __name__ == "__main__":
    unittest.main()
