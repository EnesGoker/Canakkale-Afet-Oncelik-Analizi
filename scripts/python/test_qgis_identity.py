#!/usr/bin/env python3
"""Synthetic byte-level tests for the three-field QGIS identity exception."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import unittest
import warnings
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
from qgis_identity import (
    build_metadata_revision,
    identity_normalized_sha256,
    replace_identity_values,
)


QGS = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE qgis PUBLIC "https://example.invalid/qgis.dtd" "SYSTEM">
<qgis saveUser = 'fixture-account' saveUserFull="Fixture Göker" version="3.44.10" saveDateTime="2026-01-01T10:00:00">
  <!-- saveUser="comment-account" -->
  <projectMetadata>
    <author>Fixture Author &amp; Other</author>\x20\x20
    <title>Portfolio example</title>
  </projectMetadata>
  <Layouts>
    <LayerStyle label="line" />
    <qgis saveUser="nested-account" saveUserFull="Nested User"><projectMetadata><author>Nested Author</author></projectMetadata></qgis>
  </Layouts>
</qgis>
'''.encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def qgz(xml, *, project_name="project.qgs", auxiliary=None, duplicate=None):
    stream = io.BytesIO()
    members = {"project_styles.db": b"synthetic style database", "attachments/icon.svg": b"<svg />"}
    if auxiliary is not None:
        members = auxiliary
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Intentional duplicate-member fixtures.
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as archive:
            archive.writestr(project_name, xml)
            for name, content in members.items():
                archive.writestr(name, content)
            if duplicate is not None:
                archive.writestr(*duplicate)
    return stream.getvalue()


class QgisIdentityTests(unittest.TestCase):
    def replace(self, data=QGS):
        return replace_identity_values(data, save_user="", save_user_full="", author="Public Author")

    def revision(self, current=None, **overrides):
        current = self.replace() if current is None else current
        values = {
            "exported_project_qgs_sha256": sha256(QGS),
            "before_qgz": qgz(QGS),
            "after_qgz": qgz(current),
        }
        values.update(overrides)
        return build_metadata_revision(QGS, current, **values)

    def assert_not_equivalent(self, changed):
        try:
            digest = identity_normalized_sha256(changed)
        except ValueError:
            return
        self.assertNotEqual(identity_normalized_sha256(QGS), digest)

    def test_replace_changes_only_three_value_spans(self):
        actual = self.replace()
        expected = QGS.replace(b"'fixture-account'", b"''", 1)
        expected = expected.replace('"Fixture Göker"'.encode("utf-8"), b'""', 1)
        expected = expected.replace(b">Fixture Author &amp; Other</author>", b">Public Author</author>", 1)
        self.assertEqual(actual, expected)
        self.assertIn(b'<qgis saveUser="nested-account"', actual)
        self.assertIn(b'<!-- saveUser="comment-account" -->', actual)
        self.assertEqual(identity_normalized_sha256(QGS), identity_normalized_sha256(actual))

    def test_replacement_escapes_xml_and_accepts_multibyte_values(self):
        identity = 'Göker & <example> "quoted" \'single\''
        actual = replace_identity_values(QGS, save_user=identity, save_user_full=identity, author=identity)
        xml = ET.fromstring(actual)
        self.assertEqual(xml.attrib["saveUser"], identity)
        self.assertEqual(xml.attrib["saveUserFull"], identity)
        self.assertEqual(xml.findtext("./projectMetadata/author"), identity)
        self.assertEqual(identity_normalized_sha256(QGS), identity_normalized_sha256(actual))

    def test_blank_author_preserves_explicit_tag_pair(self):
        actual = replace_identity_values(QGS, save_user="", save_user_full="", author="")
        self.assertIn(b"<author></author>  \n", actual)
        self.assertEqual(identity_normalized_sha256(QGS), identity_normalized_sha256(actual))

    def test_bom_and_fake_field_inside_other_root_attribute_are_preserved(self):
        source = b"\xef\xbb\xbf" + QGS.replace(b"<qgis ", b'''<qgis notes=" saveUser='decoy' " ''', 1)
        actual = self.replace(source)
        self.assertTrue(actual.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b'''notes=" saveUser='decoy' "''', actual)
        self.assertEqual(identity_normalized_sha256(source), identity_normalized_sha256(actual))
        self.assertNotEqual(identity_normalized_sha256(source), identity_normalized_sha256(source.replace(b"decoy", b"changed")))

    def test_all_other_xml_bytes_remain_significant(self):
        mutations = {
            "version": (b' version="3.44.10"', b' version="3.44.11"'),
            "save time": (b"2026-01-01T10:00:00", b"2026-01-02T10:00:00"),
            "title": (b"Portfolio example", b"Different example"),
            "style": (b'label="line"', b'label="fill"'),
            "indentation": (b"\n  <projectMetadata>", b"\n   <projectMetadata>"),
            "comment": (b"comment-account", b"changed-comment"),
            "author attribute": (b"<author>Fixture", b'<author role="changed">Fixture'),
            "author tail": (b"</author>  \n", b"</author>\t\n"),
            "attribute spacing": (b"saveUser = '", b"saveUser= '"),
            "nested identity": (b"nested-account", b"changed-nested"),
            "nested author": (b"Nested Author", b"Changed Nested Author"),
        }
        for label, (before, after) in mutations.items():
            with self.subTest(label=label):
                self.assertIn(before, QGS)
                self.assert_not_equivalent(QGS.replace(before, after, 1))

    def test_missing_duplicate_or_malformed_fields_are_rejected(self):
        fixtures = {
            "missing root attribute": QGS.replace(b" saveUser = 'fixture-account'", b"", 1),
            "duplicate root attribute": QGS.replace(b"<qgis ", b'<qgis saveUser="duplicate" ', 1),
            "missing author": QGS.replace(b"<author>Fixture Author &amp; Other</author>", b"", 1),
            "duplicate author": QGS.replace(b"</projectMetadata>", b"<author>Duplicate</author></projectMetadata>", 1),
            "duplicate metadata": QGS.replace(b"  <Layouts>", b"  <projectMetadata><author>Duplicate</author></projectMetadata><Layouts>", 1),
            "wrong root": QGS.replace(b"<qgis ", b"<wrong ", 1).replace(b"</qgis>\n", b"</wrong>\n", 1),
            "broken XML": QGS[:-10],
            "invalid UTF-8": QGS.replace(b"Portfolio example", b"\xff"),
            "wrong encoding declaration": QGS.replace(b'encoding="UTF-8"', b'encoding="UTF-16"', 1),
            "self-closing author": QGS.replace(b"<author>Fixture Author &amp; Other</author>", b"<author/>"),
        }
        for label, data in fixtures.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError) as caught:
                    identity_normalized_sha256(data)
                self.assertNotIn("fixture-account", str(caught.exception))
                self.assertNotIn("Fixture Author", str(caught.exception))

    def test_author_markup_and_entity_definitions_are_rejected(self):
        for content in (b"<child>hidden</child>", b"<!-- hidden -->text", b"<![CDATA[text]]>", b"<?hidden value?>text"):
            with self.subTest(content=content):
                changed = QGS.replace(b"Fixture Author &amp; Other", content, 1)
                with self.assertRaises(ValueError):
                    identity_normalized_sha256(changed)
        defined_entity = QGS.replace(
            b'<!DOCTYPE qgis PUBLIC "https://example.invalid/qgis.dtd" "SYSTEM">',
            b'<!DOCTYPE qgis [<!ENTITY identity "Synthetic identity">]>',
        ).replace(b"Fixture Author &amp; Other", b"&identity;", 1)
        with self.assertRaises(ValueError):
            identity_normalized_sha256(defined_entity)

    def test_witness_preserves_export_identity_without_old_private_values(self):
        current = self.replace()
        revision = self.revision(current)
        serialized = json.dumps(revision, ensure_ascii=False)
        self.assertIn(sha256(QGS), serialized)
        self.assertIn(sha256(current), serialized)
        self.assertIn(identity_normalized_sha256(QGS), serialized)
        for value in ("fixture-account", "Fixture Göker", "Fixture Author", "Nested Author"):
            self.assertNotIn(value, serialized)

    def test_witness_rejects_wrong_export_source_hash(self):
        with self.assertRaises(ValueError):
            self.revision(exported_project_qgs_sha256="0" * 64)

    def test_witness_rejects_any_unmasked_xml_change(self):
        current = self.replace().replace(b"Portfolio example", b"Changed report title")
        with self.assertRaises(ValueError):
            self.revision(current)

    def test_witness_rejects_qgs_qgz_mismatch(self):
        current = self.replace()
        for key, archive in (("before_qgz", qgz(current)), ("after_qgz", qgz(QGS))):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.revision(current, **{key: archive})

    def test_witness_rejects_attachment_content_name_or_set_changes(self):
        current = self.replace()
        invalid = [
            {"project_styles.db": b"different database", "attachments/icon.svg": b"<svg />"},
            {"renamed.db": b"synthetic style database", "attachments/icon.svg": b"<svg />"},
            {"project_styles.db": b"synthetic style database"},
            {"project_styles.db": b"synthetic style database", "attachments/icon.svg": b"<svg />", "extra": b"new"},
        ]
        for auxiliary in invalid:
            with self.subTest(members=sorted(auxiliary)):
                with self.assertRaises(ValueError):
                    self.revision(current, after_qgz=qgz(current, auxiliary=auxiliary))

    def test_witness_rejects_renamed_duplicate_or_multiple_project_members(self):
        current = self.replace()
        archives = [
            qgz(current, project_name="renamed.qgs"),
            qgz(current, duplicate=("project.qgs", current)),
            qgz(current, duplicate=("project_styles.db", b"synthetic style database")),
            qgz(current, auxiliary={"other.qgs": current}),
            b"invalid ZIP",
        ]
        for index, archive in enumerate(archives):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    self.revision(current, after_qgz=archive)


if __name__ == "__main__":
    unittest.main()
