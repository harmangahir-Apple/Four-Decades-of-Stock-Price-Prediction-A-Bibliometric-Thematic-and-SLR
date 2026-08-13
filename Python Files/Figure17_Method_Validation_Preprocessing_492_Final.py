from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
import plotly.graph_objects as go


# ================================================================
# FIGURE 17
# Principal method family -> validation design
# -> preprocessing boundary
# Frozen n = 492 technical-synthesis subset
# ================================================================


# ----------------------------------------------------------------
# 1. PROJECT SETTINGS
# ----------------------------------------------------------------

FIGURE_NUMBER = 17
EXPECTED_STUDIES = 492
EXPECTED_LEGACY_METHOD_ROWS = 493

PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

INPUT_DIR = PROJECT_DIR / "14_Sankey"

# Legacy finalized study-level family map. This contains 493 rows and is
# used ONLY as the baseline method-family mapping. The final 492-study
# inclusion boundary and methodological audit come from Compiled Files.xlsx.
METHOD_FILE = (
    INPUT_DIR
    / "Section7_Sankey_Working_COMPLETED.xlsx"
)

COMPILED_FILE = (
    PROJECT_DIR
    / "Compiled Files.xlsx"
)

CODING_SHEET = "Section5_Coding_Consolidated"
AUDIT_SHEET = "Section5_5_Methodological_Audit"
INCLUDED_STATUS = "Included_High_Priority"

EXPECTED_REMOVED_IDS = {"P04845"}

# Final manual family adjudications already reconciled in the frozen
# 492-study manuscript state.
FINAL_FAMILY_OVERRIDES = {
    "P00057": "Deep-learning models",
    "P00909": "Hybrid deep-learning models",
    "P03446": "Other/unclear",
}

EXPECTED_DETAILED_FAMILY_COUNTS = {
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

assert sum(EXPECTED_DETAILED_FAMILY_COUNTS.values()) == EXPECTED_STUDIES

OUTPUT_DIR = (
    PROJECT_DIR
    / f"Figure{FIGURE_NUMBER}_Output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SHOW_FIGURE = True

# ----------------------------------------------------------------
# 2. SCIE Q1 FIGURE SETTINGS
# ----------------------------------------------------------------
#
# The smaller canvas and larger fonts produce readable text when
# the vector PDF is placed at \textwidth in the manuscript.
# ----------------------------------------------------------------

FIGURE_WIDTH = 1600
FIGURE_HEIGHT = 1000
PNG_SCALE = 3

FONT_FAMILY = "Arial"

REGULAR_LABEL_FONT_SIZE = 24
SMALL_LABEL_FONT_SIZE = 20
COLUMN_HEADING_FONT_SIZE = 30

COUNT_FONT_PERCENT = 76

NODE_THICKNESS = 18
NODE_LINE_WIDTH = 0.75

# Fixed Sankey-column locations.
FAMILY_X = 0.020
VALIDATION_X = 0.500
PREPROCESSING_X = 0.980

# Figure domain.
DOMAIN_X0 = 0.060
DOMAIN_X1 = 0.940
DOMAIN_Y0 = 0.040
DOMAIN_Y1 = 0.885

# Vertical Sankey space.
NODE_TOP = 0.030
NODE_BOTTOM = 0.970

FAMILY_GAP = 0.045
VALIDATION_GAP = 0.080
PREPROCESSING_GAP = 0.080

FAMILY_TO_VALIDATION_ALPHA = 0.38
VALIDATION_TO_PREPROCESSING_ALPHA = 0.42

LABEL_BACKGROUND_ALPHA = 0.90
LABEL_BORDER_PAD = 1.2

CONNECTOR_ALPHA = 0.24
CONNECTOR_WIDTH = 0.55


# ----------------------------------------------------------------
# 3. OUTPUT STAGE HEADINGS
# ----------------------------------------------------------------

HEADING_SPECS = [
    {
        "text": "Principal method<br>family",
        "x": 0.145,
    },
    {
        "text": "Validation<br>design",
        "x": 0.500,
    },
    {
        "text": "Preprocessing<br>boundary",
        "x": 0.855,
    },
]


# ----------------------------------------------------------------
# 4. VERIFY INPUT PATHS
# ----------------------------------------------------------------

print("Project directory :", PROJECT_DIR)
print("Input directory   :", INPUT_DIR)
print("Method workbook   :", METHOD_FILE)
print("Compiled workbook :", COMPILED_FILE)
print("Output directory  :", OUTPUT_DIR)

if not PROJECT_DIR.is_dir():
    raise FileNotFoundError(
        f"Project directory was not found:\n{PROJECT_DIR}"
    )

if not INPUT_DIR.is_dir():
    raise FileNotFoundError(
        f"Input directory was not found:\n{INPUT_DIR}"
    )

if not METHOD_FILE.is_file():
    raise FileNotFoundError(
        f"Section 7 method-family workbook was not found:\n{METHOD_FILE}"
    )

if not COMPILED_FILE.is_file():
    raise FileNotFoundError(
        f"Authoritative compiled workbook was not found:\n{COMPILED_FILE}"
    )

print("\nAll required input files were found successfully.")


# ----------------------------------------------------------------
# 5. READ AUTHORITATIVE DATA
# ----------------------------------------------------------------

# Baseline principal-method-family mapping from the old finalized Sankey
# register. It is filtered to the final 492 IDs below and then only the
# explicitly adjudicated family changes are applied.
method_df = pd.read_excel(
    METHOD_FILE,
    sheet_name="Sankey_Input",
    usecols=[
        "Paper_ID",
        "Principal_Method_Family",
    ],
    dtype=str,
)

# Compiled workbook defines the final inclusion boundary.
coding_df = pd.read_excel(
    COMPILED_FILE,
    sheet_name=CODING_SHEET,
    usecols=[
        "Paper_ID",
        "Systematic_Inclusion_Status",
    ],
    dtype=str,
    keep_default_na=False,
    engine="openpyxl",
)

# Compiled workbook also supplies the final validation and preprocessing
# fields. Do not use the old 493-row reconciled CSV for this figure.
audit_df = pd.read_excel(
    COMPILED_FILE,
    sheet_name=AUDIT_SHEET,
    usecols=[
        "Paper_ID",
        "Validation_Design",
        "Preprocessing_Boundary",
    ],
    dtype=str,
    keep_default_na=False,
    engine="openpyxl",
)

for frame in (method_df, coding_df, audit_df):

    frame.columns = [
        str(column).strip()
        for column in frame.columns
    ]

    for column in frame.columns:

        frame[column] = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )


# ----------------------------------------------------------------
# 6. INTEGRITY CHECKS, FINAL-ID FILTER, AND ONE-TO-ONE MERGE
# ----------------------------------------------------------------

# --- Final included Paper_ID set from Compiled Files.xlsx ---

coding_final = coding_df.loc[
    coding_df["Systematic_Inclusion_Status"].eq(
        INCLUDED_STATUS
    )
].copy()

assert len(coding_final) == EXPECTED_STUDIES, (
    f"Compiled workbook contains {len(coding_final)} included rows; "
    f"expected {EXPECTED_STUDIES}."
)

assert coding_final["Paper_ID"].is_unique, (
    "Duplicate Paper_ID found in the final compiled inclusion register."
)

assert coding_final["Paper_ID"].ne("").all(), (
    "Blank Paper_ID found in the final compiled inclusion register."
)

final_ids = set(
    coding_final["Paper_ID"]
)

# --- Final methodological-audit rows ---

assert len(audit_df) == EXPECTED_STUDIES, (
    f"Compiled methodological audit contains {len(audit_df)} rows; "
    f"expected {EXPECTED_STUDIES}."
)

assert audit_df["Paper_ID"].is_unique, (
    "Duplicate Paper_ID found in the compiled methodological audit."
)

assert audit_df["Paper_ID"].ne("").all(), (
    "Blank Paper_ID found in the compiled methodological audit."
)

assert set(audit_df["Paper_ID"]) == final_ids, (
    "Paper_ID mismatch between the final inclusion register and "
    "Section5_5_Methodological_Audit."
)

# --- Legacy method-family map ---

assert len(method_df) == EXPECTED_LEGACY_METHOD_ROWS, (
    f"Legacy Section 7 family map contains {len(method_df)} rows; "
    f"expected {EXPECTED_LEGACY_METHOD_ROWS}."
)

assert method_df["Paper_ID"].is_unique, (
    "Duplicate Paper_ID found in the legacy Section 7 family map."
)

assert method_df["Paper_ID"].ne("").all(), (
    "Blank Paper_ID found in the legacy Section 7 family map."
)

legacy_ids = set(
    method_df["Paper_ID"]
)

missing_from_method = (
    final_ids - legacy_ids
)

obsolete_method_ids = (
    legacy_ids - final_ids
)

assert not missing_from_method, (
    "Final included Paper_ID values are missing from the Section 7 "
    f"family map: {sorted(missing_from_method)[:20]}"
)

assert obsolete_method_ids == EXPECTED_REMOVED_IDS, (
    "Unexpected difference between the legacy Section 7 family map and "
    "the frozen compiled register.\n"
    f"Expected removed IDs: {sorted(EXPECTED_REMOVED_IDS)}\n"
    f"Observed removed IDs: {sorted(obsolete_method_ids)}"
)

print(
    "\nLegacy method-family records excluded by the frozen workbook:"
)
print(sorted(obsolete_method_ids))

# Keep only the 492 studies that survive in Compiled Files.xlsx.
method_final = method_df.loc[
    method_df["Paper_ID"].isin(final_ids)
].copy()

assert len(method_final) == EXPECTED_STUDIES

# Apply the three final family adjudications.
for paper_id, final_family in FINAL_FAMILY_OVERRIDES.items():

    mask = method_final["Paper_ID"].eq(
        paper_id
    )

    assert int(mask.sum()) == 1, (
        f"{paper_id} must occur exactly once in the final family map."
    )

    method_final.loc[
        mask,
        "Principal_Method_Family",
    ] = final_family

# Validate detailed family counts before collapsing families.
observed_detailed_family_counts = (
    method_final["Principal_Method_Family"]
    .value_counts()
    .reindex(
        EXPECTED_DETAILED_FAMILY_COUNTS.keys(),
        fill_value=0,
    )
    .astype(int)
    .to_dict()
)

assert (
    observed_detailed_family_counts
    == EXPECTED_DETAILED_FAMILY_COUNTS
), (
    "Detailed principal-method-family counts do not match the frozen "
    "492-study state:\n"
    f"{observed_detailed_family_counts}"
)

# Explicit adjudication audit.
family_lookup = (
    method_final
    .set_index("Paper_ID")[
        "Principal_Method_Family"
    ]
    .to_dict()
)

assert family_lookup["P00057"] == "Deep-learning models"
assert family_lookup["P00909"] == "Hybrid deep-learning models"
assert family_lookup["P03446"] == "Other/unclear"
assert "P04845" not in family_lookup

# Merge final family assignment with final methodological audit.
df = method_final.merge(
    audit_df,
    on="Paper_ID",
    how="inner",
    validate="one_to_one",
)

assert len(df) == EXPECTED_STUDIES, (
    f"Merged dataset contains {len(df)} rows; "
    f"expected {EXPECTED_STUDIES}."
)

assert df["Paper_ID"].nunique() == EXPECTED_STUDIES

print(f"\nMerged frozen records: {len(df)}")

# ----------------------------------------------------------------
# 7. COLLAPSE DETAILED METHOD FAMILIES
# ----------------------------------------------------------------

family_map = {
    "Deep-learning models":
        "Deep and hybrid deep learning",

    "Hybrid deep-learning models":
        "Deep and hybrid deep learning",

    "Transformer/attention-based models":
        "Transformer, graph, and multimodal",

    "Graph-based models":
        "Transformer, graph, and multimodal",

    "Multimodal-fusion models":
        "Transformer, graph, and multimodal",

    "Metaheuristic-optimized models":
        "Metaheuristic and ensemble",

    "Ensemble/tree-based machine learning":
        "Metaheuristic and ensemble",

    "Sentiment/NLP-driven models":
        "Sentiment and NLP",

    "ANN/neuro-fuzzy models":
        "Sparse and other families",

    "Other/unclear":
        "Sparse and other families",
}

unknown_families = sorted(
    set(df["Principal_Method_Family"])
    - set(family_map)
)

assert not unknown_families, (
    f"Unmapped method-family values: {unknown_families}"
)

df["Method_Group"] = (
    df["Principal_Method_Family"]
    .map(family_map)
)


# ----------------------------------------------------------------
# 8. CLASSIFY VALIDATION DESIGN
# ----------------------------------------------------------------

temporally_ordered_codes = {
    "Chronological_Holdout",
    "Walk_Forward",
    "Rolling_Window",
    "Expanding_Window",
    "Blocked_CV",
}

random_codes = {
    "Random_Shuffled",
}

expected_validation_codes = (
    temporally_ordered_codes
    | random_codes
    | {"Unclear"}
)

unexpected_validation_codes = sorted(
    set(df["Validation_Design"])
    - expected_validation_codes
)

assert not unexpected_validation_codes, (
    "Unexpected Validation_Design values: "
    f"{unexpected_validation_codes}"
)


def classify_validation(value: str) -> str:
    """Collapse detailed validation codes into three categories."""

    if value in temporally_ordered_codes:
        return "Temporally ordered"

    if value in random_codes:
        return "Random or shuffled"

    return "Unclear validation"


df["Validation_Status"] = (
    df["Validation_Design"]
    .map(classify_validation)
)


# ----------------------------------------------------------------
# 9. CLASSIFY PREPROCESSING BOUNDARY
# ----------------------------------------------------------------

preprocessing_map = {
    "Training_Only":
        "Training only",

    "Full_Dataset":
        "Full dataset",

    "Unclear":
        "Unclear preprocessing",
}

unexpected_preprocessing_codes = sorted(
    set(df["Preprocessing_Boundary"])
    - set(preprocessing_map)
)

assert not unexpected_preprocessing_codes, (
    "Unexpected Preprocessing_Boundary values: "
    f"{unexpected_preprocessing_codes}"
)

df["Preprocessing_Status"] = (
    df["Preprocessing_Boundary"]
    .map(preprocessing_map)
)


# ----------------------------------------------------------------
# 10. CATEGORY ORDER
# ----------------------------------------------------------------
#
# Dominant Unclear categories are placed first to align the largest
# flows and reduce unnecessary ribbon crossing.
# ----------------------------------------------------------------

family_order = [
    "Deep and hybrid deep learning",
    "Transformer, graph, and multimodal",
    "Metaheuristic and ensemble",
    "Sentiment and NLP",
    "Sparse and other families",
]

validation_order = [
    "Unclear validation",
    "Temporally ordered",
    "Random or shuffled",
]

preprocessing_order = [
    "Unclear preprocessing",
    "Full dataset",
    "Training only",
]


# ----------------------------------------------------------------
# 11. EXPECTED FROZEN 492-STUDY COUNTS
# ----------------------------------------------------------------

expected_family_counts = {
    "Deep and hybrid deep learning": 227,
    "Transformer, graph, and multimodal": 97,
    "Metaheuristic and ensemble": 84,
    "Sentiment and NLP": 80,
    "Sparse and other families": 4,
}

expected_validation_counts = {
    "Unclear validation": 405,
    "Temporally ordered": 81,
    "Random or shuffled": 6,
}

expected_preprocessing_counts = {
    "Unclear preprocessing": 454,
    "Full dataset": 17,
    "Training only": 21,
}

assert sum(expected_family_counts.values()) == EXPECTED_STUDIES
assert sum(expected_validation_counts.values()) == EXPECTED_STUDIES
assert sum(expected_preprocessing_counts.values()) == EXPECTED_STUDIES

# ----------------------------------------------------------------
# 12. VERIFY CATEGORY COUNTS
# ----------------------------------------------------------------

family_counts = (
    df["Method_Group"]
    .value_counts()
    .reindex(
        family_order,
        fill_value=0,
    )
)

validation_counts = (
    df["Validation_Status"]
    .value_counts()
    .reindex(
        validation_order,
        fill_value=0,
    )
)

preprocessing_counts = (
    df["Preprocessing_Status"]
    .value_counts()
    .reindex(
        preprocessing_order,
        fill_value=0,
    )
)

assert family_counts.to_dict() == expected_family_counts, (
    f"Unexpected method-family totals:\n{family_counts}"
)

assert validation_counts.to_dict() == expected_validation_counts, (
    f"Unexpected validation totals:\n{validation_counts}"
)

assert preprocessing_counts.to_dict() == expected_preprocessing_counts, (
    f"Unexpected preprocessing totals:\n{preprocessing_counts}"
)

assert int(family_counts.sum()) == EXPECTED_STUDIES
assert int(validation_counts.sum()) == EXPECTED_STUDIES
assert int(preprocessing_counts.sum()) == EXPECTED_STUDIES

print("\nMETHOD-FAMILY TOTALS")
print(family_counts)

print("\nVALIDATION TOTALS")
print(validation_counts)

print("\nPREPROCESSING TOTALS")
print(preprocessing_counts)

# Frozen detailed validation-design audit.
expected_detailed_validation_counts = {
    "Chronological_Holdout": 61,
    "Walk_Forward": 11,
    "Rolling_Window": 6,
    "Expanding_Window": 2,
    "Blocked_CV": 1,
    "Random_Shuffled": 6,
    "Unclear": 405,
}

observed_detailed_validation_counts = (
    df["Validation_Design"]
    .value_counts()
    .reindex(
        expected_detailed_validation_counts.keys(),
        fill_value=0,
    )
    .astype(int)
    .to_dict()
)

assert (
    observed_detailed_validation_counts
    == expected_detailed_validation_counts
), (
    "Detailed validation-design counts do not match the frozen "
    "compiled audit:\n"
    f"{observed_detailed_validation_counts}"
)

expected_detailed_preprocessing_counts = {
    "Unclear": 454,
    "Full_Dataset": 17,
    "Training_Only": 21,
}

observed_detailed_preprocessing_counts = (
    df["Preprocessing_Boundary"]
    .value_counts()
    .reindex(
        expected_detailed_preprocessing_counts.keys(),
        fill_value=0,
    )
    .astype(int)
    .to_dict()
)

assert (
    observed_detailed_preprocessing_counts
    == expected_detailed_preprocessing_counts
), (
    "Detailed preprocessing-boundary counts do not match the frozen "
    "compiled audit:\n"
    f"{observed_detailed_preprocessing_counts}"
)

print("\nDETAILED VALIDATION-DESIGN AUDIT")
print(observed_detailed_validation_counts)

print("\nDETAILED PREPROCESSING-BOUNDARY AUDIT")
print(observed_detailed_preprocessing_counts)

# ----------------------------------------------------------------
# 13. CREATE FLOW TABLES
# ----------------------------------------------------------------

family_validation = (
    df.groupby(
        [
            "Method_Group",
            "Validation_Status",
        ],
        observed=True,
    )
    .size()
    .reset_index(name="Count")
)

family_validation = (
    family_validation[
        family_validation["Count"] > 0
    ]
    .copy()
)

family_validation_preprocessing = (
    df.groupby(
        [
            "Method_Group",
            "Validation_Status",
            "Preprocessing_Status",
        ],
        observed=True,
    )
    .size()
    .reset_index(name="Count")
)

family_validation_preprocessing = (
    family_validation_preprocessing[
        family_validation_preprocessing["Count"] > 0
    ]
    .copy()
)


# ----------------------------------------------------------------
# 14. VERIFY STUDY-LEVEL FLOW TABLES
# ----------------------------------------------------------------

# A. Method group -> validation design
family_validation_crosstab = (
    pd.crosstab(
        df["Method_Group"],
        df["Validation_Status"],
    )
    .reindex(
        index=family_order,
        columns=validation_order,
        fill_value=0,
    )
)

expected_family_validation = pd.DataFrame(
    {
        "Unclear validation": [
            199,
            73,
            67,
            64,
            2,
        ],
        "Temporally ordered": [
            26,
            22,
            16,
            15,
            2,
        ],
        "Random or shuffled": [
            2,
            2,
            1,
            1,
            0,
        ],
    },
    index=family_order,
)

assert family_validation_crosstab.equals(
    expected_family_validation
), (
    "Unexpected method-family/validation cross-tab:\n"
    f"{family_validation_crosstab}"
)

# B. Validation design -> preprocessing boundary
validation_preprocessing_crosstab = (
    pd.crosstab(
        df["Validation_Status"],
        df["Preprocessing_Status"],
    )
    .reindex(
        index=validation_order,
        columns=preprocessing_order,
        fill_value=0,
    )
)

expected_cross_tab = pd.DataFrame(
    {
        "Unclear preprocessing": [
            381,
            68,
            5,
        ],
        "Full dataset": [
            13,
            4,
            0,
        ],
        "Training only": [
            11,
            9,
            1,
        ],
    },
    index=validation_order,
)

assert validation_preprocessing_crosstab.equals(
    expected_cross_tab
), (
    "Unexpected validation-preprocessing cross-tab:\n"
    f"{validation_preprocessing_crosstab}"
)

print("\nMETHOD FAMILY -> VALIDATION")
print(family_validation_crosstab)

print("\nVALIDATION -> PREPROCESSING")
print(validation_preprocessing_crosstab)

# Key manuscript cross-tab: temporally ordered + training-only.
temporally_ordered_training_only = int(
    validation_preprocessing_crosstab.loc[
        "Temporally ordered",
        "Training only",
    ]
)

assert temporally_ordered_training_only == 9

# ----------------------------------------------------------------
# 15. COLOUR-BLIND-CONSCIOUS PALETTE
# ----------------------------------------------------------------

method_colour_map = {
    "Deep and hybrid deep learning":
        "#75B7D3",

    "Transformer, graph, and multimodal":
        "#8BCF86",

    "Metaheuristic and ensemble":
        "#F2A064",

    "Sentiment and NLP":
        "#9DA8C4",

    "Sparse and other families":
        "#E97A63",
}

neutral_node_colour = "#D2E7EA"
neutral_node_border = "#607D85"
font_colour = "#2F3D43"


def hex_to_rgba(
    hex_colour: str,
    alpha: float,
) -> str:
    """Convert #RRGGBB to Plotly RGBA format."""

    cleaned = hex_colour.strip().lstrip("#")

    if len(cleaned) != 6:
        raise ValueError(
            f"Invalid hexadecimal colour: {hex_colour!r}"
        )

    red = int(cleaned[0:2], 16)
    green = int(cleaned[2:4], 16)
    blue = int(cleaned[4:6], 16)

    return (
        f"rgba({red},{green},{blue},{alpha:.3f})"
    )


# ----------------------------------------------------------------
# 16. COMPACT DISPLAY LABELS
# ----------------------------------------------------------------

display_labels = {
    "Deep and hybrid deep learning":
        "Deep and hybrid<br>deep learning",

    "Transformer, graph, and multimodal":
        "Transformer, graph,<br>and multimodal",

    "Metaheuristic and ensemble":
        "Metaheuristic and<br>ensemble",

    "Sentiment and NLP":
        "Sentiment and NLP",

    "Sparse and other families":
        "Sparse and other<br>families",

    "Unclear validation":
        "Unclear validation",

    "Temporally ordered":
        "Temporally ordered",

    "Random or shuffled":
        "Random/shuffled",

    "Unclear preprocessing":
        "Unclear preprocessing",

    "Full dataset":
        "Full dataset",

    "Training only":
        "Training only",
}


def journal_label(
    category: str,
    count: int,
) -> str:
    """Create a compact label with a smaller count line."""

    display = display_labels.get(
        category,
        category,
    )

    return (
        f"{display}"
        f"<br>"
        f"<span style='font-size:{COUNT_FONT_PERCENT}%'>"
        f"(n={count:,})"
        f"</span>"
    )


# ----------------------------------------------------------------
# 17. CALCULATE FIXED NODE CENTRES
# ----------------------------------------------------------------

def calculate_column_centres(
    order: list[str],
    counts: dict[str, int],
    gap: float,
) -> dict[str, float]:
    """
    Calculate non-overlapping node centres proportional to counts.

    Plotly Sankey y coordinates increase from top to bottom.
    """

    node_count = len(order)

    total_span = (
        NODE_BOTTOM - NODE_TOP
    )

    total_gap = (
        gap * max(node_count - 1, 0)
    )

    available_height = (
        total_span - total_gap
    )

    if available_height <= 0:
        raise ValueError(
            "Vertical gap is too large for this node column."
        )

    total_count = sum(
        counts[item]
        for item in order
    )

    cursor = NODE_TOP
    centres: dict[str, float] = {}

    for item in order:

        node_height = (
            available_height
            * counts[item]
            / total_count
        )

        centres[item] = (
            cursor + node_height / 2.0
        )

        cursor += (
            node_height + gap
        )

    return centres


family_y = calculate_column_centres(
    family_order,
    expected_family_counts,
    FAMILY_GAP,
)

validation_y = calculate_column_centres(
    validation_order,
    expected_validation_counts,
    VALIDATION_GAP,
)

preprocessing_y = calculate_column_centres(
    preprocessing_order,
    expected_preprocessing_counts,
    PREPROCESSING_GAP,
)


# ----------------------------------------------------------------
# 18. LABEL POSITIONS
# ----------------------------------------------------------------
#
# Labels normally use the corresponding node centre. The final sparse
# family label is raised slightly to protect it from the page boundary.
# ----------------------------------------------------------------

family_label_y = family_y.copy()
validation_label_y = validation_y.copy()
preprocessing_label_y = preprocessing_y.copy()

# family_label_y["Sparse and other families"] = min(
#     family_label_y["Sparse and other families"],
#     0.945,
# )
# Manually separate labels attached to very small lower nodes.
# Smaller y values move labels upward because Sankey y uses a
# top-origin coordinate system.
family_label_y["Sentiment and NLP"] = 0.805
family_label_y["Sparse and other families"] = 0.955

validation_label_y["Temporally ordered"] = 0.785
validation_label_y["Random or shuffled"] = 0.925

preprocessing_label_y["Full dataset"] = 0.805
preprocessing_label_y["Training only"] = 0.925


# ----------------------------------------------------------------
# 19. NODE DEFINITIONS
# ----------------------------------------------------------------

node_names = (
    family_order
    + validation_order
    + preprocessing_order
)

node_stage_names = (
    ["Principal method family"]
    * len(family_order)

    + ["Validation design"]
    * len(validation_order)

    + ["Preprocessing boundary"]
    * len(preprocessing_order)
)

node_counts = (
    [
        expected_family_counts[item]
        for item in family_order
    ]
    + [
        expected_validation_counts[item]
        for item in validation_order
    ]
    + [
        expected_preprocessing_counts[item]
        for item in preprocessing_order
    ]
)

node_colours = (
    [
        method_colour_map[item]
        for item in family_order
    ]
    + [
        neutral_node_colour
        for _ in validation_order
    ]
    + [
        neutral_node_colour
        for _ in preprocessing_order
    ]
)

node_x = (
    [FAMILY_X] * len(family_order)
    + [VALIDATION_X] * len(validation_order)
    + [PREPROCESSING_X] * len(preprocessing_order)
)

node_y = (
    [
        family_y[item]
        for item in family_order
    ]
    + [
        validation_y[item]
        for item in validation_order
    ]
    + [
        preprocessing_y[item]
        for item in preprocessing_order
    ]
)

node_index = {
    name: index
    for index, name
    in enumerate(node_names)
}

node_customdata = [
    [
        category,
        stage,
        count,
    ]
    for category, stage, count
    in zip(
        node_names,
        node_stage_names,
        node_counts,
    )
]


# ----------------------------------------------------------------
# 20. LINK DEFINITIONS
# ----------------------------------------------------------------

sources: list[int] = []
targets: list[int] = []
values: list[int] = []

link_colours: list[str] = []
link_customdata: list[list[Any]] = []

flow_rows: list[dict[str, Any]] = []


# Stage 1: method family -> validation design.
for family in family_order:

    for validation in validation_order:

        matching = family_validation.loc[
            (
                family_validation["Method_Group"]
                == family
            )
            & (
                family_validation["Validation_Status"]
                == validation
            ),
            "Count",
        ]

        if matching.empty:
            continue

        count = int(matching.iloc[0])

        if count <= 0:
            continue

        sources.append(
            node_index[family]
        )

        targets.append(
            node_index[validation]
        )

        values.append(count)

        link_colours.append(
            hex_to_rgba(
                method_colour_map[family],
                FAMILY_TO_VALIDATION_ALPHA,
            )
        )

        link_customdata.append(
            [
                family,
                validation,
                count,
                "Method family → validation design",
            ]
        )

        flow_rows.append(
            {
                "Stage":
                    "Method_to_Validation",

                "Origin_Method_Group":
                    family,

                "Source":
                    family,

                "Target":
                    validation,

                "Count":
                    count,
            }
        )


# Stage 2: validation design -> preprocessing boundary.
# Separate ribbons preserve the originating method-family colour.
for family in family_order:

    for validation in validation_order:

        for preprocessing in preprocessing_order:

            matching = (
                family_validation_preprocessing.loc[
                    (
                        family_validation_preprocessing[
                            "Method_Group"
                        ]
                        == family
                    )
                    & (
                        family_validation_preprocessing[
                            "Validation_Status"
                        ]
                        == validation
                    )
                    & (
                        family_validation_preprocessing[
                            "Preprocessing_Status"
                        ]
                        == preprocessing
                    ),
                    "Count",
                ]
            )

            if matching.empty:
                continue

            count = int(matching.iloc[0])

            if count <= 0:
                continue

            sources.append(
                node_index[validation]
            )

            targets.append(
                node_index[preprocessing]
            )

            values.append(count)

            link_colours.append(
                hex_to_rgba(
                    method_colour_map[family],
                    VALIDATION_TO_PREPROCESSING_ALPHA,
                )
            )

            link_customdata.append(
                [
                    validation,
                    preprocessing,
                    count,
                    family,
                ]
            )

            flow_rows.append(
                {
                    "Stage":
                        "Validation_to_Preprocessing",

                    "Origin_Method_Group":
                        family,

                    "Source":
                        validation,

                    "Target":
                        preprocessing,

                    "Count":
                        count,
                }
            )


# ----------------------------------------------------------------
# 21. BUILD SANKEY
# ----------------------------------------------------------------

fig = go.Figure(
    go.Sankey(
        arrangement="fixed",
        orientation="h",
        valueformat=".0f",

        domain={
            "x": [
                DOMAIN_X0,
                DOMAIN_X1,
            ],

            "y": [
                DOMAIN_Y0,
                DOMAIN_Y1,
            ],
        },

        node={
            "pad": 20,

            "thickness":
                NODE_THICKNESS,

            "line": {
                "color":
                    neutral_node_border,

                "width":
                    NODE_LINE_WIDTH,
            },

            # Native labels are disabled to prevent collisions.
            "label": [
                ""
            ] * len(node_names),

            "color":
                node_colours,

            "x":
                node_x,

            "y":
                node_y,

            "customdata":
                node_customdata,

            "hovertemplate": (
                "<b>%{customdata[0]}</b><br>"
                "Stage: %{customdata[1]}<br>"
                "Studies: %{customdata[2]:,}"
                "<extra></extra>"
            ),
        },

        link={
            "source":
                sources,

            "target":
                targets,

            "value":
                values,

            "color":
                link_colours,

            "customdata":
                link_customdata,

            "hovertemplate": (
                "<b>%{customdata[0]}</b>"
                " → "
                "<b>%{customdata[1]}</b><br>"
                "Studies: %{customdata[2]:,}<br>"
                "Originating method group: "
                "%{customdata[3]}"
                "<extra></extra>"
            ),
        },
    )
)


# ----------------------------------------------------------------
# 22. COORDINATE CONVERSION
# ----------------------------------------------------------------

def sankey_to_paper_x(
    sankey_x: float,
) -> float:
    """Convert Sankey-domain x to complete-figure x."""

    return (
        DOMAIN_X0
        + sankey_x
        * (
            DOMAIN_X1 - DOMAIN_X0
        )
    )


def sankey_to_paper_y(
    sankey_y: float,
) -> float:
    """Convert top-origin Sankey y to bottom-origin paper y."""

    return (
        DOMAIN_Y0
        + (
            1.0 - sankey_y
        )
        * (
            DOMAIN_Y1 - DOMAIN_Y0
        )
    )


# ----------------------------------------------------------------
# 23. CUSTOM LABEL ANNOTATIONS
# ----------------------------------------------------------------

annotations: list[dict[str, Any]] = []
connector_shapes: list[dict[str, Any]] = []


def add_node_annotation(
    *,
    node_x_value: float,
    node_y_value: float,
    label_y_value: float,
    text: str,
    stage: str,
    font_size: int,
) -> None:
    """Add a collision-controlled label to one Sankey node."""

    node_paper_x = sankey_to_paper_x(
        node_x_value
    )

    node_paper_y = sankey_to_paper_y(
        node_y_value
    )

    label_paper_y = sankey_to_paper_y(
        label_y_value
    )

    if stage == "preprocessing":

        label_x = (
            node_paper_x - 0.012
        )

        x_anchor = "right"
        alignment = "right"

        connector_x0 = (
            node_paper_x - 0.004
        )

        connector_x1 = (
            label_x + 0.003
        )

    else:

        label_x = (
            node_paper_x + 0.012
        )

        x_anchor = "left"
        alignment = "left"

        connector_x0 = (
            node_paper_x + 0.004
        )

        connector_x1 = (
            label_x - 0.003
        )

    if abs(
        label_y_value - node_y_value
    ) >= 0.018:

        connector_shapes.append(
            {
                "type": "line",

                "xref": "paper",
                "yref": "paper",

                "x0": connector_x0,
                "y0": node_paper_y,

                "x1": connector_x1,
                "y1": label_paper_y,

                "line": {
                    "color": (
                        f"rgba(70,70,70,"
                        f"{CONNECTOR_ALPHA:.3f})"
                    ),

                    "width":
                        CONNECTOR_WIDTH,
                },

                "layer":
                    "above",
            }
        )

    annotations.append(
        {
            "x":
                label_x,

            "y":
                label_paper_y,

            "xref":
                "paper",

            "yref":
                "paper",

            "text":
                text,

            "showarrow":
                False,

            "xanchor":
                x_anchor,

            "yanchor":
                "middle",

            "align":
                alignment,

            "font": {
                "family":
                    FONT_FAMILY,

                "size":
                    font_size,

                "color":
                    font_colour,
            },

            "bgcolor": (
                f"rgba(255,255,255,"
                f"{LABEL_BACKGROUND_ALPHA:.3f})"
            ),

            "bordercolor":
                "rgba(255,255,255,0)",

            "borderpad":
                LABEL_BORDER_PAD,
        }
    )


# ----------------------------------------------------------------
# 24. ADD COLUMN HEADINGS
# ----------------------------------------------------------------

for heading in HEADING_SPECS:

    annotations.append(
        {
            "x":
                heading["x"],

            "y":
                0.965,

            "xref":
                "paper",

            "yref":
                "paper",

            "text":
                f"<b>{heading['text']}</b>",

            "showarrow":
                False,

            "xanchor":
                "center",

            "yanchor":
                "middle",

            "align":
                "center",

            "font": {
                "family":
                    FONT_FAMILY,

                "size":
                    COLUMN_HEADING_FONT_SIZE,

                "color":
                    "#252525",
            },
        }
    )


# ----------------------------------------------------------------
# 25. ADD FAMILY LABELS
# ----------------------------------------------------------------

for family in family_order:
    family_font_size = (
        18
    if family == "Sparse and other families"
    else (
        SMALL_LABEL_FONT_SIZE
        if family == "Sentiment and NLP"
        else REGULAR_LABEL_FONT_SIZE
        )
    )
    add_node_annotation(
        node_x_value=
            FAMILY_X,

        node_y_value=
            family_y[family],

        label_y_value=
            family_label_y[family],

        text=
            journal_label(
                family,
                expected_family_counts[family],
            ),

        stage=
            "family",

        font_size=
            family_font_size,
    )


# ----------------------------------------------------------------
# 26. ADD VALIDATION LABELS
# ----------------------------------------------------------------

for validation in validation_order:

    validation_font_size = (
        SMALL_LABEL_FONT_SIZE
        if validation in {
            "Temporally ordered",
            "Random or shuffled",
        }
        else REGULAR_LABEL_FONT_SIZE
    )

    add_node_annotation(
        node_x_value=
            VALIDATION_X,

        node_y_value=
            validation_y[validation],

        label_y_value=
            validation_label_y[validation],

        text=
            journal_label(
                validation,
                expected_validation_counts[validation],
            ),

        stage=
            "validation",

        font_size=
            validation_font_size,
    )


# ----------------------------------------------------------------
# 27. ADD PREPROCESSING LABELS
# ----------------------------------------------------------------

for preprocessing in preprocessing_order:

    preprocessing_font_size = (
        SMALL_LABEL_FONT_SIZE
        if preprocessing in {
            "Full dataset",
            "Training only",
        }
        else REGULAR_LABEL_FONT_SIZE
    )

    add_node_annotation(
        node_x_value=
            PREPROCESSING_X,

        node_y_value=
            preprocessing_y[preprocessing],

        label_y_value=
            preprocessing_label_y[preprocessing],

        text=
            journal_label(
                preprocessing,
                expected_preprocessing_counts[
                    preprocessing
                ],
            ),

        stage=
            "preprocessing",

        font_size=
            preprocessing_font_size,
    )


# ----------------------------------------------------------------
# 28. FINAL LAYOUT
# ----------------------------------------------------------------

fig.update_layout(
    width=
        FIGURE_WIDTH,

    height=
        FIGURE_HEIGHT,

    paper_bgcolor=
        "white",

    plot_bgcolor=
        "white",

    font={
        "family":
            FONT_FAMILY,

        "size":
            REGULAR_LABEL_FONT_SIZE,

        "color":
            font_colour,
    },

    margin={
        "l": 12,
        "r": 12,
        "t": 44,
        "b": 24,
    },

    annotations=
        annotations,

    shapes=
        connector_shapes,
)


# ----------------------------------------------------------------
# 29. OUTPUT FILES
# ----------------------------------------------------------------

base_name = (
    f"Figure{FIGURE_NUMBER}_"
    "Method_Validation_Preprocessing_"
    "Sankey_SCIE_Q1_Reconciled_Readable_Final"
)

html_file = (
    OUTPUT_DIR
    / f"{base_name}.html"
)

png_file = (
    OUTPUT_DIR
    / f"{base_name}.png"
)

pdf_file = (
    OUTPUT_DIR
    / f"{base_name}.pdf"
)

svg_file = (
    OUTPUT_DIR
    / f"{base_name}.svg"
)

flow_csv_file = (
    OUTPUT_DIR
    / f"{base_name}_Flows.csv"
)

study_level_file = (
    OUTPUT_DIR
    / f"{base_name}_Study_Level_Audit.csv"
)

cross_tab_file = (
    OUTPUT_DIR
    / f"{base_name}_Validation_Preprocessing_Crosstab.csv"
)

summary_file = (
    OUTPUT_DIR
    / f"{base_name}_Category_Totals.csv"
)


# ----------------------------------------------------------------
# 30. SAVE AUDIT DATA
# ----------------------------------------------------------------

flow_output = pd.DataFrame(flow_rows)

flow_output.to_csv(
    flow_csv_file,
    index=False,
    encoding="utf-8-sig",
)

df[
    [
        "Paper_ID",
        "Principal_Method_Family",
        "Method_Group",
        "Validation_Design",
        "Validation_Status",
        "Preprocessing_Boundary",
        "Preprocessing_Status",
    ]
].to_csv(
    study_level_file,
    index=False,
    encoding="utf-8-sig",
)

validation_preprocessing_crosstab.to_csv(
    cross_tab_file,
    encoding="utf-8-sig",
)

summary_rows = []

for category, count in expected_family_counts.items():

    summary_rows.append(
        {
            "Stage":
                "Principal method family",

            "Category":
                category,

            "Count":
                count,
        }
    )

for category, count in expected_validation_counts.items():

    summary_rows.append(
        {
            "Stage":
                "Validation design",

            "Category":
                category,

            "Count":
                count,
        }
    )

for category, count in expected_preprocessing_counts.items():

    summary_rows.append(
        {
            "Stage":
                "Preprocessing boundary",

            "Category":
                category,

            "Count":
                count,
        }
    )

pd.DataFrame(
    summary_rows
).to_csv(
    summary_file,
    index=False,
    encoding="utf-8-sig",
)


# ----------------------------------------------------------------
# 31. EXPORT INTERACTIVE HTML
# ----------------------------------------------------------------

fig.write_html(
    html_file,
    include_plotlyjs=True,
    full_html=True,

    config={
        "displaylogo":
            False,

        "responsive":
            True,

        "toImageButtonOptions": {
            "format":
                "png",

            "filename":
                base_name,

            "width":
                FIGURE_WIDTH,

            "height":
                FIGURE_HEIGHT,

            "scale":
                PNG_SCALE,
        },
    },
)


# ----------------------------------------------------------------
# 32. EXPORT STATIC PUBLICATION FILES
# ----------------------------------------------------------------

static_export_ok = True

try:

    fig.write_image(
        png_file,
        format="png",
        width=FIGURE_WIDTH,
        height=FIGURE_HEIGHT,
        scale=PNG_SCALE,
    )

    fig.write_image(
        pdf_file,
        format="pdf",
        width=FIGURE_WIDTH,
        height=FIGURE_HEIGHT,
        scale=1,
    )

    fig.write_image(
        svg_file,
        format="svg",
        width=FIGURE_WIDTH,
        height=FIGURE_HEIGHT,
        scale=1,
    )

except Exception as error:

    static_export_ok = False

    print(
        "\nHTML and CSV files were created, "
        "but static export was not completed."
    )

    print(
        "\nInstall or update Kaleido:"
    )

    print(
        "    pip install -U kaleido"
    )

    print(
        "\nRecent Kaleido versions may require Chrome:"
    )

    print(
        "    plotly_get_chrome"
    )

    print(
        f"\nExport error:\n{error}"
    )


# ----------------------------------------------------------------
# 33. FINAL AUDIT
# ----------------------------------------------------------------

assert sum(values[:len(family_validation)]) == EXPECTED_STUDIES, (
    f"Method-to-validation links do not total {EXPECTED_STUDIES}."
)

stage_two_total = int(
    family_validation_preprocessing["Count"].sum()
)

assert stage_two_total == EXPECTED_STUDIES, (
    f"Validation-to-preprocessing links do not total {EXPECTED_STUDIES}."
)

print("\nFigure generation and all audits completed successfully.")

print("\nCreated output files:")

for file_path in [
    flow_csv_file,
    study_level_file,
    cross_tab_file,
    summary_file,
    html_file,
    png_file,
    pdf_file,
    svg_file,
]:

    status = (
        "created"
        if file_path.exists()
        else "not created"
    )

    print(
        f"{status:12s} : {file_path}"
    )

print(
    "\nWindows Explorer output path:\n"
    rf"\\wsl.localhost\Ubuntu-24.04"
    rf"\home\harman\projects"
    rf"\SLR Stock Price Prediction"
    rf"\Stock_Price_Prediction_SLR_ACME"
    rf"\Figure{FIGURE_NUMBER}_Output"
)

if SHOW_FIGURE:
    fig.show()