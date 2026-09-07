import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from watch import StoreWatcher


class StoreWatcherTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Path(self.directory.name) / "store.json"
        self.seen = []
        self.watcher = StoreWatcher(self.store, self.seen.append)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, room_id, **extra):
        self.store.write_text(
            json.dumps({"room_identifier": room_id, **extra}),
            encoding="utf-8",
        )

    def test_room_change_fires_callback_once(self):
        self.write("room-a")
        self.watcher.poll_once()
        self.write("room-b")
        self.watcher.poll_once()

        self.assertEqual(self.seen, ["room-a", "room-b"])

    def test_unchanged_rewrite_does_not_fire_callback(self):
        self.write("room-a", hp=100)
        self.watcher.poll_once()
        self.write("room-a", hp=90)
        self.watcher.poll_once()

        self.assertEqual(self.seen, ["room-a"])

    def test_truncated_read_is_skipped(self):
        self.write("room-a")
        self.watcher.poll_once()
        self.store.write_text('{"room_identifier":', encoding="utf-8")

        self.assertFalse(self.watcher.poll_once())
        self.assertEqual(self.seen, ["room-a"])

    def test_missing_file_and_identifier_are_skipped(self):
        self.assertFalse(self.watcher.poll_once())
        self.store.write_text("{}", encoding="utf-8")
        self.assertFalse(self.watcher.poll_once())
        self.assertEqual(self.seen, [])

    def test_run_stops_when_requested(self):
        stop = threading.Event()
        stop.set()

        self.watcher.run(stop)

        self.assertEqual(self.seen, [])


if __name__ == "__main__":
    unittest.main()
