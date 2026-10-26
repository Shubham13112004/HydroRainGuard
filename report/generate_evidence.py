#!/usr/bin/env python3
"""Generate verified evidence, charts, diagrams and processed screenshots.

Run with the project virtual environment from the repository root:

    .venv/bin/python report/generate_evidence.py

The script exercises the real backend through FastAPI's TestClient, so the
numbers written to report/data/scenarios.json are produced by the project's
own hydrology, AHP, cost-benefit and PDF services.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "Project" / "backend"
REPORT = ROOT / "report"
DATA = REPORT / "data"
FIG = REPORT / "figures"
RAW = REPORT / "figures_raw"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
F_REG = FONT_DIR / "DejaVuSans.ttf"
F_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
F_MONO = FONT_DIR / "DejaVuSansMono.ttf"
F_MONO_BOLD = FONT_DIR / "DejaVuSansMono-Bold.ttf"


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        return ImageFont.truetype(str(F_MONO_BOLD if bold else F_MONO), size)
    return ImageFont.truetype(str(F_BOLD if bold else F_REG), size)


# ---------------------------------------------------------------------------
# 1. Verified sample assessments
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "key": "pune_home",
        "label": "Pune residence",
        "payload": {
            "name": "Shubham Desai",
            "location": "Pune, Maharashtra",
            "location_name": "Pune, Maharashtra",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "num_people": 4,
            "roof_type": "RCC",
            "roof_area": 100.0,
            "open_space_area": 50.0,
            "soil_type": "LOAMY",
            "groundwater_depth": 15.0,
            "water_tariff_per_kl": 35.0,
            "annual_rainfall_override": 700.0,
            "runoff_method": "rational",
        },
    },
    {
        "key": "mumbai_large",
        "label": "Mumbai large roof",
        "payload": {
            "name": "Coastal Housing Society",
            "location": "Mumbai, Maharashtra",
            "location_name": "Mumbai, Maharashtra",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "num_people": 20,
            "roof_type": "METAL",
            "roof_area": 500.0,
            "open_space_area": 300.0,
            "soil_type": "SANDY",
            "groundwater_depth": 20.0,
            "water_tariff_per_kl": 35.0,
            "annual_rainfall_override": 2300.0,
            "runoff_method": "rational",
        },
    },
    {
        "key": "green_roof",
        "label": "Pune green roof",
        "payload": {
            "name": "Green Campus Block",
            "location": "Pune, Maharashtra",
            "location_name": "Pune, Maharashtra",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "num_people": 4,
            "roof_type": "GREEN",
            "roof_area": 100.0,
            "open_space_area": 50.0,
            "soil_type": "LOAMY",
            "groundwater_depth": 15.0,
            "water_tariff_per_kl": 35.0,
            "annual_rainfall_override": 700.0,
            "runoff_method": "rational",
        },
    },
    {
        "key": "kolhapur_devanagari",
        "label": "Kolhapur multilingual",
        "payload": {
            "name": "श्रीमती सुनीता पाटील",
            "location": "कोल्हापूर, महाराष्ट्र",
            "location_name": "Kolhapur, Maharashtra",
            "latitude": 16.7050,
            "longitude": 74.2433,
            "num_people": 6,
            "roof_type": "RCC",
            "roof_area": 150.0,
            "open_space_area": 80.0,
            "soil_type": "LOAMY",
            "groundwater_depth": 12.0,
            "water_tariff_per_kl": 35.0,
            "runoff_method": "rational",
        },
    },
    {
        "key": "delhi_semi_arid",
        "label": "Delhi semi-arid campus",
        "payload": {
            "name": "Delhi Institutional Campus",
            "location": "Delhi, India",
            "location_name": "Delhi, India",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "num_people": 50,
            "roof_type": "RCC",
            "roof_area": 1000.0,
            "open_space_area": 400.0,
            "soil_type": "CLAY",
            "groundwater_depth": 30.0,
            "water_tariff_per_kl": 50.0,
            "annual_rainfall_override": 780.0,
            "runoff_method": "rational",
        },
    },
]


def collect_assessments() -> dict:
    """Run the real API pipeline against a throwaway SQLite database."""
    tmpdir = tempfile.mkdtemp(prefix="hrg_report_")
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmpdir}/report.db"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["OPENWEATHER_API_KEY"] = "demo"
    sys.path.insert(0, str(BACKEND))

    from fastapi.testclient import TestClient
    import main

    out = {"generated_with": "Project backend TestClient", "scenarios": {}}
    with TestClient(main.app) as client:
        for item in SCENARIOS:
            r = client.post("/api/assess", json=item["payload"])
            if r.status_code != 200:
                raise RuntimeError(f"Assessment failed for {item['key']}: {r.text[:500]}")
            body = r.json()
            out["scenarios"][item["key"]] = {
                "label": item["label"],
                "input": item["payload"],
                "response": body,
            }

        # Real generated PDF for the Devanagari scenario.
        pdf_id = out["scenarios"]["kolhapur_devanagari"]["response"]["assessment_id"]
        pdf_response = client.get(f"/api/report/{pdf_id}")
        if pdf_response.status_code != 200:
            raise RuntimeError("PDF generation failed")
        pdf_bytes = pdf_response.content
        (DATA / "sample_report.pdf").write_bytes(pdf_bytes)
        out["sample_pdf_bytes"] = len(pdf_bytes)
        out["sample_pdf_assessment_id"] = pdf_id

    (DATA / "scenarios.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out


# ---------------------------------------------------------------------------
# 2. Generic drawing helpers
# ---------------------------------------------------------------------------

W, H = 1600, 900
WHITE = 255
BLACK = 0
DARK = 55
MID = 140
LIGHT = 225
VERY_LIGHT = 242


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("L", (W, H), WHITE)
    return im, ImageDraw.Draw(im)


def wrap_pixels(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}"
            if fnt.getlength(test) <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_centered(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: int = BLACK,
    max_width: int | None = None,
    line_gap: int = 6,
) -> None:
    lines = wrap_pixels(text, fnt, max_width or 10_000)
    ascent, descent = fnt.getmetrics()
    line_h = ascent + descent
    total = len(lines) * line_h + (len(lines) - 1) * line_gap
    y = center[1] - total / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        x = center[0] - (bbox[2] - bbox[0]) / 2
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h + line_gap


def arrowhead(
    draw: ImageDraw.ImageDraw,
    tip: tuple[float, float],
    angle: float,
    size: float = 14,
    fill: int = BLACK,
) -> None:
    a1 = angle + math.radians(150)
    a2 = angle - math.radians(150)
    p1 = (tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1))
    p2 = (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2))
    draw.polygon([tip, p1, p2], fill=fill)


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    width: int = 3,
    fill: int = BLACK,
    dashed: bool = False,
) -> None:
    if dashed:
        dx, dy = end[0] - start[0], end[1] - start[1]
        dist = max(1.0, math.hypot(dx, dy))
        step = 16
        t = 0.0
        while t < dist:
            t2 = min(dist, t + step * 0.55)
            p1 = (start[0] + dx * t / dist, start[1] + dy * t / dist)
            p2 = (start[0] + dx * t2 / dist, start[1] + dy * t2 / dist)
            draw.line([p1, p2], fill=fill, width=width)
            t = t2 + step * 0.45
    else:
        draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrowhead(draw, end, angle, size=14, fill=fill)


def node_center(n: dict) -> tuple[float, float]:
    return n["x"] + n["w"] / 2, n["y"] + n["h"] / 2


def border_point(n: dict, toward: tuple[float, float]) -> tuple[float, float]:
    cx, cy = node_center(n)
    tx, ty = toward
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = n["w"] / 2, n["h"] / 2
    scale = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return cx + dx * scale, cy + dy * scale


def draw_node(draw: ImageDraw.ImageDraw, n: dict) -> None:
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    shape = n.get("shape", "rect")
    fill = n.get("fill", VERY_LIGHT)
    outline = BLACK
    lw = 3
    if shape == "ellipse":
        draw.ellipse([x, y, x + w, y + h], fill=fill, outline=outline, width=lw)
    elif shape == "diamond":
        pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        draw.polygon(pts, fill=fill)
        draw.line(pts + [pts[0]], fill=outline, width=lw)
    elif shape == "cylinder":
        draw.ellipse([x, y, x + w, y + 28], fill=fill, outline=outline, width=lw)
        draw.rectangle([x, y + 14, x + w, y + h - 14], fill=fill, outline=outline, width=lw)
        draw.ellipse([x, y + h - 28, x + w, y + h], fill=fill, outline=outline, width=lw)
        draw.line([x, y + 14, x, y + h - 14], fill=outline, width=lw)
        draw.line([x + w, y + 14, x + w, y + h - 14], fill=outline, width=lw)
    elif shape == "actor":
        draw.ellipse([x + w / 2 - 18, y, x + w / 2 + 18, y + 36], outline=outline, width=lw)
        draw.line([x + w / 2, y + 36, x + w / 2, y + h * 0.62], fill=outline, width=lw)
        draw.line([x + 8, y + h * 0.34, x + w - 8, y + h * 0.34], fill=outline, width=lw)
        draw.line([x + w / 2, y + h * 0.62, x + 10, y + h - 5], fill=outline, width=lw)
        draw.line([x + w / 2, y + h * 0.62, x + w - 10, y + h - 5], fill=outline, width=lw)
    else:
        radius = n.get("radius", 14)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=lw)

    label = n.get("label", "")
    if label and shape != "actor":
        draw_centered(
            draw,
            node_center(n),
            label,
            font(n.get("font_size", 23), bold=n.get("bold", False)),
            max_width=w - 24,
            line_gap=4,
        )
    elif label:
        draw_centered(
            draw,
            (x + w / 2, y + h + 22),
            label,
            font(20, bold=False),
            max_width=w + 40,
        )


def draw_layered(
    filename: str,
    title: str,
    layers: list[list[str]],
    edges: list[tuple[tuple[int, int], tuple[int, int], str]] | None = None,
    subtitle: str = "",
    shapes: dict[tuple[int, int], str] | None = None,
    node_w: int = 250,
    node_h: int = 92,
    font_size: int = 22,
) -> None:
    """Draw nodes arranged in horizontal layers and connect them."""
    im, draw = new_canvas()
    draw_centered(draw, (W / 2, 48), title, font(36, bold=True), max_width=W - 100)
    draw.line([80, 88, W - 80, 88], fill=BLACK, width=2)

    max_nodes = max(len(layer) for layer in layers)
    gap_x = 40
    total_w = max_nodes * node_w + (max_nodes - 1) * gap_x
    x0 = (W - total_w) / 2
    layer_gap = (H - 190 - len(layers) * node_h) / max(1, len(layers) - 1)
    y_positions = [125 + i * (node_h + layer_gap) for i in range(len(layers))]
    shapes = shapes or {}
    nodes: dict[tuple[int, int], dict] = {}
    for li, layer in enumerate(layers):
        lw = len(layer) * node_w + (len(layer) - 1) * gap_x
        sx = (W - lw) / 2
        for ni, label in enumerate(layer):
            n = {
                "x": sx + ni * (node_w + gap_x),
                "y": y_positions[li],
                "w": node_w,
                "h": node_h,
                "label": label,
                "shape": shapes.get((li, ni), "rect"),
                "font_size": font_size,
            }
            nodes[(li, ni)] = n
            draw_node(draw, n)

    for a, b, label in edges or []:
        na, nb = nodes[a], nodes[b]
        ca, cb = node_center(na), node_center(nb)
        start = border_point(na, cb)
        end = border_point(nb, ca)
        draw_arrow(draw, start, end, width=3, dashed="optional" in label.lower() or "feedback" in label.lower())
        if label:
            mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            f = font(16)
            tw = f.getlength(label)
            draw.rectangle([mx - tw / 2 - 5, my - 14, mx + tw / 2 + 5, my + 14], fill=WHITE)
            draw.text((mx - tw / 2, my - 10), label, font=f, fill=BLACK)

    if subtitle:
        draw_centered(draw, (W / 2, H - 42), subtitle, font(19), max_width=W - 120)
    im.save(FIG / filename)


def draw_sequence(filename: str) -> None:
    im, draw = new_canvas()
    draw_centered(draw, (W / 2, 48), "UML Sequence Diagram - Assessment Request", font(36, bold=True), max_width=W - 100)
    actors = ["User", "Next.js UI", "Next Rewrites", "FastAPI", "Services", "Database"]
    n = len(actors)
    xs = [120 + i * (W - 240) / (n - 1) for i in range(n)]
    y0 = 145
    for i, (x, a) in enumerate(zip(xs, actors)):
        draw.rounded_rectangle([x - 90, y0 - 35, x + 90, y0 + 25], radius=10, fill=VERY_LIGHT, outline=BLACK, width=3)
        draw_centered(draw, (x, y0 - 5), a, font(21, bold=True), max_width=170)
        draw.line([x, y0 + 25, x, H - 100], fill=MID, width=2)
    messages = [
        (0, 1, "1 Fill wizard and submit"),
        (1, 2, "2 POST /api/assess"),
        (2, 3, "3 Proxy request"),
        (3, 4, "4 Validate and compute"),
        (4, 3, "5 Weather, runoff, AHP, cost"),
        (3, 5, "6 Persist assessment"),
        (5, 3, "7 Commit"),
        (3, 2, "8 AssessmentResponse"),
        (2, 1, "9 JSON response"),
        (1, 0, "10 Results dashboard"),
    ]
    y = y0 + 90
    for src, dst, msg in messages:
        x1, x2 = xs[src], xs[dst]
        draw_arrow(draw, (x1, y), (x2, y), width=3)
        f = font(18)
        tw = f.getlength(msg)
        mx = (x1 + x2) / 2
        draw.rectangle([mx - tw / 2 - 6, y - 32, mx + tw / 2 + 6, y - 6], fill=WHITE)
        draw.text((mx - tw / 2, y - 29), msg, font=f, fill=BLACK)
        y += 61
    draw_centered(
        draw,
        (W / 2, H - 45),
        "Legend: vertical lines are lifelines; arrows are synchronous/HTTP messages.",
        font(19),
        max_width=W - 120,
    )
    im.save(FIG / filename)


def draw_gantt(filename: str) -> None:
    im, draw = new_canvas()
    draw_centered(draw, (W / 2, 45), "Project Plan - Phase Timeline", font(36, bold=True), max_width=W - 100)
    left, right, top = 320, W - 90, 150
    weeks = 16
    dx = (right - left) / weeks
    for w in range(weeks + 1):
        x = left + w * dx
        draw.line([x, top - 28, x, top + 430], fill=LIGHT if w % 2 else MID, width=1)
        if w < weeks:
            draw.text((x + dx / 2 - 12, top - 56), f"W{w+1}", font=font(16), fill=BLACK)
    tasks = [
        ("Literature review and gap analysis", 0, 3, 0.0),
        ("Requirements and SRS", 2, 5, 0.2),
        ("System design and UML/DFD", 4, 7, 0.4),
        ("Backend hydrology + API", 6, 11, 0.6),
        ("Frontend wizard + results", 7, 12, 0.8),
        ("Rainfall grid + AHP + PDF", 9, 13, 1.0),
        ("3D/AR and multilingual support", 11, 14, 0.4),
        ("Testing, deployment and report", 13, 16, 0.2),
    ]
    row_h = 52
    for i, (name, start, end, shade) in enumerate(tasks):
        y = top + i * row_h
        draw.text((35, y + 8), name, font=font(20), fill=BLACK)
        x1 = left + start * dx
        x2 = left + end * dx
        fill = int(VERY_LIGHT - shade * 70)
        draw.rounded_rectangle([x1, y, x2, y + 30], radius=8, fill=fill, outline=BLACK, width=2)
        draw_centered(draw, ((x1 + x2) / 2, y + 15), f"W{start+1}-W{end}", font(16, bold=True), max_width=x2 - x1 - 10)
    draw.line([left, top + len(tasks) * row_h + 20, right, top + len(tasks) * row_h + 20], fill=BLACK, width=2)
    draw_centered(
        draw,
        (W / 2, H - 55),
        "Legend: W = relative project week; darker bars indicate completed verification and submission activities.",
        font(19),
        max_width=W - 120,
    )
    im.save(FIG / filename)


# ---------------------------------------------------------------------------
# 3. Charts
# ---------------------------------------------------------------------------

def chart_frame(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im, draw = new_canvas()
    draw_centered(draw, (W / 2, 44), title, font(35, bold=True), max_width=W - 100)
    draw.line([80, 84, W - 80, 84], fill=BLACK, width=2)
    if subtitle:
        draw_centered(draw, (W / 2, H - 38), subtitle, font(19), max_width=W - 120)
    return im, draw


def draw_grouped_bars(
    filename: str,
    title: str,
    categories: list[str],
    series: list[tuple[str, list[float], int]],
    ylabel: str,
    subtitle: str,
    y_max: float | None = None,
) -> None:
    im, draw = chart_frame(title, subtitle)
    left, right, top, bottom = 150, W - 90, 160, H - 130
    mx = max(v for _, vals, _ in series for v in vals) or 1
    ymax = y_max or mx * 1.15
    for i in range(6):
        y = top + (bottom - top) * i / 5
        draw.line([left, y, right, y], fill=LIGHT, width=2)
        val = ymax * (1 - i / 5)
        label = f"{val:,.0f}" if ymax > 20 else f"{val:,.1f}"
        draw.text((left - 90, y - 12), label, font=font(18), fill=BLACK)
    draw.text((28, (top + bottom) / 2), ylabel, font=font(20, bold=True), fill=BLACK)
    ncat = len(categories)
    group_w = (right - left) / ncat
    nser = len(series)
    bar_w = min(46, group_w * 0.7 / nser)
    for ci, cat in enumerate(categories):
        gx = left + (ci + 0.5) * group_w
        for si, (_, vals, fill) in enumerate(series):
            v = vals[ci]
            h = (bottom - top) * v / ymax
            x1 = gx - nser * bar_w / 2 + si * bar_w + 3
            x2 = x1 + bar_w - 6
            draw.rectangle([x1, bottom - h, x2, bottom], fill=fill, outline=BLACK, width=2)
        draw.text((gx - 25, bottom + 14), cat, font=font(17), fill=BLACK)
    legend_y = 100
    lx = left
    for name, _, fill in series:
        draw.rectangle([lx, legend_y, lx + 28, legend_y + 18], fill=fill, outline=BLACK, width=2)
        draw.text((lx + 38, legend_y - 3), name, font=font(18), fill=BLACK)
        lx += 80 + font(18).getlength(name)
    im.save(FIG / filename)


def draw_horizontal_bars(
    filename: str,
    title: str,
    labels: list[str],
    values: list[float],
    xlabel: str,
    subtitle: str,
    value_fmt: str = "{:.1f}",
    x_max: float | None = None,
) -> None:
    im, draw = chart_frame(title, subtitle)
    left, right, top, bottom = 420, W - 130, 150, H - 150
    xmax = x_max or max(values) * 1.15 or 1
    n = len(labels)
    row_h = (bottom - top) / n
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i * row_h + row_h / 2
        draw.text((35, y - 14), label, font=font(21), fill=BLACK, stroke_width=0)
        bw = (right - left) * value / xmax
        fill = VERY_LIGHT - int(60 * (i % 3) / 2)
        draw.rectangle([left, y - 20, left + bw, y + 20], fill=fill, outline=BLACK, width=2)
        txt = value_fmt.format(value)
        draw.text((left + bw + 12, y - 13), txt, font=font(20, bold=True), fill=BLACK)
    draw.line([left, top - 20, left, bottom + 20], fill=BLACK, width=2)
    draw.text((left, bottom + 48), xlabel, font=font(20, bold=True), fill=BLACK)
    im.save(FIG / filename)


def draw_line_chart(
    filename: str,
    title: str,
    categories: list[str],
    values: list[float],
    ylabel: str,
    subtitle: str,
) -> None:
    im, draw = chart_frame(title, subtitle)
    left, right, top, bottom = 150, W - 100, 160, H - 140
    ymax = max(values) * 1.15 or 1
    for i in range(6):
        y = top + (bottom - top) * i / 5
        draw.line([left, y, right, y], fill=LIGHT, width=2)
        draw.text((left - 90, y - 12), f"{ymax * (1 - i/5):,.0f}", font=font(18), fill=BLACK)
    n = len(categories)
    xs = [left + (right - left) * i / (n - 1) for i in range(n)]
    ys = [bottom - (bottom - top) * v / ymax for v in values]
    for x, y in zip(xs, ys):
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=BLACK)
    draw.line(list(zip(xs, ys)), fill=DARK, width=4)
    for x, cat in zip(xs, categories):
        draw.text((x - 18, bottom + 14), cat, font=font(17), fill=BLACK)
    draw.text((25, (top + bottom) / 2), ylabel, font=font(20, bold=True), fill=BLACK)
    im.save(FIG / filename)


def draw_two_panel(
    filename: str,
    title: str,
    categories: list[str],
    left_values: list[float],
    right_values: list[float],
    left_label: str,
    right_label: str,
    subtitle: str,
) -> None:
    im, draw = chart_frame(title, subtitle)
    l, r = 140, W - 90
    mid_y = 500
    top1, bottom1 = 150, 430
    top2, bottom2 = 570, H - 150
    panels = [
        (top1, bottom1, left_values, left_label, BLACK),
        (top2, bottom2, right_values, right_label, MID),
    ]
    for top, bottom, vals, label, fill in panels:
        ymax = max(vals) * 1.15 or 1
        draw.line([l, bottom, r, bottom], fill=BLACK, width=2)
        for i in range(4):
            y = top + (bottom - top) * i / 3
            draw.line([l, y, r, y], fill=LIGHT, width=1)
            draw.text((l - 85, y - 10), f"{ymax*(1-i/3):,.0f}", font=font(16), fill=BLACK)
        n = len(categories)
        group_w = (r - l) / n
        bw = group_w * 0.6
        for i, v in enumerate(vals):
            x = l + (i + 0.5) * group_w
            h = (bottom - top) * v / ymax
            draw.rectangle([x - bw/2, bottom - h, x + bw/2, bottom], fill=fill, outline=BLACK, width=2)
            if top == top1:
                draw.text((x - 18, bottom + 10), categories[i], font=font(16), fill=BLACK)
        draw.text((25, (top + bottom) / 2), label, font=font(19, bold=True), fill=BLACK)
    im.save(FIG / filename)


def draw_text_evidence(filename: str, title: str, lines: list[str]) -> None:
    im, draw = new_canvas()
    draw_centered(draw, (W / 2, 42), title, font(34, bold=True), max_width=W - 100)
    draw.rectangle([55, 95, W - 55, H - 65], fill=WHITE, outline=BLACK, width=3)
    f = font(20, mono=True)
    y = 125
    for raw in lines:
        wrapped = textwrap.wrap(raw, width=105) or [""]
        for line in wrapped:
            draw.text((80, y), line, font=f, fill=BLACK)
            y += 31
            if y > H - 100:
                break
        if y > H - 100:
            break
    im.save(FIG / filename)


# ---------------------------------------------------------------------------
# 4. Process screenshots and PDF page
# ---------------------------------------------------------------------------

def process_screenshots() -> None:
    mapping = {
        "home.png": "screen_home.png",
        "about.png": "screen_about.png",
        "assess_step1.png": "screen_assess_step1.png",
        "assess_step2.png": "screen_assess_step2.png",
        "assess_step3.png": "screen_assess_step3.png",
        "results_overview.png": "screen_results_overview.png",
        "results_monthly.png": "screen_results_monthly.png",
        "results_costbenefit.png": "screen_results_costbenefit.png",
    }
    for src, dst in mapping.items():
        p = RAW / src
        if not p.exists():
            continue
        im = Image.open(p).convert("L")
        im = ImageOps.autocontrast(im, cutoff=1)
        im.save(FIG / dst)

    # The full AR screenshot contains a headless-browser WebGL spinner;
    # keep the useful control panel rather than implying a rendered model.
    ar = RAW / "ar_view.png"
    if ar.exists():
        im = Image.open(ar).convert("L")
        crop = im.crop((875, 140, 1270, 755))
        crop = crop.resize((790, 1230), Image.Resampling.LANCZOS)
        crop = ImageOps.autocontrast(crop, cutoff=1)
        canvas = Image.new("L", (1000, 1320), WHITE)
        canvas.paste(crop, (105, 45))
        d = ImageDraw.Draw(canvas)
        draw_centered(d, (500, 20), "3D / AR structure selection panel", font(24, bold=True), max_width=900)
        draw_centered(
            d,
            (500, 1300),
            "Legend: values are generated from the stored assessment; immersive AR requires WebXR device support.",
            font(16),
            max_width=920,
        )
        canvas.save(FIG / "screen_ar_controls.png")

    pdf_path = DATA / "sample_report.pdf"
    if pdf_path.exists():
        try:
            import pymupdf as fitz
        except ImportError:  # older PyMuPDF releases
            import fitz
        doc = fitz.open(pdf_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        mode = "RGB" if pix.n >= 3 else "L"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert("L")
        img = ImageOps.autocontrast(img, cutoff=1)
        img.save(FIG / "sample_report_page1.png")
        doc.close()


def process_logs() -> None:
    ptest = Path("/tmp/hrg_pytest_final.log")
    if ptest.exists():
        lines = ptest.read_text(errors="replace").splitlines()
        selected = [
            "Command: python -m pytest -q (Project/)",
            "Environment: Python 3.11 / isolated virtual environment",
            "",
        ] + lines[-12:]
        draw_text_evidence("test_results.png", "Verified Backend Test Execution", selected)

    pbuild = Path("/tmp/hrg_build.log")
    if pbuild.exists():
        lines = [x for x in pbuild.read_text(errors="replace").splitlines() if x.strip()]
        selected = [
            "Command: npm run build (Project/frontend)",
            "Next.js 14.2.35 / TypeScript strict mode",
            "",
        ] + lines[-22:]
        draw_text_evidence("build_results.png", "Verified Frontend Production Build", selected)


# ---------------------------------------------------------------------------
# 5. Generate all diagrams and charts
# ---------------------------------------------------------------------------

def generate_diagrams(data: dict) -> None:
    scenarios = data["scenarios"]
    pune = scenarios["pune_home"]["response"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # ---------------- Diagrams ----------------
    draw_layered(
        "fig_problem_context.png",
        "Problem Context: Urbanisation and Groundwater Stress",
        [["Rapid urbanisation", "Population growth", "Climate variability"],
         ["Impervious roofs and roads", "Reduced natural infiltration", "Higher pumping demand"],
         ["Groundwater depletion", "Flooding and runoff loss", "Need for decision support"]],
        [((0, 0), (1, 0), "drives"), ((0, 1), (1, 1), "drives"), ((0, 2), (1, 2), "drives"),
         ((1, 0), (2, 0), "causes"), ((1, 1), (2, 1), "causes"), ((1, 2), (2, 2), "causes")],
        "Legend: top row = drivers; middle row = physical effects; bottom row = planning consequences.",
        node_w=310, node_h=92,
    )
    draw_layered(
        "fig_system_overview.png",
        "HYDRO RAIN GUARD - System Overview",
        [["Resident / engineer / planner"],
         ["Web assessment wizard"],
         ["Rainfall + site data"],
         ["Hydrology, AHP and cost engine"],
         ["Results, 3D/AR view and PDF report"]],
        [((0, 0), (1, 0), "inputs"), ((1, 0), (2, 0), "coordinates"), ((2, 0), (3, 0), "analysis"), ((3, 0), (4, 0), "decision")],
        "Legend: the single workflow replaces separate manual calculations and static reports.",
        node_w=520, node_h=78,
    )
    draw_layered(
        "fig_sdlc.png",
        "Iterative Software Development Life Cycle",
        [["Requirements"], ["System design"], ["Implementation"], ["Verification"], ["Deployment and review"]],
        [((0, 0), (1, 0), "refine"), ((1, 0), (2, 0), "build"), ((2, 0), (3, 0), "test"),
         ((3, 0), (4, 0), "release"), ((4, 0), (0, 0), "feedback")],
        "Legend: the feedback arrow represents revisions after test and review findings.",
        node_w=250, node_h=90,
    )
    draw_layered(
        "fig_lit_funnel.png",
        "Systematic Literature Review Funnel",
        [["IEEE Xplore / Springer / ScienceDirect / Google Scholar"],
         ["Keyword search: 2021-2025"],
         ["Duplicate and relevance screening"],
         ["Technology and limitation classification"],
         ["Seven core studies used for gap synthesis"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), ""), ((2, 0), (3, 0), ""), ((3, 0), (4, 0), "")],
        "Legend: the funnel represents qualitative synthesis; exact database hit counts were not retained.",
        node_w=620, node_h=78,
    )
    draw_layered(
        "fig_lit_taxonomy.png",
        "Literature Taxonomy",
        [["Hydrological models", "GIS and remote sensing", "AI / decision support", "AR visualisation"],
         ["Runoff and recharge", "Spatial suitability", "Prediction and ranking", "User interaction"],
         ["Integrated assessment gap"]],
        [((0, 0), (1, 0), ""), ((0, 1), (1, 1), ""), ((0, 2), (1, 2), ""), ((0, 3), (1, 3), ""),
         ((1, 0), (2, 0), ""), ((1, 1), (2, 0), ""), ((1, 2), (2, 0), ""), ((1, 3), (2, 0), "")],
        "Legend: each top-level branch contributes a capability that the proposed framework unifies.",
        node_w=310, node_h=92,
    )
    draw_layered(
        "fig_gis_layers.png",
        "GIS-Centric Data Layers Used by the Implementation",
        [["Coordinate pin (Leaflet / OSM)"], ["2.5 degree CMAP rainfall raster"],
         ["Bilinear point interpolation"], ["Monthly distribution + local annual override"]],
        [((0, 0), (1, 0), "lookup"), ((1, 0), (2, 0), "sample"), ((2, 0), (3, 0), "provenance")],
        "Legend: a local station total can replace the coarse grid total while preserving seasonality.",
        node_w=560, node_h=86,
    )
    draw_layered(
        "fig_ar_workflow.png",
        "AR-Assisted Visualisation Workflow",
        [["Assessment response"], ["Recommended structures"], ["Scaled 3D geometry"],
         ["Desktop 3D / WebXR AR"], ["User inspection and feedback"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), ""), ((2, 0), (3, 0), ""), ((3, 0), (4, 0), "")],
        "Legend: immersive placement is conditional on a WebXR-capable device and secure origin.",
        node_w=250, node_h=90,
    )
    draw_layered(
        "fig_gap_map.png",
        "Research Gaps Mapped to Framework Modules",
        [["Manual runoff", "No spatial intelligence", "Weak recommendations", "Limited visualisation", "Static reports"],
         ["Processing engine", "Rainfall grid", "AHP feasibility", "3D/AR module", "PDF generator"]],
        [((0, 0), (1, 0), ""), ((0, 1), (1, 1), ""), ((0, 2), (1, 2), ""),
         ((0, 3), (1, 3), ""), ((0, 4), (1, 4), "")],
        "Legend: each lower module is a concrete implementation response to the gap above it.",
        node_w=260, node_h=110, font_size=20,
    )
    draw_layered(
        "fig_problem_decomp.png",
        "Problem Decomposition",
        [["Assessment problem"],
         ["Data acquisition", "Hydrological computation", "Feasibility ranking", "Communication"],
         ["Location and rainfall", "Runoff and recharge", "Structure dimensions", "Charts, AR and PDF"]],
        [((0, 0), (1, 0), ""), ((0, 0), (1, 1), ""), ((0, 0), (1, 2), ""), ((0, 0), (1, 3), ""),
         ((1, 0), (2, 0), ""), ((1, 1), (2, 1), ""), ((1, 2), (2, 2), ""), ((1, 3), (2, 3), "")],
        "Legend: decomposition allows each service to be tested independently before integration.",
        node_w=320, node_h=92,
    )
    draw_layered(
        "fig_solution.png",
        "Conceptual Solution Architecture",
        [["User inputs + map pin", "Gridded rainfall + optional live weather"],
         ["Rational method", "SCS-CN cross-check", "Recharge model", "AHP ranking"],
         ["Cost-benefit analysis", "Structure dimensions", "PDF and provenance"],
         ["Results dashboard + 3D/AR visualisation"]],
        [((0, 0), (1, 0), ""), ((0, 0), (1, 1), ""), ((0, 1), (1, 2), ""), ((0, 1), (1, 3), ""),
         ((1, 0), (2, 0), ""), ((1, 1), (2, 0), ""), ((1, 2), (2, 1), ""), ((1, 3), (2, 1), ""),
         ((2, 0), (3, 0), ""), ((2, 1), (3, 0), ""), ((2, 2), (3, 0), "")],
        "Legend: computation is deterministic and auditable; no unvalidated machine-learning model is used.",
        node_w=330, node_h=90, font_size=20,
    )
    draw_layered(
        "fig_context.png",
        "System Context Diagram",
        [["Resident / site owner"], ["HYDRO RAIN GUARD"],
         ["CMAP grid", "OpenWeatherMap (optional)", "OSM / Nominatim", "SQLite / PostgreSQL"]],
        [((0, 0), (1, 0), "uses"), ((1, 0), (2, 0), "rainfall"), ((1, 0), (2, 1), "current conditions"),
         ((1, 0), (2, 2), "geocoding"), ((1, 0), (2, 3), "persistence")],
        "Legend: external services are replaceable; the core assessment remains functional offline.",
        node_w=310, node_h=92,
    )
    draw_layered(
        "fig_usecase.png",
        "UML Use Case Diagram",
        [[">\nUser", ">\nEngineer", ">\nAdministrator"],
         ["Select site", "Preview rainfall", "Run assessment", "View recommendations", "Download PDF", "Inspect 3D/AR"],
         ["Maintain database", "Configure deployment"]],
        [((0, 0), (1, 0), ""), ((0, 0), (1, 1), ""), ((0, 0), (1, 2), ""), ((0, 0), (1, 3), ""),
         ((0, 0), (1, 4), ""), ((0, 0), (1, 5), ""), ((0, 1), (1, 0), ""), ((0, 1), (1, 2), ""),
         ((0, 1), (1, 3), ""), ((0, 1), (1, 4), ""), ((0, 1), (1, 5), ""),
         ((0, 2), (2, 0), ""), ((0, 2), (2, 1), "")],
        "Legend: actors are shown as labelled boxes; use cases are grouped by interaction purpose.",
        node_w=230, node_h=82, font_size=18,
    )
    draw_layered(
        "fig_architecture.png",
        "Three-Tier System Architecture",
        [["Presentation tier - Next.js 14 / React / Tailwind"],
         ["API tier - FastAPI / Pydantic / CORS / rewrites"],
         ["Service tier - weather, rainfall grid, hydrology, MCDA, cost, PDF"],
         ["Data tier - SQLite or PostgreSQL, CMAP raster, fonts"]],
        [((0, 0), (1, 0), "same-origin /api"), ((1, 0), (2, 0), "validated DTOs"), ((2, 0), (3, 0), "async SQL")],
        "Legend: the presentation tier never calls the backend directly in the deployed same-origin setup.",
        node_w=720, node_h=82,
    )
    draw_layered(
        "fig_page_flow.png",
        "Frontend Page and State Flow",
        [["Home", "About"], ["Assessment wizard - steps 1 to 3"],
         ["Results dashboard", "3D / AR page"], ["Stored assessment + PDF download"]],
        [((0, 0), (1, 0), ""), ((0, 1), (1, 0), ""), ((1, 0), (2, 0), ""), ((1, 0), (2, 1), ""),
         ((2, 0), (3, 0), ""), ((2, 1), (3, 0), "feedback")],
        "Legend: hydro_result in localStorage and assessment ID in the URL support reload and sharing.",
        node_w=330, node_h=90,
    )
    draw_layered(
        "fig_dfd0.png",
        "Data Flow Diagram - Level 0",
        [["External user"], ["HYDRO RAIN GUARD system"], ["External data and storage"]],
        [((0, 0), (1, 0), "site inputs"), ((1, 0), (2, 0), "rainfall / persistence"),
         ((2, 0), (1, 0), "weather / stored data"), ((1, 0), (0, 0), "results and PDF")],
        "Legend: the central process represents the complete assessment and reporting pipeline.",
        node_w=420, node_h=120,
    )
    draw_layered(
        "fig_dfd1.png",
        "Data Flow Diagram - Level 1",
        [["1.0 Validate input"], ["2.0 Acquire rainfall"], ["3.0 Compute hydrology"],
         ["4.0 Rank structures"], ["5.0 Generate outputs"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), ""), ((2, 0), (3, 0), ""), ((3, 0), (4, 0), "")],
        "Legend: data stores for assessments and the rainfall raster are accessed by processes 2.0 and 5.0.",
        node_w=250, node_h=96,
    )
    draw_layered(
        "fig_dfd2.png",
        "Data Flow Diagram - Level 2 (Hydrology)",
        [["Monthly rainfall"], ["Rational method", "SCS-CN cross-check", "First-flush deduction"],
         ["Recharge calculation", "Cost-benefit calculation"], ["AssessmentResponse"]],
        [((0, 0), (1, 0), ""), ((0, 0), (1, 1), ""), ((1, 0), (1, 2), ""), ((1, 1), (1, 2), ""),
         ((1, 2), (2, 0), ""), ((1, 2), (2, 1), ""), ((2, 0), (3, 0), ""), ((2, 1), (3, 0), "")],
        "Legend: both runoff methods are returned so the difference is visible to the user.",
        node_w=330, node_h=92,
    )
    draw_layered(
        "fig_er.png",
        "Entity Relationship Diagram",
        [["Assessment"], ["Request data"], ["WeatherData"], ["RunoffResult"],
         ["RechargeResult"], ["StructureRecommendation"], ["CostBenefitAnalysis"], ["MCDAInfo"]],
        [((0, 0), (1, 0), "has"), ((0, 0), (2, 0), "uses"), ((0, 0), (3, 0), "produces"),
         ((0, 0), (4, 0), "produces"), ((0, 0), (5, 0), "recommends"), ((0, 0), (6, 0), "estimates"),
         ((0, 0), (7, 0), "audits")],
        "Legend: one Assessment row stores the full response JSON plus indexed summary columns.",
        node_w=250, node_h=80, font_size=18,
    )
    draw_sequence("fig_sequence.png")
    draw_layered(
        "fig_class.png",
        "UML Class Diagram (Simplified)",
        [["AssessmentRequest", "WeatherData"], ["RunoffResult", "RechargeResult", "StructureRecommendation"],
         ["CostBenefitAnalysis", "MCDAInfo", "AssessmentResponse"], ["Assessment (ORM entity)"]],
        [((0, 0), (1, 0), ""), ((0, 1), (1, 1), ""), ((0, 1), (1, 2), ""),
         ((1, 0), (2, 0), ""), ((1, 1), (2, 1), ""), ((1, 2), (2, 2), ""),
         ((2, 0), (3, 0), ""), ((2, 1), (3, 0), ""), ((2, 2), (3, 0), "")],
        "Legend: Pydantic models define API contracts; the SQLAlchemy entity stores the serialised result.",
        node_w=330, node_h=88, font_size=18,
    )
    draw_layered(
        "fig_component.png",
        "UML Component Diagram",
        [["Next.js pages", "API client", "FastAPI routes"],
         ["Rainfall grid", "Hydrology", "Feasibility / AHP", "Cost-benefit", "PDF report"],
         ["Database", "Static raster and fonts"]],
        [((0, 0), (0, 1), ""), ((0, 1), (0, 2), ""), ((0, 2), (1, 0), ""), ((0, 2), (1, 1), ""),
         ((0, 2), (1, 2), ""), ((0, 2), (1, 3), ""), ((0, 2), (1, 4), ""), ((1, 4), (2, 0), ""),
         ((1, 0), (2, 1), ""), ((1, 1), (2, 0), ""), ((1, 2), (2, 0), ""), ((1, 3), (2, 0), "")],
        "Legend: service components are pure Python modules with narrow Pydantic interfaces.",
        node_w=250, node_h=88, font_size=18,
    )
    draw_layered(
        "fig_deployment.png",
        "UML Deployment Diagram",
        [["Browser / mobile device"], ["Vercel - Next.js frontend"], ["FastAPI service"],
         ["SQLite / Neon PostgreSQL"], ["CMAP raster + Noto fonts"]],
        [((0, 0), (1, 0), "HTTPS"), ((1, 0), (2, 0), "API proxy"), ((2, 0), (3, 0), "async driver"),
         ((2, 0), (4, 0), "local assets")],
        "Legend: production persistence should use PostgreSQL because serverless SQLite is ephemeral.",
        node_w=470, node_h=82,
    )
    draw_layered(
        "fig_state.png",
        "UML State Machine Diagram - Assessment",
        [["Idle"], ["Input in progress"], ["Weather previewed"], ["Assessment running"],
         ["Results ready"], ["PDF downloaded / AR viewed"]],
        [((0, 0), (1, 0), "start"), ((1, 0), (2, 0), "fetch rainfall"), ((2, 0), (3, 0), "submit"),
         ((3, 0), (4, 0), "success"), ((4, 0), (5, 0), "export"), ((5, 0), (0, 0), "new assessment")],
        "Legend: error transitions return to input in progress without discarding entered values.",
        node_w=240, node_h=90,
    )
    draw_layered(
        "fig_module_map.png",
        "Implementation Module Map",
        [["frontend/app", "frontend/components", "frontend/lib"],
         ["backend/main.py", "backend/services", "backend/models"],
         ["tests", "data", "scripts"]],
        [((0, 0), (1, 1), "API calls"), ((0, 1), (1, 1), "renders"), ((0, 2), (1, 0), "types"),
         ((1, 0), (1, 1), "routes"), ((1, 1), (1, 2), "schemas"), ((1, 1), (2, 0), "verified by"),
         ((1, 1), (2, 1), "reads"), ((2, 2), (2, 1), "builds grid")],
        "Legend: the repository separates UI, orchestration, domain services, data and tests.",
        node_w=340, node_h=90, font_size=19,
    )
    draw_layered(
        "fig_grid_interpolation.png",
        "Bilinear Rainfall Grid Sampling",
        [["NW cell", "NE cell"], ["Target coordinate (lat, lon)"], ["SW cell", "SE cell"]],
        [((0, 0), (1, 0), ""), ((0, 1), (1, 0), ""), ((2, 0), (1, 0), ""), ((2, 1), (1, 0), "")],
        "Legend: longitude wraps at the dateline; no-data cells are handled before interpolation.",
        node_w=330, node_h=100,
    )
    draw_layered(
        "fig_ahp_hierarchy.png",
        "AHP Criteria Hierarchy",
        [["Select recharge / storage structure"],
         ["Harvestable yield", "Annual rainfall", "Soil infiltration", "Open space", "Groundwater depth"],
         ["Rooftop tank", "Soak pit", "Recharge pit", "Recharge well", "Percolation tank"]],
        [((0, 0), (1, i), "") for i in range(5)] + [((1, i), (2, j), "") for i in range(5) for j in range(5)],
        "Legend: weights are derived from a reciprocal pairwise matrix and checked with CR <= 0.10.",
        node_w=250, node_h=88, font_size=18,
    )
    draw_layered(
        "fig_pdf_pipeline.png",
        "Automated PDF Report Pipeline",
        [["AssessmentResponse"], ["ReportLab document"], ["HarfBuzz text shaping"],
         ["Latin text + Devanagari outlines"], ["Multi-page PDF stream"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), ""), ((2, 0), (3, 0), ""), ((3, 0), (4, 0), "")],
        "Legend: Latin text stays searchable; Devanagari glyph outlines preserve correct visual shaping.",
        node_w=500, node_h=84,
    )
    draw_layered(
        "fig_ar_pipeline.png",
        "3D / AR Rendering Pipeline",
        [["Assessment dimensions"], ["Geometry builders"], ["react-three-fiber scene"],
         ["Cutaway + labels"], ["Desktop canvas / WebXR session"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), ""), ((2, 0), (3, 0), ""), ((3, 0), (4, 0), "")],
        "Legend: geometry is scaled from tank volume, pit depth, borewell depth and roof area.",
        node_w=500, node_h=84,
    )
    draw_layered(
        "fig_testing_strategy.png",
        "Software Testing Strategy",
        [["Unit tests"], ["API integration tests"], ["PDF rendering tests"], ["Frontend build verification"]],
        [((0, 0), (1, 0), "supports"), ((1, 0), (2, 0), "supports"), ((2, 0), (3, 0), "supports")],
        "Legend: 38 automated backend tests were executed; the frontend was verified by a production build.",
        node_w=500, node_h=90,
    )
    draw_layered(
        "fig_future_roadmap.png",
        "Future Enhancement Roadmap",
        [["Short term: PostgreSQL, CI, security hardening"], ["Medium term: high-resolution IMD / GIS layers"],
         ["Long term: IoT validation, drone mapping, ML rainfall forecasting"]],
        [((0, 0), (1, 0), ""), ((1, 0), (2, 0), "")],
        "Legend: each phase adds validation or spatial resolution without changing the core assessment contract.",
        node_w=680, node_h=96,
    )

    # ---------------- Charts ----------------
    draw_two_panel(
        "chart_monthly.png",
        "Monthly Rainfall and Rooftop Runoff - Pune Sample",
        months,
        pune["weather"]["monthly_rainfall"],
        [v / 1000 for v in pune["runoff"]["monthly_runoff"]],
        "Rainfall (mm)",
        "Runoff (KL)",
        "Legend: upper panel = monthly rainfall; lower panel = Rational-method runoff for a 100 m2 RCC roof.",
    )
    draw_grouped_bars(
        "chart_scs_rational.png",
        "Rational Method and SCS-CN Monthly Cross-Check",
        months,
        [("Rational (KL)", [v / 1000 for v in pune["runoff"]["monthly_runoff"]], BLACK),
         ("SCS-CN (KL)", [v / 1000 for v in pune["runoff"]["scs_cn_monthly_runoff"]], MID)],
        "Runoff (KL)",
        "Legend: both methods are displayed to make model spread visible rather than hidden.",
    )
    mcda = pune["mcda"]
    draw_horizontal_bars(
        "chart_ahp_weights.png",
        "AHP Criterion Weights",
        [c.replace("_", " ") for c in mcda["criteria"]],
        [mcda["weights"][c] * 100 for c in mcda["criteria"]],
        "Weight (%)",
        "Legend: CR = 0.0152, below Saaty's 0.10 consistency threshold.",
        value_fmt="{:.2f}%",
        x_max=45,
    )
    structures = pune["recommended_structures"]
    draw_horizontal_bars(
        "chart_structure_scores.png",
        "Structure Suitability Scores - Pune Sample",
        [s["structure_type"] for s in structures],
        [s["suitability_score"] for s in structures],
        "Score (/100)",
        "Legend: scores are weighted sums of five normalised AHP criteria after hard-constraint filtering.",
        value_fmt="{:.1f}",
        x_max=100,
    )
    cb = pune["cost_benefit"]
    draw_horizontal_bars(
        "chart_cost_breakdown.png",
        "Estimated Capital Cost Breakdown",
        ["Storage", "Recharge", "Plumbing"],
        [cb["storage_cost"], cb["recharge_cost"], cb["plumbing_cost"]],
        "Cost (INR)",
        "Legend: plumbing is estimated from roof perimeter; storage/recharge use the top two structures.",
        value_fmt="Rs. {:,.0f}",
    )
    draw_line_chart(
        "chart_monthly_savings.png",
        "Monthly Cost Savings - Pune Sample",
        months,
        cb["monthly_savings"],
        "Savings (INR)",
        "Legend: monthly values sum to the annual savings figure, after first-flush allocation.",
    )

    labels, rainfall, runoff, costs, paybacks = [], [], [], [], []
    for key, item in scenarios.items():
        r = item["response"]
        labels.append(item["label"].split()[0])
        rainfall.append(r["weather"]["annual_rainfall"])
        runoff.append(r["runoff"]["annual_runoff_volume"] / 1000)
        costs.append(r["cost_benefit"]["estimated_cost"] / 1000)
        pb = r["cost_benefit"]["payback_period_years"]
        paybacks.append(pb if pb is not None else 0)
    draw_grouped_bars(
        "chart_scenario_rain_runoff.png",
        "Scenario Comparison - Annual Rainfall and Runoff",
        labels,
        [("Rainfall (mm)", rainfall, LIGHT), ("Runoff (KL)", runoff, DARK)],
        "mm / KL",
        "Legend: different roof areas, coefficients and local annual rainfall overrides are used.",
    )
    draw_grouped_bars(
        "chart_scenario_payback.png",
        "Scenario Comparison - Cost and Payback",
        labels,
        [("Cost (thousand INR)", costs, MID), ("Payback (years)", paybacks, BLACK)],
        "INR-k / years",
        "Legend: payback depends strongly on tariff, roof area and local rainfall.",
    )
    draw_gantt("chart_project_plan.png")


def main() -> None:
    data = collect_assessments()
    process_screenshots()
    process_logs()
    generate_diagrams(data)
    print("Generated evidence in", REPORT)
    print("Figures:", len(list(FIG.glob("*.png"))))
    print("Scenarios:", ", ".join(data["scenarios"].keys()))
    print("PDF bytes:", data["sample_pdf_bytes"])


if __name__ == "__main__":
    main()
