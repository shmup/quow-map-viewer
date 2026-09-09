import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from viewer.rooms import Rooms


class RoomsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / "quow.db"
        connection = sqlite3.connect(self.database)
        connection.execute(
            """
            CREATE TABLE rooms (
                room_id TEXT PRIMARY KEY,
                map_id INTEGER NOT NULL,
                xpos INTEGER NOT NULL,
                ypos INTEGER NOT NULL,
                room_short TEXT NOT NULL,
                room_type TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO rooms VALUES (?, ?, ?, ?, ?, ?)",
            (
                ("a" * 40, 45, 1454, 560, "road", "outside"),
                ("LSpace", 56, 243, 275, "depths of L-space", "inside"),
            ),
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.directory.cleanup()

    def test_locates_hex_identifier(self):
        with Rooms(self.database) as rooms:
            self.assertEqual(rooms.locate("a" * 40), (45, 1454, 560, "road"))

    def test_locates_named_identifier(self):
        with Rooms(self.database) as rooms:
            self.assertEqual(
                rooms.locate("LSpace"),
                (56, 243, 275, "depths of L-space"),
            )

    def test_lists_every_room_on_a_map(self):
        with Rooms(self.database) as rooms:
            self.assertEqual(
                rooms.on_map(45),
                [("a" * 40, 1454, 560, "road")],
            )
            self.assertEqual(rooms.on_map(1), [])

    def test_returns_none_for_unknown_identifier(self):
        with Rooms(self.database) as rooms:
            self.assertIsNone(rooms.locate("unknown"))

    def test_database_is_query_only(self):
        with Rooms(self.database) as rooms:
            with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                rooms.connection.execute("DELETE FROM rooms")


if __name__ == "__main__":
    unittest.main()
