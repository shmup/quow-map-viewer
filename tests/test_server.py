import json
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from serve import create_server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.maps_dir = root / "maps"
        self.maps_dir.mkdir()
        self.maps_dir.joinpath("sto_plains.png").write_bytes(b"fixture png")
        self.maps_json = root / "maps.json"
        self.maps_json.write_text(
            json.dumps(
                {
                    "maps": {
                        "45": {
                            "filename": "sto_plains.png",
                            "title": "Sto Plains Region",
                            "background": 16777215,
                            "width": 1492,
                            "height": 1006,
                        }
                    },
                    "regions": {},
                }
            ),
            encoding="utf-8",
        )
        self.database = root / "quow.db"
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
                ("room-a", 45, 1454, 560, "road", "outside"),
                ("room-b", 45, 1200, 400, "Puns and Pies", "inside"),
                ("room-c", 56, 243, 275, "depths of L-space", "inside"),
            ),
        )
        connection.commit()
        connection.close()
        self.store = root / "store.json"
        self.write_store("room-a")
        self.map_file = root / "discworld-quow.map"
        self.map_file.write_text(
            "R {28}{0}{<fac>}{Puns and Pies}{}{}{Ankh-Morpork}{Pshop}"
            "{inside}{}{1.000}{room-b}\n",
            encoding="utf-8",
        )
        self.bookmarks = root / "bookmarks.tin"
        self.bookmarks.write_text(
            "#var bookmarks[1] {{comment}{}{label}{tshop-1-filigree}{vnum}{28}};\n",
            encoding="utf-8",
        )
        self.server = create_server(
            ("127.0.0.1", 0),
            maps_path=self.maps_json,
            maps_dir=self.maps_dir,
            database_path=self.database,
            store_path=self.store,
            map_path=self.map_file,
            bookmarks_path=self.bookmarks,
            watcher_interval=0.01,
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def write_store(self, room_id):
        temporary = self.store.with_suffix(".tmp")
        temporary.write_text(json.dumps({"room_identifier": room_id}), encoding="utf-8")
        temporary.replace(self.store)

    def read_event(self, response):
        while True:
            line = response.readline().decode("utf-8")
            if line.startswith("data: "):
                return json.loads(line.removeprefix("data: "))

    def test_serves_page_and_validated_map(self):
        with urllib.request.urlopen(f"{self.url}/") as response:
            self.assertIn(b"new EventSource", response.read())
        with urllib.request.urlopen(f"{self.url}/maps/sto_plains.png") as response:
            self.assertEqual(response.read(), b"fixture png")

        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(f"{self.url}/maps/not-listed.png")
        self.assertEqual(raised.exception.code, 404)
        raised.exception.close()

    def test_rooms_lists_one_map_with_its_notes(self):
        with urllib.request.urlopen(f"{self.url}/rooms?map=45") as response:
            rooms = json.loads(response.read())["rooms"]

        self.assertEqual(
            sorted(rooms, key=lambda room: room["name"]),
            [
                {
                    "x": 1200,
                    "y": 400,
                    "name": "Puns and Pies",
                    "tags": ["Pshop", "tshop-1-filigree"],
                },
                {"x": 1454, "y": 560, "name": "road"},
            ],
        )

    def test_rooms_rejects_a_map_it_cannot_read(self):
        for query in ("", "?map=", "?map=nine"):
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(f"{self.url}/rooms{query}")
            self.assertEqual(raised.exception.code, 404)
            raised.exception.close()

    def test_events_send_current_position_then_changes(self):
        with urllib.request.urlopen(f"{self.url}/events", timeout=2) as response:
            current = self.read_event(response)
            self.assertEqual(
                current,
                {
                    "image": "sto_plains.png",
                    "title": "Sto Plains Region",
                    "x": 1454,
                    "y": 560,
                    "w": 1492,
                    "h": 1006,
                    "bg": "#ffffff",
                    "room": "road",
                    "map": 45,
                    "known": True,
                },
            )

            self.write_store("unknown-room")
            unknown = self.read_event(response)

        self.assertEqual(unknown, {"known": False, "room": "unknown-room"})
        self.assertNotIn("x", unknown)


if __name__ == "__main__":
    unittest.main()
