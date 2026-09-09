import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from viewer.config import read_env, resolve_paths


class EnvFileTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.env = Path(self.directory.name) / ".env"
        self.addCleanup(self.directory.cleanup)

    def test_reads_assignments_and_ignores_the_rest(self):
        self.env.write_text(
            "# where the pngs live\n"
            "\n"
            "QUOW_MAPS_DIR=~/mush/quow_plugins/maps\n"
            'QUOW_DB_PATH="/opt/quow.db"\n'
            "  DISCWORLD_STORE_PATH = ../store.json  \n"
            "nonsense\n",
            encoding="utf-8",
        )
        self.assertEqual(
            read_env(self.env),
            {
                "QUOW_MAPS_DIR": "~/mush/quow_plugins/maps",
                "QUOW_DB_PATH": "/opt/quow.db",
                "DISCWORLD_STORE_PATH": "../store.json",
            },
        )

    def test_a_missing_file_is_not_an_error(self):
        self.assertEqual(read_env(self.env), {})


class PathTest(unittest.TestCase):
    def test_a_maps_directory_is_required(self):
        with self.assertRaises(KeyError):
            resolve_paths({})

    def test_database_sits_with_the_maps_by_default(self):
        paths = resolve_paths({"QUOW_MAPS_DIR": "/opt/quow_plugins/maps"})
        self.assertEqual(paths["maps_dir"], Path("/opt/quow_plugins/maps"))
        self.assertEqual(
            paths["database_path"],
            Path("/opt/quow_plugins/maps/_quowmap_database.db"),
        )

    def test_every_path_takes_an_override_and_expands_a_tilde(self):
        environ = {
            "QUOW_MAPS_DIR": "~/maps",
            "QUOW_DB_PATH": "~/elsewhere/quow.db",
            "DISCWORLD_STORE_PATH": "~/store.json",
            "DISCWORLD_MAP_PATH": "~/discworld.map",
            "DISCWORLD_BOOKMARKS_PATH": "~/bookmarks.tin",
        }
        home = Path.home()
        self.assertEqual(
            resolve_paths(environ),
            {
                "maps_dir": home / "maps",
                "database_path": home / "elsewhere/quow.db",
                "store_path": home / "store.json",
                "map_path": home / "discworld.map",
                "bookmarks_path": home / "bookmarks.tin",
            },
        )

    def test_the_tintin_paths_fall_back_to_the_parent_project(self):
        paths = resolve_paths({"QUOW_MAPS_DIR": "/opt/maps"})
        self.assertEqual(paths["store_path"], ROOT.parents[1] / "store.json")
        self.assertEqual(
            paths["map_path"], ROOT.parents[1] / "data" / "discworld-quow.map"
        )


if __name__ == "__main__":
    unittest.main()
