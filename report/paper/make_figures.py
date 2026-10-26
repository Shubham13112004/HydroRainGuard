#!/usr/bin/env python3
"""Colour figures for the IEEE conference paper.

Every figure is rendered for a single IEEE column (87 mm wide) at 400 dpi, so
the 6-8 pt labels stay readable in print. Output: report/paper/figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "report" / "figures_raw"
OUT = ROOT / "report" / "paper" / "figures"
EXTRA = ROOT / "report" / "paper" / "figures_extra"   # not used in the paper
DATA = json.loads((ROOT / "report" / "data" / "scenarios.json").read_text())
S = DATA["scenarios"]

TEAL = "#0F766E"
TEAL_L = "#2DD4BF"
GREEN = "#15803D"
LIME = "#84CC16"
BLUE = "#1D4ED8"
SKY = "#0EA5E9"
AMBER = "#D97706"
ROSE = "#BE123C"
SLATE = "#0F172A"
GREY = "#64748B"
LIGHT = "#E2E8F0"
PAPER = "#FFFFFF"

COL = 87 / 25.4  # inches

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 6.5,
    "axes.linewidth": 0.6,
    "axes.edgecolor": "#94A3B8",
    "axes.labelcolor": SLATE,
    "xtick.color": SLATE,
    "ytick.color": SLATE,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "axes.titlesize": 7,
    "axes.titleweight": "bold",
    "savefig.dpi": 400,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "legend.frameon": False,
    "legend.fontsize": 5.8,
})


def clean(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color="#E2E8F0", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.02, facecolor=PAPER)
    plt.close(fig)
    print("wrote", name)


# --------------------------------------------------------------------------- #
# 1. Screenshots (trimmed and colour-corrected copies)
# --------------------------------------------------------------------------- #
def screenshots():
    for src, dst in [
        ("assess_step2.png", "fig3_wizard.png"),
        ("results_overview.png", "fig4_results.png"),
        ("results_costbenefit.png", "fig8_cost.png"),
    ]:
        im = Image.open(RAW / src).convert("RGB")
        w, h = im.size
        # keep only the app area, dropping the empty browser band if present
        im = im.crop((0, 0, w, h))
        im = im.resize((1400, int(1400 * h / w)), Image.LANCZOS)
        OUT.mkdir(parents=True, exist_ok=True)
        im.save(OUT / dst, optimize=True)
        print("wrote", dst, im.size)


# --------------------------------------------------------------------------- #
# 2. Architecture
# --------------------------------------------------------------------------- #
def architecture():
    """Four stacked layers on a 100 x 100 canvas (single IEEE column)."""
    fig, ax = plt.subplots(figsize=(COL, 2.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def band(y, h, label, colour, fill):
        ax.add_patch(FancyBboxPatch((1.2, y), 97.6, h, boxstyle="round,pad=0.3,rounding_size=1.5",
                                    linewidth=0.7, edgecolor=colour, facecolor=fill, zorder=1))
        ax.text(3.0, y + h - 3.0, label, fontsize=4.6, color=colour, fontweight="bold",
                va="center", ha="left", zorder=3)
        return y + 1.6, h - 7.6          # inner box origin and height

    def box(x, y, w, h, text, colour, fill, bold=True, fs=5.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.3",
                                    linewidth=0.7, edgecolor=colour, facecolor=fill, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=SLATE,
                fontweight="bold" if bold else "normal", zorder=3, linespacing=1.3)

    iy, ih = band(74, 24, "CLIENT  ·  Next.js 14 App Router", BLUE, "#EFF6FF")
    box(3.5, iy, 29, ih, "Assessment\nwizard", BLUE, "#DBEAFE")
    box(35.5, iy, 29, ih, "Leaflet map\n+ Nominatim", BLUE, "#DBEAFE")
    box(67.5, iy, 29, ih, "Charts, XR\nscene, PDF", BLUE, "#DBEAFE")

    iy, ih = band(48, 21, "API  ·  FastAPI + Pydantic v2", TEAL, "#ECFDF5")
    box(3.5, iy, 29, ih, "POST\n/api/assess", TEAL, "#CCFBF1")
    box(35.5, iy, 29, ih, "GET\n/api/weather", TEAL, "#CCFBF1")
    box(67.5, iy, 29, ih, "GET\n/api/report", TEAL, "#CCFBF1")

    iy, ih = band(24, 19, "DOMAIN SERVICES  ·  tested pure functions", GREEN, "#F0FDF4")
    for i, txt in enumerate(["Rational", "SCS-CN", "Recharge", "AHP", "Cost", "PDF"]):
        box(3.5 + i * 15.7, iy, 14.4, ih, txt, GREEN, "#DCFCE7", True, 4.9)

    iy, ih = band(1, 18, "DATA & ASSETS", AMBER, "#FFFBEB")
    box(3.5, iy, 29, ih, "SQLite\nassessments", AMBER, "#FEF3C7", False, 4.9)
    box(35.5, iy, 29, ih, "CMAP grid\n72 × 144", AMBER, "#FEF3C7", False, 4.9)
    box(67.5, iy, 29, ih, "Noto fonts\n(Devanagari)", AMBER, "#FEF3C7", False, 4.9)

    for top, bottom in ((74.0, 69.6), (48.0, 43.5), (24.0, 19.5)):
        ax.add_patch(FancyArrowPatch((50, top), (50, bottom), arrowstyle="-|>", mutation_scale=6,
                                     linewidth=0.8, color=GREY, zorder=4))
    save(fig, "fig2_arch.png")


# --------------------------------------------------------------------------- #
# 3. Monthly water balance
# --------------------------------------------------------------------------- #
def monthly():
    p = S["pune_home"]["response"]
    rain = np.array(p["weather"]["monthly_rainfall"])
    runoff = np.array(p["runoff"]["monthly_runoff"]) / 1000.0  # kL
    scs = np.array(p["runoff"]["scs_cn_monthly_runoff"]) / 1000.0
    months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    x = np.arange(12)

    fig, ax = plt.subplots(figsize=(COL, 2.05))
    ax.bar(x, rain, width=0.68, color=SKY, alpha=0.35, edgecolor=SKY, linewidth=0.5,
           label="Rainfall (mm)", zorder=2)
    ax.set_ylabel("Rainfall (mm)", color=SKY)
    ax.set_ylim(0, 250)
    clean(ax)
    ax.set_xticks(x, months)
    ax.set_xlabel("Month")

    ax2 = ax.twinx()
    ax2.fill_between(x, runoff, color=TEAL_L, alpha=0.28, zorder=1)
    ax2.plot(x, runoff, color=TEAL, linewidth=1.2, marker="o", markersize=2.4,
             label="Rational runoff", zorder=3)
    ax2.plot(x, scs, color=ROSE, linewidth=1.0, linestyle=(0, (3, 1.6)), marker="s",
             markersize=2.0, label="SCS-CN runoff", zorder=3)
    ax2.set_ylabel("Runoff (kL)", color=TEAL)
    ax2.set_ylim(0, 21)
    for side in ("top", "left"):
        ax2.spines[side].set_visible(False)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", handlelength=1.4, borderaxespad=0.2,
              ncol=3, fontsize=5.0, columnspacing=0.9, handletextpad=0.4)
    jjas = runoff[5:9].sum() / runoff.sum() * 100
    jjas_caption = round(float(jjas))
    save(fig, "fig5_monthly.png")


# --------------------------------------------------------------------------- #
# 4. AHP weights and structure scores
# --------------------------------------------------------------------------- #
def ahp():
    p = S["pune_home"]["response"]
    w = p["mcda"]["weights"]
    names = {
        "harvestable_yield": "Harvestable yield",
        "annual_rainfall": "Annual rainfall",
        "soil_infiltration": "Soil infiltration",
        "open_space": "Open space",
        "groundwater_depth": "Water-table depth",
    }
    order = sorted(w, key=w.get, reverse=True)
    labels = [names[k] for k in order]
    vals = [w[k] for k in order]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(COL, 2.0),
                                  gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.5})
    colours = ["#0F766E", "#0D9488", "#14B8A6", "#2DD4BF", "#5EEAD4"]
    ax.barh(range(len(vals))[::-1], vals, color=colours, height=0.62, zorder=2)
    ax.set_yticks(range(len(vals))[::-1], labels)
    ax.set_xlim(0, 0.52)
    ax.set_xlabel("AHP weight")
    clean(ax, "x")
    for i, v in enumerate(vals):
        ax.text(v + 0.012, len(vals) - 1 - i, f"{v:.3f}", va="center", fontsize=5.4, color=SLATE)
    ax.set_title("(a) Criterion weights", loc="left", pad=3)
    ax.set_xlabel("AHP weight", fontsize=5.6)
    ax.text(0.98, 0.06, f"$\\lambda_{{max}}$ = {p['mcda']['lambda_max']:.3f}\n"
                        f"CR = {p['mcda']['consistency_ratio']:.3f}",
            transform=ax.transAxes, fontsize=4.8, color=GREY, va="bottom", ha="right",
            linespacing=1.3)

    st = p["recommended_structures"]
    short = {
        "Rooftop Storage Tank": "Storage tank",
        "Soak Pit / French Drain": "Soak pit",
        "Recharge Pit": "Recharge pit",
        "Recharge Well / Borewell Recharge": "Recharge well",
    }
    lab = [short.get(s["structure_type"], s["structure_type"]) for s in st]
    sc = [s["suitability_score"] for s in st]
    bars = ax2.bar(range(len(sc)), sc, color=[TEAL, "#0D9488", "#14B8A6", "#5EEAD4", "#99F6E4"][:len(sc)],
                   width=0.62, zorder=2)
    ax2.set_xticks(range(len(sc)), lab, fontsize=4.6, rotation=30, ha="right",
                   rotation_mode="anchor")
    ax2.set_ylim(0, 110)
    ax2.set_ylabel("Suitability (0–100)")
    clean(ax2)
    for b, v in zip(bars, sc):
        ax2.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v:.0f}", ha="center", fontsize=5.4,
                 fontweight="bold", color=SLATE)
    ax2.set_title("(b) Ranked structures", loc="left", pad=3)
    EXTRA.mkdir(parents=True, exist_ok=True)
    fig.savefig(EXTRA / "fig6_ahp_weights.png", bbox_inches="tight", pad_inches=0.02,
                facecolor=PAPER)
    plt.close(fig)
    print("wrote figures_extra/fig6_ahp_weights.png")


# --------------------------------------------------------------------------- #
# 5. Scenario comparison
# --------------------------------------------------------------------------- #
def scenarios():
    keys = ["pune_home", "green_roof", "kolhapur_devanagari", "mumbai_large", "delhi_semi_arid"]
    labels = ["Pune\nRCC 100 m²", "Pune\ngreen 100 m²", "Kolhapur\nRCC 150 m²",
              "Mumbai\nmetal 500 m²", "Delhi\nRCC 1000 m²"]
    runoff, harv, pay = [], [], []
    for k in keys:
        r = S[k]["response"]
        area = r["request"]["roof_area"]
        runoff.append(r["runoff"]["annual_runoff_volume"] / area)
        harv.append(r["runoff"]["harvestable_volume"] / area)
        pay.append(r["cost_benefit"]["payback_period_years"])
    x = np.arange(len(keys))
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(COL, 2.75), gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.62})

    ax.bar(x - 0.19, runoff, width=0.36, color=TEAL, label="Runoff", zorder=2)
    ax.bar(x + 0.19, harv, width=0.36, color=LIME, label="Harvestable", zorder=2)
    ax.set_xticks(x, [""] * len(x))
    ax.set_ylabel("L per m² of roof")
    ax.set_ylim(0, 2400)
    clean(ax)
    ax.legend(loc="upper right", ncol=2, handlelength=1.2, columnspacing=1.0, borderaxespad=0.2)
    for xi, v in zip(x, harv):
        ax.text(xi + 0.19, v + 55, f"{v:.0f}", ha="center", fontsize=4.9, color="#3F6212")
    ax.set_title("(a) Normalised annual yield", loc="left", pad=3)

    vals = [p if p is not None else 0.0 for p in pay]
    cols = [GREEN if (p is not None and p <= 10) else (AMBER if (p is not None and p <= 25) else ROSE)
            for p in pay]
    bars = ax2.bar(x, vals, width=0.55, color=cols, zorder=2)
    ax2.set_xticks(x, labels, fontsize=5.2)
    ax2.set_ylabel("Payback (years)")
    ax2.set_ylim(0, 75)
    clean(ax2)
    for b, p in zip(bars, pay):
        if p is None:
            ax2.text(b.get_x() + b.get_width() / 2, 4, "not repaid\nwithin 25 yr",
                     ha="center", va="bottom", fontsize=4.6, color=ROSE, linespacing=1.2)
        else:
            ax2.text(b.get_x() + b.get_width() / 2, min(66, b.get_height() + 2.5), f"{p:.0f}",
                     ha="center", fontsize=5.0, fontweight="bold", color=SLATE)
    ax2.axhline(25, color=GREY, linewidth=0.6, linestyle=(0, (2, 2)))
    ax2.text(4.42, 27, "25 yr", fontsize=4.7, color=GREY, ha="right")
    ax2.set_title("(b) Simple payback at the local tariff", loc="left", pad=3)
    save(fig, "fig9_scenarios.png")


def xr_panel():
    """Right-hand panel of the 3D/AR page: ranked structures and dimensions."""
    im = Image.open(RAW / "ar_view.png").convert("RGB")
    w, h = im.size
    crop = im.crop((int(w * 0.628), int(h * 0.16), int(w * 0.935), int(h * 0.60)))
    crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
    crop.save(OUT / "fig7_xr_panel.png", optimize=True)
    print("wrote fig7_xr_panel.png", crop.size)


def main() -> None:
    screenshots()
    xr_panel()
    architecture()
    monthly()
    ahp()
    scenarios()


if __name__ == "__main__":
    main()
