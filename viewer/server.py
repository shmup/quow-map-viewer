import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .config import PAGE
from .maps import Maps
from .notes import Annotation, Notes
from .position import PositionState, position_event
from .rooms import Rooms
from .watch import StoreWatcher


def map_rooms(map_id, rooms, notes):
    annotations = notes.annotations()
    listing = []
    for room_id, x, y, short in rooms.on_map(map_id):
        room = {"x": x, "y": y, "name": short}
        tags = annotations.get(room_id, Annotation()).tags
        if tags:
            room["tags"] = list(tags)
        listing.append(room)
    return listing


class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        split = urlsplit(self.path)
        path = unquote(split.path)
        if path == "/":
            self.send_file(self.server.page, "text/html; charset=utf-8")
        elif path == "/events":
            self.send_events()
        elif path == "/rooms":
            self.send_rooms(parse_qs(split.query).get("map", [""])[0])
        elif path.startswith("/maps/"):
            self.send_map(path.removeprefix("/maps/"))
        else:
            self.send_error(404)

    def send_rooms(self, map_id):
        if not map_id.isdigit():
            self.send_error(404)
            return
        listing = map_rooms(int(map_id), self.server.rooms, self.server.notes)
        content = json.dumps({"rooms": listing}, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_file(self, path, content_type):
        try:
            content = path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_map(self, name):
        if name not in self.server.maps.filenames:
            self.send_error(404)
            return
        self.send_file(self.server.maps_dir / name, "image/png")

    def send_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        revision, event = self.server.position.snapshot()
        try:
            if event is not None:
                self.write_event(event)
            while True:
                next_revision, event = self.server.position.wait_after(revision)
                if next_revision == revision:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                else:
                    revision = next_revision
                    self.write_event(event)
        except (BrokenPipeError, ConnectionResetError):
            return

    def write_event(self, event):
        data = json.dumps(event, separators=(",", ":")).encode("utf-8")
        self.wfile.write(b"data: " + data + b"\n\n")
        self.wfile.flush()

    def log_message(self, _format, *_args):
        pass


class MapServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def server_close(self):
        self.watcher_stop.set()
        self.watcher_thread.join()
        self.rooms.close()
        super().server_close()


def create_server(
    address,
    *,
    maps_path,
    maps_dir,
    database_path,
    store_path,
    map_path=None,
    bookmarks_path=None,
    watcher_interval=0.1,
):
    maps = Maps(maps_path)
    rooms = Rooms(database_path)
    position = PositionState()
    watcher = StoreWatcher(
        store_path,
        lambda room_id: position.update(position_event(room_id, maps, rooms)),
        interval=watcher_interval,
    )
    watcher.poll_once()

    server = MapServer(address, RequestHandler)
    server.page = PAGE
    server.maps = maps
    server.maps_dir = Path(maps_dir)
    server.rooms = rooms
    server.notes = Notes(map_path, bookmarks_path)
    server.position = position
    server.watcher_stop = threading.Event()
    server.watcher_thread = threading.Thread(
        target=watcher.run,
        args=(server.watcher_stop,),
        daemon=True,
    )
    server.watcher_thread.start()
    return server
