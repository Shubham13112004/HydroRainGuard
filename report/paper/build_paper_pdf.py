#!/usr/bin/env python3
"""Render the same paper content as a print-ready two-column PDF.

Used both as a submission artefact (IEEE PDF eXpress accepts A4 PDFs) and as a
visual check on the .docx layout: identical text, figures, tables and captions.
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak, Image,
                                KeepTogether, NextPageTemplate, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

import paper_content as C

ROOT = Path(__file__).resolve().parents[2]
FIGDIR = ROOT / "report" / "paper" / "figures"
OUT = ROOT / "report" / "paper" / "HydroRainGuard_IEEE_Conference_Paper.pdf"
FIG_SCALE = 1.0          # tuned by best_layout() so columns do not end in holes

PW, PH = A4
M_TOP, M_BOTTOM = 19 * mm, 43 * mm
M_LEFT, M_RIGHT = 14.32 * mm, 14.32 * mm
GAP = 4.2 * mm
COL_W = (PW - M_LEFT - M_RIGHT - GAP) / 2
BODY_H = PH - M_TOP - M_BOTTOM

# Times is a base-14 font; register metric-compatible aliases so bold/italic work.
BASE = "Times-Roman"
BOLD = "Times-Bold"
ITAL = "Times-Italic"
BI = "Times-BoldItalic"

S = {
    "title": ParagraphStyle("title", fontName=BASE, fontSize=21, leading=24, alignment=TA_CENTER,
                            spaceAfter=10),
    "author": ParagraphStyle("author", fontName=BASE, fontSize=10, leading=11.6,
                             alignment=TA_CENTER, spaceAfter=0),
    "authorname": ParagraphStyle("authorname", fontName=BASE, fontSize=10.5, leading=12.4,
                                 alignment=TA_CENTER),
    "abstract": ParagraphStyle("abstract", fontName=BOLD, fontSize=9, leading=10.4,
                               alignment=TA_JUSTIFY, firstLineIndent=4.5, spaceAfter=5,
                               allowWidows=1),
    "keywords": ParagraphStyle("keywords", fontName=BOLD, fontSize=9, leading=10.4,
                               alignment=TA_JUSTIFY, firstLineIndent=4.5, spaceAfter=9),
    "h1": ParagraphStyle("h1", fontName=BASE, fontSize=9.6, leading=11.5, alignment=TA_CENTER,
                         spaceBefore=8, spaceAfter=3.5, textTransform="uppercase",
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=ITAL, fontSize=10, leading=12, alignment=TA_LEFT,
                         spaceBefore=5, spaceAfter=1.5, keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BASE, fontSize=9.6, leading=11.2, alignment=TA_JUSTIFY,
                           firstLineIndent=4.8, spaceBefore=0, spaceAfter=0),
    "bullet": ParagraphStyle("bullet", fontName=BASE, fontSize=9.6, leading=11.2,
                             alignment=TA_JUSTIFY, leftIndent=11, bulletIndent=1, spaceAfter=2),
    "eq": ParagraphStyle("eq", fontName=BASE, fontSize=9.6, leading=13, alignment=TA_CENTER),
    "caption": ParagraphStyle("caption", fontName=BASE, fontSize=7.6, leading=9.0,
                              alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
    "tablecap": ParagraphStyle("tablecap", fontName=BASE, fontSize=7.6, leading=9.0,
                               alignment=TA_CENTER),
    "cell": ParagraphStyle("cell", fontName=BASE, fontSize=7.4, leading=8.6),
    "cellc": ParagraphStyle("cellc", fontName=BASE, fontSize=7.4, leading=8.6, alignment=TA_CENTER),
    "cellh": ParagraphStyle("cellh", fontName=BASE, fontSize=7.4, leading=8.6, alignment=TA_CENTER),
    "ref": ParagraphStyle("ref", fontName=BASE, fontSize=7.6, leading=9.2, alignment=TA_JUSTIFY,
                          leftIndent=12, firstLineIndent=-12, spaceAfter=2),
    "note": ParagraphStyle("note", fontName=BASE, fontSize=7.0, leading=8.4, alignment=TA_JUSTIFY,
                           spaceAfter=7),
}


def markup(text: str) -> str:
    """Convert *italic*, ~sub~, ^sup^ into reportlab intra-paragraph markup."""
    text = escape(text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"~(.+?)~", r"<sub>\1</sub>", text)
    text = re.sub(r"\^(.+?)\^", r"<super>\1</super>", text)
    return text.replace(" x ", " \u00d7 ")


def figure(filename, caption, width_in):
    from PIL import Image as PILImage
    path = FIGDIR / filename
    w_px, h_px = PILImage.open(path).size
    width = min(width_in * 72 * FIG_SCALE, COL_W - 1)
    height = width * h_px / w_px
    img = Image(str(path), width=width, height=height)
    img.hAlign = "CENTER"
    img.keepWithNext = 1
    return [Spacer(1, 5), img, Paragraph(caption, S["caption"])]


def table(label, title, header, rows, widths, footnote, span=False):
    base_w = (PW - M_LEFT - M_RIGHT - 4) if span else (COL_W - 2)
    scale = base_w / (sum(widths) * 72)
    col_w = [w * 72 * scale for w in widths]
    data = [[Paragraph(h, S["cellh"]) for h in header]]
    for row in rows:
        data.append([Paragraph(c, S["cellc"] if j else S["cell"]) for j, c in enumerate(row)])
    t = Table(data, colWidths=col_w, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
    ]))
    flow = [Spacer(1, 7), Paragraph(label, S["tablecap"]), Paragraph(title, S["tablecap"]),
            Spacer(1, 2.5), t]
    if footnote:
        flow.append(Spacer(1, 2))
        flow.append(Paragraph(footnote, S["note"]))
    return flow


def build(out_path: Path = OUT):
    doc_title = Paragraph(markup(C.TITLE), S["title"])

    def author_cell(info):
        name, dept, org, city, mail = info
        return [Paragraph(name, S["authorname"]),
                Paragraph(dept, S["author"]), Paragraph(org, S["author"]),
                Paragraph(city, S["author"]), Paragraph(mail, S["author"])]

    full_w = PW - M_LEFT - M_RIGHT
    six = full_w / 6
    cells = [author_cell(a) for a in C.AUTHORS[0]] + [author_cell(a) for a in C.AUTHORS[1]]
    grid = Table([[cells[0], "", cells[1], "", cells[2], ""],
                  [cells[3], "", "", cells[4], "", ""]],
                 colWidths=[six] * 6, hAlign="CENTER")
    grid.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)), ("SPAN", (2, 0), (3, 0)), ("SPAN", (4, 0), (5, 0)),
        ("SPAN", (0, 1), (2, 1)), ("SPAN", (3, 1), (5, 1)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    # measure the banner so the frames below it are sized exactly
    _, h_title = doc_title.wrap(full_w, 400)
    _, h_grid = grid.wrap(full_w, 400)
    banner_h = h_title + h_grid + 10

    doc = BaseDocTemplate(str(out_path), pagesize=A4, leftMargin=M_LEFT, rightMargin=M_RIGHT,
                          topMargin=M_TOP, bottomMargin=M_BOTTOM,
                          title=C.TITLE, author=", ".join(a[0] for row in C.AUTHORS for a in row),
                          subject="IEEE conference paper")

    col_h = PH - M_TOP - banner_h - M_BOTTOM
    first = PageTemplate(id="first", frames=[
        Frame(M_LEFT, PH - M_TOP - banner_h, full_w, banner_h, id="banner",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(M_LEFT, M_BOTTOM, COL_W, col_h, id="c1",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(M_LEFT + COL_W + GAP, M_BOTTOM, COL_W, col_h, id="c2",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ])
    later = PageTemplate(id="later", frames=[
        Frame(M_LEFT, M_BOTTOM, COL_W, BODY_H, id="l1", leftPadding=0, rightPadding=0,
              topPadding=0, bottomPadding=0),
        Frame(M_LEFT + COL_W + GAP, M_BOTTOM, COL_W, BODY_H, id="l2", leftPadding=0, rightPadding=0,
              topPadding=0, bottomPadding=0),
    ])
    doc.addPageTemplates([first, later])

    story = [doc_title, grid, NextPageTemplate("later"), FrameBreak()]

    story.append(Paragraph("<i><b>Abstract</b></i><b>\u2014" + escape(C.ABSTRACT) + "</b>",
                           S["abstract"]))
    kw = C.KEYWORDS.replace("index terms - ", "")
    story.append(Paragraph("<i><b>Index Terms</b></i><b>\u2014" + escape(kw) + "</b>", S["keywords"]))

    for block in C.BLOCKS:
        kind = block[0]
        if kind == "h1":
            story.append(Paragraph(escape(block[1]), S["h1"]))
        elif kind == "h2":
            story.append(Paragraph(escape(block[1]), S["h2"]))
        elif kind == "p":
            story.append(Paragraph(markup(block[1]), S["body"]))
        elif kind == "bullets":
            for item in block[1]:
                story.append(Paragraph(markup(item), S["bullet"], bulletText="\u2022"))
            story.append(Spacer(1, 4))
        elif kind == "eq":
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"{markup(block[1])}\u2003\u2003({block[2].strip('()')})",
                                   S["eq"]))
            story.append(Spacer(1, 3))
        elif kind == "fig":
            story.extend(figure(block[1], escape(block[2]), block[3]))
        elif kind == "tbl":
            story.extend(table(block[1], block[2], block[3], block[4], block[5], block[6]))
        elif kind == "refs":
            for i, ref in enumerate(block[1], start=1):
                story.append(Paragraph(f"[{i}]\u2002{escape(ref)}", S["ref"]))

    doc.build(story)
    return out_path


def preview(pdf_path, pages=None):
    """Rasterise pages so the layout can be inspected."""
    import pypdfium2 as pdfium
    out_dir = ROOT / "report" / "paper" / "preview"
    out_dir.mkdir(exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    idxs = pages if pages is not None else range(len(pdf))
    files = []
    for i in idxs:
        page = pdf[i]
        img = page.render(scale=1.6).to_pil()
        p = out_dir / f"page{i + 1}.png"
        img.save(p)
        files.append(p)
    print(f"pages={len(pdf)}")
    return files


def column_holes(pdf_path):
    """Total vertical white space left at the bottom of every column."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    holes, pages = 0.0, len(pdf)
    for pi in range(pages - 1):                     # the last page is meant to be short
        page = pdf[pi]
        w, h = page.get_size()
        tp = page.get_textpage()
        rects = [tp.get_rect(i) for i in range(tp.count_rects())]
        left = [b for l, b, r, t in rects if r < w / 2]
        right = [b for l, b, r, t in rects if l >= w / 2]
        floor = M_BOTTOM + 2
        for col in (left, right):
            if col:
                holes += max(0.0, min(col) - floor)
    return holes, pages


def best_layout(scales=(1.10, 1.04, 0.98, 0.92, 0.86)):
    """Rebuild the PDF at several figure scales and keep the tightest layout."""
    global FIG_SCALE
    best = None
    tmp = OUT.with_suffix(".tmp.pdf")
    for sc in scales:
        FIG_SCALE = sc
        build(tmp)
        holes, pages = column_holes(tmp)
        # a page saved is worth more than any amount of white space
        score = pages * 1000 + holes
        print(f"  scale {sc:.2f}: pages={pages} holes={holes:.0f}pt score={score:.0f}")
        if best is None or score < best[0]:
            best = (score, sc, holes, pages)
    FIG_SCALE = best[1]
    build(OUT)
    tmp.unlink(missing_ok=True)
    return best


if __name__ == "__main__":
    score, sc, holes, pages = best_layout()
    print(f"chosen scale {sc:.2f}: {pages} pages, {holes:.0f} pt of column white space")
    print("wrote", OUT.name, f"{OUT.stat().st_size / 1024:.0f} kB")
    preview(OUT)
