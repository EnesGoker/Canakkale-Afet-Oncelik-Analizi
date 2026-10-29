"""Byte-preserving QGIS identity edits and saved-export provenance witnesses.

Only three XML value spans are excluded from the identity-normalized digest.
All other bytes, including whitespace, comments, attribute order and author
markup/tail, remain covered. No XML serialization, file writes or rendering is
performed. A witness must be created from the actual original export source;
the old source SHA-256 remains the export identity, not the current file hash.
"""
from __future__ import annotations

import hashlib
import io
import re
from xml.parsers import expat
from xml.sax.saxutils import escape
import zipfile


IDENTITY_FIELDS = (
    "qgis/@saveUser",
    "qgis/@saveUserFull",
    "qgis/projectMetadata/author",
)
IDENTITY_REVISION_KIND = "qgis-identity-only-v1"
_AUTHOR_PATH = ("qgis", "projectMetadata", "author")
_ATTRIBUTE_START = re.compile(rb"([^ \t\r\n=/<>\"']+)[ \t\r\n]*=[ \t\r\n]*(['\"])")
_REVISION_KEYS = {
    "kind", "fields", "exported_project_qgs_sha256", "current_project_qgs_sha256",
    "identity_normalized_qgs_sha256", "qgz_project_member",
    "qgz_auxiliary_members_sha256", "render_performed",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _opening_tag_end(data: bytes, start: int) -> int:
    quote = None
    for index in range(start, len(data)):
        char = data[index]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in (34, 39):
            quote = char
        elif char == 62:
            return index + 1
    raise ValueError("QGIS kimlik alanının XML başlangıç etiketi geçersiz.")


def _root_attribute_spans(data: bytes, start: int, end: int) -> dict[str, tuple[int, int]]:
    spans = {}
    cursor = start + len(b"<qgis")
    while cursor < end:
        while data[cursor:cursor + 1] in (b" ", b"\t", b"\r", b"\n"):
            cursor += 1
        if data[cursor:cursor + 1] == b">" or data[cursor:cursor + 2] == b"/>":
            break
        match = _ATTRIBUTE_START.match(data, cursor, end)
        if match is None:
            raise ValueError("QGIS kök öğesinin XML özellikleri geçersiz.")
        value_start = match.end()
        value_end = data.find(match[2], value_start, end)
        if value_end < 0:
            raise ValueError("QGIS kök öğesinin XML özellikleri geçersiz.")
        if match[1] in (b"saveUser", b"saveUserFull"):
            key = "qgis/@" + match[1].decode("ascii")
            if key in spans:
                raise ValueError("QGIS kimlik alanları tekrarlı.")
            spans[key] = (value_start, value_end)
        cursor = value_end + 1
    return spans


def _identity_spans(data: bytes) -> dict[str, tuple[int, int]]:
    if not isinstance(data, bytes):
        raise ValueError("QGIS kimlik kontrolü UTF-8 XML baytları gerektirir.")
    try:
        data.decode("utf-8-sig")
    except UnicodeError:
        raise ValueError("QGIS kimlik kontrolü UTF-8 XML baytları gerektirir.") from None
    parser = expat.ParserCreate(encoding="utf-8")
    stack = []
    spans = {}
    metadata_count = author_count = 0
    author_start = None

    def start(name, _attributes):
        nonlocal metadata_count, author_count, author_start
        path = (*stack, name)
        if not stack:
            if name != "qgis":
                raise ValueError("Kimlik kontrolü yalnız QGIS proje XML'ini kabul eder.")
            offset = parser.CurrentByteIndex
            spans.update(_root_attribute_spans(data, offset, _opening_tag_end(data, offset)))
        if path == ("qgis", "projectMetadata"):
            metadata_count += 1
        if path == _AUTHOR_PATH:
            author_count += 1
            author_start = _opening_tag_end(data, parser.CurrentByteIndex)
            if data[author_start - 2:author_start] == b"/>":
                raise ValueError("QGIS author alanı açık başlangıç ve bitiş etiketleri gerektirir.")
        if len(path) > len(_AUTHOR_PATH) and path[:len(_AUTHOR_PATH)] == _AUTHOR_PATH:
            raise ValueError("QGIS author alanı yalnız düz XML metni içermeli.")
        stack.append(name)

    def end(_name):
        if tuple(stack) == _AUTHOR_PATH:
            value_end = parser.CurrentByteIndex
            if author_start is None or b"<" in data[author_start:value_end]:
                raise ValueError("QGIS author alanı yalnız düz XML metni içermeli.")
            spans[IDENTITY_FIELDS[2]] = (author_start, value_end)
        stack.pop()

    def reject_entity(*_args):
        raise ValueError("QGIS kimlik kontrolünde XML entity tanımları desteklenmez.")

    def doctype(_name, _system_id, _public_id, internal_subset):
        if internal_subset:
            reject_entity()

    def declaration(_version, encoding, _standalone):
        if encoding is not None and encoding.lower().replace("-", "") != "utf8":
            raise ValueError("QGIS kimlik kontrolü UTF-8 XML baytları gerektirir.")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.EntityDeclHandler = reject_entity
    parser.ExternalEntityRefHandler = reject_entity
    parser.StartDoctypeDeclHandler = doctype
    parser.XmlDeclHandler = declaration
    try:
        parser.Parse(data, True)
    except expat.ExpatError:
        raise ValueError("QGIS kimlik alanları için XML bozuk veya tekrarlı.") from None
    if metadata_count != 1 or author_count != 1 or set(spans) != set(IDENTITY_FIELDS):
        raise ValueError("QGIS projesinde tam üç benzersiz kimlik alanı bulunmalı.")
    return spans


def _substitute(data: bytes, spans: dict, values: dict[str, bytes]) -> bytes:
    chunks = []
    cursor = 0
    for name, (start, end) in sorted(spans.items(), key=lambda item: item[1][0]):
        chunks.extend((data[cursor:start], values[name]))
        cursor = end
    chunks.append(data[cursor:])
    return b"".join(chunks)


def identity_normalized_sha256(qgs_bytes: bytes) -> str:
    """Hash all original XML bytes except the three fixed identity value spans."""
    spans = _identity_spans(qgs_bytes)
    return _sha256(_substitute(qgs_bytes, spans, {name: b"__QGIS_IDENTITY_VALUE__" for name in IDENTITY_FIELDS}))


def replace_identity_values(qgs_bytes: bytes, *, save_user: str, save_user_full: str, author: str) -> bytes:
    """Return XML with only the three values replaced; preserve every other byte."""
    spans = _identity_spans(qgs_bytes)
    values = {}
    for name, value in zip(IDENTITY_FIELDS, (save_user, save_user_full, author)):
        if not isinstance(value, str):
            raise ValueError("Yeni QGIS kimlik alanları metin olmalı.")
        try:
            values[name] = escape(value, {"\"": "&quot;", "'": "&apos;", "\r": "&#13;", "\n": "&#10;", "\t": "&#9;"}).encode("utf-8")
        except UnicodeError:
            raise ValueError("Yeni QGIS kimlik alanları geçerli UTF-8 metni olmalı.") from None
    updated = _substitute(qgs_bytes, spans, values)
    if identity_normalized_sha256(updated) != identity_normalized_sha256(qgs_bytes):
        raise ValueError("QGIS kimlik değişimi diğer XML baytlarını değiştirmiş.")
    return updated


def _qgz_proof(qgz_bytes: bytes, qgs_bytes: bytes) -> tuple[str, dict[str, str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(qgz_bytes)) as archive:
            names = archive.namelist()
            projects = [name for name in names if name.lower().endswith(".qgs")]
            if len(set(names)) != len(names) or len(projects) != 1:
                raise ValueError("QGZ üye adları benzersiz olmalı ve tek QGS içermeli.")
            project = projects[0]
            if archive.read(project) != qgs_bytes:
                raise ValueError("QGS ve QGZ içindeki proje XML'i birebir eşleşmiyor.")
            return project, {name: _sha256(archive.read(name)) for name in sorted(names) if name != project}
    except (zipfile.BadZipFile, OSError, RuntimeError, TypeError):
        raise ValueError("QGZ kimlik değişimi kanıtı okunamadı/bozuk.") from None


def build_metadata_revision(exported_qgs: bytes, current_qgs: bytes, *, exported_project_qgs_sha256: str,
                            before_qgz: bytes, after_qgz: bytes) -> dict:
    """Verify the historical source and a strictly metadata-only edit, then attest it.

    The original private identity values are never included in the witness.
    Consumers trust this provenance record as they trust the export manifest;
    the old full-source digest alone cannot reconstruct an unavailable source.
    """
    if not _valid_sha256(exported_project_qgs_sha256) or _sha256(exported_qgs) != exported_project_qgs_sha256:
        raise ValueError("Özgün QGS mevcut dışa aktarma kaynağının SHA-256 özetiyle eşleşmiyor.")
    signature = identity_normalized_sha256(exported_qgs)
    if identity_normalized_sha256(current_qgs) != signature:
        raise ValueError("Üç kimlik alanı dışındaki QGS baytları değişmiş.")
    original_member, original_auxiliary = _qgz_proof(before_qgz, exported_qgs)
    current_member, current_auxiliary = _qgz_proof(after_qgz, current_qgs)
    if (original_member, original_auxiliary) != (current_member, current_auxiliary):
        raise ValueError("QGZ proje üye adı veya XML dışı üyeleri değişmiş.")
    return {"kind": IDENTITY_REVISION_KIND, "fields": list(IDENTITY_FIELDS),
            "exported_project_qgs_sha256": exported_project_qgs_sha256,
            "current_project_qgs_sha256": _sha256(current_qgs),
            "identity_normalized_qgs_sha256": signature,
            "qgz_project_member": original_member,
            "qgz_auxiliary_members_sha256": original_auxiliary,
            "render_performed": False}


def validate_metadata_revision(qgs_bytes: bytes, qgz_bytes: bytes, exported_project_qgs_sha256: str,
                               revision: object) -> None:
    """Validate a v2 witness against the current project without changing files."""
    if (not isinstance(revision, dict) or set(revision) != _REVISION_KEYS
            or revision.get("kind") != IDENTITY_REVISION_KIND
            or revision.get("fields") != list(IDENTITY_FIELDS)
            or revision.get("render_performed") is not False):
        raise ValueError("QGIS kimlik değişimi tanığı eksik/geçersiz veya kapsamı değiştirilmiş.")
    for value in (exported_project_qgs_sha256, revision["exported_project_qgs_sha256"],
                  revision["current_project_qgs_sha256"], revision["identity_normalized_qgs_sha256"]):
        if not _valid_sha256(value):
            raise ValueError("QGIS kimlik değişimi tanığında SHA-256 alanı geçersiz.")
    if revision["exported_project_qgs_sha256"] != exported_project_qgs_sha256:
        raise ValueError("QGIS kimlik değişimi tanığı özgün dışa aktarma kaynağıyla eşleşmiyor.")
    if revision["current_project_qgs_sha256"] != _sha256(qgs_bytes):
        raise ValueError("QGIS kimlik değişimi tanığı güncel QGS SHA-256 özetiyle eşleşmiyor.")
    if revision["identity_normalized_qgs_sha256"] != identity_normalized_sha256(qgs_bytes):
        raise ValueError("Üç kimlik alanı dışındaki QGS baytları değişmiş.")
    auxiliary = revision["qgz_auxiliary_members_sha256"]
    if (not isinstance(revision["qgz_project_member"], str)
            or not isinstance(auxiliary, dict)
            or any(not isinstance(name, str) or not _valid_sha256(value) for name, value in auxiliary.items())):
        raise ValueError("QGZ üye bütünlüğü tanığı geçersiz.")
    member, actual_auxiliary = _qgz_proof(qgz_bytes, qgs_bytes)
    if (member, actual_auxiliary) != (revision["qgz_project_member"], auxiliary):
        raise ValueError("QGZ proje üye adı veya XML dışı üyeleri değişmiş.")
