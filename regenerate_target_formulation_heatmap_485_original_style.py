#!/usr/bin/env python3
"""
Recreate the ORIGINAL viridis target-by-formulation heatmap style, using the
AUTHORITATIVE FROZEN Phase-A 485-study corpus rather than a legacy workbook.

The figure retains the original presentation:
  - Serif typeface and centered title
  - Forecasting targets in the original vertical order
  - Learning formulations across the TOP, with category marginal counts
  - Original-style 'viridis' colour scale, 0-100% within-target share
  - Light grey zero cells, thin cell borders
  - Each populated cell shows exact count and within-row percentage
  - Vector PDF/SVG and 600-dpi PNG/TIFF output

Source files (under --frozen-dir):
    Technical_Register_485_FROZEN.csv
    FigureData_Target_Primary_by_Learning_Formulation_FROZEN.csv
    Final_Freeze_Manifest_v1.json

Run:
    python regenerate_target_formulation_heatmap_485_original_style.py \
      --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \
      --output-dir Figures_485 --dpi 600

No Excel recomputation, eligibility changes, sample filtering, or inferred values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np


# Keep exactly the original figure's order, not the reordered Phase-A preview.
TARGET_ORDER = [
    "Price", "Return", "Direction", "Trend_Regime",
    "Volatility", "Multi_Target", "Not_Reported",
]
FORMULATION_ORDER = [
    "Regression", "Binary_Classification", "Multiclass_Classification",
    "Probabilistic", "Multi_Task", "Hybrid_Other", "Not_Reported",
]

TARGET_LABELS = {
    "Price": "Price level",
    "Return": "Return",
    "Direction": "Direction",
    "Trend_Regime": "Trend or regime",
    "Volatility": "Volatility",
    "Multi_Target": "Multi-target",
    "Not_Reported": "Not reported",
}
FORMULATION_LABELS = {
    "Regression": "Regression",
    "Binary_Classification": "Binary\nclassification",
    "Multiclass_Classification": "Multiclass\nclassification",
    "Probabilistic": "Probabilistic\nforecasting",
    "Multi_Task": "Multi-task\nlearning",
    "Hybrid_Other": "Hybrid or\nother",
    "Not_Reported": "Not\nreported",
}

FILE_REGISTER = "Technical_Register_485_FROZEN.csv"
FILE_CROSS_TAB = "FigureData_Target_Primary_by_Learning_Formulation_FROZEN.csv"
FILE_MANIFEST = "Final_Freeze_Manifest_v1.json"


def parse_args():
    p = argparse.ArgumentParser(
        description="Original-style viridis target-formulation heatmap for frozen n=485"
    )
    p.add_argument(
        "--frozen-dir", type=Path,
        default=Path("PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"),
    )
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--stem", default="Fig_Target_Formulation_Heatmap_485")
    p.add_argument("--no-title", action="store_true", help="Hide the in-figure title")
    return p.parse_args()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def verify_hash(path, expected):
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(block)
    observed = sha.hexdigest()
    if observed != expected:
        raise RuntimeError(
            f"FAIL-CLOSED SHA-256 MISMATCH: {path}\n"
            f"expected={expected}\nobserved={observed}"
        )


def load_frozen_matrix(folder):
    manifest_path = folder / FILE_MANIFEST
    register_path = folder / FILE_REGISTER
    cross_path = folder / FILE_CROSS_TAB
    for path in (manifest_path, register_path, cross_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing frozen source: {path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_corpus_frozen") is not True:
        raise RuntimeError("Final release manifest does not declare a frozen corpus")
    hashes = manifest["output_sha256"]
    verify_hash(register_path, hashes[FILE_REGISTER])
    verify_hash(cross_path, hashes[FILE_CROSS_TAB])

    studies = read_csv(register_path)
    if len(studies) != 485 or manifest.get("retained_studies") != 485:
        raise RuntimeError("Authoritative denominator must be exactly 485")

    ids = [r["Paper_ID"] for r in studies]
    if len(set(ids)) != 485 or not all(ids):
        raise RuntimeError("Missing or duplicate Paper_ID in frozen register")

    target_seen = {r["Target_Primary"] for r in studies}
    form_seen = {r["Learning_Formulation"] for r in studies}
    if target_seen - set(TARGET_ORDER):
        raise RuntimeError(f"Unexpected target codes: {target_seen - set(TARGET_ORDER)}")
    if form_seen - set(FORMULATION_ORDER):
        raise RuntimeError(f"Unexpected formulation codes: {form_seen - set(FORMULATION_ORDER)}")

    target_ix = {v: i for i, v in enumerate(TARGET_ORDER)}
    form_ix = {v: i for i, v in enumerate(FORMULATION_ORDER)}
    counts = np.zeros((len(TARGET_ORDER), len(FORMULATION_ORDER)), dtype=np.int64)
    for r in studies:
        counts[target_ix[r["Target_Primary"]], form_ix[r["Learning_Formulation"]]] += 1

    # Independent check against the separately frozen and SHA-verified cross-tab.
    reference = Counter()
    for r in read_csv(cross_path):
        key = (r["Target_Primary"], r["Learning_Formulation"])
        if key in reference:
            raise RuntimeError(f"Duplicate frozen cross-tab category: {key}")
        reference[key] = int(r["Count"])
    computed = Counter({
        (t, f): int(counts[i, j])
        for i, t in enumerate(TARGET_ORDER)
        for j, f in enumerate(FORMULATION_ORDER)
        if counts[i, j] != 0
    })
    if computed != reference:
        raise RuntimeError("Frozen register and frozen target-formulation cross-tab disagree")
    if int(counts.sum()) != 485:
        raise RuntimeError("Matrix entries fail to sum to 485")
    return counts


def setup_typography():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "font.size": 10,
        "axes.titlesize": 12,
        "xtick.labelsize": 9.1,
        "ytick.labelsize": 10,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })


def make_plot(counts, show_title=True):
    row_totals = counts.sum(axis=1)
    col_totals = counts.sum(axis=0)
    percentages = (counts / row_totals[:, None]) * 100.0

    # Original layout: large plot centered beneath top-aligned column headings.
    fig = plt.figure(figsize=(11.2, 6.4))
    ax = fig.add_axes([0.212, 0.073, 0.671, 0.68])
    cbax = fig.add_axes([0.904, 0.073, 0.022, 0.68])

    # Original empty-cell treatment: light grey rectangles, rather than zeros
    # coloured dark purple. Masking also prevents false evidence of 'zero share'.
    data = np.ma.masked_where(counts == 0, percentages)
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#E4E4E4")
    norm = Normalize(vmin=0, vmax=100)
    img = ax.imshow(data, interpolation="nearest", cmap=cmap,
                    norm=norm, aspect="auto")

    if show_title:
        fig.suptitle("Coupling between forecasting targets and learning formulations",
                     fontsize=13.5, fontweight="bold", x=0.52, y=0.965)

    ax.set_xticks(np.arange(len(FORMULATION_ORDER)))
    ax.set_xticklabels([
        f"{FORMULATION_LABELS[key]}\n(n={int(col_totals[j])})"
        for j, key in enumerate(FORMULATION_ORDER)
    ])
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", top=True, bottom=False,
                   labeltop=True, labelbottom=False, pad=12, length=3)

    ax.set_yticks(np.arange(len(TARGET_ORDER)))
    ax.set_yticklabels([
        f"{TARGET_LABELS[key]} (n={int(row_totals[i])})"
        for i, key in enumerate(TARGET_ORDER)
    ])
    ax.tick_params(axis="y", length=3, pad=13)

    # Original thin matrix-grid treatment.
    ax.set_xticks(np.arange(-0.5, counts.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, counts.shape[0], 1), minor=True)
    ax.grid(which="minor", color="#B9B9B9", linewidth=0.65)
    ax.tick_params(which="minor", bottom=False, left=False, top=False)
    for spine in ax.spines.values():
        spine.set_color("#2F2F2F")
        spine.set_linewidth(0.8)

    # Exact values: never write percentages for zero-count cells.
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            n = int(counts[i, j])
            if n == 0:
                continue
            pct = float(percentages[i, j])
            rgba = cmap(norm(pct))
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            ink = "black" if luminance > 0.51 else "white"
            # Count slightly larger and bolder than the row-normalised percentage.
            ax.text(j, i - 0.12, f"{n}", ha="center", va="center",
                    color=ink, fontweight="bold", fontsize=10.3)
            ax.text(j, i + 0.15, f"({pct:.1f}%)", ha="center", va="center",
                    color=ink, fontsize=9.0)

    colorbar = fig.colorbar(img, cax=cbax, ticks=[0, 20, 40, 60, 80, 100])
    colorbar.set_label("Within-target share (%)", rotation=90, labelpad=12, fontsize=10)
    colorbar.ax.tick_params(labelsize=9)
    colorbar.outline.set_edgecolor("#555555")
    colorbar.outline.set_linewidth(0.8)
    return fig


def main():
    args = parse_args()
    if args.dpi < 72:
        raise ValueError("DPI must be >= 72")
    setup_typography()
    matrix = load_frozen_matrix(args.frozen_dir)
    fig = make_plot(matrix, show_title=not args.no_title)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / args.stem
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.12)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.12)
    fig.savefig(output.with_suffix(".png"), dpi=args.dpi,
                bbox_inches="tight", pad_inches=0.12)
    fig.savefig(output.with_suffix(".tiff"), dpi=args.dpi,
                bbox_inches="tight", pad_inches=0.12,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)

    # Accompany plot with an auditable exact-count table.
    table_csv = args.output_dir / f"{args.stem}_Crosstab.csv"
    with table_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Target_Primary", *FORMULATION_ORDER, "Row_Total"])
        for i, target in enumerate(TARGET_ORDER):
            w.writerow([target, *[int(v) for v in matrix[i]], int(matrix[i].sum())])
        w.writerow(["Column_Total", *[int(v) for v in matrix.sum(axis=0)],
                    int(matrix.sum())])

    print("SOURCE: 485-study frozen register + SHA-verified official cross-tab")
    print("TARGET ROW TOTALS:", dict(zip(TARGET_ORDER, matrix.sum(axis=1).tolist())))
    print("FORMULATION COLUMN TOTALS:",
          dict(zip(FORMULATION_ORDER, matrix.sum(axis=0).tolist())))
    print("GRAND TOTAL:", int(matrix.sum()))
    print("STYLE: original serif / viridis / top x-axis / grey empty cells")
    print("OUTPUT STEM:", output.resolve())
    print("STATUS: PASS — ORIGINAL-STYLE HEATMAP REGENERATED FROM FROZEN n=485")


if __name__ == "__main__":
    main()
