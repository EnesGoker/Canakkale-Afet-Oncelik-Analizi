"""Export safeguards tested without QGIS, network, or actual map rendering."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qsl, urlencode, urlsplit
import xml.etree.ElementTree as ET

import export_map_layouts as export
from check_map_layouts import sha256_file


class CartoRuntimeAuthenticationTests(unittest.TestCase):
    def source(self, url):
        return urlencode([("crs", "EPSG:3857"), ("format", ""), ("type", "xyz"),
                          ("url", url), ("zmax", "18"), ("zmin", "0"), ("http-header:referer", "")])

    def test_nested_url_key_and_other_uri_parameters_are_preserved(self):
        source = self.source("https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?scale=2&empty=")
        result = dict(parse_qsl(export.carto_source_with_key(source, "dummy+token/with=padding"), keep_blank_values=True))
        original = dict(parse_qsl(source, keep_blank_values=True))
        self.assertEqual({k: v for k, v in result.items() if k != "url"}, {k: v for k, v in original.items() if k != "url"})
        nested = urlsplit(result["url"])
        self.assertEqual(nested.path, "/light_all/{z}/{x}/{y}.png")
        self.assertEqual(dict(parse_qsl(nested.query, keep_blank_values=True)),
                         {"scale": "2", "empty": "", "key": "dummy+token/with=padding"})

    def test_existing_repeated_keys_are_replaced_once(self):
        source = self.source("https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?api_key=old&API_KEY=older&key=oldkey&KEY=otheroldkey&x=1")
        result = dict(parse_qsl(export.carto_source_with_key(source, "new_dummy")))
        self.assertEqual(parse_qsl(urlsplit(result["url"]).query), [("x", "1"), ("key", "new_dummy")])

    def test_unapproved_host_or_style_errors_never_contain_secret_or_uri(self):
        key = "dummy_private_value"
        for url in ["https://foreign.example/light_all/{z}/{x}/{y}.png", "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", "http://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", "https://a.basemaps.cartocdn.com:bad/light_all/{z}/{x}/{y}.png"]:
            with self.subTest(url=url), self.assertRaises(ValueError) as error:
                export.carto_source_with_key(self.source(url), key)
            self.assertNotIn(key, str(error.exception))
            self.assertNotIn(url, str(error.exception))

    def test_blank_control_unicode_and_nonstring_keys_are_rejected(self):
        source = self.source("https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png")
        for key in ["", " ", "dummy\nprivate", "dummy\x00private", "özel", None]:
            with self.subTest(key=repr(key)), self.assertRaises(ValueError):
                export.carto_source_with_key(source, key)

    def test_all_approved_hosts_and_original_encoded_braces_are_supported(self):
        for prefix in ["", "a.", "b.", "c."]:
            source = "crs=EPSG:3857&format&type=xyz&url=https://" + prefix + "basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=18"
            result = dict(parse_qsl(export.carto_source_with_key(source, "dummy"), keep_blank_values=True))
            self.assertEqual(urlsplit(result["url"]).path, "/light_all/{z}/{x}/{y}.png")

    def test_uri_matches_qgis_native_encoding_golden(self):
        source = "type=xyz&url=https://a.basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=18"
        result = export.carto_source_with_key(source, "DUMMY")
        self.assertEqual(result, "type=xyz&url=https://a.basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.png?key%3DDUMMY&zmax=18")
        self.assertIn("url=https://", result)
        self.assertNotIn("https%3A", result)


class ExportSafeguardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = self.root / "candidate"
        self.qgs = self.root / "project.qgs"
        self.qgs.write_text("approved", encoding="utf-8")
        self.records = [{"layout_name": f"{i:02d}_map_layout", "output_stem": f"{i:02d}_map",
                         "layer_ids_ordered": ["local"]} for i in range(1, 14)]
        self.inputs = {"contract": {"layouts": self.records, "project_qgs": "project.qgs"},
                       "qgs_path": self.qgs, "project_qgs_sha256": sha256_file(self.qgs),
                       "contract_sha256": "a" * 64,
                       "layers": {"local": ET.fromstring("<maplayer><provider>gdal</provider></maplayer>")}}

    def tearDown(self):
        self.temporary.cleanup()

    def test_selection_preserves_contract_order(self):
        records = export.select_records(self.inputs["contract"], "13, 1,02")
        self.assertEqual([r["output_stem"] for r in records], ["01_map", "02_map", "13_map"])
        self.assertEqual(len(export.select_records(self.inputs["contract"])), 13)

    def test_selection_rejects_duplicate_unknown_and_malformed_numbers(self):
        for choice in ["1,01", "0", "14", "", "1,", "one", "001", "-1"]:
            with self.subTest(choice=choice), self.assertRaises(ValueError):
                export.select_records(self.inputs["contract"], choice)

    def test_existing_nonempty_output_is_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(ValueError):
            with export.staged_output(self.output):
                pass
        self.assertEqual(marker.read_text(), "keep")

    def test_symlink_output_is_rejected(self):
        destination = self.root / "real"
        destination.mkdir()
        self.output.symlink_to(destination, target_is_directory=True)
        with self.assertRaises(ValueError):
            export.validate_output_dir(self.output)

    def test_new_staged_output_is_published_only_on_success(self):
        with export.staged_output(self.output) as stage:
            (stage / "done").write_text("complete")
            self.assertFalse(self.output.exists())
        self.assertEqual((self.output / "done").read_text(), "complete")

    def test_failed_export_cleans_partial_new_or_existing_empty_output(self):
        for existing in [False, True]:
            with self.subTest(existing=existing):
                if existing:
                    self.output.mkdir()
                with self.assertRaises(ValueError):
                    with export.staged_output(self.output) as stage:
                        (stage / "partial").write_text("incomplete")
                        raise ValueError("render failed")
                self.assertEqual(self.output.exists(), existing)
                if existing:
                    self.assertEqual(list(self.output.iterdir()), [])
                    self.output.rmdir()
                self.assertEqual(list(self.root.glob(".canakkale-map-export-*")), [])

    def test_intervening_user_file_is_preserved(self):
        self.output.mkdir()
        with self.assertRaises(ValueError):
            with export.staged_output(self.output) as stage:
                (stage / "generated").write_text("candidate")
                (self.output / "user.txt").write_text("user work")
        self.assertEqual((self.output / "user.txt").read_text(), "user work")
        self.assertFalse((self.output / "generated").exists())

    def test_web_basemap_requires_explicit_flag_before_qgis_starts(self):
        self.inputs["layers"]["local"].find("provider").text = "wms"
        with patch.object(export, "load_export_inputs", return_value=self.inputs), patch.object(export, "render_qgis") as renderer:
            report, code = export.generate_exports(self.root, self.output)
        self.assertEqual(code, 1)
        self.assertIn("--allow-web-basemap", report["errors"][0])
        renderer.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_unavailable_qgis_returns_two_and_no_outputs(self):
        with patch.object(export, "load_export_inputs", return_value=self.inputs), patch.object(export, "render_qgis", side_effect=export.DependencyUnavailable("missing runtime")):
            report, code = export.generate_exports(self.root, self.output)
        self.assertEqual(code, 2)
        self.assertFalse(report["passed"])
        self.assertFalse(self.output.exists())

    def test_render_failure_reports_counts_without_provider_messages(self):
        diagnostics = {"network_error_count": 2, "network_timeout_count": 1,
                       "network_failure_categories": {"http_401": 1, "web_request_timed_out": 1},
                       "map_render_error_count": 1, "critical_provider_message_count": 0}
        failure = export.MapRenderingFailure("Sanitized rendering failure", diagnostics)
        with patch.object(export, "load_export_inputs", return_value=self.inputs), patch.object(export, "render_qgis", side_effect=failure):
            report, code = export.generate_exports(self.root, self.output)
        self.assertEqual(code, 1)
        self.assertEqual(report["render_diagnostics"], diagnostics)
        self.assertFalse(self.output.exists())

    def test_project_change_during_render_rejects_candidate(self):
        def worker(root, inputs, records, stage, allowed):
            (stage / "partial.png").write_bytes(b"candidate")
            self.qgs.write_text("user changed project")
            return {"files": []}
        with patch.object(export, "load_export_inputs", return_value=self.inputs), patch.object(export, "render_qgis", side_effect=worker):
            report, code = export.generate_exports(self.root, self.output)
        self.assertEqual(code, 1)
        self.assertTrue(report["project_modified"])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.qgs.read_text(), "user changed project")

    def test_success_records_relative_metadata_and_keeps_source(self):
        def worker(root, inputs, records, stage, allowed):
            (stage / "png").mkdir()
            (stage / "png/13_map.png").write_bytes(b"candidate")
            return {"files": [{"path": "png/13_map.png"}], "qgis_version": "test"}
        with patch.object(export, "load_export_inputs", return_value=self.inputs), patch.object(export, "render_qgis", side_effect=worker):
            report, code = export.generate_exports(self.root, self.output, "13")
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        self.assertEqual(report["layout_names"], ["13_map_layout"])
        saved = (self.output / "export_run.json").read_text()
        self.assertNotIn(str(self.root), saved)
        self.assertEqual(self.qgs.read_text(), "approved")

    def test_check_delegates_without_rendering_or_output(self):
        with patch("check_map_layouts.audit_project", return_value=({"status": "passed", "errors": [], "passed": True}, 0)) as check, patch.object(export, "render_qgis") as render, redirect_stdout(io.StringIO()) as stream:
            code = export.main(["--check", "--project-root", str(self.root), "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"passed": true', stream.getvalue())
        check.assert_called_once_with(self.root, export.CONTRACT)
        render.assert_not_called()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
