#!/usr/bin/env python3
"""Build the IEEE two-column conference paper as a .docx.

Layout follows the IEEE conference template: A4, title and author block across
the full width, body in two columns, 10 pt Times New Roman justified with a
0.2 inch first-line indent, small-caps section headings, 8 pt figure and table
captions, 8 pt references.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor

import paper_content as C

ROOT = Path(__file__).resolve().parents[2]
FIGDIR = ROOT / "report" / "paper" / "figures"
OUT = ROOT / "report" / "paper" / "HydroRainGuard_IEEE_Conference_Paper.docx"

MM = 1 / 25.4
PAGE_W, PAGE_H = 210, 297
M_TOP, M_BOTTOM, M_LEFT, M_RIGHT = 19.0, 43.0, 14.32, 14.32
COL_GAP = 4.2
COL_W_MM = (PAGE_W - M_LEFT - M_RIGHT - COL_GAP) / 2
COL_W_IN = COL_W_MM * MM

BODY_FONT = "Times New Roman"


# --------------------------------------------------------------------------- #
# low-level helpers
# --------------------------------------------------------------------------- #
def set_run(run, size=10, bold=False, italic=False, small_caps=False, font=BODY_FONT,
            color=None):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.small_caps = small_caps
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font)


def para(doc, text="", size=10, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         first_indent=0.2, space_before=0, space_after=0, small_caps=False,
         line=1.0, left_indent=0.0, hanging=0.0, keep_next=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.first_line_indent = Inches(first_indent)
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    pf.left_indent = Inches(left_indent)
    if hanging:
        pf.first_line_indent = Inches(-hanging)
        pf.left_indent = Inches(left_indent or hanging)
    pf.keep_with_next = keep_next
    pf.widow_control = True
    if text:
        run = p.add_run(text)
        set_run(run, size, bold, italic, small_caps)
    return p


TOKEN = re.compile(r"(\*[^*]+\*|~[^~]+~|\^[^^]+\^)")


def rich(p, text, size=10, bold=False, italic=False, font=BODY_FONT):
    """Add text with light markup: *italic*, ~subscript~, ^superscript^."""
    for chunk in TOKEN.split(text):
        if not chunk:
            continue
        if chunk.startswith("*") and chunk.endswith("*") and len(chunk) > 2:
            run = p.add_run(chunk[1:-1])
            set_run(run, size, bold, not italic, font=font)
        elif chunk.startswith("~") and chunk.endswith("~") and len(chunk) > 2:
            run = p.add_run(chunk[1:-1])
            set_run(run, size, bold, italic, font=font)
            run.font.subscript = True
        elif chunk.startswith("^") and chunk.endswith("^") and len(chunk) > 2:
            run = p.add_run(chunk[1:-1])
            set_run(run, size, bold, italic, font=font)
            run.font.superscript = True
        else:
            run = p.add_run(chunk)
            set_run(run, size, bold, italic, font=font)


def set_columns(section, num):
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(num))
    cols.set(qn("w:space"), str(int(COL_GAP / 25.4 * 1440)))
    cols.set(qn("w:equalWidth"), "1")


def setup_page(section):
    section.page_width = Mm(PAGE_W)
    section.page_height = Mm(PAGE_H)
    section.top_margin = Mm(M_TOP)
    section.bottom_margin = Mm(M_BOTTOM)
    section.left_margin = Mm(M_LEFT)
    section.right_margin = Mm(M_RIGHT)
    section.header_distance = Mm(10)
    section.footer_distance = Mm(10)


def table_borders_ieee(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 12), ("bottom", 12)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    for edge in ("left", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    tblPr.append(borders)


def cell_bottom_rule(cell, sz=6):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    el = OxmlElement("w:bottom")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")
    borders.append(el)
    tcPr.append(borders)


def set_cell_margins(table, top=20, bottom=20, left=40, right=40):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def no_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trPr.append(el)


# --------------------------------------------------------------------------- #
# equations
# --------------------------------------------------------------------------- #
def add_equation(doc, text, number):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Inches(0)
    pf.space_before = Pt(5)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.0
    pf.tab_stops.add_tab_stop(Inches(COL_W_IN / 2), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Inches(COL_W_IN - 0.02), WD_TAB_ALIGNMENT.RIGHT)

    set_run(p.add_run("\t"), 10)
    rich(p, text.replace(" x ", " \u00d7 "), 10)
    set_run(p.add_run("\t" + number), 10)
    return p


# --------------------------------------------------------------------------- #
# block renderers
# --------------------------------------------------------------------------- #
def add_figure(doc, filename, caption, width_in):
    path = FIGDIR / filename
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Inches(0)
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(path), width=Inches(min(width_in, COL_W_IN - 0.02)))

    cap = doc.add_paragraph()
    pf = cap.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Inches(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.0
    set_run(cap.add_run(caption), 8)


def add_table(doc, label, title, header, rows, widths, footnote):
    # caption: "TABLE I" then title, both 8 pt centred, small caps
    cap = doc.add_paragraph()
    pf = cap.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Inches(0)
    pf.space_before = Pt(8)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    set_run(cap.add_run(label), 8, small_caps=True)

    cap2 = doc.add_paragraph()
    pf = cap2.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Inches(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    set_run(cap2.add_run(title), 8, small_caps=True)

    n_cols = len(header)
    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    table_borders_ieee(table)
    set_cell_margins(table)

    scale = min(1.0, (COL_W_IN - 0.04) / sum(widths))
    widths = [w * scale for w in widths]

    for j, text in enumerate(header):
        cell = table.cell(0, j)
        cell.width = Inches(widths[j])
        cp = cell.paragraphs[0]
        cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(0)
        cp.paragraph_format.space_after = Pt(0)
        cp.paragraph_format.first_line_indent = Inches(0)
        cp.paragraph_format.line_spacing = 1.0
        set_run(cp.add_run(text), 8)
        cell_bottom_rule(cell)

    for i, row in enumerate(rows, start=1):
        for j, text in enumerate(row):
            cell = table.cell(i, j)
            cell.width = Inches(widths[j])
            cp = cell.paragraphs[0]
            cp.paragraph_format.alignment = (WD_ALIGN_PARAGRAPH.CENTER if j else
                                             WD_ALIGN_PARAGRAPH.LEFT)
            cp.paragraph_format.space_before = Pt(0)
            cp.paragraph_format.space_after = Pt(0)
            cp.paragraph_format.first_line_indent = Inches(0)
            cp.paragraph_format.line_spacing = 1.0
            set_run(cp.add_run(text), 8)
        no_split(table.rows[i])

    if footnote:
        f = doc.add_paragraph()
        pf = f.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = Inches(0)
        pf.space_before = Pt(3)
        pf.space_after = Pt(9)
        pf.line_spacing = 1.0
        set_run(f.add_run(footnote), 7.5)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def build():
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), BODY_FONT)

    setup_page(doc.sections[0])
    set_columns(doc.sections[0], 1)

    # ---- title block (spans both columns) ----
    t = doc.add_paragraph()
    tp = t.paragraph_format
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tp.space_before = Pt(0)
    tp.space_after = Pt(12)
    tp.line_spacing = 0.95
    tp.first_line_indent = Inches(0)
    set_run(t.add_run(C.TITLE), 24)

    grid = doc.add_table(rows=2, cols=6)
    grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    grid.autofit = False
    tblPr = grid._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    set_cell_margins(grid, top=0, bottom=0, left=60, right=60)
    span_w = (PAGE_W - M_LEFT - M_RIGHT) * MM / 6
    for row in grid.rows:
        no_split(row)
        for cell in row.cells:
            cell.width = Inches(span_w)

    row1 = [grid.cell(0, 0).merge(grid.cell(0, 1)),
            grid.cell(0, 2).merge(grid.cell(0, 3)),
            grid.cell(0, 4).merge(grid.cell(0, 5))]
    row2 = [grid.cell(1, 0).merge(grid.cell(1, 2)),
            grid.cell(1, 3).merge(grid.cell(1, 5))]

    def fill_author(cell, info):
        name, dept, org, city, mail = info
        cp = cell.paragraphs[0]
        cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_after = Pt(0)
        cp.paragraph_format.first_line_indent = Inches(0)
        cp.paragraph_format.line_spacing = 1.0
        set_run(cp.add_run(name), 11)
        for line, size, ital in ((dept, 10, False), (org, 10, False), (city, 10, False)):
            q = cell.add_paragraph()
            q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            q.paragraph_format.space_after = Pt(0)
            q.paragraph_format.first_line_indent = Inches(0)
            q.paragraph_format.line_spacing = 1.0
            set_run(q.add_run(line), size, italic=ital)
        q = cell.add_paragraph()
        q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.space_after = Pt(6)
        q.paragraph_format.first_line_indent = Inches(0)
        q.paragraph_format.line_spacing = 1.0
        set_run(q.add_run(mail), 9, italic=True)

    for cell, info in zip(row1, C.AUTHORS[0]):
        fill_author(cell, info)
    for cell, info in zip(row2, C.AUTHORS[1]):
        fill_author(cell, info)

    # ---- two-column body ----
    body = doc.add_section(WD_SECTION.CONTINUOUS)
    setup_page(body)
    set_columns(body, 2)

    # abstract
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Inches(0.2)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    set_run(p.add_run("Abstract\u2014"), 9, bold=True, italic=True)
    set_run(p.add_run(C.ABSTRACT), 9, bold=True)

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Inches(0.2)
    pf.space_after = Pt(10)
    pf.line_spacing = 1.0
    set_run(p.add_run("Index Terms\u2014"), 9, bold=True, italic=True)
    set_run(p.add_run(C.KEYWORDS.replace("index terms - ", "")), 9, bold=True, italic=True)

    first_h1 = True
    for block in C.BLOCKS:
        kind = block[0]

        if kind == "h1":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Inches(0)
            pf.space_before = Pt(0 if first_h1 else 10)
            pf.space_after = Pt(4)
            pf.line_spacing = 1.0
            pf.keep_with_next = True
            set_run(p.add_run(block[1]), 10, small_caps=True)
            first_h1 = False

        elif kind == "h2":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.first_line_indent = Inches(0)
            pf.space_before = Pt(7)
            pf.space_after = Pt(2)
            pf.line_spacing = 1.0
            pf.keep_with_next = True
            set_run(p.add_run(block[1]), 10, italic=True)

        elif kind == "h3":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf.first_line_indent = Inches(0.2)
            pf.space_before = Pt(4)
            pf.space_after = Pt(0)
            set_run(p.add_run(block[1]), 10, italic=True)
            if len(block) > 2 and block[2]:
                rich(p, " " + block[2], 10)

        elif kind == "p":
            p = para(doc, "", space_after=0)
            rich(p, block[1], 10)

        elif kind == "bullets":
            for i, item in enumerate(block[1]):
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                pf.left_indent = Inches(0.32)
                pf.first_line_indent = Inches(-0.17)
                pf.space_before = Pt(0)
                pf.space_after = Pt(2 if i < len(block[1]) - 1 else 6)
                pf.line_spacing = 1.0
                set_run(p.add_run("\u2022\t"), 10)
                rich(p, item, 10)

        elif kind == "eq":
            add_equation(doc, block[1], block[2])

        elif kind == "fig":
            add_figure(doc, block[1], block[2], block[3])

        elif kind == "tbl":
            add_table(doc, block[1], block[2], block[3], block[4], block[5], block[6])

        elif kind == "refs":
            for i, ref in enumerate(block[1], start=1):
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                pf.left_indent = Inches(0.25)
                pf.first_line_indent = Inches(-0.25)
                pf.space_before = Pt(0)
                pf.space_after = Pt(2)
                pf.line_spacing = 1.0
                set_run(p.add_run(f"[{i}]\t"), 8)
                set_run(p.add_run(ref), 8)

    doc.save(str(OUT))
    return OUT


def check():
    """Report anything that would overflow an IEEE column."""
    doc = Document(str(OUT))
    width = Inches(COL_W_IN)
    problems = []
    for i, shape in enumerate(doc.inline_shapes):
        if shape.width > width + Inches(0.02):
            problems.append(f"image {i} is {shape.width.inches:.2f} in wide")
    for t in doc.tables:
        pass
    paras = len(doc.paragraphs)
    words = sum(len(p.text.split()) for p in doc.paragraphs)
    figs = len(doc.inline_shapes)
    print(f"sections={len(doc.sections)} column_width={COL_W_IN:.2f} in")
    print(f"paragraphs={paras} words={words} figures={figs} tables={len(doc.tables)}")
    print("overflow:", problems or "none")
    return OUT


if __name__ == "__main__":
    path = build()
    print("wrote", path.relative_to(ROOT), f"({path.stat().st_size / 1024:.0f} kB)")
    check()
