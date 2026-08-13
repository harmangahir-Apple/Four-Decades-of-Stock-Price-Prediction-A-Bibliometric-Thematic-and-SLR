# ============================================================
# SECTION 6 — FINAL EXPLICIT-EVIDENCE FIGURES 13 AND 14
#
# Required input files:
# 1. Section6_Input_Modality_Coding.csv
# 2. Section6_Input_Modality_Manual_Overrides_Explicit.csv
# 3. Section6_Input_Modality_Adjudication_Summary.csv
# 4. Section6_Input_Modality_FullText_Verification.csv
#
# Outputs:
# - Fig13_Input_Modality_Prevalence_DRAFT.pdf/.png
# - Fig14_Input_Modality_Period_Heatmap_DRAFT.pdf/.png
# - Section6_Explicit_Modality_Summary.csv
# - Section6_Explicit_Period_Matrix.csv
#
# After all 42 full-text cases are resolved:
# - update the explicit override file;
# - set FULLTEXT_VERIFICATION_CLOSED = True;
# - set MANUSCRIPT_READY = True.
# ============================================================

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

QUALITY_DIR = PROJECT_DIR / "06_Quality_Assessment"

AUDIT_DIR = (
    QUALITY_DIR
    / "Section6_Input_Modality_Audit"
)

FIGURE_DIR = PROJECT_DIR / "results" / "figures"

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


# Base coding file remains inside the audit folder
BASE_CODING_PATH = (
    AUDIT_DIR
    / "Section6_Input_Modality_Coding.csv"
)

# Adjudication files are directly under 06_Quality_Assessment
EXPLICIT_OVERRIDE_PATH = (
    AUDIT_DIR
    / "Section6_Input_Modality_Manual_Overrides_Explicit_Final.csv"
)

ADJUDICATION_SUMMARY_PATH = (
    QUALITY_DIR
    / "Section6_Input_Modality_Adjudication_Summary.csv"
)

FULLTEXT_VERIFICATION_PATH = (
    QUALITY_DIR
    / "Section6_Input_Modality_FullText_Verification.csv"
)


# ============================================================
# 2. FREEZE CONTROL
# ============================================================

MANUSCRIPT_READY = False
FULLTEXT_VERIFICATION_CLOSED = False

if MANUSCRIPT_READY and not FULLTEXT_VERIFICATION_CLOSED:
    raise RuntimeError(
        "MANUSCRIPT_READY cannot be True while the remaining "
        "full-text verification cases are unresolved."
    )

OUTPUT_SUFFIX = "" if MANUSCRIPT_READY else "_DRAFT"


# ============================================================
# 3. CATEGORY DEFINITIONS
# ============================================================

CATEGORY_LABELS = {
    "Historical_Market_Data":
        "Historical market data",

    "Technical_Indicators":
        "Technical indicators",

    "Financial_News_Text":
        "Financial news and textual information",

    "Index_Sector_CrossMarket":
        "Index, sectoral, relational, or cross-market context",

    "Decomposition_Transforms":
        "Decomposition or transformed representations",

    "Social_Media_Public_Opinion":
        "Social media or public-opinion information",

    "Fundamental_Accounting":
        "Fundamental or accounting information",

    "Macroeconomic_Systemic":
        "Macroeconomic or systemic variables",

    "Alternative_Attention_Data":
        "Alternative or attention-related information",
}

CATEGORY_KEYS = list(CATEGORY_LABELS)

MISSING_KEY = "No_Recoverable_Input_Category"
MISSING_LABEL = "Input modality not recoverable"

PERIOD_ORDER = [
    "2016–2020",
    "2021–2022",
    "2023–2024",
    "2025–2026",
]


# ============================================================
# 4. FILE VALIDATION
# ============================================================

required_paths = {
    "Base coding file": BASE_CODING_PATH,
    "Explicit override file": EXPLICIT_OVERRIDE_PATH,
    "Adjudication summary": ADJUDICATION_SUMMARY_PATH,
}

missing_files = [
    f"{name}: {path}"
    for name, path in required_paths.items()
    if not path.exists()
]

if missing_files:
    raise FileNotFoundError(
        "Required files were not found:\n"
        + "\n".join(missing_files)
    )


# ============================================================
# 5. LOAD AUTOMATED STUDY-LEVEL CODING
# ============================================================

coding = pd.read_csv(
    BASE_CODING_PATH,
    dtype=str,
    keep_default_na=False,
)

required_coding_columns = [
    "Paper_ID",
    "Title",
    "Year",
] + CATEGORY_KEYS

missing_columns = [
    column
    for column in required_coding_columns
    if column not in coding.columns
]

if missing_columns:
    raise KeyError(
        "The base coding file is missing required columns:\n"
        f"{missing_columns}\n\n"
        f"Available columns:\n{list(coding.columns)}"
    )

if len(coding) != 493:
    raise AssertionError(
        f"Expected 493 studies, but found {len(coding)}."
    )

if coding["Paper_ID"].duplicated().any():
    duplicate_ids = coding.loc[
        coding["Paper_ID"].duplicated(keep=False),
        ["Paper_ID", "Title"],
    ]

    raise AssertionError(
        "Duplicate Paper_ID values were found:\n"
        f"{duplicate_ids.to_string(index=False)}"
    )

coding["Year"] = pd.to_numeric(
    coding["Year"],
    errors="raise",
).astype(int)

for category in CATEGORY_KEYS:
    coding[category] = pd.to_numeric(
        coding[category],
        errors="raise",
    ).astype(int)

    invalid_values = set(
        coding[category].unique()
    ) - {0, 1}

    if invalid_values:
        raise ValueError(
            f"{category} contains values other than 0 and 1: "
            f"{invalid_values}"
        )


# ============================================================
# 6. LOAD AND APPLY EXPLICIT-EVIDENCE OVERRIDES
# ============================================================

overrides = pd.read_csv(
    EXPLICIT_OVERRIDE_PATH,
    dtype=str,
    keep_default_na=False,
)

required_override_columns = {
    "Paper_ID",
    "Category",
    "Value",
    "Evidence_Level",
    "Reviewer_Note",
}

if not required_override_columns.issubset(
    overrides.columns
):
    raise KeyError(
        "The explicit override file must contain:\n"
        f"{sorted(required_override_columns)}"
    )

overrides = overrides.loc[
    overrides["Paper_ID"].str.strip().ne("")
    & overrides["Category"].str.strip().ne("")
].copy()

duplicate_override_pairs = overrides.duplicated(
    ["Paper_ID", "Category"],
    keep=False,
)

if duplicate_override_pairs.any():
    raise ValueError(
        "Duplicate Paper_ID–Category override combinations found:\n"
        + overrides.loc[
            duplicate_override_pairs,
            ["Paper_ID", "Category", "Value"],
        ].to_string(index=False)
    )

applied_override_rows = []

for _, override in overrides.iterrows():

    paper_id = override["Paper_ID"].strip()
    category = override["Category"].strip()
    value = override["Value"].strip()

    if category not in CATEGORY_KEYS:
        raise ValueError(
            f"Unknown override category: {category}"
        )

    if value not in {"0", "1"}:
        raise ValueError(
            f"Override value must be 0 or 1. "
            f"Observed {value!r} for {paper_id}."
        )

    matching_rows = coding["Paper_ID"].eq(paper_id)

    if matching_rows.sum() != 1:
        raise ValueError(
            f"Paper_ID {paper_id} was found "
            f"{matching_rows.sum()} times."
        )

    old_value = int(
        coding.loc[matching_rows, category].iloc[0]
    )

    new_value = int(value)

    coding.loc[
        matching_rows,
        category,
    ] = new_value

    applied_override_rows.append(
        {
            "Paper_ID": paper_id,
            "Category": category,
            "Old_Value": old_value,
            "New_Value": new_value,
            "Evidence_Level":
                override["Evidence_Level"],
            "Reviewer_Note":
                override["Reviewer_Note"],
        }
    )

applied_overrides = pd.DataFrame(
    applied_override_rows
)

print("Explicit override rows applied:", len(applied_overrides))
print(
    "Distinct studies affected:",
    applied_overrides["Paper_ID"].nunique(),
)


# ============================================================
# 7. RECOMPUTE MISSINGNESS
# ============================================================

coding["Identified_Category_Count"] = (
    coding[CATEGORY_KEYS].sum(axis=1)
)

coding[MISSING_KEY] = (
    coding["Identified_Category_Count"]
    .eq(0)
    .astype(int)
)

print("\nStudies with at least one explicit category:")
print(
    int(
        coding["Identified_Category_Count"]
        .gt(0)
        .sum()
    )
)

print("Input category not recoverable:")
print(int(coding[MISSING_KEY].sum()))


# ============================================================
# 8. PUBLICATION PERIODS
# ============================================================

def assign_publication_period(year: int) -> str:
    if 2016 <= year <= 2020:
        return "2016–2020"

    if 2021 <= year <= 2022:
        return "2021–2022"

    if 2023 <= year <= 2024:
        return "2023–2024"

    if 2025 <= year <= 2026:
        return "2025–2026"

    raise ValueError(
        f"Year {year} is outside the expected period."
    )


coding["Publication_Period"] = (
    coding["Year"].map(assign_publication_period)
)

period_sizes = (
    coding["Publication_Period"]
    .value_counts()
    .reindex(PERIOD_ORDER)
)

expected_period_sizes = pd.Series(
    {
        "2016–2020": 27,
        "2021–2022": 36,
        "2023–2024": 49,
        "2025–2026": 381,
    }
)

if not period_sizes.equals(expected_period_sizes):
    raise AssertionError(
        "Unexpected publication-period counts.\n\n"
        f"Observed:\n{period_sizes}\n\n"
        f"Expected:\n{expected_period_sizes}"
    )


# ============================================================
# 9. FINAL EXPLICIT-EVIDENCE SUMMARY
# ============================================================

summary_rows = []

for category in CATEGORY_KEYS:

    count = int(coding[category].sum())

    summary_rows.append(
        {
            "Category_Key": category,
            "Category": CATEGORY_LABELS[category],
            "Studies": count,
            "Share_Percent":
                100 * count / len(coding),
            "Evidence_Class":
                "Explicit input modality",
        }
    )

missing_count = int(coding[MISSING_KEY].sum())

summary_rows.append(
    {
        "Category_Key": MISSING_KEY,
        "Category": MISSING_LABEL,
        "Studies": missing_count,
        "Share_Percent":
            100 * missing_count / len(coding),
        "Evidence_Class":
            "Evidence-recovery status",
    }
)

summary = pd.DataFrame(summary_rows)


# ============================================================
# 10. VALIDATE AGAINST ADJUDICATION SUMMARY
# ============================================================

expected_summary = pd.read_csv(
    ADJUDICATION_SUMMARY_PATH,
    dtype=str,
    keep_default_na=False,
)

required_summary_columns = {
    "Category_Key",
    "Post_Adjudication_Explicit_Count",
}

missing_summary_columns = (
    required_summary_columns
    - set(expected_summary.columns)
)

if missing_summary_columns:
    raise KeyError(
        "The adjudication-summary file is missing columns: "
        f"{sorted(missing_summary_columns)}"
    )

expected_summary[
    "Post_Adjudication_Explicit_Count"
] = pd.to_numeric(
    expected_summary[
        "Post_Adjudication_Explicit_Count"
    ],
    errors="raise",
).astype(int)

expected_counts = dict(
    zip(
        expected_summary["Category_Key"],
        expected_summary[
            "Post_Adjudication_Explicit_Count"
        ],
    )
)

observed_counts = dict(
    zip(
        summary["Category_Key"],
        summary["Studies"],
    )
)

all_category_keys = sorted(
    set(expected_counts)
    | set(observed_counts)
)

comparison_rows = []

for category_key in all_category_keys:

    expected_count = expected_counts.get(
        category_key
    )

    observed_count = observed_counts.get(
        category_key
    )

    comparison_rows.append(
        {
            "Category_Key": category_key,
            "Expected_Count": expected_count,
            "Observed_Count": observed_count,
            "Difference": (
                observed_count - expected_count
                if (
                    expected_count is not None
                    and observed_count is not None
                )
                else np.nan
            ),
            "Matches": (
                expected_count == observed_count
            ),
        }
    )

comparison = pd.DataFrame(
    comparison_rows
)

count_mismatches = comparison.loc[
    ~comparison["Matches"]
].copy()

validation_passed = count_mismatches.empty


# ------------------------------------------------------------
# Export the reconciliation evidence
# ------------------------------------------------------------

comparison_output = (
    AUDIT_DIR
    / "Section6_Adjudication_Count_Comparison.csv"
)

comparison.to_csv(
    comparison_output,
    index=False,
    encoding="utf-8-sig",
)


# ------------------------------------------------------------
# Create a regenerated summary candidate
# ------------------------------------------------------------

regenerated_summary = expected_summary.copy()

regenerated_summary[
    "Post_Adjudication_Explicit_Count"
] = regenerated_summary[
    "Category_Key"
].map(observed_counts)

unmapped_rows = regenerated_summary[
    "Post_Adjudication_Explicit_Count"
].isna()

if unmapped_rows.any():
    raise AssertionError(
        "Some adjudication-summary categories could not be "
        "mapped to regenerated counts:\n"
        + regenerated_summary.loc[
            unmapped_rows,
            ["Category_Key"],
        ].to_string(index=False)
    )

regenerated_summary[
    "Post_Adjudication_Explicit_Count"
] = regenerated_summary[
    "Post_Adjudication_Explicit_Count"
].astype(int)

regenerated_summary_output = (
    AUDIT_DIR
    / (
        "Section6_Input_Modality_"
        "Adjudication_Summary_REGENERATED.csv"
    )
)

regenerated_summary.to_csv(
    regenerated_summary_output,
    index=False,
    encoding="utf-8-sig",
)


# ------------------------------------------------------------
# Validation decision
# ------------------------------------------------------------

if validation_passed:

    print(
        "\nPASSED: Regenerated counts match the "
        "adjudication summary."
    )

else:

    mismatch_message = (
        "\nThe regenerated explicit counts do not match "
        "the current adjudication summary:\n\n"
        + count_mismatches.to_string(index=False)
        + "\n\nComparison file:\n"
        + str(comparison_output)
        + "\n\nRegenerated summary candidate:\n"
        + str(regenerated_summary_output)
    )

    if MANUSCRIPT_READY:
        raise AssertionError(
            mismatch_message
        )

    print(
        "\nWARNING: Draft-mode count mismatch detected."
    )

    print(mismatch_message)

    print(
        "\nDraft figure generation will continue. "
        "Do not use the outputs as final manuscript figures "
        "until the regenerated summary has been reviewed and "
        "approved."
    )


print("\nEXPLICIT-EVIDENCE SUMMARY")
print("-------------------------")

print(
    summary[
        [
            "Category",
            "Studies",
            "Share_Percent",
        ]
    ]
    .assign(
        Share_Percent=lambda frame:
        frame["Share_Percent"].round(1)
    )
    .to_string(index=False)
)


# ============================================================
# 11. REPORT UNRESOLVED FULL-TEXT CASES
# ============================================================

pending_fulltext_count = 0

if FULLTEXT_VERIFICATION_PATH.exists():

    pending_fulltext = pd.read_csv(
        FULLTEXT_VERIFICATION_PATH,
        dtype=str,
        keep_default_na=False,
    )

    pending_fulltext_count = len(pending_fulltext)

print("\nFull-text verification records remaining:")
print(pending_fulltext_count)

if MANUSCRIPT_READY and pending_fulltext_count > 0:
    raise RuntimeError(
        "Final manuscript figures cannot be generated while "
        f"{pending_fulltext_count} full-text cases remain."
    )


# ============================================================
# 12. SAVE FINAL ANALYTICAL TABLES
# ============================================================

summary_output = (
    AUDIT_DIR
    / "Section6_Explicit_Modality_Summary.csv"
)

coding_output = (
    AUDIT_DIR
    / "Section6_Explicit_Modality_Coding.csv"
)

override_log_output = (
    AUDIT_DIR
    / "Section6_Applied_Explicit_Overrides.csv"
)

summary.to_csv(
    summary_output,
    index=False,
    encoding="utf-8-sig",
)

coding.to_csv(
    coding_output,
    index=False,
    encoding="utf-8-sig",
)

applied_overrides.to_csv(
    override_log_output,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 13. FIGURE 13 DATA ORDER
# ============================================================

modality_summary = (
    summary.loc[
        summary["Category_Key"].ne(MISSING_KEY)
    ]
    .sort_values(
        ["Studies", "Category"],
        ascending=[False, True],
    )
    .reset_index(drop=True)
)

missing_summary = summary.loc[
    summary["Category_Key"].eq(MISSING_KEY)
].reset_index(drop=True)

figure13_summary = pd.concat(
    [
        modality_summary,
        missing_summary,
    ],
    ignore_index=True,
)


# ============================================================
# 14. MATPLOTLIB SETTINGS
# ============================================================
FONT_FAMILY = "serif"
plt.rcParams.update(
    {
        "font.family": FONT_FAMILY,
        "font.serif": [
            "Times New Roman",
            "STIXGeneral",
            "DejaVu Serif",
        ],
        "font.size": 9.0,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "axes.linewidth": 0.6,
        "axes.edgecolor": "0.35",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


# ============================================================
# 15. GENERATE FIGURE 13
# ============================================================

fig13_pdf = (
    FIGURE_DIR
    / f"Fig13_Input_Modality_Prevalence"
      f"{OUTPUT_SUFFIX}.pdf"
)

fig13_png = (
    FIGURE_DIR
    / f"Fig13_Input_Modality_Prevalence"
      f"{OUTPUT_SUFFIX}.png"
)

number_of_modalities = len(modality_summary)

y_positions = list(
    np.arange(number_of_modalities)
)

# Add a visual gap before the evidence-recovery bar.
missing_position = number_of_modalities + 0.75
y_positions.append(missing_position)

labels = figure13_summary["Category"].tolist()
counts = figure13_summary["Studies"].to_numpy()
shares = figure13_summary[
    "Share_Percent"
].to_numpy()

fig, ax = plt.subplots(
    figsize=(9.4, 6.0)
)

bars = ax.barh(
    y_positions,
    counts,
)

# Distinguish missingness from actual input modalities.
bars[-1].set_hatch("///")

ax.set_yticks(y_positions)
ax.set_yticklabels(labels)
ax.invert_yaxis()

ax.set_xlabel("Number of studies")
ax.set_ylabel("")

ax.xaxis.grid(
    True,
    linestyle="--",
    linewidth=0.6,
    alpha=0.35,
)

ax.set_axisbelow(True)

maximum_count = int(max(counts))
label_offset = max(2, maximum_count * 0.012)

for bar, count, share in zip(
    bars,
    counts,
    shares,
):
    ax.text(
        bar.get_width() + label_offset,
        bar.get_y() + bar.get_height() / 2,
        f"{int(count)} ({share:.1f}%)",
        va="center",
        ha="left",
        fontsize=9,
    )

# Separator between modalities and missingness.
ax.axhline(
    number_of_modalities - 0.10,
    linewidth=0.8,
    linestyle=":",
)

ax.set_xlim(
    0,
    maximum_count * 1.25,
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.subplots_adjust(
    left=0.43,
    right=0.97,
    top=0.98,
    bottom=0.12,
)

fig.savefig(
    fig13_pdf,
    bbox_inches="tight",
)

fig.savefig(
    fig13_png,
    dpi=600,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)

print("\nFigure 13 saved:")
print(fig13_pdf)
print(fig13_png)


# ============================================================
# 16. GENERATE FIGURE 14 MATRIX
# ============================================================

heatmap_columns = CATEGORY_KEYS + [MISSING_KEY]

period_matrix = (
    coding.groupby(
        "Publication_Period",
        observed=False,
    )[heatmap_columns]
    .mean()
    .mul(100)
    .reindex(PERIOD_ORDER)
    .T
)

# Keep the same modality order as Figure 13.
heatmap_row_keys = (
    modality_summary["Category_Key"].tolist()
    + [MISSING_KEY]
)

period_matrix = period_matrix.reindex(
    heatmap_row_keys
)

period_matrix.index = [
    CATEGORY_LABELS.get(
        key,
        MISSING_LABEL,
    )
    for key in period_matrix.index
]

period_matrix_output = (
    AUDIT_DIR
    / "Section6_Explicit_Period_Matrix.csv"
)

period_matrix.to_csv(
    period_matrix_output,
    encoding="utf-8-sig",
)

print("\nWITHIN-PERIOD EXPLICIT-EVIDENCE MATRIX (%)")
print("------------------------------------------")

print(
    period_matrix
    .round(1)
    .to_string()
)


# ============================================================
# 17. GENERATE FIGURE 15
# ============================================================

fig14_pdf = (
    FIGURE_DIR
    / f"Fig15_Input_Modality_Period_Heatmap"
      f"{OUTPUT_SUFFIX}.pdf"
)

fig14_svg = (
    FIGURE_DIR
    / f"Fig15_Input_Modality_Period_Heatmap"
      f"{OUTPUT_SUFFIX}.svg"
)

fig14_png = (
    FIGURE_DIR
    / f"Fig15_Input_Modality_Period_Heatmap"
      f"{OUTPUT_SUFFIX}.png"
)

fig14_tiff = (
    FIGURE_DIR
    / f"Fig15_Input_Modality_Period_Heatmap"
      f"{OUTPUT_SUFFIX}.tiff"
)

heatmap_values = period_matrix.to_numpy(dtype=float)

period_labels = [
    f"{period}\n(n={int(period_sizes[period])})"
    for period in PERIOD_ORDER
]

fig, ax = plt.subplots(
    figsize=(7.55, 5.55)
)

# A genuine percentage scale is used for interpretability.
# Every period is therefore compared on the same 0--100% basis.
normalization = Normalize(
    vmin=0,
    vmax=100,
)

image = ax.imshow(
    heatmap_values,
    aspect="auto",
    cmap="viridis",
    norm=normalization,
    interpolation="nearest",
)

print(
    "Heatmap normalization:",
    type(image.norm).__name__,
    f"(vmin={image.norm.vmin}, vmax={image.norm.vmax})",
)

# Column labels are placed above the matrix to reduce unused
# lower-page space and improve manuscript readability.
ax.set_xticks(
    np.arange(len(PERIOD_ORDER))
)

ax.set_xticklabels(
    period_labels,
)

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

ax.set_yticks(
    np.arange(len(period_matrix.index))
)

ax.set_yticklabels(
    period_matrix.index,
)

ax.tick_params(
    axis="y",
    which="major",
    length=0,
    pad=7,
)

# Fine cell boundaries improve separation in print.
ax.set_xticks(
    np.arange(-0.5, len(PERIOD_ORDER), 1),
    minor=True,
)

ax.set_yticks(
    np.arange(-0.5, len(period_matrix.index), 1),
    minor=True,
)

ax.grid(
    which="minor",
    color="0.80",
    linewidth=0.55,
)

ax.tick_params(
    which="minor",
    bottom=False,
    left=False,
)

# Separate the evidence-recovery status row from true modalities.
missing_row_index = len(period_matrix.index) - 1

ax.axhline(
    missing_row_index - 0.5,
    color="0.35",
    linewidth=0.9,
    linestyle=":",
)

# Adaptive text colour is based on the displayed cell colour.
for row_index in range(
    heatmap_values.shape[0]
):
    for column_index in range(
        heatmap_values.shape[1]
    ):
        value = float(
            heatmap_values[
                row_index,
                column_index,
            ]
        )

        rgba = image.cmap(
            image.norm(value)
        )

        luminance = (
            0.2126 * rgba[0]
            + 0.7152 * rgba[1]
            + 0.0722 * rgba[2]
        )

        text_colour = (
            "white"
            if luminance < 0.48
            else "black"
        )

        # Keep zero values visible but visually subordinate.
        if np.isclose(value, 0.0):
            annotation = "0.0"
            text_colour = "0.55"
            font_weight = "normal"
        else:
            annotation = f"{value:.1f}"
            font_weight = (
                "bold"
                if value >= 50
                else "normal"
            )

        ax.text(
            column_index,
            row_index,
            annotation,
            ha="center",
            va="center",
            fontsize=7.9,
            color=text_colour,
            fontweight=font_weight,
        )

colour_bar = fig.colorbar(
    image,
    ax=ax,
    pad=0.028,
    fraction=0.038,
)

colour_bar.set_label(
    "Studies within period (%)",
    labelpad=8,
)

colour_bar.set_ticks(
    [0, 20, 40, 60, 80, 100]
)

colour_bar.ax.tick_params(
    labelsize=8,
)

ax.set_xlabel("")
ax.set_ylabel("")

for spine in ax.spines.values():
    spine.set_visible(False)

fig.subplots_adjust(
    left=0.44,
    right=0.90,
    top=0.80,
    bottom=0.06,
)

fig.savefig(
    fig14_pdf,
    bbox_inches="tight",
)

fig.savefig(
    fig14_svg,
    bbox_inches="tight",
)

fig.savefig(
    fig14_png,
    dpi=600,
    bbox_inches="tight",
)

fig.savefig(
    fig14_tiff,
    dpi=600,
    bbox_inches="tight",
    pil_kwargs={
        "compression": "tiff_lzw",
    },
)

plt.show()
plt.close(fig)

print("\nFigure 15 saved:")
print(fig14_pdf)
print(fig14_svg)
print(fig14_png)
print(fig14_tiff)


# ============================================================
# 18. FINAL STATUS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 6 FIGURE GENERATION STATUS")
print("=" * 70)

print("Evidence basis: explicit-evidence adjudication")
print("Studies:", len(coding))
print("Explicit override rows:", len(applied_overrides))
print("Input category not recoverable:", missing_count)
print("Full-text verification pending:", pending_fulltext_count)
print("Manuscript-ready mode:", MANUSCRIPT_READY)

if not MANUSCRIPT_READY:
    print(
        "\nDraft figures generated. Do not remove the '_DRAFT' "
        "suffix until the remaining full-text cases have been "
        "resolved and the explicit override file has been updated."
    )
else:
    print(
        "\nFinal manuscript figures generated successfully."
    )