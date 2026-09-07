#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///

import argparse
import json
import re
import textwrap
from pathlib import Path


MAPS_BLOCK = re.compile(r"sQuowMapfiles\s*=\s*\{(?P<body>.*?)\n\}", re.DOTALL)
MAP = re.compile(
    r"\[(?P<id>\d+)\]\s*=\s*\{\s*"
    r'"(?P<filename>[^"]+)",\s*"(?P<title>[^"]+)",\s*'
    r"-?\d+,\s*-?\d+,\s*-?\d+,\s*-?\d+,\s*"
    r'"[^"]*",\s*(?:true|false),\s*'
    r"(?P<background>\d+),\s*(?P<width>\d+),\s*(?P<height>\d+),"
)
REGIONS_BLOCK = re.compile(r"sRegionLinkGroups\s*=\s*\{(?P<body>.*?)\n\}", re.DOTALL)
REGION = re.compile(r"\[(?P<id>\d+)\]\s*=\s*\{(?P<body>[^}]*)\}")
REGION_MAP = re.compile(r"\[(\d+)\]\s*=\s*true")


def extract_maps(source):
    source = textwrap.dedent(source)
    maps_match = MAPS_BLOCK.search(source)
    if not maps_match:
        raise ValueError("sQuowMapfiles table not found")

    maps = {}
    for match in MAP.finditer(maps_match.group("body")):
        maps[match.group("id")] = {
            "filename": match.group("filename"),
            "title": match.group("title"),
            "background": int(match.group("background")),
            "width": int(match.group("width")),
            "height": int(match.group("height")),
        }

    regions = {}
    regions_match = REGIONS_BLOCK.search(source)
    if regions_match:
        for match in REGION.finditer(regions_match.group("body")):
            regions[match.group("id")] = [
                int(map_id) for map_id in REGION_MAP.findall(match.group("body"))
            ]

    if not maps:
        raise ValueError("sQuowMapfiles table is empty")
    return {"maps": maps, "regions": regions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).with_name("maps.json"),
    )
    args = parser.parse_args()

    data = extract_maps(args.source.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
