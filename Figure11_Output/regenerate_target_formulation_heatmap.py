"""
Publication-ready target x learning-formulation heatmap.

Recommended encoding:
- Cell colour: within-target row percentage
- Cell annotation: exact study count and within-target percentage
- Marginal totals: shown directly in axis labels
- Empty combinations: left blank
- Exports: vector PDF/SVG and 600-dpi PNG/TIFF

Run:
    python regenerate_target_formulation_heatmap.py

Optional:
    python regenerate_target_formulation_heatmap.py \
        --xlsx "Section5_5_Review_264_Closed_45_Pending.xlsx" \
        --output-dir "figures" \
        --mode row_percent \
        --show-title
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, PowerNorm


TARGET_ORDER = [
    "Price",
    "Return",
    "Direction",
    "Trend_Regime",
    "Multi_Target",
    "Not_Reported",
]

FORMULATION_ORDER = [
    "Regression",
    "Binary_Classification",
    "Multiclass_Classification",
    "Probabilistic",
    "Multi_Task",
    "Hybrid_Other",
    "Not_Reported",
]

TARGET_LABELS = {
    "Price": "Price level",
    "Return": "Return",
    "Direction": "Direction",
    "Trend_Regime": "Trend or regime",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a publication-ready target-formulation heatmap."
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=Path("Section5_5_Review_264_Closed_45_Pending.xlsx"),
        help="Path to the authoritative Section 5 workbook.",
    )
    parser.add_argument(
        "--sheet",
        default="Section5_Coding_Consolidated",
        help="Coding sheet name.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures"),
        help="Directory for exported figure files.",
    )
    parser.add_argument(
        "--mode",
        choices=("row_percent", "count_power"),
        default="row_percent",
        help=(
            "row_percent: colour shows within-target percentage; "
            "count_power: colour shows absolute count on a nonlinear scale."
        ),
    )
    parser.add_argument(
        "--show-title",
        action="store_true",
        help="Show an in-figure title. Usually omit it when a journal caption is used.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="Raster export resolution.",
    )
    return parser.parse_args()


def load_included_studies(xlsx_path: Path, sheet_name: str) -> pd.DataFrame:
    if not xlsx_path.exists():
        raise FileNotFoundError(
            f"Workbook not found: {xlsx_path.resolve()}\n"
            "Pass the correct path with --xlsx."
        )

    coding_all = pd.read_excel(
        xlsx_path,
        sheet_name=sheet_name,
        dtype=str,
        engine="openpyxl",
    ).fillna("")

    required_columns = {
        "Paper_ID",
        "Systematic_Inclusion_Status",
        "Target_Primary",
        "Learning_Formulation",
    }
    missing = required_columns.difference(coding_all.columns)
    if missing:
        raise KeyError(
            "The coding sheet is missing required columns: "
            + ", ".join(sorted(missing))
        )

    coding = coding_all.loc[
        coding_all["Systematic_Inclusion_Status"].eq(
            "Included_High_Priority"
        )
    ].copy()

    if len(coding) != 493:
        raise AssertionError(
            f"Expected 493 included studies, found {len(coding)}."
        )

    if coding["Paper_ID"].nunique() != 493:
        raise AssertionError(
            "Duplicate Paper_ID values were found in the included set."
        )

    unexpected_targets = sorted(
        set(coding["Target_Primary"]) - set(TARGET_ORDER)
    )
    unexpected_formulations = sorted(
        set(coding["Learning_Formulation"]) - set(FORMULATION_ORDER)
    )

    if unexpected_targets:
        raise ValueError(
            f"Unexpected Target_Primary values: {unexpected_targets}"
        )
    if unexpected_formulations:
        raise ValueError(
            "Unexpected Learning_Formulation values: "
            f"{unexpected_formulations}"
        )

    return coding


def build_cross_table(coding: pd.DataFrame) -> pd.DataFrame:
    cross_table = pd.crosstab(
        coding["Target_Primary"],
        coding["Learning_Formulation"],
    ).reindex(
        index=TARGET_ORDER,
        columns=FORMULATION_ORDER,
        fill_value=0,
    )

    if int(cross_table.to_numpy().sum()) != len(coding):
        raise AssertionError(
            "Cross-table total does not match the included-study count."
        )

    return cross_table


def configure_typography() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "STIXGeneral",
                "DejaVu Serif",
            ],
            "font.size": 9.0,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.2,
            "ytick.labelsize": 8.8,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def make_axis_labels(
    counts: np.ndarray,
) -> tuple[list[str], list[str]]:
    row_totals = counts.sum(axis=1)
    column_totals = counts.sum(axis=0)

    y_labels = [
        f"{TARGET_LABELS[key]}  (n={int(total)})"
        for key, total in zip(TARGET_ORDER, row_totals)
    ]

    x_labels = [
        f"{FORMULATION_LABELS[key]}\n(n={int(total)})"
        for key, total in zip(FORMULATION_ORDER, column_totals)
    ]

    return x_labels, y_labels


def create_heatmap(
    cross_table: pd.DataFrame,
    mode: str = "row_percent",
    show_title: bool = False,
) -> tuple[plt.Figure, plt.Axes]:
    counts = cross_table.to_numpy(dtype=int)
    row_totals = counts.sum(axis=1, keepdims=True)

    with np.errstate(divide="ignore", invalid="ignore"):
        row_percent = np.divide(
            counts * 100.0,
            row_totals,
            out=np.zeros_like(counts, dtype=float),
            where=row_totals != 0,
        )

    if mode == "row_percent":
        colour_values = row_percent
        colourbar_label = "Within-target share (%)"
        norm = Normalize(vmin=0, vmax=100)
    else:
        colour_values = counts.astype(float)
        colourbar_label = "Number of studies"
        norm = PowerNorm(
            gamma=0.42,
            vmin=0,
            vmax=float(max(1, counts.max())),
        )

    # Empty combinations are masked so they remain visually blank.
    displayed = np.ma.masked_where(counts == 0, colour_values)

    fig, ax = plt.subplots(figsize=(7.45, 4.55))

    image = ax.imshow(
        displayed,
        aspect="auto",
        cmap="viridis",
        norm=norm,
        interpolation="nearest",
    )

    print(
        "Heatmap normalization:",
        type(image.norm).__name__,
        f"(vmin={image.norm.vmin}, vmax={image.norm.vmax})",
    )

    x_labels, y_labels = make_axis_labels(counts)

    ax.set_xticks(np.arange(len(FORMULATION_ORDER)))
    ax.set_xticklabels(x_labels)
    ax.xaxis.tick_top()
    ax.tick_params(
        axis="x",
        which="major",
        top=True,
        bottom=False,
        labeltop=True,
        labelbottom=False,
        pad=7,
        length=0,
    )

    ax.set_yticks(np.arange(len(TARGET_ORDER)))
    ax.set_yticklabels(y_labels)
    ax.tick_params(axis="y", length=0, pad=7)

    # Thin cell boundaries improve print readability.
    ax.set_xticks(
        np.arange(-0.5, len(FORMULATION_ORDER), 1),
        minor=True,
    )
    ax.set_yticks(
        np.arange(-0.5, len(TARGET_ORDER), 1),
        minor=True,
    )
    ax.grid(which="minor", color="0.78", linewidth=0.55)
    ax.tick_params(which="minor", bottom=False, left=False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    if show_title:
        ax.set_title(
            "Forecasting targets and learning formulations",
            loc="left",
            fontweight="bold",
            pad=16,
        )

    # Exact counts remain the primary annotation. Percentages explain
    # the coupling within each target category.
    for row in range(counts.shape[0]):
        for col in range(counts.shape[1]):
            count = int(counts[row, col])
            if count == 0:
                continue

            pct = float(row_percent[row, col])
            annotation = f"{count}\n({pct:.1f}%)"

            # Use the actual displayed cell colour to choose readable text.
            rgba = image.cmap(image.norm(colour_values[row, col]))
            luminance = (
                0.2126 * rgba[0]
                + 0.7152 * rgba[1]
                + 0.0722 * rgba[2]
            )
            text_colour = "white" if luminance < 0.48 else "black"

            ax.text(
                col,
                row,
                annotation,
                ha="center",
                va="center",
                fontsize=7.4,
                color=text_colour,
                fontweight="bold" if pct >= 75 else "normal",
                linespacing=1.05,
            )

    colourbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.035,
        pad=0.028,
    )
    colourbar.set_label(colourbar_label, labelpad=8)
    colourbar.ax.tick_params(labelsize=8)

    ax.set_xlabel("")
    ax.set_ylabel("")

    fig.subplots_adjust(
        left=0.205,
        right=0.905,
        top=0.80,
        bottom=0.08,
    )

    return fig, ax


def export_figure(
    fig: plt.Figure,
    output_dir: Path,
    stem: str,
    dpi: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_dir / f"{stem}.pdf")
    fig.savefig(output_dir / f"{stem}.svg")
    fig.savefig(output_dir / f"{stem}.png", dpi=dpi)
    fig.savefig(
        output_dir / f"{stem}.tiff",
        dpi=dpi,
        pil_kwargs={"compression": "tiff_lzw"},
    )


def main() -> None:
    args = parse_args()
    configure_typography()

    coding = load_included_studies(args.xlsx, args.sheet)
    cross_table = build_cross_table(coding)

    fig, _ = create_heatmap(
        cross_table=cross_table,
        mode=args.mode,
        show_title=args.show_title,
    )

    stem = (
        "fig_sec5_target_formulation_heatmap_row_percent"
        if args.mode == "row_percent"
        else "fig_sec5_target_formulation_heatmap_count_power"
    )

    export_figure(
        fig=fig,
        output_dir=args.output_dir,
        stem=stem,
        dpi=args.dpi,
    )
    plt.close(fig)

    cross_table.to_csv(
        args.output_dir / f"{stem}_counts.csv"
    )

    print("\nCross-table:")
    print(cross_table)
    print("\nRow totals:")
    print(cross_table.sum(axis=1).to_dict())
    print("\nColumn totals:")
    print(cross_table.sum(axis=0).to_dict())
    print("\nGrand total:", int(cross_table.to_numpy().sum()))
    print("\nFiles saved in:", args.output_dir.resolve())


if __name__ == "__main__":
    main()