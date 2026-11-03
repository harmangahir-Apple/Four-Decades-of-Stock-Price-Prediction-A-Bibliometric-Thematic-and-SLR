
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# ================================================================
# FIGURE 16
# Model family -> validation design -> preprocessing boundary
# ================================================================

# Put the notebook/script in the same folder as the two Excel files,
# or replace BASE_DIR with their folder.
BASE_DIR = Path.cwd()

METHOD_FILE = BASE_DIR / "Section7_Sankey_Working_COMPLETED.xlsx"
AUDIT_FILE = BASE_DIR / "Section5_5_Review_264_Closed_45_Pending.xlsx"
OUTPUT_DIR = BASE_DIR / "Figure16_Output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------
# 1. Read only the required columns
# ------------------------------------------------
method_df = pd.read_excel(
    METHOD_FILE,
    sheet_name="Sankey_Input",
    usecols=["Paper_ID", "Principal_Method_Family"],
    dtype=str,
)

audit_df = pd.read_excel(
    AUDIT_FILE,
    sheet_name="Section5_5_Methodological_Audit",
    usecols=["Paper_ID", "Validation_Design", "Preprocessing_Boundary"],
    dtype=str,
)

for frame in (method_df, audit_df):
    for column in frame.columns:
        frame[column] = frame[column].fillna("").str.strip()

# ------------------------------------------------
# 2. Integrity checks
# ------------------------------------------------
assert len(method_df) == 493, f"Section 7 contains {len(method_df)} rows, expected 493."
assert len(audit_df) == 493, f"Section 5.5 contains {len(audit_df)} rows, expected 493."
assert method_df["Paper_ID"].is_unique, "Duplicate Paper_ID in Section 7 workbook."
assert audit_df["Paper_ID"].is_unique, "Duplicate Paper_ID in Section 5.5 workbook."

df = method_df.merge(
    audit_df,
    on="Paper_ID",
    how="inner",
    validate="one_to_one",
)

assert len(df) == 493, f"The merged dataset contains {len(df)} rows, expected 493."

missing_method_ids = sorted(set(audit_df["Paper_ID"]) - set(method_df["Paper_ID"]))
missing_audit_ids = sorted(set(method_df["Paper_ID"]) - set(audit_df["Paper_ID"]))
assert not missing_method_ids, f"Missing from method workbook: {missing_method_ids[:10]}"
assert not missing_audit_ids, f"Missing from audit workbook: {missing_audit_ids[:10]}"

# ------------------------------------------------
# 3. Collapse ten method families to five readable groups
#    for the main-manuscript figure
# ------------------------------------------------
family_map = {
    "Deep-learning models": "Deep + hybrid deep learning",
    "Hybrid deep-learning models": "Deep + hybrid deep learning",

    "Transformer/attention-based models": "Transformer + graph + multimodal",
    "Graph-based models": "Transformer + graph + multimodal",
    "Multimodal-fusion models": "Transformer + graph + multimodal",

    "Metaheuristic-optimized models": "Metaheuristic + ensemble",
    "Ensemble/tree-based machine learning": "Metaheuristic + ensemble",

    "Sentiment/NLP-driven models": "Sentiment / NLP",

    "ANN/neuro-fuzzy models": "ANN / other",
    "Other/unclear": "ANN / other",
}

unknown_families = sorted(set(df["Principal_Method_Family"]) - set(family_map))
assert not unknown_families, f"Unmapped method families: {unknown_families}"

df["Method_Group"] = df["Principal_Method_Family"].map(family_map)

# ------------------------------------------------
# 4. Validation classification
# ------------------------------------------------
temporally_ordered_codes = {
    "Chronological_Holdout",
    "Walk_Forward",
    "Rolling_Window",
    "Expanding_Window",
    "Blocked_CV",
}
random_codes = {"Random_Shuffled"}

expected_validation_codes = (
    temporally_ordered_codes | random_codes | {"Unclear"}
)
unexpected_validation_codes = sorted(
    set(df["Validation_Design"]) - expected_validation_codes
)
assert not unexpected_validation_codes, (
    "Unexpected Validation_Design codes: "
    f"{unexpected_validation_codes}"
)

def classify_validation(value):
    if value in temporally_ordered_codes:
        return "Temporally ordered"
    if value in random_codes:
        return "Random or shuffled"
    return "Unclear validation"

df["Validation_Status"] = df["Validation_Design"].map(classify_validation)

# ------------------------------------------------
# 5. Preprocessing-boundary classification
# ------------------------------------------------
preprocessing_map = {
    "Training_Only": "Training only",
    "Full_Dataset": "Full dataset",
    "Unclear": "Unclear preprocessing",
}

unexpected_preprocessing_codes = sorted(
    set(df["Preprocessing_Boundary"]) - set(preprocessing_map)
)
assert not unexpected_preprocessing_codes, (
    "Unexpected Preprocessing_Boundary codes: "
    f"{unexpected_preprocessing_codes}"
)

df["Preprocessing_Status"] = (
    df["Preprocessing_Boundary"].map(preprocessing_map)
)

# ------------------------------------------------
# 6. Fix category order
# ------------------------------------------------
family_order = [
    "Deep + hybrid deep learning",
    "Transformer + graph + multimodal",
    "Metaheuristic + ensemble",
    "Sentiment / NLP",
    "ANN / other",
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

# ------------------------------------------------
# 7. Verify the published denominators
# ------------------------------------------------
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
    "Deep + hybrid deep learning": 227,
    "Transformer + graph + multimodal": 97,
    "Metaheuristic + ensemble": 85,
    "Sentiment / NLP": 81,
    "ANN / other": 3,
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

assert family_counts.to_dict() == expected_family_counts
assert validation_counts.to_dict() == expected_validation_counts
assert preprocessing_counts.to_dict() == expected_preprocessing_counts

print("Method-family totals")
print(family_counts)
print("\nValidation totals")
print(validation_counts)
print("\nPreprocessing totals")
print(preprocessing_counts)

# ------------------------------------------------
# 8. Create the two flow tables
# ------------------------------------------------
family_validation = (
    df.groupby(["Method_Group", "Validation_Status"], observed=True)
      .size()
      .reset_index(name="Count")
)

validation_preprocessing = (
    df.groupby(
        ["Validation_Status", "Preprocessing_Status"],
        observed=True
    )
    .size()
    .reset_index(name="Count")
)

family_validation = family_validation[
    family_validation["Count"] > 0
].copy()

validation_preprocessing = validation_preprocessing[
    validation_preprocessing["Count"] > 0
].copy()

print("\nModel family -> validation")
print(
    family_validation.pivot(
        index="Method_Group",
        columns="Validation_Status",
        values="Count",
    )
    .fillna(0)
    .astype(int)
    .reindex(index=family_order, columns=validation_order, fill_value=0)
)

print("\nValidation -> preprocessing boundary")
print(
    validation_preprocessing.pivot(
        index="Validation_Status",
        columns="Preprocessing_Status",
        values="Count",
    )
    .fillna(0)
    .astype(int)
    .reindex(
        index=validation_order,
        columns=preprocessing_order,
        fill_value=0,
    )
)

# ------------------------------------------------
# 9. Save an audit-ready flow table
# ------------------------------------------------
flow_part_1 = family_validation.rename(
    columns={
        "Method_Group": "Source",
        "Validation_Status": "Target",
    }
)
flow_part_1.insert(0, "Source_Stage", "Model family")
flow_part_1.insert(2, "Target_Stage", "Validation")

flow_part_2 = validation_preprocessing.rename(
    columns={
        "Validation_Status": "Source",
        "Preprocessing_Status": "Target",
    }
)
flow_part_2.insert(0, "Source_Stage", "Validation")
flow_part_2.insert(2, "Target_Stage", "Preprocessing boundary")

flow_table = pd.concat(
    [flow_part_1, flow_part_2],
    ignore_index=True,
)

flow_table.to_csv(
    OUTPUT_DIR / "Figure16_Sankey_Flows.csv",
    index=False,
)

# ------------------------------------------------
# 10. Construct Sankey nodes and links
# ------------------------------------------------
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

node_names = family_order + validation_order + preprocessing_order
node_labels = family_labels + validation_labels + preprocessing_labels
node_index = {name: index for index, name in enumerate(node_names)}

sources = []
targets = []
values = []
hover_text = []

for _, row in family_validation.iterrows():
    sources.append(node_index[row["Method_Group"]])
    targets.append(node_index[row["Validation_Status"]])
    values.append(int(row["Count"]))
    hover_text.append(
        f'{row["Method_Group"]} -> {row["Validation_Status"]}'
    )

for _, row in validation_preprocessing.iterrows():
    sources.append(node_index[row["Validation_Status"]])
    targets.append(node_index[row["Preprocessing_Status"]])
    values.append(int(row["Count"]))
    hover_text.append(
        f'{row["Validation_Status"]} -> '
        f'{row["Preprocessing_Status"]}'
    )

# Lock nodes into three vertical stages.
node_x = (
    [0.01] * len(family_order)
    + [0.50] * len(validation_order)
    + [0.99] * len(preprocessing_order)
)

node_y = (
    [0.02, 0.22, 0.42, 0.62, 0.82]
    + [0.05, 0.38, 0.68]
    + [0.05, 0.38, 0.68]
)

fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="fixed",
            node=dict(
                label=node_labels,
                x=node_x,
                y=node_y,
                pad=24,
                thickness=24,
                line=dict(width=0.8),
                hovertemplate="%{label}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                customdata=hover_text,
                hovertemplate=(
                    "%{customdata}"
                    "<br>Studies: %{value}"
                    "<extra></extra>"
                ),
            ),
        )
    ]
)

fig.update_layout(
    title=dict(
        text=(
            "Model family -> validation design -> "
            "preprocessing boundary"
            "<br><sup>Technical-synthesis subset (n=493)</sup>"
        ),
        x=0.5,
        xanchor="center",
    ),
    font=dict(size=15),
    width=1800,
    height=1050,
    margin=dict(l=40, r=40, t=110, b=45),
)

# ------------------------------------------------
# 11. Export
# ------------------------------------------------
html_file = (
    OUTPUT_DIR
    / "Figure16_Model_Validation_Preprocessing.html"
)
fig.write_html(
    html_file,
    include_plotlyjs="cdn",
)

# Requires Kaleido:
# pip install --upgrade kaleido
#
# Plotly/Kaleido may also request a local Chrome installation.
try:
    fig.write_image(
        OUTPUT_DIR
        / "Figure16_Model_Validation_Preprocessing.png",
        scale=2,
    )
    fig.write_image(
        OUTPUT_DIR
        / "Figure16_Model_Validation_Preprocessing.pdf"
    )
    fig.write_image(
        OUTPUT_DIR
        / "Figure16_Model_Validation_Preprocessing.svg"
    )
    print("\nPNG, PDF, and SVG exported successfully.")
except Exception as error:
    print("\nInteractive HTML was exported successfully.")
    print("Static export was skipped:")
    print(error)
    print(
        "\nInstall/upgrade Kaleido in a notebook cell:\n"
        "%pip install --upgrade kaleido"
    )

print(f"\nOutput folder: {OUTPUT_DIR.resolve()}")
fig.show()
