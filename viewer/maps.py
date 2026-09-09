import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MapInfo:
    map_id: int
    filename: str
    title: str
    background: str
    width: int
    height: int


class Maps:
    def __init__(self, path=Path(__file__).with_name("maps.json")):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._maps = {
            int(map_id): MapInfo(
                map_id=int(map_id),
                filename=record["filename"],
                title=record["title"],
                background=f"#{record['background']:06x}",
                width=record["width"],
                height=record["height"],
            )
            for map_id, record in data["maps"].items()
        }
        self._regions = {
            int(map_id): tuple(region)
            for map_id, region in data.get("regions", {}).items()
        }

    def map_info(self, map_id):
        return self._maps.get(map_id)

    def region_maps(self, map_id):
        return self._regions.get(map_id, (map_id,))

    @property
    def filenames(self):
        return frozenset(info.filename for info in self._maps.values())
