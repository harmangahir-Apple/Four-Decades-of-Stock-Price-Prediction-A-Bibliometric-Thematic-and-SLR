from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# ================================================================
# FIGURE 16
# Model family -> validation design -> preprocessing boundary
# ================================================================

# ----------------------------------------------------------------
# 0. Exact WSL project paths
# ----------------------------------------------------------------
PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

INPUT_DIR = PROJECT_DIR / "14_Sankey"

METHOD_FILE = (
    INPUT_DIR
    / "Section7_Sankey_Working_COMPLETED.xlsx"
)

AUDIT_FILE = (
    INPUT_DIR
    / "Section5_5_Review_264_Closed_45_Pending.xlsx"
)

# Required output directory:
# \\wsl.localhost\Ubuntu-24.04\home\harman\projects\
# SLR Stock Price Prediction\Stock_Price_Prediction_SLR_ACME\
# Figure16_Output
OUTPUT_DIR = PROJECT_DIR / "Figure16_Output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# 1. Verify paths
# ----------------------------------------------------------------
print("Project directory :", PROJECT_DIR)
print("Input directory   :", INPUT_DIR)
print("Method workbook   :", METHOD_FILE)
print("Audit workbook    :", AUDIT_FILE)
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
        f"Section 7 workbook was not found:\n{METHOD_FILE}"
    )

if not AUDIT_FILE.is_file():
    raise FileNotFoundError(
        f"Section 5.5 workbook was not found:\n{AUDIT_FILE}"
    )

print("\nAll required input files were found successfully.\n")

# ----------------------------------------------------------------
# 2. Read only the required columns
# ----------------------------------------------------------------
method_df = pd.read_excel(
    METHOD_FILE,
    sheet_name="Sankey_Input",
    usecols=["Paper_ID", "Principal_Method_Family"],
    dtype=str,
)

audit_df = pd.read_excel(
    AUDIT_FILE,
    sheet_name="Section5_5_Methodological_Audit",
    usecols=[
        "Paper_ID",
        "Validation_Design",
        "Preprocessing_Boundary",
    ],
    dtype=str,
)

for frame in (method_df, audit_df):
    for column in frame.columns:
        frame[column] = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

# ----------------------------------------------------------------
# 3. Integrity checks and one-to-one merge
# ----------------------------------------------------------------
assert len(method_df) == 493, (
    f"Section 7 contains {len(method_df)} rows; expected 493."
)

assert len(audit_df) == 493, (
    f"Section 5.5 contains {len(audit_df)} rows; expected 493."
)

assert method_df["Paper_ID"].is_unique, (
    "Duplicate Paper_ID found in the Section 7 workbook."
)

assert audit_df["Paper_ID"].is_unique, (
    "Duplicate Paper_ID found in the Section 5.5 workbook."
)

missing_from_method = sorted(
    set(audit_df["Paper_ID"]) - set(method_df["Paper_ID"])
)

missing_from_audit = sorted(
    set(method_df["Paper_ID"]) - set(audit_df["Paper_ID"])
)

assert not missing_from_method, (
    "Paper_ID values missing from the Section 7 workbook: "
    f"{missing_from_method[:10]}"
)

assert not missing_from_audit, (
    "Paper_ID values missing from the Section 5.5 workbook: "
    f"{missing_from_audit[:10]}"
)

df = method_df.merge(
    audit_df,
    on="Paper_ID",
    how="inner",
    validate="one_to_one",
)

assert len(df) == 493, (
    f"Merged dataset contains {len(df)} rows; expected 493."
)

print(f"Merged records: {len(df)}")

# ----------------------------------------------------------------
# 4. Collapse the ten detailed method families into five
#    higher-order groups for readability at journal-page size
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
    set(df["Principal_Method_Family"]) - set(family_map)
)

assert not unknown_families, (
    f"Unmapped method-family values: {unknown_families}"
)

df["Method_Group"] = (
    df["Principal_Method_Family"]
    .map(family_map)
)

# ----------------------------------------------------------------
# 5. Classify validation design
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
# 6. Classify preprocessing boundary
# ----------------------------------------------------------------
preprocessing_map = {
    "Training_Only": "Training only",
    "Full_Dataset": "Full dataset",
    "Unclear": "Unclear preprocessing",
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
# 7. Set category order
# ----------------------------------------------------------------
family_order = [
    "Deep and hybrid deep learning",
    "Transformer, graph, and multimodal",
    "Metaheuristic and ensemble",
    "Sentiment and NLP",
    "Sparse and other families",
]

validation_order = [
    "Temporally ordered",
    "Random or shuffled",
    "Unclear validation",
]

preprocessing_order = [
    "Training only",
    "Full dataset",
    "Unclear preprocessing",
]

# ----------------------------------------------------------------
# 8. Verify all published denominators
# ----------------------------------------------------------------
family_counts = (
    df["Method_Group"]
    .value_counts()
    .reindex(family_order, fill_value=0)
)

validation_counts = (
    df["Validation_Status"]
    .value_counts()
    .reindex(validation_order, fill_value=0)
)

preprocessing_counts = (
    df["Preprocessing_Status"]
    .value_counts()
    .reindex(preprocessing_order, fill_value=0)
)

expected_family_counts = {
    "Deep and hybrid deep learning": 227,
    "Transformer, graph, and multimodal": 97,
    "Metaheuristic and ensemble": 85,
    "Sentiment and NLP": 81,
    "Sparse and other families": 3,
}

expected_validation_counts = {
    "Temporally ordered": 77,
    "Random or shuffled": 6,
    "Unclear validation": 410,
}

expected_preprocessing_counts = {
    "Training only": 21,
    "Full dataset": 18,
    "Unclear preprocessing": 454,
}

assert family_counts.to_dict() == expected_family_counts, (
    f"Unexpected method-family totals:\n{family_counts}"
)

assert validation_counts.to_dict() == expected_validation_counts, (
    f"Unexpected validation totals:\n{validation_counts}"
)

assert (
    preprocessing_counts.to_dict()
    == expected_preprocessing_counts
), (
    "Unexpected preprocessing totals:\n"
    f"{preprocessing_counts}"
)

assert family_counts.sum() == 493
assert validation_counts.sum() == 493
assert preprocessing_counts.sum() == 493

print("\nMETHOD-FAMILY TOTALS")
print(family_counts)

print("\nVALIDATION TOTALS")
print(validation_counts)

print("\nPREPROCESSING TOTALS")
print(preprocessing_counts)

# ----------------------------------------------------------------
# 9. Create flow tables
# ----------------------------------------------------------------

# Stage 1: method family -> validation
family_validation = (
    df.groupby(
        ["Method_Group", "Validation_Status"],
        observed=True,
    )
    .size()
    .reset_index(name="Count")
)

family_validation = family_validation[
    family_validation["Count"] > 0
].copy()

# Stage 2: validation -> preprocessing, while preserving
# the originating method family for ribbon colour
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

print("\nMODEL FAMILY -> VALIDATION")
print(
    family_validation.pivot(
        index="Method_Group",
        columns="Validation_Status",
        values="Count",
    )
    .fillna(0)
    .astype(int)
    .reindex(
        index=family_order,
        columns=validation_order,
        fill_value=0,
    )
)

print("\nVALIDATION -> PREPROCESSING")
print(validation_preprocessing_crosstab)

expected_cross_tab = pd.DataFrame(
    {
        "Training only": [9, 1, 11],
        "Full dataset": [4, 0, 14],
        "Unclear preprocessing": [64, 5, 385],
    },
    index=validation_order,
)

assert validation_preprocessing_crosstab.equals(
    expected_cross_tab
), (
    "Unexpected validation-preprocessing cross-tab:\n"
    f"{validation_preprocessing_crosstab}"
)

# ----------------------------------------------------------------
# 10. Save audit-ready flow data
# ----------------------------------------------------------------
flow_stage_1 = family_validation.rename(
    columns={
        "Method_Group": "Source",
        "Validation_Status": "Target",
    }
)

flow_stage_1.insert(
    0,
    "Source_Stage",
    "Model family",
)

flow_stage_1.insert(
    2,
    "Target_Stage",
    "Validation",
)

flow_stage_2 = (
    family_validation_preprocessing.rename(
        columns={
            "Validation_Status": "Source",
            "Preprocessing_Status": "Target",
        }
    )
)

flow_stage_2.insert(
    0,
    "Source_Stage",
    "Validation",
)

flow_stage_2.insert(
    2,
    "Target_Stage",
    "Preprocessing boundary",
)

flow_table = pd.concat(
    [
        flow_stage_1[
            [
                "Source_Stage",
                "Source",
                "Target_Stage",
                "Target",
                "Count",
            ]
        ],
        flow_stage_2[
            [
                "Source_Stage",
                "Source",
                "Target_Stage",
                "Target",
                "Count",
            ]
        ],
    ],
    ignore_index=True,
)

flow_csv_file = (
    OUTPUT_DIR
    / "Figure16_Sankey_Flows.csv"
)

flow_table.to_csv(
    flow_csv_file,
    index=False,
)

# Also save the joined study-level audit used to construct the figure.
study_level_file = (
    OUTPUT_DIR
    / "Figure16_Study_Level_Audit.csv"
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
)

# ----------------------------------------------------------------
# 11. Screenshot-inspired, colour-blind-conscious soft palette
# ----------------------------------------------------------------
method_colour_map = {
    "Deep and hybrid deep learning":
        "#91C4DB",  # soft blue

    "Transformer, graph, and multimodal":
        "#9BD596",  # soft green

    "Metaheuristic and ensemble":
        "#F5A066",  # soft orange

    "Sentiment and NLP":
        "#AEB7CF",  # muted blue-purple

    "Sparse and other families":
        "#EF8065",  # soft coral
}

neutral_node_colour = "#C7E2E7"
neutral_node_border = "#6F9099"
font_colour = "#334955"


def hex_to_rgba(
    hex_colour: str,
    alpha: float = 0.60,
) -> str:
    """
    Convert a hexadecimal colour into Plotly RGBA format.
    """
    cleaned = hex_colour.lstrip("#")

    red = int(cleaned[0:2], 16)
    green = int(cleaned[2:4], 16)
    blue = int(cleaned[4:6], 16)

    return (
        f"rgba({red}, {green}, {blue}, {alpha})"
    )

# ----------------------------------------------------------------
# 12. Construct Sankey nodes
# ----------------------------------------------------------------
family_labels = [
    f"{name}<br>(n={int(family_counts[name])})"
    for name in family_order
]

validation_labels = [
    f"{name}<br>(n={int(validation_counts[name])})"
    for name in validation_order
]

preprocessing_labels = [
    f"{name}<br>(n={int(preprocessing_counts[name])})"
    for name in preprocessing_order
]

node_names = (
    family_order
    + validation_order
    + preprocessing_order
)

node_labels = (
    family_labels
    + validation_labels
    + preprocessing_labels
)

node_index = {
    name: index
    for index, name in enumerate(node_names)
}

source_node_colours = [
    method_colour_map[name]
    for name in family_order
]

node_colours = (
    source_node_colours
    + [neutral_node_colour] * len(validation_order)
    + [neutral_node_colour] * len(preprocessing_order)
)

# Keep each stage in its own column.
node_x = (
    [0.01] * len(family_order)
    + [0.50] * len(validation_order)
    + [0.97] * len(preprocessing_order)
)

# ----------------------------------------------------------------
# 13. Construct coloured Sankey links
# ----------------------------------------------------------------
sources = []
targets = []
values = []
link_colours = []
hover_text = []

# Stage 1: method family -> validation
for _, row in family_validation.iterrows():
    method_group = row["Method_Group"]
    validation_status = row["Validation_Status"]
    count = int(row["Count"])

    sources.append(
        node_index[method_group]
    )

    targets.append(
        node_index[validation_status]
    )

    values.append(count)

    link_colours.append(
        hex_to_rgba(
            method_colour_map[method_group],
            alpha=0.60,
        )
    )

    hover_text.append(
        f"{method_group}"
        f"<br>→ {validation_status}"
        f"<br>Studies: {count}"
    )

# Stage 2: validation -> preprocessing
# Separate links retain the source method-family colour.
for _, row in family_validation_preprocessing.iterrows():
    method_group = row["Method_Group"]
    validation_status = row["Validation_Status"]
    preprocessing_status = row["Preprocessing_Status"]
    count = int(row["Count"])

    sources.append(
        node_index[validation_status]
    )

    targets.append(
        node_index[preprocessing_status]
    )

    values.append(count)

    link_colours.append(
        hex_to_rgba(
            method_colour_map[method_group],
            alpha=0.60,
        )
    )

    hover_text.append(
        f"{method_group}"
        f"<br>{validation_status}"
        f"<br>→ {preprocessing_status}"
        f"<br>Studies: {count}"
    )

# ----------------------------------------------------------------
# 14. Generate the Q1-ready Sankey figure
# ----------------------------------------------------------------
fig = go.Figure(
    data=[
        go.Sankey(
            # Plotly determines non-overlapping vertical placement.
            arrangement="snap",

            orientation="h",

            node=dict(
                label=node_labels,
                x=node_x,

                # Do not provide fixed y positions.
                # This avoids clipping and overlapping nodes.
                pad=34,
                thickness=20,

                color=node_colours,

                line=dict(
                    color=neutral_node_border,
                    width=0.9,
                ),

                hovertemplate=(
                    "%{label}"
                    "<extra></extra>"
                ),
            ),

            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colours,
                customdata=hover_text,

                hovertemplate=(
                    "%{customdata}"
                    "<extra></extra>"
                ),
            ),
        )
    ]
)

fig.update_layout(
    title=None,

    font=dict(
        family="Arial",
        size=19,
        color=font_colour,
    ),

    paper_bgcolor="white",
    plot_bgcolor="white",

    width=1900,
    height=1250,

    margin=dict(
        l=85,
        r=130,
        t=85,
        b=35,
    ),
)

# ----------------------------------------------------------------
# 15. Add stage headings
# ----------------------------------------------------------------
fig.add_annotation(
    x=0.01,
    y=1.035,
    xref="paper",
    yref="paper",
    text="<b>Principal method family</b>",
    showarrow=False,
    xanchor="left",
    yanchor="bottom",
    font=dict(
        family="Arial",
        size=19,
        color=font_colour,
    ),
)


fig.add_annotation(
    x=0.99,
    y=1.035,
    xref="paper",
    yref="paper",
    text="<b>Preprocessing boundary</b>",
    showarrow=False,
    xanchor="right",
    yanchor="bottom",
    font=dict(
        family="Arial",
        size=19,
        color=font_colour,
    ),
)

fig.add_annotation(
    x=0.50,
    y=1.035,
    xref="paper",
    yref="paper",
    text="<b>Validation design</b>",
    showarrow=False,
    xanchor="center",
    yanchor="bottom",
    font=dict(
        family="Arial",
        size=20,
        color=font_colour,
    ),
)

# Optional short figure note within the bottom margin.
fig.add_annotation(
    x=0.50,
    y=-0.035,
    xref="paper",
    yref="paper",
    text=(
        "Ribbon colour identifies the originating method-family group; "
        "each study contributes one unit at every stage (n=493)."
    ),
    showarrow=False,
    xanchor="center",
    yanchor="top",
    font=dict(
        family="Arial",
        size=13,
        color="#5B6D76",
    ),
)

# ----------------------------------------------------------------
# 16. Export paths
# ----------------------------------------------------------------
html_file = (
    OUTPUT_DIR
    / "Figure16_Model_Validation_Preprocessing_Colour.html"
)

png_file = (
    OUTPUT_DIR
    / "Figure16_Model_Validation_Preprocessing_Colour.png"
)

pdf_file = (
    OUTPUT_DIR
    / "Figure16_Model_Validation_Preprocessing_Colour.pdf"
)

svg_file = (
    OUTPUT_DIR
    / "Figure16_Model_Validation_Preprocessing_Colour.svg"
)

# ----------------------------------------------------------------
# 17. Export interactive HTML
# ----------------------------------------------------------------
fig.write_html(
    html_file,
    include_plotlyjs="cdn",
)

# ----------------------------------------------------------------
# 18. Export static publication files
# Requires:
# %pip install --upgrade kaleido
#
# If Plotly requests Chrome:
# plotly_get_chrome
# ----------------------------------------------------------------
try:
    fig.write_image(
        png_file,
        width=1900,
        height=1250,
        scale=2,
    )

    fig.write_image(
        pdf_file,
        width=1900,
        height=1250,
    )

    fig.write_image(
        svg_file,
        width=1900,
        height=1250,
    )

    print("\nStatic exports completed successfully.")

except Exception as error:
    print("\nInteractive HTML and CSV files were created.")
    print("Static export was not completed.")
    print(error)
    print(
        "\nRun this once in a notebook cell:\n"
        "%pip install --upgrade kaleido\n"
        "\nIf Chrome is requested, run in the VS Code terminal:\n"
        "plotly_get_chrome"
    )

# ----------------------------------------------------------------
# 19. Report output files
# ----------------------------------------------------------------
print("\nCreated output files:")

for file_path in [
    flow_csv_file,
    study_level_file,
    html_file,
    png_file,
    pdf_file,
    svg_file,
]:
    status = "created" if file_path.exists() else "not created"
    print(f"{status:12s} : {file_path}")

print(
    "\nWindows Explorer output path:\n"
    r"\\wsl.localhost\Ubuntu-24.04\home\harman\projects"
    r"\SLR Stock Price Prediction\Stock_Price_Prediction_SLR_ACME"
    r"\Figure16_Output"
)

# Display inside Jupyter/VS Code.
fig.show()
