#!/usr/bin/env python3
"""Build a copy-paste pack of the Stage-II report from the finished DOCX.

Outputs (report/direct/):
  index.html              - landing page with links and paste instructions
  full_report.html        - the whole report as one styled page
  00_Cover.html ...       - one HTML file per chapter / appendix / front-matter page
  full_report.md          - plain Markdown mirror (text + image links + pipe tables)
  images/Fig_x.y_slug.png - every figure extracted with a readable file name
  README.md               - how to paste into Word without losing tables/figures

The HTML uses Times New Roman 12 pt, 1.5 line spacing, justified body text with a
36 pt first-line indent, 14 pt bold centred chapter titles and real <table>
elements, so a browser "Select all -> Copy" pastes into Word as formatted text,
real tables and inline pictures.
"""
from __future__ import annotations

import html
import re
import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "report" / "HydroRainGuard_BE_Project_Stage_II_Report.docx"
OUT = ROOT / "report" / "direct"
IMG = OUT / "images"

# --------------------------------------------------------------------------- #
# 1. Read the DOCX into an ordered block list
# --------------------------------------------------------------------------- #


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[1]
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def run_info(run, doc):
    """Return (text, bold, italic, size_pt, image) for one run."""
    bold = run.bold
    italic = run.italic
    size = run.font.size.pt if run.font.size is not None else None
    image = None
    drawings = run._r.findall(".//" + qn("w:drawing"))
    if drawings:
        blip = run._r.find(".//" + qn("a:blip"))
        if blip is not None:
            rid = blip.get(qn("r:embed"))
            part = doc.part.related_parts[rid]
            extent = run._r.find(".//" + qn("wp:extent"))
            width_pt = int(extent.get("cx")) / 12700.0 if extent is not None else 420.0
            suffix = Path(str(part.partname)).suffix or ".png"
            image = {"blob": part.blob, "ext": suffix, "width": width_pt, "name": None}
    return {"text": run.text, "bold": bold, "italic": italic, "size": size, "image": image}


def cell_html(cell):
    parts = []
    for para in cell.paragraphs:
        runs = []
        head = para.style.name == "TableHeadText"
        for run in para.runs:
            txt = html.escape(run.text)
            if run.bold or head:
                txt = f"<b>{txt}</b>"
            if run.italic:
                txt = f"<i>{txt}</i>"
            runs.append(txt)
        parts.append("".join(runs))
    text = "<br>".join(p for p in parts if p.strip())
    return text


def parse_table(table):
    rows = []
    for row in table.rows:
        rows.append([cell_html(c) for c in row.cells])
    header = bool(rows) and any("<b>" in c for c in rows[0])
    return {"type": "tbl", "rows": rows, "header": header}


def parse_blocks(doc):
    blocks = []
    for item in iter_blocks(doc):
        if isinstance(item, Paragraph):
            runs = [run_info(r, doc) for r in item.runs]
            blocks.append({
                "type": "p",
                "style": item.style.name,
                "text": item.text,
                "runs": runs,
            })
        else:
            blocks.append(parse_table(item))
    return blocks


# --------------------------------------------------------------------------- #
# 2. Name and save images
# --------------------------------------------------------------------------- #


def slugify(text: str, limit: int = 42) -> str:
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", text)
    words = [w for w in text.split() if w][:7]
    slug = "_".join(words)
    return (slug[:limit].rstrip("_") or "figure")


def name_images(blocks):
    counter = 0
    for i, block in enumerate(blocks):
        if block["type"] != "p":
            continue
        for run in block["runs"]:
            if not run["image"]:
                continue
            counter += 1
            caption, number = "", f"{counter:02d}"
            for nxt in blocks[i + 1: i + 4]:
                if nxt["type"] == "p" and nxt["text"].strip().startswith("Figure "):
                    caption = nxt["text"].strip()
                    break
            m = re.match(r"Figure\s+([0-9A-Z]+\.[0-9]+)\s*:?\s*(.*)", caption)
            if m:
                number = m.group(1)
                caption = m.group(2)
            run["image"]["name"] = f"Fig_{number}_{slugify(caption)}{run['image']['ext']}"


def save_images(blocks):
    IMG.mkdir(parents=True, exist_ok=True)
    used = set()
    saved = 0
    for block in blocks:
        if block["type"] != "p":
            continue
        for run in block["runs"]:
            img = run["image"]
            if not img:
                continue
            name = img["name"]
            stem, suffix = Path(name).stem, Path(name).suffix
            k = 2
            while name in used:
                name = f"{stem}_{k}{suffix}"
                k += 1
            used.add(name)
            (IMG / name).write_bytes(img["blob"])
            img["name"] = name
            saved += 1
    return saved


# --------------------------------------------------------------------------- #
# 3. Render HTML
# --------------------------------------------------------------------------- #

CLASS = {
    "Normal": "body",
    "CertificateBody": "cert",
    "ChapterTitle": "chapter",
    "FrontHeading": "front",
    "SectionHeading": "section",
    "SubHeading": "sub",
    "Caption": "caption",
    "Legend": "legend",
    "TableCaption": "tablecap",
    "Signature": "sig",
    "CoverTitle": "cover-title",
    "CoverLine": "cover-line",
    "TOCEntry": "toc",
    "ListEntry": "list",
    "ReferenceEntry": "ref",
    "CodeBlock": "code",
}

CSS = """
:root { --ink:#111; --rule:#333; }
* { box-sizing: border-box; }
body { margin:0; background:#eceff1; color:var(--ink);
       font-family:"Times New Roman", Times, Georgia, serif; font-size:12pt; line-height:1.5; }
.sheet { width:210mm; min-height:297mm; padding:23.4mm 23.4mm 32mm 37mm; margin:14px auto;
         background:#fff; box-shadow:0 2px 10px rgba(0,0,0,.18); }
.sheet-body { width:149.6mm; }
p { margin:0 0 12pt 0; }
p.body, p.cert { text-align:justify; text-indent:36pt; }
p.cert { margin-bottom:10pt; }
p.blank { margin:0; line-height:1; font-size:12pt; }
h1 { font-size:14pt; font-weight:bold; text-align:center; text-transform:uppercase;
     margin:0 0 10pt 0; line-height:1.5; page-break-before:always; }
h1.front { margin-bottom:12pt; }
h2 { font-size:12pt; font-weight:bold; text-align:left; margin:8pt 0 6pt 0; line-height:1.5;
     page-break-after:avoid; }
h3 { font-size:12pt; font-weight:bold; text-align:left; margin:6pt 0 4pt 0; line-height:1.5;
     page-break-after:avoid; }
p.cover-title { font-size:16pt; font-weight:bold; text-align:center; line-height:1.1; margin:0 0 6pt 0; }
p.cover-line { font-size:12pt; font-weight:bold; text-align:center; line-height:1.15; margin:0 0 5pt 0; }
p.caption { font-size:12pt; text-align:center; text-indent:0; line-height:1.1; margin:2pt 0 0 0; }
p.legend  { font-size:10pt; text-align:center; text-indent:0; line-height:1.1; margin:0 0 8pt 0; }
p.tablecap{ font-size:12pt; font-weight:bold; text-align:center; text-indent:0; line-height:1.1;
            margin:6pt 0 4pt 0; }
p.sig     { font-size:12pt; text-align:center; text-indent:0; line-height:1.2; margin:4pt 0; }
p.toc     { font-size:10pt; text-indent:0; line-height:1.2; margin:0; }
p.list    { font-size:9pt; text-indent:0; line-height:1.2; margin:0 0 1pt 0; }
p.ref     { font-size:10.5pt; text-align:justify; text-indent:-21.6pt; margin:0 0 7pt 21.6pt;
            line-height:1.15; }
p.code    { font-family:"Courier New", monospace; font-size:9pt; text-indent:0; line-height:1.1;
            margin:0; }
p.figure  { text-align:center; text-indent:0; margin:6pt 0 0 0; page-break-inside:avoid; }
p.figure img { max-width:100%; height:auto; }
table.grid { border-collapse:collapse; width:100%; margin:4pt 0 10pt 0; font-size:9pt;
             line-height:1.15; page-break-inside:auto; }
table.grid th, table.grid td { border:0.5pt solid var(--rule); padding:2.5pt 4pt; vertical-align:top;
                               text-align:left; }
table.grid th { font-weight:bold; text-align:center; background:#f2f2f2; }
@media print {
  body { background:#fff; }
  .sheet { width:auto; min-height:0; margin:0; padding:0; box-shadow:none; }
  .sheet-body { width:auto; }
  @page { size:A4; margin:23.4mm 23.4mm 32mm 37mm; }
  h1, h1.front { page-break-before:always; }
  .sheet-body > :first-child { page-break-before:avoid; }
}
"""

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head><body>
<div class="sheet"><div class="sheet-body">
"""

TAIL = """</div></div>
</body></html>
"""


def render_run(run):
    img = run["image"]
    if img:
        return (f'<img src="images/{html.escape(img["name"])}" '
                f'style="width:{img["width"]:.1f}pt" alt="{html.escape(img["name"])}">')
    text = html.escape(run["text"]).replace("\t", "    ")
    if not text:
        return ""
    if run["bold"]:
        text = f"<b>{text}</b>"
    if run["italic"]:
        text = f"<i>{text}</i>"
    if run["size"]:
        text = f'<span style="font-size:{run["size"]:g}pt">{text}</span>'
    return text


def render_para(block):
    cls = CLASS.get(block["style"], "body")
    inner = "".join(render_run(r) for r in block["runs"])
    has_img = any(r["image"] for r in block["runs"])
    text_only = "".join(r["text"] for r in block["runs"]).strip()
    if has_img and not text_only:
        return f'<p class="figure">{inner}</p>\n'
    if not text_only:
        return '<p class="blank">&nbsp;</p>\n' 
    if cls == "chapter":
        return f'<h1 class="chapter">{inner}</h1>\n'
    if cls == "front":
        return f'<h1 class="front">{inner}</h1>\n'
    if cls == "section":
        return f'<h2>{inner}</h2>\n'
    if cls == "sub":
        return f'<h3>{inner}</h3>\n'
    return f'<p class="{cls}">{inner}</p>\n'


def render_table(block):
    rows = block["rows"]
    if not rows:
        return ""
    out = ['<table class="grid">']
    start = 0
    if block["header"]:
        out.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
        start = 1
    out.append("<tbody>")
    for row in rows[start:]:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>\n")
    return "".join(out)


def render_blocks(blocks):
    out = []
    for block in blocks:
        out.append(render_table(block) if block["type"] == "tbl" else render_para(block))
    return "".join(out)


# --------------------------------------------------------------------------- #
# 4. Split into sections
# --------------------------------------------------------------------------- #

FRONT_ORDER = [
    ("CERTIFICATE", "01_Certificate"),
    ("ACKNOWLEDGEMENT", "02_Acknowledgement"),
    ("ABSTRACT", "03_Abstract"),
    ("TABLE OF CONTENTS", "04_Table_of_Contents"),
    ("LIST OF ABBREVIATIONS", "05_Abbreviations"),
    ("NOMENCLATURE", "06_Nomenclature"),
    ("LIST OF FIGURES", "07_List_of_Figures"),
    ("LIST OF TABLES", "08_List_of_Tables"),
]


def section_name(title: str, index: int):
    t = title.strip().upper()
    if t.startswith("CERTIFICATE"):
        return "01_Certificate", "Certificate"
    if t.startswith("ACKNOWLEDGEMENT"):
        return "02_Acknowledgement", "Acknowledgement"
    if t.startswith("ABSTRACT"):
        return "03_Abstract", "Abstract"
    if t.startswith("TABLE OF CONTENTS"):
        return "04_Table_of_Contents", "Table of Contents"
    if t.startswith("LIST OF ABBREVIATIONS"):
        return "05_Abbreviations", "List of Abbreviations"
    if t.startswith("NOMENCLATURE"):
        return "06_Nomenclature", "Nomenclature"
    if t.startswith("LIST OF FIGURES"):
        return "07_List_of_Figures", "List of Figures"
    if t.startswith("LIST OF TABLES"):
        return "08_List_of_Tables", "List of Tables"
    m = re.match(r"(\d+)\s+(.*)", title.strip())
    if m and int(m.group(1)) <= 11:
        num = int(m.group(1))
        known = {
            1: ("Introduction", "Introduction"),
            2: ("LiteratureSurvey", "Literature Survey"),
            3: ("ProblemStatement", "Problem Statement"),
            4: ("SoftwareRequirementsSpecification", "Software Requirements Specification"),
            5: ("SystemDesign", "System Design"),
            6: ("ProjectImplementation", "Project Implementation"),
            7: ("SoftwareTesting", "Software Testing"),
            8: ("ResultsAndDiscussion", "Results and Discussion"),
            9: ("OtherSpecifications", "Other Specifications"),
            10: ("ProjectPlan", "Project Plan"),
            11: ("ConclusionsAndFutureWork", "Conclusions and Future Work"),
        }
        slug, display = known[num]
        return f"Ch{num:02d}_{slug}", f"{num}. {display}"
    m = re.match(r"APPENDIX\s+([A-Z])", title.strip().upper())
    if m:
        return f"Appendix_{m.group(1)}", f"Appendix {m.group(1)}"
    if t.startswith("12 REFERENCES"):
        return "12_References", "References"
    return f"S{index:02d}_{slugify(title, 24)}", title.title()


def split_sections(blocks):
    sections = []
    current = {"title": "Cover", "file": "00_Cover", "blocks": []}
    for block in blocks:
        if block["type"] == "p" and block["style"] in ("FrontHeading", "ChapterTitle"):
            text = block["text"].strip()
            if text.upper().endswith("(CONTINUED)"):
                current["blocks"].append(block)
                continue
            if current["blocks"]:
                sections.append(current)
                current = {"title": text, "file": None, "blocks": []}
            else:
                current["title"] = text
                current["file"] = None
        current["blocks"].append(block)
    if current["blocks"]:
        sections.append(current)
    for i, sec in enumerate(sections):
        if sec["file"] is None:
            sec["file"], sec["title"] = section_name(sec["title"], i)
    return sections


# --------------------------------------------------------------------------- #
# 5. Markdown mirror
# --------------------------------------------------------------------------- #


def md_run(run):
    img = run["image"]
    if img:
        return f'\n\n![{img["name"]}](images/{img["name"]})\n\n'
    text = run["text"]
    if not text.strip():
        return ""
    if run["bold"]:
        text = f"**{text.strip()}**"
    if run["italic"]:
        text = f"*{text.strip()}*"
    return text


def md_blocks(blocks):
    out = []
    for block in blocks:
        if block["type"] == "tbl":
            rows = block["rows"]
            if not rows:
                continue
            width = max(len(r) for r in rows)
            norm = [r + [""] * (width - len(r)) for r in rows]
            out.append("")
            out.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in norm[0]) + " |")
            out.append("|" + "|".join([" --- "] * width) + "|")
            for row in norm[1:]:
                out.append("| " + " | ".join(c.replace("|", "\\|").replace("<br>", " ") for c in row) + " |")
            out.append("")
            continue
        cls = CLASS.get(block["style"], "body")
        inner = "".join(md_run(r) for r in block["runs"]).strip()
        if not inner:
            continue
        if cls in ("chapter", "front"):
            out.append(f"\n\n# {inner}\n")
        elif cls == "section":
            out.append(f"\n## {inner}\n")
        elif cls == "sub":
            out.append(f"\n### {inner}\n")
        elif cls == "caption":
            out.append(f"\n*{inner}*\n")
        elif cls == "legend":
            out.append(f"\n<sub>{inner}</sub>\n")
        elif cls == "tablecap":
            out.append(f"\n**{inner}**\n")
        else:
            out.append(inner + "\n")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# 6. Main
# --------------------------------------------------------------------------- #


def main() -> None:
    doc = Document(str(DOCX))
    blocks = parse_blocks(doc)
    name_images(blocks)
    OUT.mkdir(parents=True, exist_ok=True)
    if IMG.exists():
        for old in IMG.glob("*"):
            old.unlink()
    saved = save_images(blocks)
    sections = split_sections(blocks)

    ORDER = ["00_Cover", "01_Certificate", "02_Acknowledgement", "03_Abstract", "04_Table_of_Contents",
             "05_Abbreviations", "06_Nomenclature", "07_List_of_Figures", "08_List_of_Tables",
             "Ch01_Introduction", "Ch02_LiteratureSurvey", "Ch03_ProblemStatement", "Ch04_SoftwareRequirementsSpecification",
             "Ch05_SystemDesign", "Ch06_ProjectImplementation", "Ch07_SoftwareTesting", "Ch08_ResultsAndDiscussion",
             "Ch09_OtherSpecifications", "Ch10_ProjectPlan", "Ch11_ConclusionsAndFutureWork",
             "Appendix_A", "Appendix_B", "Appendix_C", "Appendix_D", "Appendix_E", "Appendix_F",
             "12_References"]
    pos = {name: i for i, name in enumerate(ORDER)}
    sections.sort(key=lambda s: pos.get(s["file"], 99))

    # per-section HTML
    nav = []
    for sec in sections:
        title = sec["title"].title() if sec["title"].isupper() else sec["title"]
        body = render_blocks(sec["blocks"])
        page = HEAD.format(title=html.escape(title), css=CSS) + body + TAIL
        (OUT / f'{sec["file"]}.html').write_text(page, encoding="utf-8")
        nav.append((sec["file"], title))

    # full report
    full_body = render_blocks(blocks)
    (OUT / "full_report.html").write_text(
        HEAD.format(title="HYDRO RAIN GUARD - BE Project Stage-II Report", css=CSS) + full_body + TAIL,
        encoding="utf-8")

    # single self-contained file (images embedded) for offline use
    import base64 as _b64
    full_html = (OUT / "full_report.html").read_text(encoding="utf-8")
    for img_file in sorted(IMG.glob("*")):
        data = _b64.b64encode(img_file.read_bytes()).decode("ascii")
        mime = "image/png" if img_file.suffix.lower() == ".png" else "image/jpeg"
        full_html = full_html.replace(f'src="images/{img_file.name}"',
                                      f'src="data:{mime};base64,{data}"')
    (OUT / "full_report_offline.html").write_text(full_html, encoding="utf-8")

    # markdown mirror
    md = ["# HYDRO RAIN GUARD: Intelligent Rainwater Harvesting and Artificial Groundwater Recharge Assessment System",
          "", "*BE Project Stage-II report - plain-text mirror of the Word file.*", ""]
    md.append(md_blocks(blocks))
    (OUT / "full_report.md").write_text("\n".join(md), encoding="utf-8")

    # plain text mirror (no markup) for pasting into Word/Docs
    txt = []
    for block in blocks:
        if block["type"] == "tbl":
            for row in block["rows"]:
                txt.append(" | ".join(html.unescape(re.sub("<[^>]+>", " ", c)) for c in row))
            txt.append("")
            continue
        text = "".join(r["text"] for r in block["runs"]).strip()
        if text:
            txt.append(text)
    (OUT / "full_report.txt").write_text("\n\n".join(txt), encoding="utf-8")

    # sample outputs the report refers to
    sample_dir = OUT / "sample_outputs"
    sample_dir.mkdir(exist_ok=True)
    for src, name in [
        (ROOT / "report" / "data" / "sample_report.pdf", "sample_report.pdf"),
        (ROOT / "report" / "data" / "scenarios.json", "scenarios.json"),
        (ROOT / "report" / "data" / "ui_assessment.json", "ui_assessment.json"),
    ]:
        if src.exists():
            shutil.copyfile(src, sample_dir / name)

    # one download with everything
    zip_path = OUT / "hydrorainguard_report_pack.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(OUT.rglob("*")):
            if f.is_file() and f != zip_path:
                zf.write(f, f.relative_to(OUT))

    # landing page
    links = "\n".join(
        f'<li><a href="{f}.html">{html.escape(t)}</a></li>' for f, t in nav)
    index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Report pack - HYDRO RAIN GUARD</title>
<style>
body {{ font-family:"Segoe UI", Arial, sans-serif; background:#f4f6f8; color:#15202b; margin:0; }}
.wrap {{ max-width:900px; margin:32px auto; background:#fff; padding:32px 40px; border-radius:10px;
         box-shadow:0 2px 14px rgba(0,0,0,.08); }}
h1 {{ font-size:24px; margin:0 0 6px; }}
p, li {{ font-size:15px; line-height:1.6; }}
code {{ background:#eef1f4; padding:1px 5px; border-radius:4px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:10px; padding:0; list-style:none; }}
.grid a {{ display:block; padding:12px 14px; border:1px solid #d7dee5; border-radius:8px; text-decoration:none;
           color:#0b5cad; background:#fbfcfd; }}
.grid a:hover {{ background:#eef6ff; border-color:#9cc6ef; }}
.big {{ display:inline-block; margin:18px 0; padding:14px 22px; background:#0b5cad; color:#fff;
        border-radius:8px; text-decoration:none; font-weight:600; }}
.note {{ background:#fff8e1; border-left:4px solid #f0b429; padding:12px 16px; border-radius:4px; }}
</style></head><body><div class="wrap">
<h1>HYDRO RAIN GUARD - report paste pack</h1>
<p>Every file below holds the same report text, figures and tables in a form you can copy straight into Word.</p>
<a class="big" href="full_report.html">Open the full report &rarr;</a>
<p>One-file version (images embedded, works offline): <a href="full_report_offline.html">full_report_offline.html</a></p>
<p class="note"><b>To paste into Word:</b> open <code>full_report.html</code> (or a single chapter), press
<code>Ctrl+A</code> then <code>Ctrl+C</code>, and paste into Word with <code>Keep Source Formatting</code>.
Headings, justified 12 pt Times New Roman text, real tables and all pictures come across. Then set A4 with
top 23.4 mm, left 37 mm, bottom 32 mm, right 23.4 mm and add the footer.</p>
<h2>Chapters and front matter</h2>
<ul class="grid">
{links}
</ul>
<h2>Sample outputs</h2>
<ul>
<li><a href="sample_outputs/sample_report.pdf">sample_report.pdf</a> - the PDF the system generates for an assessment</li>
<li><a href="sample_outputs/scenarios.json">scenarios.json</a> - the five verification scenarios used in Chapter 8</li>
<li><a href="sample_outputs/ui_assessment.json">ui_assessment.json</a> - the live UI run recorded for the results chapter</li>
</ul>
<h2>Also in this folder</h2>
<ul>
<li><a href="hydrorainguard_report_pack.zip">hydrorainguard_report_pack.zip</a> - everything above in one download</li>
<li><code>images/</code> - all 53 figures as separate PNG files named <code>Fig_8.1_....png</code></li>
<li><code>full_report.md</code> / <code>full_report.txt</code> - the same text as Markdown or plain text</li>
<li><code>README.md</code> - the same instructions in text form</li>
</ul>
</div></body></html>
"""
    (OUT / "index.html").write_text(index, encoding="utf-8")

    (OUT / "README.md").write_text(
        "# Report paste pack\n\n"
        "Generated from `report/HydroRainGuard_BE_Project_Stage_II_Report.docx`.\n\n"
        "## Fastest route into Word\n\n"
        "1. Open `index.html` in a browser (or the live preview) and click the chapter you need.\n"
        "2. Select all (`Ctrl+A`), copy (`Ctrl+C`).\n"
        "3. In Word paste with *Keep Source Formatting*.\n\n"
        "Chapter titles, 12 pt Times New Roman body text (justified, 1.5 spacing, 36 pt first-line\n"
        "indent), captions, legends and real bordered tables are reproduced. Pictures paste inline.\n\n"
        "## Page setup in Word\n\n"
        "- A4, margins: top 23.4 mm, left 37 mm, bottom 32 mm, right 23.4 mm.\n"
        "- Footer: `RSCOE, Department of Information Technology 2026-27`, then\n"
        "  Insert > Page Number > Bottom of Page.\n"
        "- Chapter titles already carry a page break before them.\n\n"
        "## Files\n\n"
        "- `full_report.html` - complete report in one page.\n"
        "- `full_report_offline.html` - same page with every picture embedded, so it\n"
        "  opens by double-click without the images folder.\n"
        "- `00_Cover.html` ... `12_References.html` - one file per chapter/appendix.\n"
        "- `images/` - 53 extracted figures, named `Fig_<chapter>.<n>_<title>.png`.\n"
        "- `full_report.md` - plain Markdown mirror of the text.\n",
        encoding="utf-8")

    chars = sum(len(b.get("text", "")) for b in blocks)
    print(f"sections={len(sections)}  images={saved}  html_chars={chars}")
    print(f"full_report.html  {(OUT / 'full_report.html').stat().st_size / 1e6:.2f} MB")
    print(f"full_report.md    {(OUT / 'full_report.md').stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
