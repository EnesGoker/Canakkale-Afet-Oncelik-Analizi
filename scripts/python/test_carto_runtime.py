"""CARTO request isolation and launcher checks; no real credentials or network."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qsl, urlsplit

import open_qgis_with_carto as runtime


class CartoRuntimeTests(unittest.TestCase):
    def test_only_approved_https_tile_requests_receive_key(self):
        approved = "https://a.basemaps.cartocdn.com/light_all/8/146/97.png?scale=2&key=OLD&API_KEY=OLDER"
        result = runtime.authenticated_url(approved, "DUMMY_KEY")
        self.assertEqual(parse_qsl(urlsplit(result).query), [("scale", "2"), ("key", "DUMMY_KEY")])
        for url in [
            "https://foreign.example/light_all/8/146/97.png",
            "https://a.basemaps.cartocdn.com.foreign.example/light_all/8/146/97.png",
            "http://a.basemaps.cartocdn.com/light_all/8/146/97.png",
            "https://a.basemaps.cartocdn.com:8443/light_all/8/146/97.png",
            "https://user@a.basemaps.cartocdn.com/light_all/8/146/97.png",
            "https://a.basemaps.cartocdn.com/light_all/8/146/97.png#fragment",
            "https://a.basemaps.cartocdn.com/dark_all/8/146/97.png",
            "https://a.basemaps.cartocdn.com/light_all/../private/file.png",
            "https://a.basemaps.cartocdn.com:bad/light_all/8/146/97.png",
        ]:
            with self.subTest(url=url):
                self.assertEqual(runtime.authenticated_url(url, "DUMMY_KEY"), url)

    def test_private_file_precedes_environment_key_and_errors_are_redacted(self):
        with tempfile.TemporaryDirectory() as folder:
            keyfile = Path(folder) / "private.key"
            keyfile.write_text("FILE_DUMMY\n")
            self.assertEqual(runtime.read_key(keyfile, {"CARTO_BASEMAPS_API_KEY": "ENV_DUMMY"}), "FILE_DUMMY")
            self.assertEqual(runtime.read_key(None, {"CARTO_BASEMAPS_API_KEY": "ENV_DUMMY"}), "ENV_DUMMY")
            keyfile.write_text("DUMMY_WITH\nNEWLINE")
            with self.assertRaises(ValueError) as failure:
                runtime.read_key(keyfile, {})
            self.assertNotIn("DUMMY", str(failure.exception))

    def test_local_check_never_launches_or_writes_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / "project.qgs"
            project.write_bytes(b"<qgis/>")
            keyfile = root / "private.key"
            keyfile.write_text("DUMMY_KEY")
            with patch.object(runtime, "qgis_executable", return_value=Path("/dummy/qgis")), \
                    patch.object(runtime.subprocess, "Popen") as launch, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                result = runtime.main(["--check", "--key-file", str(keyfile), "--project", str(project)])
            self.assertEqual(result, 0)
            launch.assert_not_called()
            self.assertEqual(project.read_bytes(), b"<qgis/>")
            self.assertNotIn("DUMMY_KEY", output.getvalue())

    def test_launch_passes_only_private_path_and_isolates_gis_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / "project.qgs"
            project.write_bytes(b"<qgis/>")
            keyfile = root / "private.key"
            keyfile.write_text("DUMMY_KEY")
            with patch.dict(runtime.os.environ, {"PYTHONHOME": "/foreign/python", "PROJ_DATA": "/foreign/proj",
                                                "CARTO_BASEMAPS_API_KEY": "ENV_DUMMY"}), \
                    patch.object(runtime, "qgis_executable", return_value=Path("/dummy/qgis")), \
                    patch.object(runtime.subprocess, "Popen") as launch, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runtime.main(["--key-file", str(keyfile), "--project", str(project)]), 0)
            args, kwargs = launch.call_args
            self.assertNotIn("DUMMY_KEY", str(args))
            self.assertNotIn("DUMMY_KEY", str(kwargs))
            self.assertEqual(kwargs["env"]["CARTO_BASEMAPS_KEY_FILE"], str(keyfile.resolve()))
            self.assertNotIn("CARTO_BASEMAPS_API_KEY", kwargs["env"])
            self.assertNotIn("PYTHONHOME", kwargs["env"])
            self.assertNotIn("PROJ_DATA", kwargs["env"])
            self.assertEqual(project.read_bytes(), b"<qgis/>")


if __name__ == "__main__":
    unittest.main()
