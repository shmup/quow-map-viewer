#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from maps import Maps
from rooms import Rooms
from watch import StoreWatcher


ROOT = Path(__file__).parents[2]
PAGE = Path(__file__).with_name("page.html")


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
        "known": True,
    }


class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            self.send_file(self.server.page, "text/html; charset=utf-8")
        elif path == "/events":
            self.send_events()
        elif path.startswith("/maps/"):
            self.send_map(path.removeprefix("/maps/"))
        else:
            self.send_error(404)

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
    server.position = position
    server.watcher_stop = threading.Event()
    server.watcher_thread = threading.Thread(
        target=watcher.run,
        args=(server.watcher_stop,),
        daemon=True,
    )
    server.watcher_thread.start()
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = create_server(
        (args.bind, args.port),
        maps_path=Path(__file__).with_name("maps.json"),
        maps_dir=Path(
            os.environ.get(
                "QUOW_MAPS_DIR",
                "~/Desktop/mush/MUSHclient/quow_plugins/maps",
            )
        ).expanduser(),
        database_path=ROOT / "quow" / "_quowmap_database.db",
        store_path=Path(
            os.environ.get("DISCWORLD_STORE_PATH", ROOT / "store.json")
        ).expanduser(),
    )
    print(f"http://{args.bind}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
