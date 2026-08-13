from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

XLSX_PATH = (
    PROJECT_DIR
    / "09_Tables"
    / "Table_Top_15_Sources_Final.xlsx"
)

SHEET_NAME = "Sheet1"

OUTPUT_DIR = (
    PROJECT_DIR
    / "08_Figures"
    / "Figure3_Top15_Sources_DotPlot"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DPI = 600
TOTAL_RECORDS = 5022


# ============================================================
# 2. FIGURE SETTINGS
# ============================================================

SHOW_TITLE = False

TITLE = (
    "Top 15 publication sources in stock price prediction research"
)

SOURCE_NOTE = (
    "Source: deduplicated Scopus, Web of Science, and "
    "IEEE Xplore records (n = 5022)."
)

OUTPUT_STEM = (
    "Fig3_Top15_Publication_Sources_Ranked_DotPlot_Q1"
)

LABEL_WRAP_WIDTH = 61


# ============================================================
# 3. LOAD AND VALIDATE DATA
# ============================================================

if not XLSX_PATH.exists():
    raise FileNotFoundError(
        "Workbook not found:\n"
        f"{XLSX_PATH.resolve()}"
    )

df = pd.read_excel(
    XLSX_PATH,
    sheet_name=SHEET_NAME,
    engine="openpyxl",
)

required_columns = [
    "Source_Title",
    "Count",
    "Percentage",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise KeyError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )

df = df[required_columns].copy()

df["Source_Title"] = (
    df["Source_Title"]
    .astype(str)
    .str.strip()
)

df["Count"] = pd.to_numeric(
    df["Count"],
    errors="raise",
).astype(int)

df["Percentage"] = pd.to_numeric(
    df["Percentage"],
    errors="coerce",
)

df["Percentage"] = df["Percentage"].fillna(
    100 * df["Count"] / TOTAL_RECORDS
)

df = (
    df.sort_values(
        ["Count", "Source_Title"],
        ascending=[False, True],
    )
    .reset_index(drop=True)
)

if len(df) != 15:
    raise AssertionError(
        f"Expected 15 publication sources, found {len(df)}."
    )

df["Rank"] = np.arange(
    1,
    len(df) + 1,
)


# ============================================================
# 4. WRAP AND RANK SOURCE LABELS
# ============================================================

def wrap_ranked_label(
    rank: int,
    source_title: str,
    width: int = LABEL_WRAP_WIDTH,
) -> str:
    """
    Prefix each source with its rank and wrap long titles.
    Keeping rank and source in one tick label avoids overlap.
    """

    prefix = f"{rank:>2}.  "

    wrapped_lines = textwrap.wrap(
        " ".join(str(source_title).split()),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )

    if not wrapped_lines:
        return prefix

    continuation_indent = " " * len(prefix)

    return "\n".join(
        [
            prefix + wrapped_lines[0],
            *[
                continuation_indent + line
                for line in wrapped_lines[1:]
            ],
        ]
    )


df["Ranked_Label"] = [
    wrap_ranked_label(
        rank=int(rank),
        source_title=title,
    )
    for rank, title in zip(
        df["Rank"],
        df["Source_Title"],
    )
]


# ============================================================
# 5. TYPOGRAPHY
# ============================================================

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": [
            "Times New Roman",
            "STIXGeneral",
            "DejaVu Serif",
        ],
        "font.size": 10.5,
        "axes.labelsize": 11.0,
        "xtick.labelsize": 9.8,
        "ytick.labelsize": 10.0,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


# ============================================================
# 6. RANKED CLEVELAND DOT PLOT
# ============================================================

counts = df["Count"].to_numpy()
percentages = df["Percentage"].to_numpy()
y_positions = np.arange(len(df))

fig_height = max(
    6.4,
    0.53 * len(df) + 1.8,
)

fig, ax = plt.subplots(
    figsize=(8.0, 7.2)
)

# Thin stems give scale context without the visual weight of bars.
ax.hlines(
    y=y_positions,
    xmin=0,
    xmax=counts,
    linewidth=1.05,
    alpha=0.70,
    zorder=1,
)

ax.scatter(
    counts,
    y_positions,
    s=44,
    zorder=3,
)
ax.set_yticks(
    y_positions
)

ax.set_yticklabels(
    df["Ranked_Label"]
)

ax.invert_yaxis()

ax.set_xlabel(
    "Number of publications"
)

# The y-axis title is intentionally omitted because the labels
# already make the variable self-evident.
ax.set_ylabel("")

if SHOW_TITLE:
    ax.set_title(
        TITLE,
        loc="left",
        fontweight="bold",
        pad=9,
    )

ax.grid(
    axis="x",
    linestyle="--",
    linewidth=0.6,
    alpha=0.32,
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.tick_params(
    axis="y",
    length=0,
    pad=8,
)

maximum_count = int(
    counts.max()
)

label_offset = max(
    2.0,
    maximum_count * 0.014,
)

ax.set_xlim(
    0,
    maximum_count * 1.24,
)

for y_position, count, percentage in zip(
    y_positions,
    counts,
    percentages,
):
    ax.hlines(
    y=y_positions,
    xmin=0,
    xmax=counts,
    linewidth=1.0,
    alpha=0.72,
    zorder=1,
)

ax.scatter(
    counts,
    y_positions,
    s=42,
    zorder=3,
)

ax.margins(
    y=0.025
)

# fig.text(
#     0.01,
#     0.012,
#     SOURCE_NOTE,
#     ha="left",
#     va="bottom",
#     fontsize=8.1,
# )

fig.subplots_adjust(
    left=0.51,
    right=0.98,
    top=0.98,
    bottom=0.09,
)


# ============================================================
# 7. EXPORT
# ============================================================

fig.savefig(
    OUTPUT_DIR / f"{OUTPUT_STEM}.pdf",
    bbox_inches="tight",
    pad_inches=0.02,
)

fig.savefig(
    OUTPUT_DIR / f"{OUTPUT_STEM}.svg",
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_DIR / f"{OUTPUT_STEM}.png",
    dpi=DPI,
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_DIR / f"{OUTPUT_STEM}.tiff",
    dpi=DPI,
    bbox_inches="tight",
    pil_kwargs={
        "compression": "tiff_lzw",
    },
)

plt.show()
plt.close(fig)


# ============================================================
# 8. VERIFICATION OUTPUT
# ============================================================

print("\nWorkbook:")
print(XLSX_PATH.resolve())

print("\nOutput directory:")
print(OUTPUT_DIR.resolve())

print("\nTop-source total shown:")
print(int(df["Count"].sum()))

print("\nFiles saved:")
for extension in [
    "pdf",
    "svg",
    "png",
    "tiff",
]:
    print(
        OUTPUT_DIR
        / f"{OUTPUT_STEM}.{extension}"
    )