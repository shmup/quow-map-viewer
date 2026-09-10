import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PAGE = ROOT / "viewer" / "page.html"


class PageBehaviourTest(unittest.TestCase):
    ROOMS = json.dumps(
        [
            {"x": 10, "y": 20, "name": "Puns and Pies", "tags": ["Pshop", "tshop-1-filigree"]},
            {"x": 20, "y": 20, "name": "kitchen", "tags": ["Elm Street"]},
            {"x": 20, "y": 20, "name": "hall", "tags": ["Elm Street"]},
            {"x": 30, "y": 40, "name": "Lancre general store"},
        ]
    )

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

    def test_search_finds_names_and_tags_case_insensitively(self):
        self.assertEqual(
            self.run_javascript(f"matches({self.ROOMS}, 'PSHOP').map(p => p.x)"),
            [10],
        )
        self.assertEqual(
            self.run_javascript(f"matches({self.ROOMS}, 'general').map(p => p.x)"),
            [30],
        )

    def test_search_without_a_query_finds_nothing(self):
        self.assertEqual(self.run_javascript(f"matches({self.ROOMS}, '  ')"), [])

    def test_search_waits_for_three_characters(self):
        self.assertEqual(self.run_javascript(f"matches({self.ROOMS}, 'ge')"), [])
        self.assertEqual(
            self.run_javascript(f"matches({self.ROOMS}, 'gen').map(p => p.x)"),
            [30],
        )

    def test_debounce_runs_once_after_the_typing_stops(self):
        self.assertEqual(
            self.run_javascript(
                "await (async () => {"
                "  let calls = 0;"
                "  const bump = debounce(() => calls += 1, 30);"
                "  bump(); bump(); bump();"
                "  await new Promise(done => setTimeout(done, 10));"
                "  const during = calls;"
                "  await new Promise(done => setTimeout(done, 100));"
                "  return [during, calls];"
                "})()"
            ),
            [0, 1],
        )

    def test_search_groups_rooms_that_share_a_point(self):
        points = self.run_javascript(f"matches({self.ROOMS}, 'street')")
        self.assertEqual(len(points), 1)
        self.assertEqual([room["name"] for room in points[0]["rooms"]], ["kitchen", "hall"])

    def test_point_label_names_the_tags_and_the_rooms_behind_it(self):
        self.assertEqual(
            self.run_javascript(f"pointLabel(matches({self.ROOMS}, 'pshop')[0])"),
            "Puns and Pies — Pshop, tshop-1-filigree",
        )
        self.assertEqual(
            self.run_javascript(f"pointLabel(matches({self.ROOMS}, 'street')[0])"),
            "kitchen — Elm Street (+1)",
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
