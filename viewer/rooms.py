import sqlite3
from pathlib import Path


class Rooms:
    def __init__(self, path):
        uri = f"{Path(path).resolve().as_uri()}?mode=ro"
        self.connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.connection.execute("PRAGMA query_only=ON")

    def locate(self, room_id):
        row = self.connection.execute(
            """
            SELECT map_id, xpos, ypos, room_short
            FROM rooms
            WHERE room_id = ?
            """,
            (room_id,),
        ).fetchone()
        return tuple(row) if row else None

    def on_map(self, map_id):
        return [
            tuple(row)
            for row in self.connection.execute(
                """
                SELECT room_id, xpos, ypos, room_short
                FROM rooms
                WHERE map_id = ?
                """,
                (map_id,),
            )
        ]

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()
