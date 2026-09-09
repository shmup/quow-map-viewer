import threading


class PositionState:
    def __init__(self):
        self._condition = threading.Condition()
        self._revision = 0
        self._event = None

    def update(self, event):
        with self._condition:
            self._revision += 1
            self._event = event
            self._condition.notify_all()

    def snapshot(self):
        with self._condition:
            return self._revision, self._event

    def wait_after(self, revision, timeout=15):
        with self._condition:
            self._condition.wait_for(
                lambda: self._revision > revision,
                timeout=timeout,
            )
            return self._revision, self._event


def position_event(room_id, maps, rooms):
    location = rooms.locate(room_id)
    if location is None:
        return {"known": False, "room": room_id}

    map_id, x, y, room = location
    info = maps.map_info(map_id)
    if info is None:
        return {"known": False, "room": room_id}

    return {
        "image": info.filename,
        "title": info.title,
        "x": x,
        "y": y,
        "w": info.width,
        "h": info.height,
        "bg": info.background,
        "room": room,
        "map": map_id,
        "known": True,
    }
