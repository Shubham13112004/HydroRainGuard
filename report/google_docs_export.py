#!/usr/bin/env python3
"""Export the Stage-II report to a Google-Docs-friendly linear text stream.

The script writes:
  report/google_docs_text.txt       - full text with figure placeholders
  report/google_docs_batches.json   - style / image requests for batchUpdate
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

import report_content as C
from build_report import build_reference_map, build_index_records, replace_refs

ROOT = Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "report" / "figures"
OUT_TEXT = ROOT / "report" / "google_docs_text.txt"
OUT_BATCHES = ROOT / "report" / "google_docs_batches.json"

PAGES = C.PAGES
REF_MAP, REF_ORDER = build_reference_map(PAGES)
FIG_RECORDS, TAB_RECORDS = build_index_records(PAGES)

RAW_BASE = "https://github.com/Shubham13112004/HydroRainGuard/raw/refs/heads/arena/52b0ccd0-hydrorainguard/report/figures/"

PLACEHOLDER = "\ufffc"  # object replacement character; one index in Docs


class Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.idx = 1  # Google Docs body starts at index 1
        self.paragraphs: list[dict] = []
        self.images: list[dict] = []

    def add(self, text: str, *, style: str = "NORMAL_TEXT",
            align: str | None = None, font_size: float | None = None,
            font: str | None = None, bold: bool | None = None,
            center: bool = False, page_break: bool = False,
            indent_first: float | None = None,
            indent_start: float | None = None,
            space_below: float | None = None,
            line_spacing: float | None = None,
            no_indent: bool = False) -> None:
        """Add one paragraph (with trailing newline) and record its range."""
        s = replace_refs(text, REF_MAP) + "\n"
        start = self.idx
        end = start + len(s)
        self.parts.append(s)
        self.idx = end
        self.paragraphs.append({
            "start": start,
            "end": end,
            "text": text,
            "style": style,
            "align": align or ("CENTER" if center else ("START" if no_indent else None)),
            "font_size": font_size,
            "font": font,
            "bold": bold,
            "page_break": page_break,
            "indent_first": indent_first,
            "indent_start": indent_start,
            "space_below": space_below,
            "line_spacing": line_spacing,
            "no_indent": no_indent,
        })

    def add_image(self, path: str, caption: str, legend: str, number: str,
                  *, page_break: bool = False) -> None:
        # Placeholder occupies one character; image replaces it later.
        s = PLACEHOLDER + "\n"
        start = self.idx
        end = start + len(s)
        self.parts.append(s)
        self.idx = end
        self.paragraphs.append({
            "start": start,
            "end": end,
            "text": PLACEHOLDER,
            "style": "NORMAL_TEXT",
            "align": "CENTER",
            "no_indent": True,
            "page_break": page_break,
            "space_below": 2,
            "line_spacing": 100,
        })
        p = FIGDIR / path
        with Image.open(p) as im:
            w, h = im.size
        aspect = w / h
        if aspect >= 1.0:
            width_pt = 420.0
            height_pt = 420.0 / aspect
        else:
            height_pt = 340.0
            width_pt = 340.0 * aspect
        self.images.append({
            "index": start,
            "uri": RAW_BASE + path,
            "width": round(width_pt, 2),
            "height": round(height_pt, 2),
            "number": number,
            "caption": caption,
            "legend": legend,
        })

    def blank(self, count: int = 1) -> None:
        for _ in range(count):
            self.add("", style="NORMAL_TEXT", no_indent=True, space_below=0,
                     line_spacing=100)


def build_cover(b: Builder) -> None:
    b.blank(4)
    b.add("A PROJECT REPORT ON", style="HEADING_3", center=True, page_break=False,
          font_size=12, bold=True, no_indent=True, space_below=6)
    b.blank(2)
    for line in [
        "HYDRO RAIN GUARD:",
        "INTELLIGENT RAINWATER HARVESTING AND",
        "ARTIFICIAL GROUNDWATER RECHARGE",
        "ASSESSMENT SYSTEM",
    ]:
        b.add(line, style="TITLE", center=True, font_size=16, bold=True,
              no_indent=True, space_below=8)
    b.blank(2)
    for line in [
        "SUBMITTED TO THE SAVITRIBAI PHULE PUNE UNIVERSITY, PUNE",
        "IN THE PARTIAL FULFILLMENT OF THE REQUIREMENTS",
        "FOR THE AWARD OF THE DEGREE",
        "OF",
        "BACHELOR OF TECHNOLOGY",
        "(INFORMATION TECHNOLOGY)",
        "SUBMITTED BY",
    ]:
        b.add(line, style="HEADING_3", center=True, font_size=12, bold=True,
              no_indent=True, space_below=6)
    b.blank(1)
    for s in C.STUDENTS:
        b.add(f"{s.upper()}     ROLL NO: __________     EXAM NO: __________",
              style="HEADING_3", center=True, font_size=11, bold=True,
              no_indent=True, space_below=4)
    b.blank(1)
    b.add("DEPARTMENT OF INFORMATION TECHNOLOGY", style="TITLE", center=True,
          font_size=16, bold=True, no_indent=True, space_below=8)
    b.blank(1)
    for line in [
        "JSPM'S RAJARSHI SHAHU COLLEGE OF ENGINEERING",
        "TATHAWADE, PUNE 411033",
        "(AN AUTONOMOUS INSTITUTE AFFILIATED TO SAVITRIBAI PHULE PUNE UNIVERSITY, PUNE)",
        "2026-2027",
    ]:
        b.add(line, style="HEADING_3", center=True,
              font_size=10 if line.startswith("(AN") else 12,
              bold=True, no_indent=True, space_below=6)


def build_certificate(b: Builder) -> None:
    b.add("CERTIFICATE", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    b.blank(2)
    b.add("This is to certify that the project report entitled", no_indent=True,
          align="START", space_below=4)
    b.add("\u201C" + C.TITLE + "\u201D", style="HEADING_3", center=True,
          font_size=12, bold=True, no_indent=True, space_below=6)
    b.blank(1)
    b.add("Submitted by", center=True, no_indent=True, space_below=6)
    b.blank(1)
    for s in C.STUDENTS:
        b.add(f"{s.upper()}     ROLL NO: __________     EXAM NO: __________",
              style="HEADING_3", center=True, font_size=11, bold=True,
              no_indent=True, space_below=4)
    b.blank(1)
    b.add(
        "is a bonafide student of this institute and the work has been carried out by them under the "
        f"supervision of {C.GUIDE} and is approved for the partial fulfillment of the requirement of "
        f"{C.UNIVERSITY}, for the award of the degree of Bachelor of Technology (Information Technology).",
        space_below=8,
    )
    b.blank(2)
    for line in [
        f"({C.GUIDE})", "Guide", " ", f"({C.HOD})",
        "Head, Department of Information Technology", " ",
        "Name & Signature of External Examiner: ______________________________",
        f"({C.DIRECTOR})", f"Director, {C.COLLEGE}, Pune - 33", " ",
        "Place: Pune                         Date: ____________________",
        "Note: Industry certificate is not applicable; this is an institute-sponsored academic project.",
    ]:
        b.add(line, style="HEADING_3" if line and not line.startswith("Note") else "NORMAL_TEXT",
              center=not line.startswith("Note"), font_size=10 if line.startswith("Note") else 11,
              bold=not line.startswith("Note"), no_indent=True, space_below=2)


def build_front_matter(b: Builder) -> None:
    b.add("ACKNOWLEDGEMENT", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    b.add(
        "We express our sincere gratitude to our project guide, " + C.GUIDE +
        ", for continuous guidance, technical insight and constructive review throughout the project. "
        "The guidance helped us connect hydrological theory, software architecture and research writing into a "
        "single coherent Stage-II submission.",
    )
    b.add(
        f"We are grateful to {C.HOD}, Head of the {C.DEPARTMENT}, for providing academic support and "
        f"encouragement, and to {C.DIRECTOR}, Director of {C.COLLEGE}, for the institutional facilities and "
        "environment that made this work possible. We also thank the faculty members of the department for "
        "their valuable suggestions during reviews and evaluations.",
    )
    b.add(
        "We acknowledge the open-source communities behind FastAPI, Next.js, ReportLab, HarfBuzz, Leaflet, "
        "react-three-fiber, pytest and the public NOAA PSL CMAP precipitation dataset. Their documented work "
        "enabled a transparent and reproducible implementation. Finally, we thank our families and classmates "
        "for their patience and support during development, testing and report preparation.",
    )
    b.blank(1)
    b.add("NAME OF THE STUDENTS", style="HEADING_3", center=True,
          font_size=12, bold=True, no_indent=True)
    for s in C.STUDENTS:
        b.add(s.upper() + " (ROLL NO: __________)", style="HEADING_3",
              center=True, font_size=12, bold=True, no_indent=True, space_below=2)

    b.add("ABSTRACT", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    b.add(C.ABSTRACT)
    b.add("Keywords: " + C.KEYWORDS, bold=False, no_indent=True, space_below=0)

    b.add("TABLE OF CONTENTS", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    toc_lines = [
        "CERTIFICATE .................................................................................... i",
        "ACKNOWLEDGEMENT .................................................................. ii",
        "ABSTRACT .......................................................................................... iii",
        "TABLE OF CONTENTS ................................................................. iv",
        "LIST OF ABBREVIATIONS ........................................................... vi",
        "NOMENCLATURE ............................................................................ vii",
        "LIST OF FIGURES ....................................................................... viii",
        "LIST OF TABLES ......................................................................... x",
    ]
    starts = {}
    for i, p in enumerate(PAGES, 1):
        starts.setdefault(p["ch"], i)
    for ch in [str(i) for i in range(1, 12)]:
        title = next(p["chapter_title"] for p in PAGES if p["ch"] == ch and p["chapter_title"])
        toc_lines.append(f"{title} ......................................................................... {starts[ch]}")
    for ch in "ABCDEF":
        title = next(p["chapter_title"] for p in PAGES if p["ch"] == ch and p["chapter_title"])
        toc_lines.append(f"{title} ......................................................................... {starts[ch]}")
    toc_lines.append(f"12 REFERENCES ................................................................ {len(PAGES)+1}")
    for line in toc_lines:
        b.add(line, no_indent=True, align="START", font_size=11, space_below=0,
              line_spacing=100)

    b.add("LIST OF ABBREVIATIONS", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    for a, meaning in C.ABBREVIATIONS:
        b.add(f"{a:<12} {meaning}", no_indent=True, align="START", font_size=10,
              space_below=0, line_spacing=100)

    b.add("NOMENCLATURE", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    b.add("The following symbols and notations are used in this report. All symbolic definitions are confined to this section in accordance with the institute report guidelines.")
    for sym, desc, unit in C.NOMENCLATURE:
        b.add(f"{sym:<10} {desc:<55} {unit}", no_indent=True, align="START",
              font_size=9, space_below=0, line_spacing=100)

    b.add("LIST OF FIGURES", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    for n, cap, pg in FIG_RECORDS:
        b.add(f"Figure {n:<6} {cap[:95]:<95} {pg}", no_indent=True,
              align="START", font_size=9, space_below=0, line_spacing=100)

    b.add("LIST OF TABLES", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    for n, cap, pg in TAB_RECORDS:
        b.add(f"Table {n:<6} {cap[:95]:<95} {pg}", no_indent=True,
              align="START", font_size=9, space_below=0, line_spacing=100)


def build_main(b: Builder) -> None:
    fig_iter = iter(FIG_RECORDS)
    tab_iter = iter(TAB_RECORDS)
    for page_no, page in enumerate(PAGES, 1):
        first = True
        if page.get("chapter_title"):
            b.add(replace_refs(page["chapter_title"], REF_MAP), style="HEADING_1",
                  center=True, font_size=14, bold=True, no_indent=True,
                  page_break=(page_no > 1))
            first = False
        b.add(replace_refs(page["heading"], REF_MAP), style="HEADING_2",
              align="START", font_size=12, bold=True, no_indent=True,
              page_break=(first and page_no > 1))
        first = False
        for para in page["paras"]:
            b.add(replace_refs(para, REF_MAP), style="NORMAL_TEXT",
                  align="JUSTIFY", page_break=(first and page_no > 1))
            first = False
        figs = page.get("figures", [])
        for f in figs:
            rec = next(fig_iter)
            b.add_image(f["path"], f["caption"], f["legend"], rec[0],
                        page_break=(first and page_no > 1))
            first = False
            b.add(f"Figure {rec[0]}: {replace_refs(f['caption'], REF_MAP)}",
                  align="CENTER", font_size=12, no_indent=True, space_below=0,
                  line_spacing=100)
            b.add(replace_refs(f["legend"], REF_MAP), align="CENTER",
                  font_size=10, no_indent=True, space_below=6, line_spacing=100)
        if page.get("table"):
            rec = next(tab_iter)
            b.add(f"Table {rec[0]}: {replace_refs(page['table']['caption'], REF_MAP)}",
                  style="HEADING_3", align="CENTER", font_size=12, bold=True,
                  no_indent=True, space_below=4, page_break=(first and page_no > 1))
            first = False
            rows = page["table"]["rows"]
            fs = 8.5 if len(rows) > 8 else 9
            for row in rows:
                cells = [replace_refs(c, REF_MAP) for c in row]
                b.add(" | ".join(cells), no_indent=True, align="START",
                      font_size=fs, space_below=0, line_spacing=100)
        for line in page.get("code", []):
            b.add(replace_refs(line, REF_MAP), no_indent=True, align="START",
                  font="Courier New", font_size=9, space_below=0,
                  line_spacing=100, page_break=(first and page_no > 1))
            first = False


def build_references(b: Builder) -> None:
    b.add("12 REFERENCES", style="HEADING_1", center=True, page_break=True,
          font_size=14, bold=True, no_indent=True)
    refs = [f"[{REF_MAP[k]}] {C.REFS[k]}" for k in REF_ORDER]
    for text in refs:
        b.add(text, no_indent=True, align="JUSTIFY", font_size=10.5,
              indent_start=21.6, indent_first=-21.6, space_below=4,
              line_spacing=115)
    b.add("12.1 Bibliography", style="HEADING_2", align="START",
          page_break=True, font_size=12, bold=True, no_indent=True)
    for i, item in enumerate(C.BIBLIOGRAPHY, 1):
        b.add(f"[B{i}] {item}", no_indent=True, align="JUSTIFY", font_size=10.5,
              indent_start=21.6, indent_first=-21.6, space_below=4,
              line_spacing=115)


def build_figures_appendix(b: Builder) -> None:
    b.add("APPENDIX G: FIGURES", style="HEADING_1", center=True,
          page_break=True, font_size=14, bold=True, no_indent=True)
    b.add(
        "The following pages reproduce the report figures in monochrome. Each figure is inserted from the "
        "project's public evidence folder and is accompanied by the same number, title and legend used in "
        "the main text.",
        no_indent=False,
    )
    # Reuse image specs from main pages; insert a second copy in the appendix.
    for spec in list(b.images):
        b.add(f"Figure {spec['number']}: {replace_refs(spec['caption'], REF_MAP)}",
              align="CENTER", font_size=12, no_indent=True, space_below=2,
              line_spacing=100)
        b.add(replace_refs(spec["legend"], REF_MAP), align="CENTER", font_size=10,
              no_indent=True, space_below=8, line_spacing=100)
        # Placeholder for appendix copy.
        s = PLACEHOLDER + "\n"
        start = b.idx
        end = start + len(s)
        b.parts.append(s)
        b.idx = end
        b.paragraphs.append({
            "start": start,
            "end": end,
            "text": PLACEHOLDER,
            "style": "NORMAL_TEXT",
            "align": "CENTER",
            "no_indent": True,
            "space_below": 8,
            "line_spacing": 100,
        })
        b.images.append({
            **spec,
            "index": start,
        })


def style_requests(paragraphs: list[dict]) -> list[dict]:
    def signature(p: dict) -> tuple:
        return (
            p.get("style"), p.get("align"), p.get("font_size"), p.get("font"),
            p.get("bold"), p.get("page_break"), p.get("indent_first"),
            p.get("indent_start"), p.get("space_below"), p.get("line_spacing"),
            p.get("no_indent"),
        )

    groups: list[dict] = []
    for p in paragraphs:
        sig = signature(p)
        if groups and groups[-1]["sig"] == sig and groups[-1]["end"] == p["start"]:
            groups[-1]["end"] = p["end"]
        else:
            groups.append({"sig": sig, "start": p["start"], "end": p["end"], "p": p})

    reqs: list[dict] = []
    for g in groups:
        p = g["p"]
        start, end = g["start"], g["end"]
        ps: dict = {"namedStyleType": p["style"]}
        fields = ["namedStyleType"]
        if p.get("align"):
            ps["alignment"] = p["align"]
            fields.append("alignment")
        if p.get("page_break"):
            ps["pageBreakBefore"] = True
            fields.append("pageBreakBefore")
        if p.get("no_indent"):
            ps["indentFirstLine"] = {"magnitude": 0, "unit": "PT"}
            fields.append("indentFirstLine")
        if p.get("indent_first") is not None:
            ps["indentFirstLine"] = {"magnitude": p["indent_first"], "unit": "PT"}
            if "indentFirstLine" not in fields:
                fields.append("indentFirstLine")
        if p.get("indent_start") is not None:
            ps["indentStart"] = {"magnitude": p["indent_start"], "unit": "PT"}
            fields.append("indentStart")
        if p.get("space_below") is not None:
            ps["spaceBelow"] = {"magnitude": p["space_below"], "unit": "PT"}
            fields.append("spaceBelow")
        if p.get("line_spacing") is not None:
            ps["lineSpacing"] = p["line_spacing"]
            fields.append("lineSpacing")
        reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": ps,
                "fields": ",".join(fields),
            }
        })

        ts: dict = {}
        tfields: list[str] = []
        if p.get("font_size") is not None:
            ts["fontSize"] = {"magnitude": p["font_size"], "unit": "PT"}
            tfields.append("fontSize")
        if p.get("font"):
            ts["weightedFontFamily"] = {"fontFamily": p["font"], "weight": 400}
            tfields.append("weightedFontFamily")
        elif p.get("style") in ("TITLE", "HEADING_1", "HEADING_2", "HEADING_3"):
            ts["weightedFontFamily"] = {"fontFamily": "Times New Roman", "weight": 400}
            tfields.append("weightedFontFamily")
        if p.get("bold") is not None:
            ts["bold"] = p["bold"]
            tfields.append("bold")
        if tfields:
            reqs.append({
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": ts,
                    "fields": ",".join(tfields),
                }
            })
    return reqs


def image_requests(images: list[dict]) -> list[dict]:
    # Process from bottom to top so earlier indices stay valid.
    reqs: list[dict] = []
    for spec in sorted(images, key=lambda x: x["index"], reverse=True):
        i = spec["index"]
        reqs.append({
            "deleteContentRange": {
                "range": {"startIndex": i, "endIndex": i + 1}
            }
        })
        reqs.append({
            "insertInlineImage": {
                "uri": spec["uri"],
                "location": {"index": i},
                "objectSize": {
                    "width": {"magnitude": spec["width"], "unit": "PT"},
                    "height": {"magnitude": spec["height"], "unit": "PT"},
                },
            }
        })
    return reqs


def chunk(reqs: list[dict], size: int) -> list[list[dict]]:
    return [reqs[i:i + size] for i in range(0, len(reqs), size)]


def main() -> None:
    b = Builder()
    build_cover(b)
    build_certificate(b)
    build_front_matter(b)
    build_main(b)
    build_references(b)

    text = "".join(b.parts)
    OUT_TEXT.write_text(text, encoding="utf-8")

    style_reqs = style_requests(b.paragraphs)
    image_reqs = image_requests(b.images)
    batches = chunk(style_reqs, 180) + chunk(image_reqs, 100)
    with OUT_BATCHES.open("w", encoding="utf-8") as f:
        json.dump({
            "insert_text": text,
            "batches": batches,
            "counts": {
                "characters": len(text),
                "paragraphs": len(b.paragraphs),
                "images": len(b.images),
                "style_requests": len(style_reqs),
                "image_requests": len(image_reqs),
            },
        }, f, ensure_ascii=False, separators=(",", ":"))

    print(json.dumps({
        "text_file": str(OUT_TEXT),
        "batches_file": str(OUT_BATCHES),
        "counts": {
            "characters": len(text),
            "paragraphs": len(b.paragraphs),
            "images": len(b.images),
            "style_requests": len(style_reqs),
            "image_requests": len(image_reqs),
            "batches": len(batches),
        },
    }, indent=2))


if __name__ == "__main__":
    main()
