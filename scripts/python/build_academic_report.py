#!/usr/bin/env python3
"""Tanımlı canonical varlıklardan A4 akademik DOCX raporu üretir."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Mm, Pt, RGBColor


OUTPUT_DOCX_NAME = "canakkale_disaster_priority_academic_report.docx"

DOC_TITLE = "Çanakkale Çok Kriterli Afet Öncelik Alanları Analizi"
DOC_SUBTITLE = "Processed-canonical veri seviyesine dayalı akademik rapor"
REPORT_DATE = date.today().isoformat()

PROJECT_ASSETS = {
    "asset_lock": Path("docs/report_asset_outline_lock.md"),
    "weight_config": Path("config/mcda_weights.tsv"),
    "source_inventory": Path("docs/data_source_inventory.md"),
    "canonical_policy": Path("docs/canonical_data_policy.md"),
    "methodology": Path("docs/methodology/updated_mcda_methodology_note.md"),
    "scientific_limits": Path("docs/methodology/scientific_limits.md"),
    "class_distribution": Path("outputs/tables/mcda_class_distribution.csv"),
    "district_classes": Path("outputs/tables/mcda_class_area_by_district.csv"),
    "raster_stats": Path("outputs/tables/criterion_raster_statistics.csv"),
    "sensitivity_summary": Path("outputs/tables/mcda_sensitivity_scenario_summary.csv"),
    "sensitivity_interpretation": Path("outputs/tables/mcda_sensitivity_interpretation.csv"),
    "atlas_pdf": Path("outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf"),
}

BASELINE_WEIGHT_SCENARIO = "baseline"
WEIGHT_COLUMNS = [
    "scenario_id",
    "scenario_label",
    "scenario_role",
    "criterion_order",
    "criterion_id",
    "display_name_tr",
    "raster_path",
    "weight",
    "block_tr",
    "note_tr",
]
EXPECTED_WEIGHT_IDS = [
    "earthquake_pga_score",
    "fault_proximity_score",
    "site_condition_score",
    "population_exposure_score",
    "building_exposure_density_score",
    "flood_score",
    "hydrography_proximity_score",
    "slope_score",
    "landcover_sensitivity_score",
    "tree_cover_score",
    "road_accessibility_difficulty_score",
]

MAPS = [
    (
        1,
        "Çok Kriterli Afet Öncelik Sınıfı",
        "outputs/maps/png/01_cok_kriterli_oncelik_sinifi.png",
        "Nihai MCDA sınıf haritası; sınıf 1 çok düşük, sınıf 5 çok yüksek göreli önceliği gösterir.",
    ),
    (
        2,
        "Fay Yakınlık Skoru",
        "outputs/maps/png/02_fay_yakinlik_skoru.png",
        "Diri fay hatlarına yakınlık etkisini temsil eden normalize kriter skoru.",
    ),
    (
        3,
        "Nüfus Maruziyet Skoru",
        "outputs/maps/png/03_nufus_maruziyet_skoru.png",
        "WorldPop tabanlı yerleşik nüfus maruziyeti için log-normalize skor.",
    ),
    (
        4,
        "Zemin Koşulu Skoru",
        "outputs/maps/png/04_zemin_kosulu_skoru.png",
        "USGS Global Vs30 Mosaic verisinden türetilmiş düşük VS30 / yumuşak zemin proxy skoru.",
    ),
    (
        5,
        "Deprem PGA Skoru",
        "outputs/maps/png/05_deprem_pga_skoru.png",
        "AFAD TDTH parametrelerinden türetilmiş PGA destek yüzeyinin normalize skoru.",
    ),
    (
        6,
        "Yapı Maruziyet Yoğunluk Skoru",
        "outputs/maps/png/06_yapi_maruziyet_yogunluk_skoru.png",
        "Microsoft building footprints ve OSM gap-fill tabanlı yapı yoğunluğu proxy skoru.",
    ),
    (
        7,
        "Taşkın Skoru",
        "outputs/maps/png/07_taskin_skoru.png",
        "JRC/CEMS RP100 taşkın derinlik rasterinden türetilmiş taşkın destek skoru.",
    ),
    (
        8,
        "Hidrografya Yakınlık Skoru",
        "outputs/maps/png/08_hidrografya_yakinlik_skoru.png",
        "HydroRIVERS ve OSM waterways hibrit hidrografya ağına yakınlık skoru.",
    ),
    (
        9,
        "Eğim Skoru",
        "outputs/maps/png/09_egim_skoru.png",
        "Copernicus DEM GLO-30 tabanlı eğim destek skorunun mekansal dağılımı.",
    ),
    (
        10,
        "Arazi Örtüsü Duyarlılık Skoru",
        "outputs/maps/png/10_arazi_ortusu_duyarlilik_skoru.png",
        "ESA WorldCover 2021 sınıflarına dayalı arazi örtüsü duyarlılık skoru.",
    ),
    (
        11,
        "Ağaç Örtüsü Skoru",
        "outputs/maps/png/11_agac_ortusu_skoru.png",
        "Copernicus/CLMS Tree Cover Density 2021 tabanlı vejetasyon destek skoru.",
    ),
    (
        12,
        "Yol Erişim Zorluğu Skoru",
        "outputs/maps/png/12_yol_erisim_zorlugu_skoru.png",
        "OSM yol ağına dayalı operasyonel erişim zorluğu proxy skoru.",
    ),
]

DATA_SOURCES = [
    (
        "İdari sınır / AOI",
        "HGM idari sınır verileri; HGM metadata'sında 2021/2023 işlem tarihleri; OSM destekli ilçe adı aktarımı",
        "AOI ve ilçe özet birimi",
    ),
    (
        "DEM / eğim",
        "Copernicus DEM GLO-30; kaynak yıl/sürüm proje metadata'sında kayıtlı değil",
        "Yükseklik ve eğim destek girdisi",
    ),
    (
        "Taşkın",
        "JRC / CEMS RP100 flood depth raster; kaynak yıl/sürüm proje metadata'sında kayıtlı değil",
        "Taşkın duyarlılık destek girdisi",
    ),
    (
        "Deprem yer hareketi",
        "AFAD TDTH parametre değerleri; kaynak workbook yılında proje metadata kaydı yok",
        "PGA tabanlı sismik tehlike destek yüzeyi",
    ),
    ("Diri fay", "MTA Türkiye Diri Fay Haritası veri paketi", "Fay yakınlık skoru"),
    ("Nüfus", "WorldPop Turkey 2020 constrained UN-adjusted population raster", "Yerleşik nüfus maruziyeti"),
    (
        "VS30",
        "USGS Global Vs30 Mosaic; kaynak yıl/sürüm proje metadata'sında kayıtlı değil",
        "Zemin koşulu proxy skoru",
    ),
    (
        "Yapılı çevre",
        "Microsoft Global ML Building Footprints; OSM buildings gap-fill; kaynak yılı/extract tarihi proje metadata'sında kayıtlı değil",
        "Bina yoğunluğu proxy skoru",
    ),
    (
        "Hidrografya",
        "HydroRIVERS v10; OSM waterways gap-fill; OSM extract tarihi proje metadata'sında kayıtlı değil",
        "Nehir/akarsu/canal yakınlık skoru",
    ),
    ("Arazi örtüsü", "ESA WorldCover 2021", "Arazi örtüsü duyarlılık girdisi"),
    ("Ağaç örtüsü", "Copernicus / CLMS HRL Tree Cover Density 2021", "Vejetasyon destek girdisi"),
    (
        "Yol erişimi",
        "OpenStreetMap / Geofabrik Turkey road network; extract tarihi proje metadata'sında kayıtlı değil",
        "Erişim zorluğu proxy skoru",
    ),
]

CLASS_LABEL_TR = {
    "1": "Çok düşük",
    "2": "Düşük",
    "3": "Orta",
    "4": "Yüksek",
    "5": "Çok yüksek",
}


class ReportBuildError(RuntimeError):
    """Rapor girdileri veya render varsayımları geçersiz olduğunda kullanılır."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Çanakkale akademik DOCX raporunu üretir.")
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_mcda_weights(project_root: Path, scenario_id: str = BASELINE_WEIGHT_SCENARIO) -> list[dict[str, Any]]:
    path = project_root / PROJECT_ASSETS["weight_config"]
    rows: list[dict[str, Any]] = []

    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != WEIGHT_COLUMNS:
            raise ReportBuildError("MCDA ağırlık config kolonları beklenen sözleşmeyle eşleşmiyor.")

        for row in reader:
            if row["scenario_id"] != scenario_id:
                continue
            try:
                order = int(row["criterion_order"])
                weight = float(row["weight"])
            except ValueError as exc:
                raise ReportBuildError(
                    f"MCDA ağırlık config içinde geçersiz sayı: {row['criterion_id']}"
                ) from exc
            if weight < 0 or weight > 1:
                raise ReportBuildError(f"MCDA ağırlığı 0-1 aralığı dışında: {row['criterion_id']}")
            rows.append(
                {
                    "order": order,
                    "criterion_id": row["criterion_id"],
                    "display_name": row["display_name_tr"],
                    "weight": weight,
                }
            )

    rows.sort(key=lambda item: item["order"])
    ids = [row["criterion_id"] for row in rows]
    if ids != EXPECTED_WEIGHT_IDS:
        raise ReportBuildError("Baseline MCDA ağırlık sırası veya kriter seti beklenen değerlerle eşleşmiyor.")

    total = sum(row["weight"] for row in rows)
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ReportBuildError(f"Baseline MCDA ağırlıkları toplamı 1.00 olmalı, gelen {total:.12f}")

    return rows


def require_inputs(project_root: Path) -> None:
    required = list(PROJECT_ASSETS.values())
    required.extend(Path(path) for _, _, path, _ in MAPS)
    missing = [str(path) for path in required if not (project_root / path).is_file()]
    if missing:
        raise ReportBuildError("Gerekli rapor varlıkları eksik:\n" + "\n".join(missing))


def rgb(hex_color: str) -> RGBColor:
    clean = hex_color.lstrip("#")
    return RGBColor(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def set_run_font(
    run: Any,
    *,
    name: str = "Calibri",
    size: float | None = None,
    color: str | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    run._element.rPr.rFonts.set(qn("w:cs"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = rgb(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def set_paragraph_spacing(paragraph: Any, *, before: float = 0, after: float = 8, line: float = 1.25) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def set_cell_shading(cell: Any, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill.lstrip("#"))


def set_cell_margins(cell: Any, top: int = 90, bottom: int = 90, start: int = 120, end: int = 120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin_name, value in (("top", top), ("bottom", bottom), ("start", start), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin_name}"))
        if node is None:
            node = OxmlElement(f"w:{margin_name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_width(cell: Any, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_geometry(table: Any, widths_dxa: list[int], indent_dxa: int = 120) -> None:
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl = table._tbl
    tbl_pr = tbl.tblPr

    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths_dxa)))
    tbl_w.set(qn("w:type"), "dxa")

    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent_dxa))
    tbl_ind.set(qn("w:type"), "dxa")

    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")

    grid = tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for index, cell in enumerate(row.cells):
            set_cell_width(cell, widths_dxa[index])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_table_borders(table: Any, color: str = "BFC7D1", size: str = "6") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def shade_header(row: Any, fill: str = "F4F6F9") -> None:
    for cell in row.cells:
        set_cell_shading(cell, fill)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                set_run_font(run, size=8.5, bold=True, color="0B2545")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(paragraph, after=0, line=1.1)


def set_repeat_table_header(row: Any) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def style_table_text(table: Any, font_size: float = 8.5) -> None:
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                set_paragraph_spacing(paragraph, after=0, line=1.1)
                for run in paragraph.runs:
                    set_run_font(run, size=font_size, color="111827")


def add_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    widths_dxa: list[int],
    *,
    font_size: float = 8.5,
) -> Any:
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_geometry(table, widths_dxa)
    set_table_borders(table)
    header_cells = table.rows[0].cells
    for idx, header in enumerate(headers):
        header_cells[idx].text = header
    shade_header(table.rows[0])
    set_repeat_table_header(table.rows[0])

    for row_values in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row_values):
            cells[idx].text = value

    style_table_text(table, font_size=font_size)
    shade_header(table.rows[0])
    return table


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, size=9, color="374151", italic=True)
    set_paragraph_spacing(p, before=3, after=6, line=1.1)


def add_table_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="Caption")
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, size=9, color="374151", italic=True)
    set_paragraph_spacing(p, before=6, after=4, line=1.1)


def add_body_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_paragraph_spacing(p, after=8, line=1.25)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    set_paragraph_spacing(p, after=3, line=1.15)


def add_note_box(doc: Document, title: str, body: str) -> None:
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [9600], indent_dxa=120)
    set_table_borders(table, color="D0D7E2", size="8")
    set_repeat_table_header(table.rows[0])
    cell = table.cell(0, 0)
    set_cell_shading(cell, "F4F6F9")
    cell.text = ""
    p_title = cell.paragraphs[0]
    run_title = p_title.add_run(title)
    set_run_font(run_title, size=10.5, bold=True, color="0B2545")
    set_paragraph_spacing(p_title, after=2, line=1.15)
    p_body = cell.add_paragraph(body)
    set_paragraph_spacing(p_body, after=0, line=1.15)
    for run in p_body.runs:
        set_run_font(run, size=9.5, color="111827")


def add_page_break(doc: Document) -> None:
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def set_picture_alt(paragraph: Any, title: str, description: str) -> None:
    inline_shapes = paragraph._p.xpath(".//wp:inline")
    if not inline_shapes:
        return
    inline = inline_shapes[-1]
    doc_pr = inline.xpath(".//wp:docPr")
    if doc_pr:
        doc_pr[0].set("title", title)
        doc_pr[0].set("descr", description)


def configure_document() -> Document:
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(18)
    section.bottom_margin = Mm(18)
    section.left_margin = Mm(18)
    section.right_margin = Mm(18)
    section.header_distance = Mm(9)
    section.footer_distance = Mm(9)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.25

    for style_name, size, color, before, after in (
        ("Heading 1", 16, "2E74B5", 16, 8),
        ("Heading 2", 13, "2E74B5", 12, 6),
        ("Heading 3", 12, "1F4D78", 8, 4),
    ):
        style = styles[style_name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(size)
        style.font.color.rgb = rgb(color)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    caption = styles["Caption"]
    caption.font.name = "Calibri"
    caption._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    caption._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    caption.font.size = Pt(9)
    caption.font.italic = True
    caption.font.color.rgb = rgb("374151")

    for list_style in ("List Bullet", "List Number"):
        style = styles[list_style]
        style.font.name = "Calibri"
        style.font.size = Pt(10.5)
        style.paragraph_format.left_indent = Inches(0.38)
        style.paragraph_format.first_line_indent = Inches(-0.19)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.15

    header = section.header.paragraphs[0]
    header.text = "Çanakkale Afet Öncelik Analizi"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_spacing(header, after=0, line=1.0)
    for run in header.runs:
        set_run_font(run, size=8.5, color="6B7280")

    footer = section.footer.paragraphs[0]
    footer.text = "Processed-canonical akademik rapor"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(footer, after=0, line=1.0)
    for run in footer.runs:
        set_run_font(run, size=8.5, color="6B7280")

    props = doc.core_properties
    props.title = DOC_TITLE
    props.subject = "Çanakkale MCDA afet öncelik akademik raporu"
    props.author = "Codex"
    props.comments = "Canonical proje varlıklarından üretildi."

    return doc


def format_number(value: str | float, decimals: int = 2) -> str:
    number = float(value)
    return f"{number:,.{decimals}f}".replace(",", " ")


def format_int(value: str | int) -> str:
    return f"{int(value):,}".replace(",", " ")


def class_distribution_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    output = []
    for row in rows:
        output.append(
            [
                row["class_value"],
                CLASS_LABEL_TR[row["class_value"]],
                format_int(row["pixel_count"]),
                format_number(row["area_km2"], 2),
                format_number(row["share_of_aoi_percent"], 2),
            ]
        )
    return output


def district_summary_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    by_district: dict[str, dict[str, Any]] = defaultdict(lambda: {"classes": {}, "area": 0.0})
    for row in rows:
        name = row["district_name"]
        by_district[name]["area"] = float(row["district_area_km2"])
        by_district[name]["classes"][row["class_value"]] = float(row["area_km2"])

    output = []
    for name in sorted(by_district):
        classes = by_district[name]["classes"]
        high_area = classes.get("4", 0.0) + classes.get("5", 0.0)
        district_area = by_district[name]["area"]
        output.append(
            [
                name,
                format_number(classes.get("1", 0.0), 1),
                format_number(classes.get("2", 0.0), 1),
                format_number(classes.get("3", 0.0), 1),
                format_number(classes.get("4", 0.0), 1),
                format_number(classes.get("5", 0.0), 2),
                format_number(high_area / district_area * 100.0 if district_area else 0.0, 2),
            ]
        )
    return output


def top_high_priority(rows: list[dict[str, str]], limit: int = 5) -> list[tuple[str, float, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"district_area": 0.0, "high": 0.0})
    for row in rows:
        name = row["district_name"]
        grouped[name]["district_area"] = float(row["district_area_km2"])
        if row["class_value"] in {"4", "5"}:
            grouped[name]["high"] += float(row["area_km2"])
    ranked = []
    for name, values in grouped.items():
        share = values["high"] / values["district_area"] * 100.0 if values["district_area"] else 0.0
        ranked.append((name, values["high"], share))
    return sorted(ranked, key=lambda item: item[1], reverse=True)[:limit]


def rows_by_scenario(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["scenario_id"]: row for row in rows}


def scenario_label(row: dict[str, str]) -> str:
    labels = {
        "baseline": "Baseline",
        "earthquake-heavy": "Deprem ağırlıklı",
        "equal-weight": "Eşit ağırlık",
    }
    return labels.get(row["scenario_id"], row.get("scenario_label", row["scenario_id"]))


def sensitivity_table_rows(
    summary_rows: list[dict[str, str]],
    interpretation_rows: list[dict[str, str]],
) -> list[list[str]]:
    interpretation = rows_by_scenario(interpretation_rows)
    output = []
    for row in summary_rows:
        scenario_id = row["scenario_id"]
        output.append(
            [
                scenario_label(row),
                format_number(row["high_plus_area_km2"], 2),
                format_number(row["delta_high_plus_area_km2_vs_baseline"], 2),
                format_number(row["class_agreement_with_baseline_percent"], 2),
                interpretation.get(scenario_id, {}).get("interpretation_level", ""),
            ]
        )
    return output


def raster_stat_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    output = []
    for row in rows:
        output.append(
            [
                row["display_name"],
                "Kriter" if row["role"] == "criterion" else "MCDA",
                row["minimum"],
                row["maximum"],
                row["mean"],
                row["stddev"],
                row["valid_percent"],
            ]
        )
    return output


def validate_assets(project_root: Path, weights: list[dict[str, Any]]) -> None:
    png_paths = [project_root / Path(path) for _, _, path, _ in MAPS]
    for path in png_paths:
        with Image.open(path) as img:
            if img.size != (4960, 3507):
                raise ReportBuildError(f"{path} için beklenmeyen harita PNG boyutu: {img.size}")

    total_weight = sum(row["weight"] for row in weights)
    if not math.isclose(total_weight, 1.0, abs_tol=1e-9):
        raise ReportBuildError(f"MCDA ağırlıkları toplamı 1.00 olmalı, gelen {total_weight}")


def build_cover(doc: Document) -> None:
    for _ in range(5):
        doc.add_paragraph()

    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = kicker.add_run("AKADEMİK RAPOR")
    set_run_font(run, size=11, bold=True, color="2E74B5")
    set_paragraph_spacing(kicker, after=14, line=1.0)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(DOC_TITLE)
    set_run_font(run, size=26, bold=True, color="0B2545")
    set_paragraph_spacing(title, after=8, line=1.1)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(DOC_SUBTITLE)
    set_run_font(run, size=13, color="374151")
    set_paragraph_spacing(subtitle, after=24, line=1.15)

    add_note_box(
        doc,
        "Kapsam notu",
        "Bu rapor, resmi afet risk haritası veya hukuki/operasyonel karar ürünü değildir. "
        "Sonuçlar açık/veri tabanlı proxy katmanlarla üretilmiş ön değerlendirme niteliğindedir.",
    )

    doc.add_paragraph()
    metadata = [
        ["Proje", "Çanakkale çok kriterli afet öncelik alanları analizi"],
        ["Analiz veri seviyesi", "data/processed ve data/reference canonical katmanları"],
        ["CRS ve grid", "EPSG:32635, 100 m analiz grid'i"],
        ["Rapor tarihi", REPORT_DATE],
    ]
    add_table(doc, ["Alan", "Değer"], metadata, [2200, 7400], font_size=9.5)
    add_page_break(doc)


def build_front_matter(
    doc: Document,
    class_rows: list[dict[str, str]],
    sensitivity_rows: list[dict[str, str]],
) -> None:
    doc.add_heading("Öz", level=1)
    add_body_paragraph(
        doc,
        "Bu rapor, Çanakkale ili için çok kriterli karar analizi yaklaşımıyla üretilmiş "
        "göreli afet öncelik alanlarını açıklamaktadır. Çalışma, büyük ham kaynak dosyalarını "
        "DOCX üretim girdisi olarak beklemez; processed-canonical ve reference katmanlarını "
        "analiz veri tabanı olarak kullanır.",
    )
    add_body_paragraph(
        doc,
        "Model 11 normalize kriteri ağırlıklı doğrusal kombinasyonla birleştirir. Sonuçta "
        "geçerli analiz alanı 9810.33 km²'dir. Çok yüksek öncelik sınıfı 6.99 km² ile oldukça "
        "seçici kalırken, düşük ve orta sınıflar toplam geçerli alanın büyük bölümünü oluşturur.",
    )

    add_table_caption(doc, "Tablo 1. MCDA öncelik sınıflarının genel alan dağılımı.")
    add_table(
        doc,
        ["Sınıf", "Etiket", "Piksel", "Alan (km²)", "Pay (%)"],
        class_distribution_rows(class_rows),
        [900, 2100, 1700, 1800, 1500],
        font_size=9,
    )

    doc.add_heading("Yönetici Özeti", level=1)
    add_bullet(doc, "Rapor, 11 kriterli MCDA modelini ve 100 m ortak analiz grid'ini esas alır.")
    add_bullet(doc, "12 haritanın tamamı ana gövdeye alınmıştır; birleşik atlas PDF ek ürün olarak korunur.")
    sensitivity = rows_by_scenario(sensitivity_rows)
    add_bullet(
        doc,
        "Üç senaryolu ağırlık duyarlılığı kontrolünde deprem ağırlıklı senaryonun baseline class "
        f"agreement değeri yüzde {format_number(sensitivity['earthquake-heavy']['class_agreement_with_baseline_percent'], 2)}, "
        "eşit ağırlıklı senaryonun baseline class agreement değeri "
        f"yüzde {format_number(sensitivity['equal-weight']['class_agreement_with_baseline_percent'], 2)} olarak hesaplanmıştır.",
    )
    add_bullet(doc, "Büyük upstream ham veri dosyaları DOCX üretim girdisi değildir; kaynaklar dataset, kurum ve yıl/sürüm düzeyinde raporlanır.")
    add_bullet(doc, "Sonuçlar resmi risk, hasar, tehlike veya acil durum planı olarak yorumlanmamalıdır.")


def build_intro_and_data(doc: Document) -> None:
    doc.add_heading("1. Giriş", level=1)
    add_body_paragraph(
        doc,
        "Afet önceliklendirme çalışmaları, farklı tehlike ve maruziyet boyutlarını birlikte "
        "okuyabilmek için tutarlı veri yönetimi, açık yöntem tanımı ve dikkatli kartografik "
        "sunum gerektirir. Bu raporun amacı, Çanakkale için üretilen çok kriterli mekansal "
        "öncelik analizini veri kaynakları, yöntem, bulgular ve sınırlılıklar açısından "
        "akademik biçimde belgelendirmektir.",
    )
    add_body_paragraph(
        doc,
        "Çalışma, kesin tehlike veya risk modellemesi yerine, seçilmiş açık veri katmanlarını "
        "karşılaştırılabilir 0-1 skor yüzeylerine dönüştüren bir ön tarama yaklaşımıdır. Bu nedenle "
        "çıktılar karar destek niteliğinde keşifsel ürünlerdir; yerel mühendislik, hidrodinamik, "
        "mikrobölgeleme veya saha doğrulama çalışmalarının yerine geçmez.",
    )

    doc.add_heading("2. Çalışma Alanı, CRS ve Grid", level=1)
    add_body_paragraph(
        doc,
        "Tüm mekansal analiz katmanları EPSG:32635 - WGS 84 / UTM Zone 35N koordinat "
        "sisteminde standartlaştırılmıştır. Mesafe, tampon, alan, yoğunluk ve raster overlay "
        "hesaplarının projeksiyonlu bir sistemde yapılması gerektiği için bu CRS çalışma alanına "
        "uygun kabul edilmiştir.",
    )
    add_body_paragraph(
        doc,
        "Ortak analiz grid'i 100 m piksel boyutuna, 1586 x 1423 raster boyutuna ve aynı extent'e "
        "sahiptir. Sürekli skor rasterlarında AOI dışı değer -9999 NoData, sınıf rasterında ise "
        "AOI dışı değer 0 olarak yönetilir.",
    )

    doc.add_heading("3. Veri ve Veri Yönetimi", level=1)
    add_body_paragraph(
        doc,
        "Raporun veri seviyesi `data/processed` ve `data/reference` katmanlarıdır. Microsoft "
        "building footprints, ham OSM paketleri, DEM karoları, landcover karoları, flood rasterleri, "
        "HydroRIVERS paketleri, WorldPop ham rasteri ve VS30 ham extract dosyaları rapor üretim "
        "sürecinde dosya olarak beklenmez.",
    )
    add_body_paragraph(
        doc,
        "Bu yaklaşım, kaynakların yok sayılması anlamına gelmez. Kaynak bilgisi veri seti adı, kurum "
        "ve bilinen yıl/sürüm düzeyinde raporlanır; ancak büyük upstream ham dosyalar DOCX "
        "üretim girdisi olarak sunulmaz.",
    )
    add_body_paragraph(
        doc,
        "Bu çalışma, büyük upstream ham veri paketlerinden tüm veri hazırlama sürecinin birebir "
        "yeniden üretimini değil; data/processed ve data/reference canonical katmanlarından analiz, "
        "QA, tablo ve rapor çıktılarının yeniden üretimini hedefler. Bu nedenle yeniden "
        "üretilebilirlik kapsamı, processed-canonical veri seviyesinden başlayan analiz süreciyle "
        "sınırlıdır.",
    )

    add_table_caption(doc, "Tablo 2. Analizde kullanılan veri kaynakları ve rolleri.")
    add_table(
        doc,
        ["Tema", "Kaynak veri seti / kurum", "Analizdeki rol"],
        [list(row) for row in DATA_SOURCES],
        [1600, 4300, 3700],
        font_size=7.8,
    )


def mcda_formula_text(weights: list[dict[str, Any]]) -> str:
    parts = [f"{row['weight']:.2f} × {row['display_name']}" for row in weights]
    return "MCDA skoru = " + " + ".join(parts) + "."


def build_methodology(doc: Document, weights: list[dict[str, Any]]) -> None:
    doc.add_heading("4. Yöntem", level=1)
    add_body_paragraph(
        doc,
        "Çalışma, çok kriterli karar analizi mantığıyla 11 kriter skor rasterını ağırlıklı doğrusal "
        "kombinasyon üzerinden birleştirir. Her kriter 0-1 aralığında yorumlanır; yüksek değerler "
        "ilgili kriter açısından daha yüksek göreli öncelik veya duyarlılık anlamına gelir.",
    )

    add_table_caption(doc, "Tablo 3. MCDA kriterleri ve ağırlıkları.")
    add_table(
        doc,
        ["No", "Kriter", "Ağırlık"],
        [[str(row["order"]), row["display_name"], f"{row['weight']:.2f}"] for row in weights]
        + [["", "Toplam", "1.00"]],
        [700, 7100, 1800],
        font_size=8.8,
    )

    add_body_paragraph(
        doc,
        "Ağırlıklı overlay formülü config dosyasında tanımlı baseline ağırlıklarıyla aşağıdaki "
        f"şekilde uygulanır: {mcda_formula_text(weights)}",
    )
    add_body_paragraph(
        doc,
        "Baseline ağırlık seti AHP, ikili karşılaştırma matrisi, resmi uzman anketi veya gözlenmiş "
        "afet kaybı kalibrasyonu ile üretilmiş nihai karar ağırlığı değildir. Ağırlıklar; tehlike "
        "ve maruziyet göstergelerine daha yüksek açıklayıcı rol vermek, kavramsal olarak örtüşen "
        "proxy katmanlarda çift sayımı sınırlamak ve destekleyici çevresel/topoğrafik/erişilebilirlik "
        "kriterlerinin modeli domine etmesini önlemek amacıyla keşifsel bir MCDA öncelik indeksi "
        "için kullanılmıştır.",
    )
    add_body_paragraph(
        doc,
        "Ağırlık varsayımının sonuç üzerindeki etkisini görünür kılmak için baseline, deprem "
        "ağırlıklı ve eşit ağırlıklı olmak üzere üç senaryolu sınırlı bir sensitivity/robustness "
        "kontrolü rapora eklenmiştir. Alternatif senaryolar nihai raster üretmez; yalnızca baseline "
        "sonucun ağırlık değişimine ne kadar duyarlı olduğunu tablo düzeyinde test eder.",
    )
    add_body_paragraph(
        doc,
        "Ham MCDA skoru min-max normalizasyonuyla 0-1 aralığına çevrilmiş ve beş öncelik sınıfına "
        "ayrılmıştır: çok düşük, düşük, orta, yüksek ve çok yüksek. Çok yüksek sınıfın düşük alan "
        "payı, modelin en güçlü birleşik skor alanlarını seçici biçimde ayırdığını gösterir.",
    )


def build_results(
    doc: Document,
    class_rows: list[dict[str, str]],
    district_rows: list[dict[str, str]],
    sensitivity_summary_rows_in: list[dict[str, str]],
    sensitivity_interpretation_rows: list[dict[str, str]],
) -> None:
    doc.add_heading("5. Bulgular", level=1)
    add_body_paragraph(
        doc,
        "MCDA sınıf dağılımı, geçerli analiz alanının büyük bölümünün düşük ve orta öncelik "
        "sınıflarında toplandığını göstermektedir. Sınıf 2 toplam geçerli alanın %49.25'ini, "
        "sınıf 3 ise %33.54'ünü oluşturur. Yüksek sınıf %5.49, çok yüksek sınıf ise %0.07 "
        "düzeyindedir.",
    )
    add_body_paragraph(
        doc,
        "Bu dağılım, modelin çok yüksek öncelik alanlarını geniş bir alan olarak değil, birden çok "
        "kriterin aynı anda yüksek skor verdiği seçici mekansal kümeler olarak tanımladığını gösterir.",
    )

    ranked = top_high_priority(district_rows)
    add_table_caption(doc, "Tablo 4. Yüksek + çok yüksek sınıf alanına göre ilk beş ilçe.")
    add_table(
        doc,
        ["Sıra", "İlçe", "Yüksek+çok yüksek alan (km²)", "İlçe alanına oran (%)"],
        [
            [str(i), name, format_number(area, 2), format_number(share, 2)]
            for i, (name, area, share) in enumerate(ranked, 1)
        ],
        [800, 2600, 3300, 2900],
        font_size=8.8,
    )

    doc.add_heading("5.1 Ağırlık Duyarlılığı", level=2)
    add_body_paragraph(
        doc,
        "Ağırlık eleştirisini nicel olarak sınamak için baseline sonuca karşı iki küçük robustness "
        "senaryosu hesaplanmıştır: deprem ilişkili kriterleri öne çıkaran senaryo ve tüm kriterleri "
        "eşit kabul eden senaryo. Bu analiz, kapsamlı AHP veya Monte Carlo yerine, mevcut rapor "
        "kapsamında ağırlık varsayımının sonuç desenini ne ölçüde değiştirdiğini göstermeyi amaçlar.",
    )
    add_table_caption(doc, "Tablo 5. Üç senaryolu ağırlık duyarlılığı özeti.")
    add_table(
        doc,
        ["Senaryo", "Yüksek+çok yüksek alan (km²)", "Baseline farkı (km²)", "Class agreement (%)", "Yorum"],
        sensitivity_table_rows(sensitivity_summary_rows_in, sensitivity_interpretation_rows),
        [1650, 2300, 1800, 1900, 1950],
        font_size=7.6,
    )

    interpretation = rows_by_scenario(sensitivity_interpretation_rows)
    add_body_paragraph(doc, interpretation["earthquake-heavy"]["report_sentence_tr"])
    add_body_paragraph(doc, interpretation["equal-weight"]["report_sentence_tr"])
    add_body_paragraph(
        doc,
        interpretation["earthquake-heavy"]["top_district_comment_tr"]
        + " "
        + interpretation["equal-weight"]["top_district_comment_tr"],
    )

    doc.add_heading("5.2 Nihai Öncelik Haritası", level=2)
    add_figure_page(doc, 1, MAPS[0])


def add_figure_page(doc: Document, figure_no: int, map_record: tuple[int, str, str, str]) -> None:
    _, title, path, note = map_record
    add_caption(doc, f"Şekil {figure_no}. {title}.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Inches(6.45))
    set_picture_alt(p, f"Şekil {figure_no}. {title}", note)
    set_paragraph_spacing(p, after=4, line=1.0)
    small = doc.add_paragraph()
    small.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run_note = small.add_run(note)
    set_run_font(run_note, size=9.2, color="374151")
    set_paragraph_spacing(small, after=4, line=1.15)


def build_maps_section(doc: Document) -> None:
    add_page_break(doc)
    doc.add_heading("6. Kriter Haritaları", level=1)
    add_body_paragraph(
        doc,
        "Bu bölümde nihai MCDA sonucu dışındaki 11 kriter haritası ana gövdede sunulmaktadır. "
        "Haritalar, aynı CRS ve grid standardına sahip normalize skor katmanlarıdır; renk ve sınıf "
        "yorumları kriterin göreli mekansal etkisini okumak için kullanılmalıdır.",
    )

    for figure_no, map_record in enumerate(MAPS[1:], start=2):
        if figure_no > 2:
            add_page_break(doc)
        doc.add_heading(f"6.{figure_no - 1} {map_record[1]}", level=2)
        add_figure_page(doc, figure_no, map_record)


def build_discussion_conclusion(doc: Document) -> None:
    doc.add_heading("7. Tartışma ve Sınırlılıklar", level=1)
    add_body_paragraph(
        doc,
        "Modeldeki kriterlerin bir kısmı doğrudan ölçüm değil proxy göstergedir. Fay yakınlığı deprem "
        "riski, hidrografya yakınlığı taşkın riski, eğim heyelan riski, ağaç örtüsü yangın riski ve "
        "bina footprint yoğunluğu yapısal kırılganlık anlamına gelmez. Bu göstergeler yalnızca çok "
        "kriterli önceliklendirme bağlamında yorumlanmalıdır.",
    )
    add_body_paragraph(
        doc,
        "Heyelan teması için MTA WMS üzerinde mta:YERHEYELAN katmanı belirlenmiştir; ancak WFS "
        "erişimi kapalı olduğu ve indirilebilir/nicel GIS vektör ya da raster veri seti proje veri "
        "tabanında bulunmadığı için MCDA kriteri olarak kullanılmamıştır. WMS, PDF harita veya ekran "
        "görüntüsünden türetilmiş raster yüzeyler nicel ağırlıklı overlay girdisi olarak güvenilir "
        "kabul edilmemiştir. Bu nedenle eğim kriteri heyelan envanteri yerine geçmez; yalnızca "
        "topoğrafik duyarlılık göstergesi olarak yorumlanmalıdır.",
    )
    add_body_paragraph(
        doc,
        "Ağırlıklar model sonucunu doğrudan etkiler; farklı uzman değerlendirmeleri veya farklı "
        "politika hedefleri farklı sonuçlar üretebilir. Ayrıca nüfus verisi dinamik nüfusu, VS30 "
        "verisi yerel jeoteknik etütleri, bina footprint verisi yapı yaşı veya taşıyıcı sistem "
        "bilgisini temsil etmez.",
    )
    add_body_paragraph(
        doc,
        "Bu raporda yapılan sensitivity kontrolü üç senaryolu sınırlı bir robustness testidir. "
        "AHP tutarlılık oranı, uzman paneli, kapsamlı Monte Carlo ağırlık örneklemesi veya resmi "
        "risk kabul kriteri üretmez. Bu nedenle sensitivity çıktıları, baseline sonucun ağırlık "
        "varsayımına duyarlılığını açıklamak için kullanılmalı; nihai kurumsal ağırlık kararı gibi "
        "yorumlanmamalıdır.",
    )
    add_body_paragraph(
        doc,
        "Çıktı gözlenmiş afet kayıpları, tarihsel olay envanteri veya saha doğrulamasıyla kalibre "
        "edilmemiştir. Kaynak yılları ve extract tarihleri, proje metadata'sında kayıtlı "
        "olduğu ölçüde raporlanmıştır; kaydı bulunmayan büyük upstream kaynaklar için yıl/sürüm "
        "belirsizliği açıkça belirtilmiştir.",
    )
    add_note_box(
        doc,
        "Uygun kullanım",
        "Rapor, saha çalışması, yerel uzman değerlendirmesi ve resmi kurum verileriyle desteklenmesi "
        "gereken bir ön tarama ve portfolyo düzeyi karar destek ürünüdür.",
    )

    doc.add_heading("8. Sonuç", level=1)
    add_body_paragraph(
        doc,
        "Çanakkale için üretilen processed-canonical MCDA modeli, 11 kriterli dengeli bir yapı ile "
        "göreli mekansal öncelik alanlarını tanımlamaktadır. Rapor, nihai öncelik haritası, 11 kriter "
        "haritası, sınıf dağılımı ve ilçe bazlı alan tablolarını birlikte sunarak yöntemin hem "
        "kartografik hem de sayısal izlenebilirliğini güçlendirir.",
    )
    add_body_paragraph(
        doc,
        "İleri analizlerde yerel zemin/mikrobölgeleme verileri, bina yaşı ve yapı türü verileri, "
        "dinamik nüfus katmanları, resmi taşkın model çıktıları, resmi heyelan envanteri ve uzman "
        "temelli ağırlık duyarlılık analizleri modele ek doğrulama sağlayabilir.",
    )


def build_sources_appendices(
    doc: Document,
    district_rows: list[dict[str, str]],
    raster_rows: list[dict[str, str]],
) -> None:
    doc.add_heading("Kaynak Veri Setleri", level=1)
    add_body_paragraph(
        doc,
        "Kaynakça bu raporda dataset/kaynak kurum/yıl veya sürüm düzeyinde tutulmuştur. Büyük ham "
        "dosya varlığı iddia edilmez; kaynaklar processed ve reference katmanların "
        "seceresi olarak açıklanır.",
    )
    for theme, source, role in DATA_SOURCES:
        add_bullet(doc, f"{theme}: {source}. Rol: {role}.")

    add_page_break(doc)
    doc.add_heading("Ek A. İlçe Bazlı MCDA Sınıf Alanları", level=1)
    add_body_paragraph(
        doc,
        "Aşağıdaki tablo, 100 m raster hücre alanı üzerinden hesaplanan ilçe bazlı sınıf alanlarını "
        "özetler. Değerler resmi kadastro veya idari istatistik değildir; raster sınıf alanı "
        "özetidir.",
    )
    add_table_caption(doc, "Tablo A1. İlçelere göre MCDA sınıf alanları.")
    add_table(
        doc,
        ["İlçe", "S1 km²", "S2 km²", "S3 km²", "S4 km²", "S5 km²", "S4+S5 %"],
        district_summary_rows(district_rows),
        [2100, 1200, 1200, 1200, 1200, 1200, 1500],
        font_size=7.4,
    )

    doc.add_heading("Ek B. Raster İstatistikleri", level=1)
    add_body_paragraph(
        doc,
        "Kriter raster istatistikleri, ortak grid doğrulaması sonrası üretilen rapor tablosundan "
        "alınmıştır. Tüm istatistikler canonical raster katmanlarına aittir.",
    )
    add_table_caption(doc, "Tablo B1. Kriter ve MCDA raster istatistikleri.")
    add_table(
        doc,
        ["Katman", "Rol", "Min", "Maks", "Ortalama", "Std.", "Geçerli %"],
        raster_stat_rows(raster_rows),
        [3300, 1000, 850, 850, 1150, 1000, 1450],
        font_size=7.0,
    )


def audit_tables(doc: Document) -> None:
    for table in doc.tables:
        tbl_pr = table._tbl.tblPr
        tbl_w = tbl_pr.find(qn("w:tblW"))
        if tbl_w is None or tbl_w.get(qn("w:type")) != "dxa":
            raise ReportBuildError("Bir tabloda sabit DXA genişliği eksik.")
        grid_widths = [int(col.get(qn("w:w"))) for col in table._tbl.tblGrid.gridCol_lst]
        for row in table.rows:
            for idx, cell in enumerate(row.cells):
                tc_w = cell._tc.tcPr.tcW
                if tc_w is None or int(tc_w.get(qn("w:w"))) != grid_widths[idx]:
                    raise ReportBuildError("Bir tablo hücresi genişliği tblGrid ile eşleşmiyor.")


def build_report(project_root: Path, output_dir: Path) -> Path:
    project_root = project_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    require_inputs(project_root)
    weights = load_mcda_weights(project_root)
    validate_assets(project_root, weights)

    class_rows = read_csv(project_root / PROJECT_ASSETS["class_distribution"])
    district_rows = read_csv(project_root / PROJECT_ASSETS["district_classes"])
    raster_rows = read_csv(project_root / PROJECT_ASSETS["raster_stats"])
    sensitivity_summary_rows_in = read_csv(project_root / PROJECT_ASSETS["sensitivity_summary"])
    sensitivity_interpretation_rows = read_csv(project_root / PROJECT_ASSETS["sensitivity_interpretation"])

    if (
        len(class_rows) != 5
        or len(district_rows) != 60
        or len(raster_rows) != 14
        or len(sensitivity_summary_rows_in) != 3
        or len(sensitivity_interpretation_rows) != 3
    ):
        raise ReportBuildError("Rapor tablo satır sayıları tanımlı varlık sözleşmesiyle eşleşmiyor.")

    old_cwd = Path.cwd()
    try:
        # Harita kayıtlarındaki görsel yolları proje köküne göre relativedir.
        import os

        os.chdir(project_root)
        doc = configure_document()
        build_cover(doc)
        build_front_matter(doc, class_rows, sensitivity_summary_rows_in)
        build_intro_and_data(doc)
        build_methodology(doc, weights)
        build_results(doc, class_rows, district_rows, sensitivity_summary_rows_in, sensitivity_interpretation_rows)
        build_maps_section(doc)
        build_discussion_conclusion(doc)
        build_sources_appendices(doc, district_rows, raster_rows)
        audit_tables(doc)

        output_path = output_dir / OUTPUT_DOCX_NAME
        doc.save(output_path)
    finally:
        import os

        os.chdir(old_cwd)

    return output_path


def main() -> int:
    args = parse_args()
    try:
        output = build_report(args.project_root, args.output_dir)
    except ReportBuildError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1

    print("Akademik rapor DOCX üretildi:")
    print(f"- {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
