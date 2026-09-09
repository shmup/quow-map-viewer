# quow-map-viewer

renders Quow's discworld maps in a browser while updating with player location

### HOW

- page draws the map png — drag to pan, scroll to zoom, search lights up matching rooms
- server pushes position over sse, no polling in the browser
- position comes from a json file on disk, polled 10x/sec
- room id → map + x,y via Quow's sqlite db, read-only
- notes/bookmark tags read out of tintin's `.map` and `bookmarks.tin`

### REQUIRES

- uv (the shebang runs it) or plain python3 — stdlib only
- Quow's pngs and `_quowmap_database.db` — [MUSHclient.zip](https://www.quow.co.uk/MUSHclient.zip), 16mb
- something writing `{"room_identifier": "<gmcp hash>"}` to a file

**MAPS**

```sh
curl -O https://www.quow.co.uk/MUSHclient.zip
unzip MUSHclient.zip
export QUOW_MAPS_DIR=$PWD/MUSHclient/quow_plugins/maps
```

the db lives in that same directory, so one path covers both.

**RUN**

```sh
./serve.py # http://127.0.0.1:9000
./serve.py --bind 0.0.0.0 --port 9000
```

**PATHS**

```sh
QUOW_MAPS_DIR=~/Desktop/mush/MUSHclient/quow_plugins/maps
QUOW_DB_PATH=$QUOW_MAPS_DIR/_quowmap_database.db    # only if you moved it
DISCWORLD_STORE_PATH=../../store.json
DISCWORLD_MAP_PATH=../../data/discworld-quow.map    # optional, notes
DISCWORLD_BOOKMARKS_PATH=../../data/bookmarks.tin   # optional, labels
```

### ANY CLIENT

I drive it with tintin++, but nothing here knows that - it's whatever writes
the json. mudlet, mushclient, same deal. only the notes overlay is
tintin-shaped: it parses `R {...}` lines and `#var bookmarks[...]`. skip it and
you still get maps and the marker.

**TEST**

```sh
python3 -m unittest discover -s tests
```
