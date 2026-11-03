#!/usr/bin/env python3
"""Phase A (n=485): input-modality prevalence in the original Fig. 14 style.

Source of truth: the frozen 51-field technical register, NOT the legacy
492/491-study modality workbook. Verifies the source SHA-256 from the
immutable freeze manifest and validates every plotted count.

Outputs: vector PDF and SVG, 600-dpi PNG and LZW-TIFF, plus an audit CSV.

Usage:
    python regenerate_input_modality_prevalence_485_original_style_readable.py \
        --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \
        --output-dir Figures_485 --dpi 600
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Safe in WSL, remote terminals and notebooks.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MultipleLocator

N = 485

# The nine modality indicators are NOT mutually exclusive.
# A value of 'No' means no explicitly recoverable affirmative coding;
# it does not necessarily prove the input was never used.
MODALITIES = [
    ("Historical_Market_Data", "Historical market data", 291),
    ("Technical_Indicators", "Technical indicators", 118),
    ("Financial_News_Text", "Financial news and textual information", 91),
    ("Decomposition_Transformation", "Decomposition or transformed\nrepresentations", 62),
    ("Social_Media_Public_Opinion", "Social media or public-opinion\ninformation", 37),
    ("Relational_Cross_Market", "Index, sectoral, relational, or\ncross-market context", 27),
    ("Macroeconomic_Systemic", "Macroeconomic or systemic variables", 21),
    ("Fundamental_Accounting", "Fundamental or accounting information", 19),
    ("Alternative_Attention", "Alternative or attention-related\ninformation", 5),
]
UNKNOWN_KEY = "Input_Modality_Recoverable"
UNKNOWN_COUNT = 34
BASE_NAME = "Figure14_Input_Modality_Prevalence_485_Original_Style_Readable"

BLUE = "#3F83A6"                  # Original figure's bars
MISSING_BLUE = "#9FC3D5"          # Original hatched row
HATCH_EDGE = "#394952"
LABEL_COLOR = "#202020"
GRID_COLOR = "#D0D5D9"
DIVIDER_COLOR = "#90BED0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def arguments() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--frozen-dir", type=Path,
        default=Path("PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"),
        help="Folder holding Technical_Register_485_FROZEN.csv and Final_Freeze_Manifest_v1.json",
    )
    ap.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--show-title", action="store_true", help="Optional in-figure title; omit when journal caption supplies title")
    return ap.parse_args()


def load_and_check(folder: Path) -> pd.DataFrame:
    data_path = folder / "Technical_Register_485_FROZEN.csv"
    manifest_path = folder / "Final_Freeze_Manifest_v1.json"
    if not data_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Missing frozen register or manifest in {folder.resolve()}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("output_sha256", {}).get(data_path.name)
    if not expected or sha256(data_path) != expected:
        raise RuntimeError("Frozen register SHA-256 mismatch: refusing to plot")
    if manifest.get("retained_studies") != N or manifest.get("final_corpus_frozen") is not True:
        raise RuntimeError("Manifest does not describe the approved frozen 485-study corpus")

    frame = pd.read_csv(data_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    needed = ["Paper_ID", UNKNOWN_KEY] + [c[0] for c in MODALITIES]
    missing = sorted(set(needed) - set(frame.columns))
    if missing:
        raise KeyError(f"Frozen register lacks required columns: {missing}")
    if len(frame) != N or frame.Paper_ID.nunique() != N or frame.Paper_ID.eq("").any():
        raise RuntimeError("Study number or Paper_ID uniqueness is invalid")

    excluded = set(manifest.get("excluded_ids", []))
    if excluded & set(frame.Paper_ID):
        raise RuntimeError("Author-excluded study IDs found in the frozen register")

    for col in [c[0] for c in MODALITIES] + [UNKNOWN_KEY]:
        bad = sorted(set(frame[col]) - {"Yes", "No"})
        if bad:
            raise ValueError(f"{col}: unexpected values {bad}; expected Yes/No")

    positive = np.column_stack([frame[key].eq("Yes").to_numpy() for key, _, _ in MODALITIES])
    no_positive = ~positive.any(axis=1)
    actual_no = frame[UNKNOWN_KEY].eq("No").to_numpy()
    if not np.array_equal(no_positive, actual_no):
        raise RuntimeError("Input recoverability disagrees with the nine modality indicators")
    if int(no_positive.sum()) != UNKNOWN_COUNT:
        raise RuntimeError(f"Expected {UNKNOWN_COUNT} modality-unrecoverable studies, found {no_positive.sum()}")

    for key, _, expected_n in MODALITIES:
        found = int(frame[key].eq("Yes").sum())
        if found != expected_n:
            raise RuntimeError(f"Frozen modality count mismatch for {key}: {found} vs {expected_n}")

    # Independently check technical indicators against the frozen manuscript-category table.
    category_path = folder / "Manuscript_Category_Counts_FROZEN.csv"
    category_expected = manifest.get("output_sha256", {}).get(category_path.name)
    if not category_path.is_file() or not category_expected or sha256(category_path) != category_expected:
        raise RuntimeError("Frozen category-count file SHA-256 mismatch")
    category = pd.read_csv(category_path, keep_default_na=False, encoding="utf-8-sig")
    ti = category.loc[
        (category["Field"] == "Technical_Indicators") & (category["Category"] == "Yes"),
        "Count",
    ]
    if len(ti) != 1 or int(ti.iloc[0]) != 118:
        raise RuntimeError("Frozen technical-indicator category table does not reconcile")

    return frame


def draw(rows: list[dict], output_dir: Path, dpi: int, show_title: bool):
    # Wide enough for full category names; typography kept large for two-column journal use.
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "font.size": 10.2,
        "axes.labelsize": 10.3,
        "xtick.labelsize": 9.4,
        "ytick.labelsize": 10.0,
        "axes.edgecolor": "#545454",
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })

    fig, ax = plt.subplots(figsize=(8.5, 5.9))

    # Extra space before the non-recoverable evidence-status row.
    positions = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9.75], dtype=float)
    bar_height = 0.70
    plotted_bars = []
    for y, item in zip(positions, rows):
        is_unknown = item["Category_Key"] == "Input_Modality_Not_Recoverable"
        patch = ax.barh(
            y, item["Studies"], height=bar_height,
            color=MISSING_BLUE if is_unknown else BLUE,
            edgecolor=HATCH_EDGE if is_unknown else "none",
            hatch="///" if is_unknown else None,
            linewidth=0.7 if is_unknown else 0,
            zorder=3,
        )[0]
        plotted_bars.append(patch)

    ax.set_yticks(positions)
    ax.set_yticklabels([x["Display_Label"] for x in rows], linespacing=1.08)
    ax.invert_yaxis()
    ax.set_ylabel("")
    ax.set_xlabel("Number of studies", labelpad=9)
    ax.set_xlim(0, 365)
    ax.xaxis.set_major_locator(MultipleLocator(50))
    ax.xaxis.grid(True, linestyle=(0, (2, 3)), linewidth=0.66,
                  color=GRID_COLOR, alpha=0.70, zorder=0)
    ax.yaxis.grid(False)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.tick_params(axis="x", width=0.7, length=4)
    ax.axhline(8.90, color=DIVIDER_COLOR, linewidth=0.9,
               linestyle=(0, (2.0, 2.4)), zorder=1)

    for bar, item in zip(plotted_bars, rows):
        ax.text(
            bar.get_width() + 4.0,
            bar.get_y() + bar.get_height() / 2,
            f"{item['Studies']} ({item['Share_Percent']:.1f}%)",
            ha="left", va="center", fontsize=10.0,
            color=LABEL_COLOR, clip_on=False, zorder=4,
        )

    if show_title:
        ax.set_title("Explicit input-modality prevalence in the frozen technical synthesis ($n=485$)",
                     fontsize=11, fontweight="bold", pad=15)

    # Note is outside the axes and does not intrude into the chart.
    fig.text(
        0.53, 0.035,
        "Modalities are non-mutually exclusive; the hatched row denotes evidence recoverability.",
        fontsize=8.5, ha="center", va="center", color="#555555"
    )

    # Keep visible label and annotation sizes rather than producing excessive blank space.
    fig.subplots_adjust(left=0.435, right=0.975, top=0.965 if not show_title else 0.91,
                        bottom=0.135)

    output_dir.mkdir(parents=True, exist_ok=True)
    for fmt in ("pdf", "svg", "png", "tiff"):
        kwargs = {"format": fmt, "bbox_inches": "tight", "pad_inches": 0.08}
        if fmt in ("png", "tiff"):
            kwargs["dpi"] = dpi
        if fmt == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(output_dir / f"{BASE_NAME}.{fmt}", **kwargs)
    plt.close(fig)


def main():
    args = arguments()
    frozen = load_and_check(args.frozen_dir)
    rows = [
        {"Category_Key": key, "Display_Label": label,
         "Studies": int(frozen[key].eq("Yes").sum()),
         "Share_Percent": 100 * int(frozen[key].eq("Yes").sum()) / N,
         "Classification": "Explicit input modality"}
        for key, label, _ in MODALITIES
    ]
    rows.append({
        "Category_Key": "Input_Modality_Not_Recoverable",
        "Display_Label": "Input modality not recoverable",
        "Studies": int(frozen[UNKNOWN_KEY].eq("No").sum()),
        "Share_Percent": 100 * int(frozen[UNKNOWN_KEY].eq("No").sum()) / N,
        "Classification": "Evidence recoverability, not a modality",
    })
    draw(rows, args.output_dir, args.dpi, args.show_title)
    summary = args.output_dir / f"{BASE_NAME}_Verified_Counts.csv"
    pd.DataFrame(rows).to_csv(summary, index=False, encoding="utf-8-sig", float_format="%.4f")
    print("Frozen Phase A technical studies:", N)
    print("Source register and category-table SHA-256: PASS")
    print("Modality indicator/recoverability consistency: PASS")
    for row in rows:
        print(f"  {row['Display_Label'].replace(chr(10),' '):46s} {row['Studies']:>3}  ({row['Share_Percent']:.1f}%)")
    print("Figure output:", args.output_dir.resolve())
    print("STATUS: PASS — ORIGINAL-STYLE REVISED MODALITY FIGURE CREATED")


if __name__ == "__main__":
    main()
