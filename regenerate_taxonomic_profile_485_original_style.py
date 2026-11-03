#!/usr/bin/env python3
"""Regenerate the original four-panel SCIE-Q1 lollipop taxonomy plot for n=485.

Source: the author-frozen Phase A technical-synthesis corpus (NOT Compiled Files.xlsx).
Visual design: original 492-study figure's four panels, category ordering, panel
colours, lollipop stems/dots, serif text, pale grids, and count/share labels.

Run from the WSL project root:
    python regenerate_taxonomic_profile_485_original_style.py \
        --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \
        --output-dir Figures_485 --dpi 600

Exports PDF, SVG, PNG, TIFF (600 dpi default) and one traceable count table.
The frozen files are read only. The script fails before drawing if the source
SHA-256 fingerprints, membership, category domains, totals or frozen summary
are inconsistent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # works on headless WSL/SSH and local desktops
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

STUDIES = 485
STEM = "Figure12_Taxonomic_Profile_485_Original_Style"

# Keep the same four-panel arrangement and category sequence as the original.
PANELS = [
    {
        "letter": "A", "field": "Target_Primary",
        "title": "A. Primary forecasting targets", "colour": "#347FA6",
        "order": ["Price", "Direction", "Multi_Target", "Return", "Trend_Regime", "Volatility", "Not_Reported"],
        "names": {"Price": "Price level", "Direction": "Direction", "Multi_Target": "Multi-target",
                  "Return": "Return", "Trend_Regime": "Trend or regime", "Volatility": "Volatility",
                  "Not_Reported": "Not reported"},
        "xlim": 440, "tick": 100,
        "expected": {"Price":378,"Direction":47,"Multi_Target":32,"Return":17,"Trend_Regime":8,"Volatility":1,"Not_Reported":2},
    },
    {
        "letter": "B", "field": "Forecast_Horizon",
        "title": "B. Standardized forecast horizons", "colour": "#4C9972",
        "order": ["Intraday", "One_Day", "Short_Multiday_2_5", "Weekly_6_10", "Monthly_11_22",
                  "Longer_Than_Monthly", "Multiple_Horizons", "Not_Reported"],
        "names": {"Intraday": "Intraday", "One_Day": "One trading day",
                  "Short_Multiday_2_5": "2–5 trading days", "Weekly_6_10": "6–10 trading days",
                  "Monthly_11_22": "11–22 trading days", "Longer_Than_Monthly": "Longer than one month",
                  "Multiple_Horizons": "Multiple horizons", "Not_Reported": "Not reported"},
        "xlim": 374, "tick": 50,
        "expected": {"Intraday":17,"One_Day":79,"Short_Multiday_2_5":4,"Weekly_6_10":11,
                     "Monthly_11_22":4,"Longer_Than_Monthly":9,"Multiple_Horizons":44,"Not_Reported":317},
    },
    {
        "letter": "C", "field": "Learning_Formulation",
        "title": "C. Learning formulations", "colour": "#C86E51",
        "order": ["Regression", "Binary_Classification", "Multiclass_Classification", "Probabilistic",
                  "Multi_Task", "Hybrid_Other", "Not_Reported"],
        "names": {"Regression": "Regression", "Binary_Classification": "Binary classification",
                  "Multiclass_Classification": "Multiclass classification",
                  "Probabilistic": "Probabilistic forecasting", "Multi_Task": "Multi-task learning",
                  "Hybrid_Other": "Hybrid or other", "Not_Reported": "Not reported"},
        "xlim": 455, "tick": 100,
        "expected": {"Regression":393,"Binary_Classification":43,"Multiclass_Classification":6,
                     "Probabilistic":5,"Multi_Task":28,"Hybrid_Other":7,"Not_Reported":3},
    },
    {
        "letter": "D", "field": "Asset_Scope",
        "title": "D. Asset scope", "colour": "#826BA9",
        "order": ["Single_Stock", "Multiple_Stocks", "Stock_Index", "Multiple_Indices", "Portfolio",
                  "Cross_Market", "Not_Reported"],
        "names": {"Single_Stock": "Single stock", "Multiple_Stocks": "Multiple stocks",
                  "Stock_Index": "Single stock index", "Multiple_Indices": "Multiple indices",
                  "Portfolio": "Portfolio", "Cross_Market": "Cross-market", "Not_Reported": "Not reported"},
        "xlim": 185, "tick": 25,
        "expected": {"Single_Stock":103,"Multiple_Stocks":153,"Stock_Index":62,
                     "Multiple_Indices":19,"Portfolio":1,"Cross_Market":12,"Not_Reported":135},
    },
]

NEUTRAL = "#AAB1B9"
TEXT = "#252525"
GRID = "#D7DADD"


def get_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path,
                   default=Path("PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--show", action="store_true", help="Open the figure after saving, if a display is available")
    return p.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def verify_and_count(folder: Path) -> list[tuple[dict, dict[str, int]]]:
    manifest_path = folder / "Final_Freeze_Manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_corpus_frozen") is not True or manifest.get("retained_studies") != STUDIES:
        raise RuntimeError("Manifest does not identify the frozen 485-study technical corpus")

    for name in ("Technical_Register_485_FROZEN.csv", "Manuscript_Category_Counts_FROZEN.csv"):
        path = folder / name
        expected_digest = manifest["output_sha256"].get(name)
        if expected_digest is None or sha256(path) != expected_digest:
            raise RuntimeError(f"SHA-256 mismatch for {name}; the frozen source must not be changed")

    headers, rows = read_csv(folder / "Technical_Register_485_FROZEN.csv")
    summary_headers, summary = read_csv(folder / "Manuscript_Category_Counts_FROZEN.csv")
    if len(rows) != STUDIES or "Paper_ID" not in headers:
        raise RuntimeError("The frozen register does not contain exactly 485 studies")
    identifiers = [r["Paper_ID"] for r in rows]
    if len(set(identifiers)) != STUDIES or any(not sid for sid in identifiers):
        raise RuntimeError("Missing or duplicated Paper_ID")

    required = {"Field", "Category", "Count", "Denominator"}
    if not required.issubset(summary_headers):
        raise RuntimeError("Frozen category summary has an unrecognized schema")
    lookup = {(r["Field"],r["Category"]): r for r in summary}
    if len(lookup) != len(summary):
        raise RuntimeError("Duplicate summary category entries")

    result = []
    for panel in PANELS:
        field = panel["field"]
        if field not in headers:
            raise RuntimeError(f"Missing required frozen field {field}")
        values = Counter(r[field].strip() for r in rows)
        if set(values) != set(panel["order"]):
            raise RuntimeError(f"Unexpected or missing categories in {field}: {values}")
        observed = {key: int(values.get(key, 0)) for key in panel["order"]}
        if observed != panel["expected"]:
            raise RuntimeError(f"Frozen counts differ from audited Phase A values ({field}): {observed}")
        if sum(observed.values()) != STUDIES:
            raise RuntimeError(f"Category totals do not reconcile: {field}")
        for category,count in observed.items():
            key = (field, category)
            if key not in lookup:
                raise RuntimeError(f"Missing frozen summary row {key}")
            source = lookup[key]
            if int(source["Count"]) != count or int(source["Denominator"]) != STUDIES:
                raise RuntimeError(f"Frozen summary mismatch for {key}")
        result.append((panel, observed))
    return result


def configure_typography() -> None:
    plt.rcParams.update({
        # Closely follows the serif typography of the previously published plot.
        "font.family": "serif",
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "font.size": 10.4,
        "axes.titlesize": 12.2,
        "axes.labelsize": 10.7,
        "xtick.labelsize": 9.7,
        "ytick.labelsize": 10.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",  # preserve editable SVG text
        "savefig.facecolor": "white",
    })


def draw_panel(ax: plt.Axes, cfg: dict, counts: dict[str, int]) -> None:
    order, colour = cfg["order"], cfg["colour"]
    positions = np.arange(len(order))
    values = [counts[key] for key in order]
    colours = [NEUTRAL if key == "Not_Reported" else colour for key in order]

    for y, value, c in zip(positions, values, colours):
        ax.hlines(y, 0, value, color=c, linewidth=2.1, alpha=0.88, zorder=2)
        ax.scatter(value, y, s=58, color=c, edgecolor="white", linewidth=0.75, zorder=3)
        ax.text(value + cfg["xlim"] * 0.016, y, f"{value} ({100*value/STUDIES:.1f}%)",
                ha="left", va="center", fontsize=9.55, color=TEXT, clip_on=False, zorder=4)

    ax.set_yticks(positions)
    ax.set_yticklabels([cfg["names"][key] for key in order])
    ax.invert_yaxis()
    ax.set_xlim(0, cfg["xlim"])
    ax.xaxis.set_major_locator(MultipleLocator(cfg["tick"]))
    ax.set_xlabel("Number of studies", labelpad=8)
    ax.set_title(cfg["title"], loc="left", fontweight="bold", pad=11, fontsize=12.2)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=GRID, linestyle=(0, (2, 3)), linewidth=0.8, alpha=0.70)
    ax.yaxis.grid(False)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#707070")
    ax.spines["bottom"].set_linewidth(0.9)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.tick_params(axis="x", direction="out", length=4, width=0.8, color="#707070")


def main() -> None:
    args = get_args()
    if args.dpi < 72:
        raise ValueError("DPI must be >=72")
    groups = verify_and_count(args.frozen_dir)
    configure_typography()

    # Original 2x2 arrangement, enlarged proportionally for legible journal PDFs.
    fig = plt.figure(figsize=(11.2, 8.6), facecolor="white")
    grid = fig.add_gridspec(2, 2, left=0.20, right=0.946, top=0.930,
                            bottom=0.085, wspace=0.82, hspace=0.41)
    axes = [fig.add_subplot(grid[0,0]), fig.add_subplot(grid[0,1]),
            fig.add_subplot(grid[1,0]), fig.add_subplot(grid[1,1])]
    for ax, (cfg,counts) in zip(axes, groups):
        draw_panel(ax, cfg, counts)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "svg", "png", "tiff"):
        options = {"bbox_inches": "tight", "pad_inches": 0.08}
        if suffix in ("png", "tiff"):
            options["dpi"] = args.dpi
        if suffix == "tiff":
            options["pil_kwargs"] = {"compression": "tiff_lzw"}
        filename = out / f"{STEM}.{suffix}"
        fig.savefig(filename, format=suffix, **options)
        print("Created:", filename)

    count_path = out / f"{STEM}_Verified_Counts.csv"
    with count_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Panel","Field","Category","Label","Count","Percentage","Denominator"])
        writer.writeheader()
        for cfg,counts in groups:
            for category in cfg["order"]:
                value = counts[category]
                writer.writerow({"Panel":cfg["letter"],"Field":cfg["field"],"Category":category,
                                 "Label":cfg["names"][category],"Count":value,
                                 "Percentage":f"{value/STUDIES*100:.4f}","Denominator":STUDIES})
    print("Created:", count_path)
    print("PASS: four independent 485-study category distributions, source SHA-256 and frozen summary")
    if args.show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
