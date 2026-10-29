#!/usr/bin/env python3
"""Tiny, dependency-free project fixtures exercise layout and export failures.

These fixtures test the XML/byte-integrity checker, not raster validity or PDF
rendering. Actual GIS providers and exported page geometry are checked elsewhere.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
from check_map_layouts import AGREEMENT_COLORS, audit_project, sha256_file, xml_sha256
from qgis_identity import build_metadata_revision, replace_identity_values

SCRIPT = Path(__file__).with_name("check_map_layouts.py")


class MapLayoutTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="canakkale-layout-tests-")
        self.root = Path(self.folder.name)
        for name in ("config", "qgis", "data", "outputs/maps/png", "outputs/maps/pdf", "outputs/atlas"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.qgs = self.root / "qgis/project.qgs"
        self.qgz = self.root / "qgis/project.qgz"
        self.contract_file = self.root / "config/map_layouts_v1.json"
        self.manifest_file = self.root / "outputs/maps/map_export_manifest.json"
        self.auxiliary_members = {}
        self.xml = ET.Element("qgis")
        projectlayers = ET.SubElement(self.xml, "projectlayers")
        layers = ET.SubElement(self.xml, "Layouts")
        records = []
        for number in range(1, 14):
            layer_id = f"score_{number:02d}"
            filename = f"data/{layer_id}.tif"
            (self.root / filename).write_bytes(b"synthetic file; provider validity checked elsewhere")
            layer = ET.SubElement(projectlayers, "maplayer")
            ET.SubElement(layer, "id").text = layer_id
            ET.SubElement(layer, "provider").text = "gdal"
            ET.SubElement(layer, "datasource").text = "../" + filename
            layout = ET.SubElement(layers, "Layout", name=f"{number:02d}_map_layout", units="mm")
            map_item = ET.SubElement(layout, "LayoutItem", type="65639", keepLayerSet="true", followPreset="false", uuid=f"{{map-{number}}}", size="299,233,mm")
            layer_set = ET.SubElement(map_item, "LayerSet")
            ET.SubElement(layer_set, "Layer", source="../" + filename, provider="gdal").text = layer_id
            styles = ET.SubElement(map_item, "LayerStyles")
            entry = ET.SubElement(styles, "LayerStyle", layerid=layer_id, source="../" + filename, provider="gdal")
            style = ET.SubElement(entry, "qgis")
            shader = ET.SubElement(style, "colorrampshader", colorRampType="EXACT")
            for value, color in enumerate(AGREEMENT_COLORS):
                ET.SubElement(shader, "item", value=str(value), color=color, alpha="255", label=f"Class {value}")
            ET.SubElement(shader, "rampLegendSettings", useContinuousLegend="0")
            legend = ET.SubElement(layout, "LayoutItem", type="65642", map_uuid=f"{{map-{number}}}")
            legend_tree = ET.SubElement(legend, "layer-tree-group")
            ET.SubElement(legend_tree, "layer-tree-layer", id=layer_id, source="../" + filename, providerKey="gdal")
            records.append({"layout_name": layout.get("name"), "output_stem": f"{number:02d}_map", "thematic_layer_id": layer_id,
                            "raster_path": filename, "layer_ids_ordered": [layer_id],
                            "expected_layer_style_hashes": {layer_id: xml_sha256(style)}, "layout_sha256": xml_sha256(layout)})
        self.contract = {"format_version": 1, "project_qgs": "qgis/project.qgs", "project_qgz": "qgis/project.qgz",
                         "export_manifest": "outputs/maps/map_export_manifest.json", "atlas_path": "outputs/atlas/maps.pdf", "layouts": records}
        self.manifest = {"format_version": 1, "files": []}
        for record in records:
            for kind in ("png", "pdf"):
                relative = f"outputs/maps/{kind}/{record['output_stem']}.{kind}"
                data = (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 4960, 3507)) if kind == "png" else b"%PDF-1.7\nfixture"
                (self.root / relative).write_bytes(data)
                row = {"path": relative, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                if kind == "pdf":
                    row["page_count"] = 1
                else:
                    row.update(width_px=4960, height_px=3507)
                self.manifest["files"].append(row)
        atlas = self.root / self.contract["atlas_path"]
        atlas.write_bytes(b"%PDF-1.7\natlas-fixture")
        self.manifest["files"].append({"path": self.contract["atlas_path"], "size_bytes": atlas.stat().st_size,
                                       "sha256": sha256_file(atlas), "page_count": 13})
        self.save()

    def tearDown(self):
        self.folder.cleanup()

    def save(self, *, sync_zip=True, refresh_manifest=True, refresh_contract=False):
        if refresh_contract:
            for record, layout in zip(self.contract["layouts"], self.xml.findall("./Layouts/Layout")):
                record["layout_sha256"] = xml_sha256(layout)
                record["expected_layer_style_hashes"] = {e.get("layerid"): xml_sha256(e.find("qgis")) for e in layout.findall("./LayoutItem/LayerStyles/LayerStyle")}
        ET.ElementTree(self.xml).write(self.qgs, encoding="utf-8", xml_declaration=True)
        if sync_zip:
            with zipfile.ZipFile(self.qgz, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.write(self.qgs, "project.qgs")
                for name, data in self.auxiliary_members.items():
                    archive.writestr(name, data)
        if refresh_manifest:
            if self.manifest["format_version"] == 1:
                self.manifest["project_qgs_sha256"] = sha256_file(self.qgs)
            else:
                self.manifest["metadata_revision"]["current_project_qgs_sha256"] = sha256_file(self.qgs)
        self.contract_file.write_text(json.dumps(self.contract), encoding="utf-8")
        self.manifest_file.write_text(json.dumps(self.manifest), encoding="utf-8")

    def enable_metadata_revision(self):
        self.xml.set("saveUser", "fixture-account")
        self.xml.set("saveUserFull", "Fixture Account")
        self.xml.set("saveDateTime", "2020-01-01T00:00:00")
        self.xml.set("version", "fixture-version")
        metadata = ET.SubElement(self.xml, "projectMetadata")
        ET.SubElement(metadata, "author").text = "Fixture Account"
        ET.SubElement(metadata, "title").text = "Fixture project"
        self.auxiliary_members = {"styles.db": b"fixture styles", "attachments/item.bin": b"fixture attachment"}
        self.save()
        exported_qgs, exported_qgz = self.qgs.read_bytes(), self.qgz.read_bytes()
        exported_hash = self.manifest["project_qgs_sha256"]
        current = replace_identity_values(exported_qgs, save_user="", save_user_full="", author="Public Author")
        self.xml = ET.fromstring(current)
        self.manifest["format_version"] = 2
        self.save(refresh_manifest=False)
        self.manifest["metadata_revision"] = build_metadata_revision(
            exported_qgs, self.qgs.read_bytes(), exported_project_qgs_sha256=exported_hash,
            before_qgz=exported_qgz, after_qgz=self.qgz.read_bytes())
        self.save(refresh_manifest=False)

    def check(self, expected, phrase=None):
        result, code = audit_project(self.root)
        self.assertEqual(code, expected, result)
        self.assertEqual(result["passed"], expected == 0)
        if phrase:
            self.assertIn(phrase, " ".join(result["errors"]))
        return result

    def layout(self, index=0):
        return self.xml.findall("./Layouts/Layout")[index]

    def map(self, index=0):
        return self.layout(index).find("./LayoutItem[@type='65639']")

    def legend(self, index=0):
        return self.layout(index).find("./LayoutItem[@type='65642']")

    def shader(self):
        return self.map(12).find(".//colorrampshader")

    def test_valid_read_only_without_external_modules(self):
        before = {p.relative_to(self.root).as_posix(): sha256_file(p) for p in self.root.rglob("*") if p.is_file()}
        result = self.check(0)
        self.assertEqual((result["layout_count"], result["export_count"]), (13, 27))
        process = subprocess.run([sys.executable, "-S", str(SCRIPT), "--check", "--project-root", str(self.root), "--json"], capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertTrue(json.loads(process.stdout)["passed"])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): sha256_file(p) for p in self.root.rglob("*") if p.is_file()})

    def test_qgs_qgz_mismatch_fails(self):
        self.xml.set("version", "changed")
        self.save(sync_zip=False)
        self.check(1, "birebir")

    def test_missing_layout_fails(self):
        self.xml.find("Layouts").remove(self.layout(0))
        self.save()
        self.check(1, "13")

    def test_unlocked_map_fails_even_after_new_layout_fingerprint(self):
        self.map().set("keepLayerSet", "false")
        self.save(refresh_contract=True)
        self.check(1, "kilitli")

    def test_followed_theme_fails(self):
        self.map().set("followPreset", "true")
        self.save(refresh_contract=True)
        self.check(1, "tema")

    def test_wrong_map_layer_set_fails(self):
        self.map().find("LayerSet/Layer").text = "score_02"
        self.save(refresh_contract=True)
        self.check(1, "katman kümesi")

    def test_layer_style_missing_fails(self):
        self.map().remove(self.map().find("LayerStyles"))
        self.save()
        self.check(1, "Kilitli")

    def test_style_changed_fails(self):
        self.map().find(".//qgis").set("opacity", "0.1")
        self.save()
        self.check(1, "stili")

    def test_wrong_linked_legend_map_fails(self):
        self.legend().set("map_uuid", "{map-2}")
        self.save(refresh_contract=True)
        self.check(1, "UUID")

    def test_foreign_thematic_legend_fails(self):
        self.legend().find(".//layer-tree-layer").set("id", "score_02")
        self.save(refresh_contract=True)
        self.check(1, "Lejant")

    def test_absolute_saved_layer_source_fails(self):
        self.map().find("LayerSet/Layer").set("source", str(self.root / "data/score_01.tif"))
        self.save(refresh_contract=True)
        self.check(1, "göreli")

    def test_missing_local_file_fails(self):
        (self.root / "data/score_01.tif").unlink()
        self.check(1, "kaynağı eksik")

    def test_source_outside_project_fails(self):
        self.xml.find("./projectlayers/maplayer/datasource").text = "../../outside.tif"
        self.save()
        self.check(1, "kökünün dışında")

    def test_wrong_thematic_raster_contract_fails(self):
        self.contract["layouts"][0]["raster_path"] = "data/score_02.tif"
        self.save()
        self.check(1, "dosya yolu")

    def test_rounded_or_duplicate_class_values_fail(self):
        self.shader().findall("item")[1].set("value", "0.75")
        self.save(refresh_contract=True)
        self.check(1, "0, 1, 2, 3")

    def test_linear_interpolation_fails(self):
        self.shader().set("colorRampType", "INTERPOLATED")
        self.save(refresh_contract=True)
        self.check(1, "EXACT")

    def test_wrong_approved_color_fails(self):
        self.shader().findall("item")[2].set("color", "#ffffff")
        self.save(refresh_contract=True)
        self.check(1, "renkleri")

    def test_continuous_legend_fails(self):
        self.shader().find("rampLegendSettings").set("useContinuousLegend", "1")
        self.save(refresh_contract=True)
        self.check(1, "sürekli")

    def test_changed_geometry_fingerprint_fails(self):
        self.map().set("size", "199,133,mm")
        self.save()
        self.check(1, "tasarımı")

    def test_missing_export_fails(self):
        (self.root / self.manifest["files"][0]["path"]).unlink()
        self.check(1, "çıktısı eksik")

    def test_tampered_export_fails(self):
        (self.root / self.manifest["files"][0]["path"]).write_bytes(b"bad")
        self.check(1, "SHA-256")

    def test_stale_export_project_hash_fails(self):
        self.xml.set("version", "changed")
        self.save(refresh_manifest=False)
        self.check(1, "güncel QGS")

    def test_v1_identity_edit_still_requires_exact_export_source_hash(self):
        self.xml.set("saveUser", "fixture-account")
        self.save()
        self.xml.set("saveUser", "")
        self.save(refresh_manifest=False)
        self.check(1, "güncel QGS")

    def test_v2_identity_only_revision_is_read_only_and_keeps_export_identity(self):
        original_files = copy.deepcopy(self.manifest["files"])
        self.enable_metadata_revision()
        revision = self.manifest["metadata_revision"]
        self.assertEqual(self.manifest["project_qgs_sha256"], revision["exported_project_qgs_sha256"])
        self.assertNotEqual(self.manifest["project_qgs_sha256"], sha256_file(self.qgs))
        self.assertEqual(original_files, self.manifest["files"])
        before = {p.relative_to(self.root).as_posix(): sha256_file(p) for p in self.root.rglob("*") if p.is_file()}
        self.check(0)
        process = subprocess.run([sys.executable, "-S", str(SCRIPT), "--check", "--project-root", str(self.root), "--json"], capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertTrue(json.loads(process.stdout)["passed"])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): sha256_file(p) for p in self.root.rglob("*") if p.is_file()})

    def test_invalid_export_manifest_versions_fail(self):
        for version in (None, True, 2.0, "2", 0, 3):
            with self.subTest(version=version):
                self.manifest["format_version"] = version
                self.save(refresh_manifest=False)
                self.check(1, "manifesti geçersiz")

    def test_v2_does_not_accept_other_xml_changes_after_current_hash_and_contract_refresh(self):
        self.enable_metadata_revision()
        original_xml, original_contract = copy.deepcopy(self.xml), copy.deepcopy(self.contract)
        changes = {
            "version": lambda: self.xml.set("version", "other-version"),
            "saveDateTime": lambda: self.xml.set("saveDateTime", "2021-01-01T00:00:00"),
            "other metadata": lambda: setattr(self.xml.find("projectMetadata/title"), "text", "Different title"),
            "extent/geometry": lambda: self.map().set("size", "199,133,mm"),
            "locked style": lambda: self.map().find(".//qgis").set("opacity", "0.1"),
            "layer source": lambda: self.map().find("LayerSet/Layer").set("source", "../data/score_02.tif"),
            "author attribute": lambda: self.xml.find("projectMetadata/author").set("role", "editor"),
            "author tail": lambda: setattr(self.xml.find("projectMetadata/author"), "tail", " "),
            "layout whitespace": lambda: setattr(self.layout(), "text", "\n  "),
            "comment": lambda: self.xml.append(ET.Comment("unrelated change")),
        }
        for label, change in changes.items():
            with self.subTest(change=label):
                self.xml, self.contract = copy.deepcopy(original_xml), copy.deepcopy(original_contract)
                change()
                self.save(refresh_contract=True)
                self.check(1, "dışındaki QGS baytları")

    def test_v2_rejects_author_children(self):
        self.enable_metadata_revision()
        ET.SubElement(self.xml.find("projectMetadata/author"), "extra").text = "hidden"
        self.save()
        self.check(1, "yalnız düz XML metni")

    def test_v2_rejects_missing_or_extended_revision_policy(self):
        self.enable_metadata_revision()
        original_revision = copy.deepcopy(self.manifest["metadata_revision"])
        variants = [None, {}, {**original_revision, "kind": "allow-all-metadata"},
                    {**original_revision, "fields": original_revision["fields"] + ["qgis/Layouts"]},
                    {**original_revision, "render_performed": True},
                    {**original_revision, "ignored_extra_field": "value"}]
        for revision in variants:
            with self.subTest(revision=revision):
                self.manifest["metadata_revision"] = revision
                self.save(refresh_manifest=False)
                self.check(1, "tanığı")

    def test_v2_rejects_changed_historical_or_current_hash(self):
        self.enable_metadata_revision()
        original_revision = copy.deepcopy(self.manifest["metadata_revision"])
        for field in ("exported_project_qgs_sha256", "current_project_qgs_sha256", "identity_normalized_qgs_sha256"):
            with self.subTest(field=field):
                self.manifest["metadata_revision"] = {**original_revision, field: "0" * 64}
                self.save(refresh_manifest=False)
                self.check(1)

    def test_v2_rejects_changed_or_removed_qgz_auxiliary_member(self):
        self.enable_metadata_revision()
        original_auxiliary = self.auxiliary_members.copy()
        for members in ({**original_auxiliary, "styles.db": b"changed"}, {},
                        {**original_auxiliary, "new.bin": b"added"}):
            with self.subTest(members=tuple(members)):
                self.auxiliary_members = members
                self.save()
                self.check(1, "XML dışı üyeleri")

    def test_v2_rejects_changed_qgz_project_member_name(self):
        self.enable_metadata_revision()
        with zipfile.ZipFile(self.qgz, "w") as archive:
            archive.writestr("renamed.qgs", self.qgs.read_bytes())
            for name, data in self.auxiliary_members.items():
                archive.writestr(name, data)
        self.check(1, "üye adı")

    def test_v2_does_not_bypass_export_file_integrity(self):
        self.enable_metadata_revision()
        (self.root / self.manifest["files"][0]["path"]).write_bytes(b"changed output")
        self.check(1, "SHA-256")

    def test_missing_manifest_fails(self):
        self.manifest_file.unlink()
        self.check(1, "okunamadı")

    def test_unlisted_or_duplicate_export_fails(self):
        self.manifest["files"].append(copy.deepcopy(self.manifest["files"][0]))
        self.save()
        self.check(1, "13 PNG")

    def test_wrong_atlas_page_count_record_fails(self):
        self.manifest["files"][-1]["page_count"] = 12
        self.save()
        self.check(1, "sayfa")

    def test_png_dimensions_mismatch_fails(self):
        self.manifest["files"][0]["width_px"] = 999
        self.save()
        self.check(1, "boyutları")

    def test_bad_contract_fails_cleanly(self):
        self.contract_file.write_text('{"layouts": []}', encoding="utf-8")
        self.check(1, "sürümü")


if __name__ == "__main__":
    unittest.main()
