import json
from pathlib import Path


class StoreWatcher:
    def __init__(self, path, callback, interval=0.1):
        self.path = Path(path)
        self.callback = callback
        self.interval = interval
        self._room_id = None

    def poll_once(self):
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False

        room_id = state.get("room_identifier")
        if room_id is None or room_id == self._room_id:
            return False

        self._room_id = room_id
        self.callback(room_id)
        return True

    def run(self, stop):
        while not stop.is_set():
            self.poll_once()
            stop.wait(self.interval)
