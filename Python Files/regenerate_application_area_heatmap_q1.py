from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

from matplotlib.colors import LogNorm
from matplotlib.ticker import ScalarFormatter


# ============================================================
# 1. USER SETTINGS
# ============================================================

PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

HEATMAP_FILE = (
    PROJECT_DIR
    / "World_Map_Heatmap_Output"
    / "Application_Area_Year_Matrix.csv"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "08_Figures"
    / "Figure5_Application_Area_Heatmap"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EXPECTED_TOTAL = 4_974
PARTIAL_YEAR = 2026
DPI = 600

ANNOTATION_MIN = 3

ALWAYS_ANNOTATE_YEARS = {
    2024,
    2025,
    2026,
}

SHOW_TITLE = False


# ============================================================
# 2. TYPOGRAPHY
# ============================================================

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": [
            "Times New Roman",
            "STIXGeneral",
            "DejaVu Serif",
        ],
        "font.size": 9.0,
        "axes.titlesize": 11.5,
        "axes.labelsize": 9.8,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.7,
        "axes.linewidth": 0.6,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


# ============================================================
# 3. LOCATE AND LOAD THE MATRIX
# ============================================================

def locate_heatmap_file() -> Path:
    if HEATMAP_FILE.exists():
        return HEATMAP_FILE.resolve()

    matches = list(
        PROJECT_DIR.rglob(
            "Application_Area_Year_Matrix.csv"
        )
    )

    if not matches:
        raise FileNotFoundError(
            "Application_Area_Year_Matrix.csv was not found under:\n"
            f"{PROJECT_DIR}"
        )

    if len(matches) > 1:
        print(
            "Multiple heatmap matrices found; using:\n"
            f"{matches[0]}"
        )

    return matches[0].resolve()


heatmap_path = locate_heatmap_file()

heat_df = pd.read_csv(
    heatmap_path,
)

if "Application_Area" not in heat_df.columns:
    raise KeyError(
        "The matrix must contain an Application_Area column."
    )

year_columns = sorted(
    [
        column
        for column in heat_df.columns
        if str(column).isdigit()
        and 1900 <= int(column) <= 2100
    ],
    key=int,
)

if not year_columns:
    raise ValueError(
        "No publication-year columns were found."
    )

heat_df = heat_df[
    ["Application_Area"] + year_columns
].copy()

for column in year_columns:
    heat_df[column] = pd.to_numeric(
        heat_df[column],
        errors="raise",
    ).astype(int)

heat_df = heat_df.set_index(
    "Application_Area"
)

heatmap_total = int(
    heat_df.to_numpy().sum()
)

if heatmap_total != EXPECTED_TOTAL:
    raise AssertionError(
        f"Expected {EXPECTED_TOTAL:,} publications, "
        f"but the matrix contains {heatmap_total:,}."
    )


# ============================================================
# 4. LABELS
# ============================================================

DISPLAY_LABELS = {
    "Price_Index_Forecasting":
        "Price and index forecasting",

    "Direction_Trend_Regime":
        "Direction, trend, and regime",

    "Return_Forecasting":
        "Return forecasting",

    "Volatility_Risk_Uncertainty":
        "Volatility, risk, and uncertainty",

    "Sentiment_News_Social_Media":
        "Sentiment, news, and social media",

    "Trading_Portfolio_Decision_Support":
        "Trading, portfolio, and decision support",

    "High_Frequency_Market_Microstructure":
        "High-frequency and market microstructure",

    "Multi_Asset_Cross_Market":
        "Multi-asset and cross-market",

    "General_Multi_Target_Other":
        "General, multi-target, and other",
}


def clean_application_label(value: str) -> str:
    text = str(value).strip()

    if text in DISPLAY_LABELS:
        return DISPLAY_LABELS[text]

    return (
        text.replace("_", " ")
        .replace("&", "and")
        .strip()
    )


publication_years = [
    int(column)
    for column in year_columns
]

values = heat_df.to_numpy(
    dtype=int,
)

row_totals = values.sum(
    axis=1,
)

row_labels = [
    f"{clean_application_label(label)}  (n={int(total):,})"
    for label, total in zip(
        heat_df.index,
        row_totals,
    )
]


# ============================================================
# 5. PUBLICATION-READY HEATMAP
# ============================================================

masked_values = np.ma.masked_equal(
    values,
    0,
)

positive_values = values[
    values > 0
]

if positive_values.size == 0:
    raise ValueError(
        "The application-area matrix has no positive counts."
    )

colour_map = plt.get_cmap(
    "viridis"
).copy()

colour_map.set_bad(
    "#f7f7f7"
)

normalization = LogNorm(
    vmin=1,
    vmax=int(positive_values.max()),
)

fig, ax = plt.subplots(
    figsize=(10.8, 5.15)
)

image = ax.imshow(
    masked_values,
    aspect="auto",
    cmap=colour_map,
    norm=normalization,
    interpolation="nearest",
)

ax.set_yticks(
    np.arange(len(row_labels))
)

ax.set_yticklabels(
    row_labels,
)

ax.tick_params(
    axis="y",
    which="major",
    length=0,
    pad=7,
)

preferred_tick_years = [
    1987,
    1990,
    1995,
    2000,
    2005,
    2010,
    2015,
    2020,
    2023,
    2026,
]

tick_years = [
    year
    for year in preferred_tick_years
    if year in publication_years
]

tick_positions = [
    publication_years.index(year)
    for year in tick_years
]

tick_labels = [
    f"{year}*"
    if year == PARTIAL_YEAR
    else str(year)
    for year in tick_years
]

ax.set_xticks(tick_positions)

ax.set_xticklabels(
    tick_labels,
    rotation=0,
    ha="center",
)

for year in publication_years:
    if (
        year == publication_years[0]
        or year == publication_years[-1]
    ):
        tick_years.append(year)

tick_positions = [
    publication_years.index(year)
    for year in tick_years
]

tick_labels = [
    f"{year}*"
    if year == PARTIAL_YEAR
    else str(year)
    for year in tick_years
]

ax.set_xticks(
    tick_positions
)

ax.set_xticklabels(
    tick_labels,
    rotation=0,
    ha="center",
)

ax.tick_params(
    axis="x",
    which="major",
    length=0,
    pad=6,
)

ax.set_xlabel(
    "Publication year (* partial year)"
)

ax.set_ylabel(
    ""
)

if SHOW_TITLE:
    ax.set_title(
        "Application-area publication trends by year",
        loc="left",
        fontweight="bold",
        pad=10,
    )

ax.set_xticks(
    np.arange(-0.5, len(publication_years), 1),
    minor=True,
)

ax.set_yticks(
    np.arange(-0.5, len(row_labels), 1),
    minor=True,
)

ax.grid(
    which="minor",
    color="white",
    linewidth=0.45,
    alpha=0.80,
)

ax.tick_params(
    which="minor",
    bottom=False,
    left=False,
)

for spine in ax.spines.values():
    spine.set_visible(False)

if PARTIAL_YEAR in publication_years:
    partial_index = publication_years.index(
        PARTIAL_YEAR
    )

    ax.axvline(
        partial_index - 0.5,
        linestyle="--",
        linewidth=0.8,
        color="0.25",
    )

    ax.axvline(
        partial_index + 0.5,
        linestyle="--",
        linewidth=0.8,
        color="0.25",
    )

for row_index in range(values.shape[0]):
    for column_index in range(values.shape[1]):
        value = int(
            values[row_index, column_index]
        )

        year = publication_years[
            column_index
        ]

        should_annotate = (
            value >= ANNOTATION_MIN
            or (
                year in ALWAYS_ANNOTATE_YEARS
                and value > 0
            )
        )

        if not should_annotate:
            continue

        rgba = colour_map(
            normalization(value)
        )

        luminance = (
            0.2126 * rgba[0]
            + 0.7152 * rgba[1]
            + 0.0722 * rgba[2]
        )

        text_colour = (
            "white"
            if luminance < 0.46
            else "black"
        )

        ax.text(
            column_index,
            row_index,
            str(value),
            ha="center",
            va="center",
            fontsize=5.9,
            color=text_colour,
            fontweight=(
                "bold"
                if value >= 100
                else "normal"
            ),
        )

colour_bar = fig.colorbar(
    image,
    ax=ax,
    fraction=0.022,
    pad=0.018,
)

colour_bar.set_label(
    "Publications (log scale)",
    labelpad=8,
)

candidate_ticks = [
    1,
    2,
    5,
    10,
    20,
    50,
    100,
    200,
    500,
]

colour_bar_ticks = [
    tick
    for tick in candidate_ticks
    if tick <= positive_values.max()
]

colour_bar.set_ticks(
    colour_bar_ticks
)

colour_bar.ax.yaxis.set_major_formatter(
    ScalarFormatter()
)

colour_bar.ax.tick_params(
    labelsize=7.8,
)

colour_bar.outline.set_linewidth(
    0.5
)

fig.subplots_adjust(
    left=0.275,
    right=0.935,
    top=0.96 if not SHOW_TITLE else 0.90,
    bottom=0.13,
)

output_stem = (
    OUTPUT_DIR
    / "Fig5_Application_Area_Annual_Heatmap_Q1"
)

fig.savefig(
    output_stem.with_suffix(".pdf"),
    bbox_inches="tight",
    pad_inches=0.025,
)

fig.savefig(
    output_stem.with_suffix(".svg"),
    bbox_inches="tight",
    pad_inches=0.025,
)

fig.savefig(
    output_stem.with_suffix(".png"),
    dpi=DPI,
    bbox_inches="tight",
    pad_inches=0.025,
)

fig.savefig(
    output_stem.with_suffix(".tiff"),
    dpi=DPI,
    bbox_inches="tight",
    pad_inches=0.025,
    pil_kwargs={
        "compression": "tiff_lzw",
    },
)

plt.show()
plt.close(fig)


# ============================================================
# 6. VERIFICATION OUTPUT
# ============================================================

print("\nInput matrix:")
print(heatmap_path)

print("\nPublication total:")
print(f"{heatmap_total:,}")

print("\nMaximum annual cell:")
print(int(positive_values.max()))

print("\nRow totals:")
for label, total in zip(
    row_labels,
    row_totals,
):
    print(label, "=", int(total))

print("\nFiles saved:")
for extension in [
    "pdf",
    "svg",
    "png",
    "tiff",
]:
    print(
        output_stem.with_suffix(
            f".{extension}"
        )
    )
