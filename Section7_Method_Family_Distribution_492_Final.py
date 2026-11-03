from __future__ import annotations

from pathlib import Path
from typing import Final
import textwrap

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# PRINCIPAL METHOD-FAMILY DISTRIBUTION
# Frozen 492-study technical-synthesis subset
# SCIE Q1-ready horizontal bar chart
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT AND INPUT SETTINGS
# ------------------------------------------------------------

PROJECT_DIR: Final[Path] = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

COMPILED_FILENAME: Final[str] = "Compiled Files.xlsx"
REVIEW_QUEUE_FILENAME: Final[str] = "Section7_Method_Family_Review_Queue.csv"
BASELINE_FAMILY_FILENAME: Final[str] = "Section7_Final_Study_Level_Sankey_Input.csv"

CODING_SHEET: Final[str] = "Section5_Coding_Consolidated"
INCLUDED_STATUS: Final[str] = "Included_High_Priority"

COMPILED_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / COMPILED_FILENAME,
    PROJECT_DIR / "07_Reference_Outputs" / COMPILED_FILENAME,
    Path(COMPILED_FILENAME),
    Path("/mnt/data") / COMPILED_FILENAME,
]

REVIEW_QUEUE_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / "07_Reference_Outputs" / REVIEW_QUEUE_FILENAME,
    PROJECT_DIR / REVIEW_QUEUE_FILENAME,
    PROJECT_DIR / "Figure17_Output" / REVIEW_QUEUE_FILENAME,
    PROJECT_DIR / "13_Systematic_Review_Section5" / REVIEW_QUEUE_FILENAME,
    Path(REVIEW_QUEUE_FILENAME),
    Path("/mnt/data") / REVIEW_QUEUE_FILENAME,
]

# IMPORTANT:
# The review queue is retained for audit/provenance, but its
# Principal_Method_Family field is NOT the frozen family map.
# The finalized pre-reconciliation family assignment is taken from the
# study-level Sankey input, then constrained to the 492 IDs in Compiled Files.xlsx.
BASELINE_FAMILY_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / "07_Reference_Outputs" / BASELINE_FAMILY_FILENAME,
    PROJECT_DIR / "14_Sankey" / BASELINE_FAMILY_FILENAME,
    PROJECT_DIR / BASELINE_FAMILY_FILENAME,
    PROJECT_DIR / "Figure17_Output" / BASELINE_FAMILY_FILENAME,
    Path(BASELINE_FAMILY_FILENAME),
    Path("/mnt/data") / BASELINE_FAMILY_FILENAME,
]

OUTPUT_DIR: Final[Path] = PROJECT_DIR / "Method_Family_Distribution_Output"

# Fall back to a local output directory when the project directory is not
# available (useful for testing a copied script).
if not PROJECT_DIR.exists():
    OUTPUT_DIR = Path("Method_Family_Distribution_Output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. FROZEN COUNTS AND FINAL ADJUDICATIONS
# ------------------------------------------------------------

EXPECTED_STUDIES: Final[int] = 492
EXPECTED_LEGACY_ROWS: Final[int] = 493

EXPECTED_FAMILY_COUNTS: Final[dict[str, int]] = {
    "Deep-learning models": 117,
    "Hybrid deep-learning models": 110,
    "Sentiment/NLP-driven models": 80,
    "Transformer/attention-based models": 68,
    "Metaheuristic-optimized models": 51,
    "Ensemble/tree-based machine learning": 33,
    "Graph-based models": 16,
    "Multimodal-fusion models": 13,
    "Other/unclear": 3,
    "ANN/neuro-fuzzy models": 1,
}

assert sum(EXPECTED_FAMILY_COUNTS.values()) == EXPECTED_STUDIES

# These are the final study-level family reconciliations after full-text review.
FINAL_FAMILY_OVERRIDES: Final[dict[str, str]] = {
    "P00057": "Deep-learning models",
    "P00909": "Hybrid deep-learning models",
    "P03446": "Other/unclear",
}

# P04845 is not part of the final 492-study technical-synthesis dataset.
EXPECTED_REMOVED_IDS: Final[set[str]] = {"P04845"}


# ------------------------------------------------------------
# 3. FIGURE SETTINGS
# ------------------------------------------------------------

FIGURE_WIDTH: Final[float] = 11.8
FIGURE_HEIGHT: Final[float] = 7.1
PNG_DPI: Final[int] = 600

FONT_FAMILY: Final[str] = "serif"
BAR_COLOUR: Final[str] = "#3F83A6"
TEXT_COLOUR: Final[str] = "#222222"
GRID_COLOUR: Final[str] = "#B8B8B8"

ADD_FIGURE_TITLE: Final[bool] = False
FIGURE_TITLE: Final[str] = (
    "Distribution of the 492-study technical-synthesis subset across "
    "principal computational-intelligence method families"
)


# ------------------------------------------------------------
# 4. INPUT DISCOVERY
# ------------------------------------------------------------

def find_file(
    filename: str,
    candidates: list[Path],
    *,
    allow_recursive: bool = True,
) -> Path:
    """Locate exactly one intended input file."""

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    if allow_recursive and PROJECT_DIR.exists():
        matches = list(PROJECT_DIR.rglob(filename))

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            formatted = "\n".join(str(path) for path in matches)
            raise RuntimeError(
                f"More than one {filename!r} file was found:\n{formatted}\n\n"
                "Put the intended path first in the corresponding candidate list."
            )

    checked = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(
        f"Required input file {filename!r} was not found.\n\n"
        f"Checked locations:\n{checked}"
    )


# ------------------------------------------------------------
# 5. LABEL FORMATTING
# ------------------------------------------------------------

DISPLAY_LABELS: Final[dict[str, str]] = {
    "Deep-learning models": "Deep-learning models",
    "Hybrid deep-learning models": "Hybrid deep-learning models",
    "Sentiment/NLP-driven models": "Sentiment/NLP-driven models",
    "Transformer/attention-based models": "Transformer/attention-based models",
    "Metaheuristic-optimized models": "Metaheuristic-optimized models",
    "Ensemble/tree-based machine learning": "Ensemble/tree-based\nmachine learning",
    "Graph-based models": "Graph-based models",
    "Multimodal-fusion models": "Multimodal-fusion models",
    "Other/unclear": "Other/unclear",
    "ANN/neuro-fuzzy models": "ANN/neuro-fuzzy models",
}


def format_method_label(value: str) -> str:
    value = str(value).strip()

    if value in DISPLAY_LABELS:
        return DISPLAY_LABELS[value]

    return "\n".join(
        textwrap.wrap(
            value,
            width=36,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]

    for column in frame.columns:
        frame[column] = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return frame


# ------------------------------------------------------------
# 6. LOCATE AND LOAD INPUTS
# ------------------------------------------------------------

compiled_file = find_file(COMPILED_FILENAME, COMPILED_CANDIDATES)
review_queue_file = find_file(REVIEW_QUEUE_FILENAME, REVIEW_QUEUE_CANDIDATES)
baseline_family_file = find_file(
    BASELINE_FAMILY_FILENAME,
    BASELINE_FAMILY_CANDIDATES,
)

print("\nCompiled workbook:")
print(compiled_file)

print("\nMethod-family review queue:")
print(review_queue_file)

print("\nFinalized baseline family map:")
print(baseline_family_file)

coding_all = pd.read_excel(
    compiled_file,
    sheet_name=CODING_SHEET,
    dtype=str,
    keep_default_na=False,
    engine="openpyxl",
)

review_queue = pd.read_csv(
    review_queue_file,
    dtype=str,
    keep_default_na=False,
    encoding="utf-8-sig",
)

baseline_all = pd.read_csv(
    baseline_family_file,
    dtype=str,
    keep_default_na=False,
    encoding="utf-8-sig",
)

coding_all = clean_dataframe(coding_all)
review_queue = clean_dataframe(review_queue)
baseline_all = clean_dataframe(baseline_all)


# ------------------------------------------------------------
# 7. VALIDATE INPUT SCHEMAS
# ------------------------------------------------------------

required_coding_columns = {
    "Paper_ID",
    "Systematic_Inclusion_Status",
}

required_review_columns = {
    "Paper_ID",
    "Title",
    "Method_Category",
    "Specific_Model",
    "Principal_Method_Family",
}

required_baseline_columns = {
    "Paper_ID",
    "Principal_Method_Family",
}

for name, frame, required in [
    ("Compiled Files.xlsx", coding_all, required_coding_columns),
    ("Section7_Method_Family_Review_Queue.csv", review_queue, required_review_columns),
    ("Section7_Final_Study_Level_Sankey_Input.csv", baseline_all, required_baseline_columns),
]:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(
            f"{name} is missing required columns:\n{missing}\n\n"
            f"Available columns:\n{list(frame.columns)}"
        )


# ------------------------------------------------------------
# 8. DEFINE THE AUTHORITATIVE FINAL 492-STUDY SET
# ------------------------------------------------------------

coding = coding_all.loc[
    coding_all["Systematic_Inclusion_Status"].eq(INCLUDED_STATUS)
].copy()

if len(coding) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} final included studies in the compiled "
        f"workbook; found {len(coding)}."
    )

if coding["Paper_ID"].eq("").any():
    raise AssertionError("Blank Paper_ID values found in the compiled register.")

if coding["Paper_ID"].nunique() != EXPECTED_STUDIES:
    raise AssertionError(
        "The compiled 492-study register contains duplicate Paper_ID values."
    )

final_ids = set(coding["Paper_ID"])


# ------------------------------------------------------------
# 9. AUDIT THE LEGACY 493-ROW FILES AGAINST THE FINAL WORKBOOK
# ------------------------------------------------------------

for name, frame in [
    ("review queue", review_queue),
    ("baseline family map", baseline_all),
]:
    if len(frame) != EXPECTED_LEGACY_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_LEGACY_ROWS} rows in the legacy {name}; "
            f"found {len(frame)}."
        )

    if frame["Paper_ID"].nunique() != EXPECTED_LEGACY_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_LEGACY_ROWS} unique Paper_ID values in the "
            f"legacy {name}."
        )

    extra_ids = set(frame["Paper_ID"]) - final_ids
    missing_ids = final_ids - set(frame["Paper_ID"])

    if extra_ids != EXPECTED_REMOVED_IDS:
        raise AssertionError(
            f"Unexpected IDs in legacy {name} but not in the frozen workbook:\n"
            f"{sorted(extra_ids)}\n"
            f"Expected only: {sorted(EXPECTED_REMOVED_IDS)}"
        )

    if missing_ids:
        raise AssertionError(
            f"Frozen study IDs missing from legacy {name}:\n{sorted(missing_ids)}"
        )

print("\nLegacy record removed by final full-text reconciliation:")
print(sorted(EXPECTED_REMOVED_IDS))


# ------------------------------------------------------------
# 10. BUILD THE FINAL 492-STUDY FAMILY REGISTER
# ------------------------------------------------------------

# The review queue is not used as the final family map because its
# Principal_Method_Family column reflects a different/provisional grouping.
# We nevertheless retain its descriptors in the exported audit table.

family_df = baseline_all.loc[
    baseline_all["Paper_ID"].isin(final_ids)
].copy()

if len(family_df) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} baseline family rows after workbook "
        f"filtering; found {len(family_df)}."
    )

if family_df["Paper_ID"].nunique() != EXPECTED_STUDIES:
    raise AssertionError(
        "Duplicate Paper_ID values remain in the filtered baseline family map."
    )

# Apply only the final adjudicated corrections.
for paper_id, final_family in FINAL_FAMILY_OVERRIDES.items():
    mask = family_df["Paper_ID"].eq(paper_id)

    if int(mask.sum()) != 1:
        raise AssertionError(
            f"{paper_id} must occur exactly once in the baseline family map."
        )

    family_df.loc[mask, "Principal_Method_Family"] = final_family

if family_df["Principal_Method_Family"].eq("").any():
    bad_ids = family_df.loc[
        family_df["Principal_Method_Family"].eq(""),
        "Paper_ID",
    ].tolist()
    raise AssertionError(
        "Blank Principal_Method_Family values found for:\n"
        f"{bad_ids}"
    )

# Add review-queue descriptors for traceability without using the queue's
# provisional Principal_Method_Family field as the final classification.
review_descriptors = review_queue.loc[
    review_queue["Paper_ID"].isin(final_ids),
    [
        "Paper_ID",
        "Title",
        "Method_Category",
        "Specific_Model",
        "Principal_Method_Family",
    ],
].rename(
    columns={
        "Principal_Method_Family": "Review_Queue_Family",
    }
)

family_df = family_df.merge(
    review_descriptors,
    on="Paper_ID",
    how="left",
    validate="one_to_one",
)

if len(family_df) != EXPECTED_STUDIES:
    raise AssertionError("Descriptor merge changed the final study count.")

# This is the dataframe used for the figure.
df = family_df.copy()


# ------------------------------------------------------------
# 11. CALCULATE AND STRICTLY VALIDATE FINAL COUNTS
# ------------------------------------------------------------

summary_df = (
    df["Principal_Method_Family"]
    .value_counts()
    .rename_axis("Principal_Method_Family")
    .reset_index(name="Count")
)

summary_df["Percentage"] = (
    summary_df["Count"] / EXPECTED_STUDIES * 100.0
)

observed_family_counts = (
    summary_df
    .set_index("Principal_Method_Family")["Count"]
    .astype(int)
    .to_dict()
)

if observed_family_counts != EXPECTED_FAMILY_COUNTS:
    rows = []

    for category in sorted(
        set(EXPECTED_FAMILY_COUNTS) | set(observed_family_counts)
    ):
        expected = int(EXPECTED_FAMILY_COUNTS.get(category, 0))
        observed = int(observed_family_counts.get(category, 0))

        if expected != observed:
            rows.append(
                {
                    "Method_Family": category,
                    "Expected": expected,
                    "Observed": observed,
                }
            )

    comparison_df = pd.DataFrame(rows)

    raise AssertionError(
        "Method-family distribution differs from the frozen 492-study "
        "register:\n\n"
        + comparison_df.to_string(index=False)
    )

if int(summary_df["Count"].sum()) != EXPECTED_STUDIES:
    raise AssertionError(
        "Method-family counts do not total "
        f"{EXPECTED_STUDIES}."
    )

if len(summary_df) != 10:
    raise AssertionError(
        "Expected 10 principal method families; "
        f"found {len(summary_df)}."
    )

family_lookup = df.set_index("Paper_ID")["Principal_Method_Family"].to_dict()

for paper_id, expected_family in FINAL_FAMILY_OVERRIDES.items():
    observed_family = family_lookup.get(paper_id)

    if observed_family != expected_family:
        raise AssertionError(
            f"{paper_id}: expected {expected_family!r}, "
            f"found {observed_family!r}."
        )

if "P04845" in family_lookup:
    raise AssertionError(
        "P04845 must not remain in the frozen 492-study technical synthesis."
    )

# Prepare display labels and plot order (smallest at bottom, largest at top).
summary_df["Display_Label"] = summary_df[
    "Principal_Method_Family"
].map(format_method_label)

summary_df = (
    summary_df
    .sort_values(
        by=["Count", "Principal_Method_Family"],
        ascending=[True, True],
    )
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# 12. MATPLOTLIB PUBLICATION SETTINGS
# ------------------------------------------------------------

plt.rcParams.update(
    {
        "font.family": FONT_FAMILY,
        "font.serif": [
            "Times New Roman",
            "Times",
            "DejaVu Serif",
        ],
        "font.size": 10.5,
        "axes.labelsize": 11.5,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10.5,
        "axes.linewidth": 0.75,
        "axes.edgecolor": "#4A4A4A",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


# ------------------------------------------------------------
# 13. CREATE FIGURE
# ------------------------------------------------------------

# ------------------------------------------------------------
# BAR COLORS
# Match the original blue-shaded style from the previous figure
# ------------------------------------------------------------

FAMILY_COLORS = [
    "#2f7fb5",  # Deep-learning models
    "#3f8fc0",  # Hybrid deep-learning models
    "#5497c4",  # Sentiment/NLP-driven models
    "#6aa5cb",  # Transformer/attention-based models
    "#7fb1d1",  # Metaheuristic-optimized models
    "#92bdd8",  # Ensemble/tree-based machine learning
    "#a6c9df",  # Graph-based models
    "#b9d4e5",  # Multimodal-fusion models
    "#cddfeb",  # Other/unclear
    "#dce9f2",  # ANN/neuro-fuzzy models
]

fig, ax = plt.subplots(
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT)
)

bars = ax.barh(
    summary_df["Principal_Method_Family"],
    summary_df["Count"],
    color=FAMILY_COLORS[:len(summary_df)],
    edgecolor="#5f6f7a",
    linewidth=0.7,
    zorder=3,
)

maximum_count = float(summary_df["Count"].max())
label_offset = maximum_count * 0.012

for bar, count, percentage in zip(
    bars,
    summary_df["Count"],
    summary_df["Percentage"],
):
    ax.text(
        bar.get_width() + label_offset,
        bar.get_y() + bar.get_height() / 2,
        f"{int(count)} ({percentage:.1f}%)",
        ha="left",
        va="center",
        fontsize=10,
        color=TEXT_COLOUR,
        clip_on=False,
        zorder=5,
    )

right_limit = maximum_count * 1.19
ax.set_xlim(0, right_limit)

ax.set_xlabel("Number of studies", labelpad=8)
ax.set_ylabel(
    "Principal computational-intelligence method family",
    labelpad=14,
)

ax.xaxis.grid(
    True,
    which="major",
    linestyle=(0, (3, 3)),
    linewidth=0.65,
    color=GRID_COLOUR,
    alpha=0.55,
    zorder=0,
)

ax.yaxis.grid(False)

ax.tick_params(
    axis="both",
    which="major",
    direction="out",
    length=3.5,
    width=0.7,
    color="#444444",
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color("#4A4A4A")
ax.tick_params(axis="y", length=0)

ax.set_title(
    "Distribution of the 492-study technical-synthesis subset across\n"
    "principal computational-intelligence method families",
    fontsize=15,
    fontweight="normal",
    pad=10,
)

# Sample-size note.
ax.text(
    0.995,
    0.018,
    rf"$n={EXPECTED_STUDIES}$",
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    fontsize=10,
    color="#555555",
)

fig.subplots_adjust(
    left=0.355,
    right=0.955,
    top=0.955,
    bottom=0.125,
)


# ------------------------------------------------------------
# 14. EXPORT
# ------------------------------------------------------------

base_name = "Principal_Method_Family_Distribution_492_SCIE_Q1_Final"

png_file = OUTPUT_DIR / f"{base_name}.png"
pdf_file = OUTPUT_DIR / f"{base_name}.pdf"
svg_file = OUTPUT_DIR / f"{base_name}.svg"
summary_file = OUTPUT_DIR / f"{base_name}_Counts.csv"
audit_file = OUTPUT_DIR / f"{base_name}_Study_Level_Audit.csv"

summary_export = (
    summary_df[
        [
            "Principal_Method_Family",
            "Count",
            "Percentage",
        ]
    ]
    .sort_values("Count", ascending=False)
    .reset_index(drop=True)
)

summary_export.to_csv(
    summary_file,
    index=False,
    encoding="utf-8-sig",
    float_format="%.4f",
)

# Study-level audit export preserves the final family assignment and the
# review-queue family field side-by-side for transparent reconciliation.
audit_columns = [
    "Paper_ID",
    "Principal_Method_Family",
    "Review_Queue_Family",
    "Title",
    "Method_Category",
    "Specific_Model",
]

available_audit_columns = [
    column for column in audit_columns if column in df.columns
]

df[available_audit_columns].sort_values("Paper_ID").to_csv(
    audit_file,
    index=False,
    encoding="utf-8-sig",
)

fig.savefig(
    png_file,
    dpi=PNG_DPI,
    bbox_inches="tight",
    pad_inches=0.04,
)

fig.savefig(
    pdf_file,
    format="pdf",
    bbox_inches="tight",
    pad_inches=0.04,
)

fig.savefig(
    svg_file,
    format="svg",
    bbox_inches="tight",
    pad_inches=0.04,
)

plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 15. FINAL REPORT
# ------------------------------------------------------------

print("\nValidation passed:")
print(f"  Frozen study rows      : {len(df):,}")
print(f"  Unique Paper_ID        : {df['Paper_ID'].nunique():,}")
print(f"  Principal families     : {len(summary_df):,}")
print(f"  Total family count     : {int(summary_df['Count'].sum()):,}")

print("\nFinal adjudicated records:")
for paper_id, family in FINAL_FAMILY_OVERRIDES.items():
    print(f"  {paper_id}: {family}")
print("  P04845: excluded from final technical synthesis")

print("\nObserved method-family distribution:")
print(
    summary_export.to_string(
        index=False,
        formatters={
            "Percentage": lambda value: f"{value:.1f}%",
        },
    )
)

print("\nCreated files:")
for output_file in [
    png_file,
    pdf_file,
    svg_file,
    summary_file,
    audit_file,
]:
    status = "created" if output_file.exists() else "not created"
    print(f"{status:12s} : {output_file}")
