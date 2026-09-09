import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from notes import Notes


MAP = """C 4

V 20231
#NOP {quow-map source map git deadbeef};
R {27}{0}{<fac>}{Filigree Street east of some shops}{}{}{Ankh-Morpork}{}{outside}{}{1.000}{aaaaaaaa}
R {28}{0}{<fac>}{Puns and Pies}{}{}{Ankh-Morpork}{Pshop}{inside}{}{1.000}{bbbbbbbb}
R {12978}{0}{<bba>}{living room}{}{}{Ohulan-Cutash}{shop: logs}{inside}{{building_entry}{w}{building_outside}{12976}}{1.000}{cccccccc}
R {99}{0}{<fac>}{the void}{}{}{}{}{inside}{}{1.000}{}
E {27}{28}{0}{east}{}{}{}{}
"""

BOOKMARKS = """#var bookmarks[1] {{comment}{Filigree Street east of some shops}{label}{tshop-1-filigree}{vnum}{27}};
#var bookmarks[2] {{comment}{}{label}{kingsdown-stable AM}{vnum}{28}};
#var bookmarks[3] {{comment}{}{label}{somewhere unmapped}{vnum}{4242}};
"""


class NotesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.map_path = root / "discworld-quow.map"
        self.bookmarks_path = root / "bookmarks.tin"
        self.map_path.write_text(MAP, encoding="utf-8")
        self.bookmarks_path.write_text(BOOKMARKS, encoding="utf-8")
        self.notes = Notes(self.map_path, self.bookmarks_path)

    def tearDown(self):
        self.directory.cleanup()

    def test_reads_room_notes_by_quow_identifier(self):
        self.assertEqual(self.notes.annotations()["bbbbbbbb"].note, "Pshop")

    def test_reads_note_past_a_nested_field(self):
        self.assertEqual(self.notes.annotations()["cccccccc"].note, "shop: logs")

    def test_skips_rooms_quow_does_not_know(self):
        self.assertNotIn("", self.notes.annotations())

    def test_joins_bookmarks_through_the_room_number(self):
        annotation = self.notes.annotations()["aaaaaaaa"]
        self.assertEqual(annotation.label, "tshop-1-filigree")
        self.assertEqual(annotation.comment, "Filigree Street east of some shops")

    def test_drops_bookmarks_for_rooms_outside_the_map(self):
        labels = {a.label for a in self.notes.annotations().values()}
        self.assertNotIn("somewhere unmapped", labels)

    def test_tags_collect_the_searchable_text(self):
        annotations = self.notes.annotations()
        self.assertEqual(
            annotations["bbbbbbbb"].tags,
            ("Pshop", "kingsdown-stable AM"),
        )
        self.assertEqual(annotations["cccccccc"].tags, ("shop: logs",))

    def test_rereads_when_the_map_changes(self):
        self.assertEqual(self.notes.annotations()["aaaaaaaa"].note, "")
        self.map_path.write_text(
            MAP.replace("{Ankh-Morpork}{}{outside}", "{Ankh-Morpork}{Gather}{outside}"),
            encoding="utf-8",
        )
        self.assertEqual(self.notes.annotations()["aaaaaaaa"].note, "Gather")

    def test_missing_files_yield_no_annotations(self):
        missing = Path(self.directory.name) / "gone"
        self.assertEqual(Notes(missing, missing).annotations(), {})


if __name__ == "__main__":
    unittest.main()
