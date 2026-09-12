# quow-map-viewer

renders Quow's discworld maps in a browser while updating with player location

<img width="1364" height="747" alt="image" src="https://github.com/user-attachments/assets/4def5f5d-046a-4a2f-8b99-a881f1711633" />

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

**SETUP**

```sh
curl -O https://www.quow.co.uk/MUSHclient.zip
curl -O http://luggage.gg/dark.zip (optional)
unzip MUSHclient.zip
cp .env.example .env    # point QUOW_MAPS_DIR at MUSHclient/quow_plugins/maps
```

the pngs and the db sit in that one directory, so one path covers both.
for dark maps, extract the `dark/` folder from `dark.zip` into `QUOW_MAPS_DIR`.
the sun/moon button in the title bar switches maps and remembers your choice.

`.env` is read at startup, real environment variables win over it, and the
rest of `.env.example` is optional — see it for what else you can set.

the pngs, the db and `maps.json` have to come from the same Quow release —
pixel coords only mean anything against the pngs they were drawn for. the
committed `maps.json` is from plugin 4.96 (2026-05-17); if yours differs, run
`tools/extract_maps.py MUSHclient/quow_plugins/QuowMinimap.xml`.

**RUN**

```sh
./serve.py # http://127.0.0.1:9000
./serve.py --bind 0.0.0.0 --port 9000
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
