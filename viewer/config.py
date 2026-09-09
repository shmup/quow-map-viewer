from pathlib import Path


PACKAGE = Path(__file__).parent
REPO = PACKAGE.parent
ROOT = REPO.parents[1]

PAGE = PACKAGE / "page.html"
MAPS = PACKAGE / "maps.json"
ENV_FILE = REPO / ".env"
DATABASE = "_quowmap_database.db"


def read_env(path):
    values = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value.strip().strip("\"'")
    return values


def resolve_paths(environ):
    """Quow ships the database inside his maps directory; keep them together."""
    maps_dir = Path(environ["QUOW_MAPS_DIR"]).expanduser()
    paths = {
        "database_path": environ.get("QUOW_DB_PATH", maps_dir / DATABASE),
        "store_path": environ.get("DISCWORLD_STORE_PATH", ROOT / "store.json"),
        "map_path": environ.get(
            "DISCWORLD_MAP_PATH", ROOT / "data" / "discworld-quow.map"
        ),
        "bookmarks_path": environ.get(
            "DISCWORLD_BOOKMARKS_PATH", ROOT / "data" / "bookmarks.tin"
        ),
    }
    resolved = {name: Path(path).expanduser() for name, path in paths.items()}
    return {"maps_dir": maps_dir, **resolved}
