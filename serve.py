#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///

import argparse
import os

from viewer.config import ENV_FILE, MAPS, read_env, resolve_paths
from viewer.server import create_server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        paths = resolve_paths({**read_env(ENV_FILE), **os.environ})
    except KeyError as missing:
        parser.error(f"{missing.args[0]} is unset — copy .env.example to .env")

    server = create_server((args.bind, args.port), maps_path=MAPS, **paths)
    print(f"http://{args.bind}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
