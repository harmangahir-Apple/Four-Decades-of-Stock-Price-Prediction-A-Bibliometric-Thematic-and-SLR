from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pandas as pd


# ============================================================
# METHODOLOGICAL RELIABILITY OF THE 492-STUDY TECHNICAL SUBSET
#
# A. Validation-design reporting
# B. Explicitly documented methodological practices
# C. Passage-verified leakage signals
#
# SCIE Q1-ready alternative figure
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT AND INPUT SETTINGS
# ------------------------------------------------------------

PROJECT_DIR: Final[Path] = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

WORKBOOK_NAME: Final[str] = "Compiled Files.xlsx"

AUDIT_SHEET: Final[str] = (
    "Section5_5_Methodological_Audit"
)

INPUT_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / WORKBOOK_NAME,
    Path(WORKBOOK_NAME),
]

EXPECTED_STUDIES: Final[int] = 492



OUTPUT_DIR: Final[Path] = (
    PROJECT_DIR
    / "Methodological_Reliability_Figure_Output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SHOW_FIGURE: Final[bool] = True
EXPECTED_STUDIES: Final[int] = 492


# ------------------------------------------------------------
# 2. VERIFIED VALIDATION-DESIGN COUNTS
# ------------------------------------------------------------

VALIDATION_LABELS: Final[dict[str, str]] = {
    "Chronological_Holdout":
        "Chronological holdout",

    "Walk_Forward":
        "Walk-forward",

    "Rolling_Window":
        "Rolling window",

    "Expanding_Window":
        "Expanding window",

    "Blocked_CV":
        "Blocked cross-validation",

    "Random_Shuffled":
        "Random or shuffled",

    "Unclear":
        "Unclear",
}

VALIDATION_DETAIL_ORDER: Final[list[str]] = [
    "Chronological_Holdout",
    "Walk_Forward",
    "Rolling_Window",
    "Expanding_Window",
    "Blocked_CV",
    "Random_Shuffled",
]

EXPECTED_VALIDATION_COUNTS: Final[dict[str, int]] = {
    "Chronological_Holdout": 61,
    "Walk_Forward": 11,
    "Rolling_Window": 6,
    "Expanding_Window": 2,
    "Blocked_CV": 1,
    "Random_Shuffled": 6,
    "Unclear": 405,
}


# ------------------------------------------------------------
# 3. VERIFIED METHODOLOGICAL-PRACTICE COUNTS
# ------------------------------------------------------------

PRACTICE_COLUMNS: Final[list[tuple[str, str]]] = [
    (
        "Chronological split",
        "Chronological_Split",
    ),
    (
        "Non-stationarity acknowledged",
        "Nonstationarity_Acknowledged",
    ),
    (
        "Shock context mentioned",
        "Shock_Context_Mentioned",
    ),
    (
        "Statistical testing",
        "Statistical_Testing",
    ),
    (
        "Economic evaluation",
        "Economic_Evaluation_Claimed",
    ),
    (
        "Shock-period evaluation",
        "Shock_Period_Evaluation",
    ),
    (
        "Transaction costs",
        "Transaction_Costs",
    ),
    (
        "Regime-specific evaluation",
        "Regime_Specific_Evaluation",
    ),
    (
        "Regime-aware model",
        "Regime_Aware_Model",
    ),
    (
        "Code available",
        "Code_Available",
    ),
    (
        "Data available",
        "Data_Available",
    ),
]

EXPECTED_PRACTICE_COUNTS: Final[dict[str, int]] = {
    "Chronological split": 109,
    "Non-stationarity acknowledged": 74,
    "Shock context mentioned": 58,
    "Statistical testing": 48,
    "Economic evaluation": 37,
    "Shock-period evaluation": 15,
    "Transaction costs": 14,
    "Regime-specific evaluation": 9,
    "Regime-aware model": 7,
    "Code available": 7,
    "Data available": 5,
}


# ------------------------------------------------------------
# 4. VERIFIED LEAKAGE-SIGNAL COUNTS
# ------------------------------------------------------------

LEAKAGE_LABELS: Final[dict[str, str]] = {
    "Global_Scaling":
        "Global scaling",

    "Full_Dataset_Feature_Selection":
        "Full-dataset feature selection",

    "Random_Split":
        "Random or shuffled splitting",

    "Test_Set_Tuning":
        "Test-set tuning",

    "Overlapping_Windows":
        "Overlapping windows",

    "Label_Lookahead":
        "Label look-ahead",

    "Text_Timing":
        "Text-timing problem",

    "Future_Aware_Imputation":
        "Future-aware imputation",

    "Test_Set_Fitted_Transformation":
        "Test-set-fitted transformation",
}

LEAKAGE_ORDER: Final[list[str]] = [
    "Global_Scaling",
    "Full_Dataset_Feature_Selection",
    "Random_Split",
    "Test_Set_Tuning",
    "Overlapping_Windows",
    "Label_Lookahead",
    "Text_Timing",
    "Future_Aware_Imputation",
    "Test_Set_Fitted_Transformation",
]

EXPECTED_LEAKAGE_COUNTS: Final[dict[str, int]] = {
    "Global_Scaling": 17,
    "Full_Dataset_Feature_Selection": 6,
    "Random_Split": 6,
    "Test_Set_Tuning": 2,
    "Overlapping_Windows": 1,
    "Label_Lookahead": 1,
    "Text_Timing": 1,
    "Future_Aware_Imputation": 1,
    "Test_Set_Fitted_Transformation": 1,
}

EXPECTED_LEAKAGE_ASSIGNMENTS: Final[int] = 36

EXPECTED_HIGH_RISK_STUDIES: Final[int] = 32
EXPECTED_LOW_RISK_STUDIES: Final[int] = 7
EXPECTED_UNCLEAR_RISK_STUDIES: Final[int] = 453


def normalize_leakage_signal(value: str) -> str | None:
    """Map workbook leakage labels to the frozen canonical taxonomy."""

    key = (
        clean(value)
        .casefold()
        .replace("_", " ")
        .replace("-", " ")
    )

    key = " ".join(key.split())

    mapping = {
        "global scaling":
            "Global_Scaling",

        "full dataset feature selection":
            "Full_Dataset_Feature_Selection",

        "random split":
            "Random_Split",

        "random or shuffled splitting":
            "Random_Split",

        "test set tuning":
            "Test_Set_Tuning",

        "overlapping windows":
            "Overlapping_Windows",

        "label lookahead":
            "Label_Lookahead",

        "label look ahead":
            "Label_Lookahead",

        "text timing":
            "Text_Timing",

        "future aware imputation":
            "Future_Aware_Imputation",

        "test set fitted transformation":
            "Test_Set_Fitted_Transformation",

        "none explicitly identified":
            None,

        "unclear":
            None,

        "":
            None,
    }

    if key not in mapping:
        raise ValueError(
            f"Unexpected Leakage_Signals value: {value!r}"
        )

    return mapping[key]

# ------------------------------------------------------------
# 5. FIGURE SETTINGS
# ------------------------------------------------------------

FIGURE_WIDTH: Final[float] = 14.6
FIGURE_HEIGHT: Final[float] = 9.4
PNG_DPI: Final[int] = 600

FONT_FAMILY: Final[str] = "Arial"

TEXT_COLOUR: Final[str] = "#252525"
GRID_COLOUR: Final[str] = "#D3D7DA"

VALIDATION_COLOUR: Final[str] = "#3F83A6"
RANDOM_COLOUR: Final[str] = "#D99245"
UNCLEAR_COLOUR: Final[str] = "#B8BDC5"

PRACTICE_COLOUR: Final[str] = "#4F9A73"

LEAKAGE_COLOUR: Final[str] = "#CB6C55"

SUMMARY_BAR_HEIGHT: Final[float] = 0.50
STEM_WIDTH: Final[float] = 2.15
DOT_SIZE: Final[int] = 58


# ------------------------------------------------------------
# 6. GENERAL HELPERS
# ------------------------------------------------------------

def clean(value: object) -> str:
    """Remove repeated, leading, and trailing whitespace."""

    return " ".join(
        str(value or "").strip().split()
    )


def find_input_file() -> Path:
    """Find the reconciled methodological-audit CSV."""

    for candidate in INPUT_CANDIDATES:
        if candidate.is_file():
            return candidate

    matches = list(
        PROJECT_DIR.rglob(RECONCILED_AUDIT_NAME)
    )

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise RuntimeError(
            "More than one reconciled audit file was found:\n"
            + "\n".join(str(path) for path in matches)
            + "\n\nSet the intended path explicitly."
        )

    raise FileNotFoundError(
        "The reconciled methodological-audit CSV was not found.\n\n"
        "Expected file:\n"
        f"{RECONCILED_AUDIT_NAME}\n\n"
        "Checked:\n"
        + "\n".join(
            str(path)
            for path in INPUT_CANDIDATES
        )
        + "\n\nRun the leakage reconciliation first and save the CSV "
          "before generating Figure 13."
    )


def is_yes(value: object) -> bool:
    """Identify an explicit affirmative audit value."""

    return clean(value).casefold() == "yes"


def percentage(count: int) -> float:
    """Calculate percentage using n=492."""

    return (
        100.0
        * count
        / EXPECTED_STUDIES
    )


def validate_counts(
    label: str,
    observed: dict[str, int],
    expected: dict[str, int],
) -> None:
    """Verify that observed values equal the frozen audit values."""

    if observed == expected:
        return

    comparison_rows = []

    for category, expected_count in expected.items():
        comparison_rows.append(
            {
                "Category": category,
                "Expected": expected_count,
                "Observed": observed.get(category, 0),
            }
        )

    comparison = pd.DataFrame(comparison_rows)

    comparison = comparison.loc[
        comparison["Expected"]
        .ne(comparison["Observed"])
    ]

    raise AssertionError(
        f"{label} counts differ from the verified audit:\n\n"
        + comparison.to_string(index=False)
    )


# ------------------------------------------------------------
# 7. JOURNAL-STYLE DOT PLOT
# ------------------------------------------------------------

def draw_dot_plot(
    *,
    ax: plt.Axes,
    labels: list[str],
    counts: list[int],
    colours: list[str],
    x_limit: float,
    tick_step: float,
    xlabel: str = "Number of studies",
    annotation_font_size: float = 9.6,
) -> None:
    """
    Draw a compact horizontal stem-and-dot chart.

    Counts are plotted on the x-axis. Each annotation reports
    count and percentage using n=492.
    """

    y_positions = list(
        range(len(labels))
    )

    for y, count, colour in zip(
        y_positions,
        counts,
        colours,
    ):
        ax.hlines(
            y=y,
            xmin=0,
            xmax=count,
            color=colour,
            linewidth=STEM_WIDTH,
            alpha=0.82,
            zorder=2,
        )

        ax.scatter(
            count,
            y,
            s=DOT_SIZE,
            color=colour,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )

    annotation_offset = (
        x_limit * 0.013
    )

    for y, count in zip(
        y_positions,
        counts,
    ):
        ax.text(
            count + annotation_offset,
            y,
            (
                f"{count} "
                f"({percentage(count):.1f}%)"
            ),
            ha="left",
            va="center",
            fontsize=annotation_font_size,
            color=TEXT_COLOUR,
            clip_on=False,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    ax.set_xlim(0, x_limit)
    ax.xaxis.set_major_locator(
        MultipleLocator(tick_step)
    )

    ax.set_xlabel(
        xlabel,
        labelpad=10,
    )

    ax.xaxis.grid(
        True,
        linestyle=(0, (2, 3)),
        linewidth=0.50,
        color=GRID_COLOUR,
        alpha=0.58,
        zorder=0,
    )

    ax.yaxis.grid(False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(
        "#545454"
    )

    ax.tick_params(
        axis="y",
        length=0,
        pad=4,
    )

    ax.tick_params(
        axis="x",
        direction="out",
        length=3.2,
        width=0.7,
        color="#555555",
    )


# ------------------------------------------------------------
# 8. LOAD THE WORKBOOK
# ------------------------------------------------------------

input_file = find_input_file()

print("\nInput workbook:")
print(input_file)

df = pd.read_excel(
    input_file,
    sheet_name=AUDIT_SHEET,
    dtype=str,
    keep_default_na=False,
    engine="openpyxl",
)

df.columns = [
    clean(column)
    for column in df.columns
]

for column in df.columns:
    df[column] = (
        df[column]
        .fillna("")
        .astype(str)
        .map(clean)
    )

print(f"\nRows loaded: {len(df):,}")


# ------------------------------------------------------------
# 9. STUDY-LEVEL INTEGRITY CHECKS
# ------------------------------------------------------------

required_columns = {
    "Paper_ID",
    "Validation_Design",
    "Leakage_Signals",
    "Leakage_Risk",
    *[
        column
        for _, column in PRACTICE_COLUMNS
    ],
}

missing_columns = sorted(
    required_columns - set(df.columns)
)

if missing_columns:
    raise KeyError(
        "Required audit columns are missing:\n"
        f"{missing_columns}\n\n"
        "Available columns:\n"
        f"{list(df.columns)}"
    )

if len(df) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} rows; "
        f"found {len(df)}."
    )

if df["Paper_ID"].eq("").any():
    raise AssertionError(
        "Blank Paper_ID values were found."
    )

if not df["Paper_ID"].is_unique:
    duplicate_ids = (
        df.loc[
            df["Paper_ID"].duplicated(keep=False),
            "Paper_ID",
        ]
        .sort_values()
        .unique()
        .tolist()
    )

    raise AssertionError(
        "Duplicate Paper_ID values were found:\n"
        f"{duplicate_ids[:20]}"
    )


# ------------------------------------------------------------
# 10. PANEL A COUNTS
# ------------------------------------------------------------

validation_counter = Counter(
    df["Validation_Design"]
)

validation_counts = {
    category:
        int(validation_counter.get(category, 0))
    for category in EXPECTED_VALIDATION_COUNTS
}

validate_counts(
    "Validation-design",
    validation_counts,
    EXPECTED_VALIDATION_COUNTS,
)

identified_design_count = (
    EXPECTED_STUDIES
    - validation_counts["Unclear"]
)

unclear_design_count = (
    validation_counts["Unclear"]
)

temporally_ordered_count = (
    validation_counts["Chronological_Holdout"]
    + validation_counts["Walk_Forward"]
    + validation_counts["Rolling_Window"]
    + validation_counts["Expanding_Window"]
    + validation_counts["Blocked_CV"]
)

if identified_design_count != 87:
    raise AssertionError(
        "Expected 87 studies with an identified design."
    )

if temporally_ordered_count != 81:
    raise AssertionError(
        "Expected 81 temporally ordered validation designs."
    )


# ------------------------------------------------------------
# 11. PANEL B COUNTS
# ------------------------------------------------------------

practice_counts: dict[str, int] = {}

for label, column in PRACTICE_COLUMNS:
    practice_counts[label] = int(
        df[column]
        .map(is_yes)
        .sum()
    )

validate_counts(
    "Methodological-practice",
    practice_counts,
    EXPECTED_PRACTICE_COUNTS,
)


# ------------------------------------------------------------
# 12. PANEL C COUNTS
# ------------------------------------------------------------

leakage_counter: Counter[str] = Counter()

for raw_value in df["Leakage_Signals"]:

    raw_value = clean(raw_value)

    if not raw_value:
        continue

    signals = [
        clean(token)
        for token in raw_value.split(";")
        if clean(token)
    ]

    for signal in signals:

        canonical_signal = normalize_leakage_signal(
            signal
        )

        if canonical_signal is not None:
            leakage_counter[canonical_signal] += 1

leakage_counts = {
    category:
        int(leakage_counter.get(category, 0))
    for category in EXPECTED_LEAKAGE_COUNTS
}

validate_counts(
    "Leakage-signal",
    leakage_counts,
    EXPECTED_LEAKAGE_COUNTS,
)

leakage_assignment_count = int(
    sum(leakage_counts.values())
)

if leakage_assignment_count != EXPECTED_LEAKAGE_ASSIGNMENTS:
    raise AssertionError(
        "Expected "
        f"{EXPECTED_LEAKAGE_ASSIGNMENTS} leakage-mechanism "
        f"assignments; found {leakage_assignment_count}."
    )

risk_counts = (
    df["Leakage_Risk"]
    .value_counts()
    .to_dict()
)

expected_risk_counts = {
    "High": EXPECTED_HIGH_RISK_STUDIES,
    "Low": EXPECTED_LOW_RISK_STUDIES,
    "Unclear": EXPECTED_UNCLEAR_RISK_STUDIES,
}

validate_counts(
    "Overall leakage-risk",
    {
        category: int(risk_counts.get(category, 0))
        for category in expected_risk_counts
    },
    expected_risk_counts,
)




# ------------------------------------------------------------
# 13. SAVE VERIFIED COUNT TABLE
# ------------------------------------------------------------

summary_rows = []

for category, count in validation_counts.items():
    summary_rows.append(
        {
            "Panel": "A",
            "Measure": "Validation design",
            "Category": VALIDATION_LABELS[category],
            "Count": count,
            "Percentage": percentage(count),
        }
    )

for category, count in practice_counts.items():
    summary_rows.append(
        {
            "Panel": "B",
            "Measure": "Documented methodological practice",
            "Category": category,
            "Count": count,
            "Percentage": percentage(count),
        }
    )

for category, count in leakage_counts.items():
    summary_rows.append(
        {
            "Panel": "C",
            "Measure": "Passage-verified leakage mechanism",
            "Category": LEAKAGE_LABELS[category],
            "Count": count,
            "Percentage": percentage(count),
        }
    )

for category, count in expected_risk_counts.items():
    summary_rows.append(
        {
            "Panel": "C-status",
            "Measure": "Overall study-level leakage risk",
            "Category": category,
            "Count": count,
            "Percentage": percentage(count),
        }
    )

summary_df = pd.DataFrame(summary_rows)


# ------------------------------------------------------------
# 14. MATPLOTLIB SETTINGS
# ------------------------------------------------------------

plt.rcParams.update(
    {
        "font.family": "sans-serif",

        "font.sans-serif": [
            FONT_FAMILY,
            "Liberation Sans",
            "DejaVu Sans",
        ],

        "font.size": 10.2,

        "axes.labelsize": 10.8,
        "axes.titlesize": 12.8,

        "xtick.labelsize": 9.2,
        "ytick.labelsize": 9.5,

        "axes.linewidth": 0.75,
        "axes.edgecolor": "#555555",

        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",

        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


# ------------------------------------------------------------
# 15. CREATE FIGURE GRID
# ------------------------------------------------------------

# ------------------------------------------------------------
# CREATE FIGURE GRID WITH RESERVED FOOTER SPACE
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.8, 10.2),
    facecolor="white",
)

outer_grid = fig.add_gridspec(
    nrows=2,
    ncols=2,
    height_ratios=[1.0, 1.16],
    width_ratios=[1.0, 1.08],

    left=0.155,
    right=0.985,
    top=0.955,
    bottom=0.085,

    hspace=0.48,
    wspace=0.75,
)

panel_a_grid = outer_grid[0, 0].subgridspec(
    nrows=2,
    ncols=1,
    height_ratios=[0.27, 0.73],
    hspace=0.30,
)

ax_a_summary = fig.add_subplot(panel_a_grid[0, 0])
ax_a_detail = fig.add_subplot(panel_a_grid[1, 0])

ax_b = fig.add_subplot(outer_grid[0, 1])
ax_c = fig.add_subplot(outer_grid[1, :])


# ------------------------------------------------------------
# PANEL A SUMMARY STRIP — NON-OVERLAPPING VERSION
# ------------------------------------------------------------

identified_share = percentage(
    identified_design_count
)

unclear_share = percentage(
    unclear_design_count
)

ax_a_summary.barh(
    y=0,
    width=identified_share,
    left=0,
    height=0.42,
    color=VALIDATION_COLOUR,
    edgecolor="white",
    linewidth=0.7,
)

ax_a_summary.barh(
    y=0,
    width=unclear_share,
    left=identified_share,
    height=0.42,
    color=UNCLEAR_COLOUR,
    edgecolor="white",
    linewidth=0.7,
)

# Keep only compact numerical information inside the narrow segments.
ax_a_summary.text(
    identified_share / 2,
    0,
    (
        f"{identified_design_count}\n"
        f"({identified_share:.1f}%)"
    ),
    ha="center",
    va="center",
    fontsize=8.5,
    color="white",
    weight="semibold",
    linespacing=1.0,
)

ax_a_summary.text(
    identified_share + unclear_share / 2,
    0,
    (
        f"{unclear_design_count}\n"
        f"({unclear_share:.1f}%)"
    ),
    ha="center",
    va="center",
    fontsize=8.7,
    color="#303030",
    weight="semibold",
    linespacing=1.0,
)

# Place category names outside the bars so that neither is clipped.
ax_a_summary.text(
    identified_share / 2,
    -0.36,
    "Design identified",
    ha="center",
    va="top",
    fontsize=8.7,
    color=VALIDATION_COLOUR,
    weight="semibold",
)

ax_a_summary.text(
    identified_share + unclear_share / 2,
    -0.36,
    "Unclear",
    ha="center",
    va="top",
    fontsize=8.7,
    color="#62676D",
    weight="semibold",
)

ax_a_summary.set_xlim(0, 100)
ax_a_summary.set_ylim(-0.64, 0.48)

ax_a_summary.set_xticks([])
ax_a_summary.set_yticks([])

for spine in ax_a_summary.spines.values():
    spine.set_visible(False)

ax_a_summary.set_title(
    "A. Validation-design reporting",
    loc="left",
    pad=11,
    fontsize=12.5,
    weight="semibold",
)


# ------------------------------------------------------------
# 17. PANEL A DETAILED DESIGNS
# ------------------------------------------------------------

validation_labels = [
    VALIDATION_LABELS[category]
    for category in VALIDATION_DETAIL_ORDER
]

validation_values = [
    validation_counts[category]
    for category in VALIDATION_DETAIL_ORDER
]

validation_colours = [
    (
        RANDOM_COLOUR
        if category == "Random_Shuffled"
        else VALIDATION_COLOUR
    )
    for category in VALIDATION_DETAIL_ORDER
]

draw_dot_plot(
    ax=ax_a_detail,
    labels=validation_labels,
    counts=validation_values,
    colours=validation_colours,
    x_limit=66,
    tick_step=10,
)


# ------------------------------------------------------------
# 18. PANEL B DOCUMENTED PRACTICES
# ------------------------------------------------------------

practice_labels = [
    label
    for label, _ in PRACTICE_COLUMNS
]

practice_values = [
    practice_counts[label]
    for label in practice_labels
]

draw_dot_plot(
    ax=ax_b,
    labels=practice_labels,
    counts=practice_values,
    colours=[
        PRACTICE_COLOUR
    ] * len(practice_labels),
    x_limit=116,
    tick_step=20,
)

ax_b.set_title(
    "B. Explicitly documented\nmethodological practices",
    loc="left",
    pad=11,
    fontsize=12.5,
    weight="semibold",
    linespacing=1.05,
)

# ------------------------------------------------------------
# 19. PANEL C LEAKAGE SIGNALS
# ------------------------------------------------------------

leakage_labels = [
    LEAKAGE_LABELS[category]
    for category in LEAKAGE_ORDER
]

leakage_values = [
    leakage_counts[category]
    for category in LEAKAGE_ORDER
]

leakage_colours = [
    LEAKAGE_COLOUR
] * len(LEAKAGE_ORDER)

draw_dot_plot(
    ax=ax_c,
    labels=leakage_labels,
    counts=leakage_values,
    colours=leakage_colours,
    x_limit=20.5,
    tick_step=5
)

ax_c.set_title(
    "C. Specific passage-verified leakage mechanisms",
    loc="left",
    pad=10,
    weight="semibold",
)

ax_c.set_xlabel(
    "Number of studies",
    labelpad=9,
)
# ------------------------------------------------------------
# 20. FIGURE NOTE
# ------------------------------------------------------------

fig.text(
    0.50,
    0.018,
    (
        "Percentages use n = 492; Panel C categories are "
        "non-mutually exclusive (36 mechanism assignments "
        "across 32 high-risk studies)."
    ),
    ha="center",
    va="bottom",
    fontsize=8.4,
    color="#666666",
)


# ------------------------------------------------------------
# 21. EXPORT
# ------------------------------------------------------------

BASE_NAME: Final[str] = (
    "Methodological_Reliability_"
    "SCIE_Q1_Reconciled"
)

PNG_FILE = OUTPUT_DIR / f"{BASE_NAME}.png"
PDF_FILE = OUTPUT_DIR / f"{BASE_NAME}.pdf"
SVG_FILE = OUTPUT_DIR / f"{BASE_NAME}.svg"
SUMMARY_FILE = OUTPUT_DIR / f"{BASE_NAME}_Counts.csv"

summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig",
    float_format="%.4f",
)

fig.savefig(
    PDF_FILE,
    format="pdf",
    bbox_inches="tight",
    pad_inches=0.02,
)

fig.savefig(
    SVG_FILE,
    format="svg",
    bbox_inches="tight",
    pad_inches=0.02,
)

fig.savefig(
    PNG_FILE,
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.02,
)

if SHOW_FIGURE:
    plt.show()

plt.close(fig)


# ------------------------------------------------------------
# 22. FINAL REPORT
# ------------------------------------------------------------

print("\nAll count and integrity checks passed.")

print("\nPanel A:")
print(
    f"  Design identified       : "
    f"{identified_design_count} "
    f"({identified_share:.1f}%)"
)
print(
    f"  Temporally ordered      : "
    f"{temporally_ordered_count} "
    f"({percentage(temporally_ordered_count):.1f}%)"
)
print(
    f"  Random or shuffled      : "
    f"{validation_counts['Random_Shuffled']} "
    f"({percentage(validation_counts['Random_Shuffled']):.1f}%)"
)
print(
    f"  Unclear                 : "
    f"{unclear_design_count} "
    f"({unclear_share:.1f}%)"
)

print("\nPanel C:")
print(
    f"  Mechanism assignments   : "
    f"{leakage_assignment_count}"
)
print(
    f"  Unique high-risk studies: "
    f"{EXPECTED_HIGH_RISK_STUDIES}"
)
print(
    f"  Low-risk studies        : "
    f"{EXPECTED_LOW_RISK_STUDIES}"
)
print(
    f"  Unclear-risk studies    : "
    f"{EXPECTED_UNCLEAR_RISK_STUDIES}"
)

print("\nCreated files:")

for output_file in [
    PNG_FILE,
    PDF_FILE,
    SVG_FILE,
    SUMMARY_FILE,
]:
    status = (
        "created"
        if output_file.exists()
        else "not created"
    )

    print(
        f"{status:12s} : {output_file}"
    )