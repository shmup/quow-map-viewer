from dataclasses import dataclass
from pathlib import Path


VNUM = 0
NOTE = 7
ROOM_ID = 11
FIELDS = 12


@dataclass(frozen=True)
class Annotation:
    note: str = ""
    label: str = ""
    comment: str = ""

    @property
    def tags(self):
        return tuple(t for t in (self.note, self.label, self.comment) if t)


def braced(text):
    fields = []
    depth = 0
    start = 0
    for index, character in enumerate(text):
        if character == "{":
            if depth == 0:
                start = index + 1
            depth += 1
        elif character == "}" and depth:
            depth -= 1
            if depth == 0:
                fields.append(text[start:index])
    return fields


def parse_map(text):
    rooms = {}
    for line in text.splitlines():
        if not line.startswith("R "):
            continue
        fields = braced(line)
        if len(fields) < FIELDS or not fields[ROOM_ID]:
            continue
        rooms[fields[VNUM]] = (fields[ROOM_ID], fields[NOTE])
    return rooms


def parse_bookmarks(text):
    bookmarks = {}
    for line in text.splitlines():
        if not line.startswith("#var bookmarks["):
            continue
        fields = braced(braced(line)[-1])
        record = dict(zip(fields[::2], fields[1::2]))
        if "vnum" in record:
            bookmarks[record["vnum"]] = (
                record.get("label", ""),
                record.get("comment", ""),
            )
    return bookmarks


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def signature(path):
    try:
        status = Path(path).stat()
    except OSError:
        return None
    return status.st_mtime_ns, status.st_size


class Notes:
    def __init__(self, map_path, bookmarks_path):
        self.map_path = map_path
        self.bookmarks_path = bookmarks_path
        self._signatures = None
        self._annotations = {}

    def annotations(self):
        signatures = (signature(self.map_path), signature(self.bookmarks_path))
        if signatures != self._signatures:
            self._signatures = signatures
            self._annotations = self._build()
        return self._annotations

    def _build(self):
        rooms = parse_map(read(self.map_path))
        bookmarks = parse_bookmarks(read(self.bookmarks_path))
        annotations = {}
        for vnum, (room_id, note) in rooms.items():
            label, comment = bookmarks.get(vnum, ("", ""))
            if note or label or comment:
                annotations[room_id] = Annotation(note, label, comment)
        return annotations
