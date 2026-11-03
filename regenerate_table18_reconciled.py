from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pandas as pd


# ============================================================
# TABLE 18 — RECONCILED METHOD-FAMILY RELIABILITY PROFILE
#
# Reads:
#   1. Section5_5_Methodological_Audit_Reconciled.csv
#   2. Section5_5_Review_264_Closed_45_Pending.xlsx
#      (only when the reconciled CSV does not contain the
#       principal method-family field)
#
# Produces:
#   - reconciled CSV and Excel tables
#   - a ready-to-paste LaTeX table
#   - row-level audit flags
#   - old-versus-new change logs
#
# IMPORTANT:
# The currently reconciled validation counts used in Figure 13 are:
# 59 chronological holdout + 11 walk-forward + 5 rolling
# + 2 expanding + 1 blocked = 78 temporally ordered studies.
# Therefore, a Table 18 total of 77 would be inconsistent with
# the reconciled Figure 13.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_DIR: Final[Path] = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

RECONCILED_AUDIT_NAME: Final[str] = (
    "Section5_5_Methodological_Audit_Reconciled.csv"
)

WORKBOOK_NAME: Final[str] = (
    "Section5_5_Review_264_Closed_45_Pending.xlsx"
)

CODING_SHEET_NAME: Final[str] = (
    "Section5_Coding_Consolidated"
)

OUTPUT_DIR: Final[Path] = (
    PROJECT_DIR
    / "Table18_Reconciled_Output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EXPECTED_STUDIES: Final[int] = 493


# ------------------------------------------------------------
# 2. INPUT CANDIDATES
# ------------------------------------------------------------

AUDIT_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / RECONCILED_AUDIT_NAME,
    PROJECT_DIR / "06_Quality_Assessment" / RECONCILED_AUDIT_NAME,
    PROJECT_DIR / "Methodological_Reliability_Figure_Output"
    / RECONCILED_AUDIT_NAME,
    Path("/mnt/data") / RECONCILED_AUDIT_NAME,
]

WORKBOOK_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / WORKBOOK_NAME,
    PROJECT_DIR / "06_Quality_Assessment" / WORKBOOK_NAME,
    PROJECT_DIR / "14_Sankey" / WORKBOOK_NAME,
    Path("/mnt/data") / WORKBOOK_NAME,
]


# ------------------------------------------------------------
# 3. COLUMN CANDIDATES
# ------------------------------------------------------------

FAMILY_COLUMN_CANDIDATES: Final[list[str]] = [
    "Principal_Method_Family",
    "Method_Family_Standardized",
    "Standardized_Method_Family",
    "Method_Family_Final",
    "Method_Family",
    "Method_Category",
    "Principal_Family",
]

STATUS_COLUMN_CANDIDATES: Final[list[str]] = [
    "Systematic_Inclusion_Status",
    "Final_Status",
    "Inclusion_Status",
]


# ------------------------------------------------------------
# 4. METHOD-FAMILY DEFINITIONS
# ------------------------------------------------------------

FAMILY_ORDER_UNCOMBINED: Final[list[str]] = [
    "Deep-learning models",
    "Hybrid deep-learning models",
    "Sentiment/NLP-driven models",
    "Transformer/attention-based models",
    "Metaheuristic-optimized models",
    "Ensemble/tree-based machine learning",
    "Graph-based models",
    "Multimodal-fusion models",
    "Other/unclear",
    "ANN/neuro-fuzzy models",
]

EXPECTED_FAMILY_COUNTS_UNCOMBINED: Final[dict[str, int]] = {
    "Deep-learning models": 117,
    "Hybrid deep-learning models": 110,
    "Sentiment/NLP-driven models": 81,
    "Transformer/attention-based models": 68,
    "Metaheuristic-optimized models": 51,
    "Ensemble/tree-based machine learning": 34,
    "Graph-based models": 16,
    "Multimodal-fusion models": 13,
    "Other/unclear": 2,
    "ANN/neuro-fuzzy models": 1,
}

TABLE_FAMILY_ORDER: Final[list[str]] = [
    "Deep-learning models",
    "Hybrid deep-learning models",
    "Sentiment/NLP-driven models",
    "Transformer/attention-based models",
    "Metaheuristic-optimized models",
    "Ensemble/tree-based machine learning",
    "Graph-based models",
    "Multimodal-fusion models",
    "ANN/neuro-fuzzy/other",
]

EXPECTED_TABLE_FAMILY_COUNTS: Final[dict[str, int]] = {
    "Deep-learning models": 117,
    "Hybrid deep-learning models": 110,
    "Sentiment/NLP-driven models": 81,
    "Transformer/attention-based models": 68,
    "Metaheuristic-optimized models": 51,
    "Ensemble/tree-based machine learning": 34,
    "Graph-based models": 16,
    "Multimodal-fusion models": 13,
    "ANN/neuro-fuzzy/other": 3,
}


# ------------------------------------------------------------
# 5. RELIABILITY INDICATORS
# ------------------------------------------------------------

TEMPORALLY_ORDERED_DESIGNS: Final[set[str]] = {
    "Chronological_Holdout",
    "Walk_Forward",
    "Rolling_Window",
    "Expanding_Window",
    "Blocked_CV",
}

INDICATOR_ORDER: Final[list[str]] = [
    "Temporally ordered",
    "Training-only preprocessing",
    "Explicit high leakage risk",
    "Economic evaluation",
    "Formal statistical testing",
    "Code available",
]

# These totals must match the reconciled audit and the updated Figure 13.
EXPECTED_RECONCILED_TOTALS: Final[dict[str, int]] = {
    "Temporally ordered": 78,
    "Training-only preprocessing": 21,
    "Explicit high leakage risk": 31,
    "Economic evaluation": 38,
    "Formal statistical testing": 48,
    "Code available": 7,
}


# ------------------------------------------------------------
# 6. OLD TABLE 18 VALUES — FOR CHANGE LOG ONLY
# ------------------------------------------------------------

OLD_TABLE_VALUES: Final[dict[str, dict[str, int]]] = {
    "Deep-learning models": {
        "Temporally ordered": 11,
        "Explicit high leakage risk": 5,
    },
    "Hybrid deep-learning models": {
        "Temporally ordered": 12,
        "Explicit high leakage risk": 9,
    },
    "Sentiment/NLP-driven models": {
        "Temporally ordered": 15,
        "Explicit high leakage risk": 5,
    },
    "Transformer/attention-based models": {
        "Temporally ordered": 18,
        "Explicit high leakage risk": 6,
    },
    "Metaheuristic-optimized models": {
        "Temporally ordered": 8,
        "Explicit high leakage risk": 2,
    },
    "Ensemble/tree-based machine learning": {
        "Temporally ordered": 8,
        "Explicit high leakage risk": 4,
    },
    "Graph-based models": {
        "Temporally ordered": 4,
        "Explicit high leakage risk": 1,
    },
    "Multimodal-fusion models": {
        "Temporally ordered": 0,
        "Explicit high leakage risk": 1,
    },
    "ANN/neuro-fuzzy/other": {
        "Temporally ordered": 1,
        "Explicit high leakage risk": 0,
    },
}


# ------------------------------------------------------------
# 7. GENERAL HELPERS
# ------------------------------------------------------------

def clean(value: object) -> str:
    """Normalize whitespace without changing substantive content."""

    if value is None:
        return ""

    return " ".join(
        str(value).strip().split()
    )


def normalized_key(value: object) -> str:
    """Create a lowercase alphanumeric key for robust matching."""

    text = clean(value).casefold()

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    ).strip()


def find_existing_file(
    candidates: list[Path],
    filename: str,
) -> Path:
    """Find one intended input file."""

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    matches = list(
        PROJECT_DIR.rglob(filename)
    )

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise RuntimeError(
            f"More than one copy of {filename} was found:\n"
            + "\n".join(str(path) for path in matches)
            + "\n\nSet the intended path explicitly."
        )

    raise FileNotFoundError(
        f"Could not find {filename}.\n\nChecked:\n"
        + "\n".join(str(path) for path in candidates)
    )


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """Find a column case-insensitively."""

    lookup = {
        clean(column).casefold(): clean(column)
        for column in dataframe.columns
    }

    for candidate in candidates:
        match = lookup.get(candidate.casefold())

        if match is not None:
            return match

    return None


def affirmative(value: object) -> bool:
    """Return True only for an explicitly affirmative audit value."""

    return normalized_key(value) in {
        "yes",
        "true",
        "1",
        "available",
        "established",
        "explicit yes",
    }


def percent(
    count: int,
    denominator: int,
) -> float:
    """Calculate a percentage."""

    if denominator <= 0:
        return 0.0

    return 100.0 * count / denominator


def formatted_cell(
    count: int,
    denominator: int,
) -> str:
    """Format a table cell as n (row percentage)."""

    if count == 0:
        return "0"

    return (
        f"{count} "
        f"({percent(count, denominator):.1f}%)"
    )


def latex_cell(
    count: int,
    denominator: int,
) -> str:
    """Format a LaTeX table cell."""

    if count == 0:
        return "0"

    return (
        f"{count} "
        f"({percent(count, denominator):.1f}\\%)"
    )


def family_from_value(value: object) -> str:
    """
    Normalize a source method-family value to the manuscript taxonomy.

    The order of the rules matters: hybrid deep learning must be
    identified before general deep learning.
    """

    key = normalized_key(value)

    if not key:
        return ""

    if (
        "hybrid" in key
        and (
            "deep" in key
            or "lstm" in key
            or "cnn" in key
            or "gru" in key
        )
    ):
        return "Hybrid deep-learning models"

    if (
        "transformer" in key
        or "attention" in key
    ):
        return "Transformer/attention-based models"

    if (
        "sentiment" in key
        or "nlp" in key
        or "natural language" in key
        or "text driven" in key
    ):
        return "Sentiment/NLP-driven models"

    if (
        "metaheuristic" in key
        or "evolutionary" in key
        or "optimized" in key
        or "optimised" in key
    ):
        return "Metaheuristic-optimized models"

    if (
        "ensemble" in key
        or "tree based" in key
        or "random forest" in key
        or "boosting" in key
        or "xgboost" in key
        or "lightgbm" in key
    ):
        return "Ensemble/tree-based machine learning"

    if "graph" in key:
        return "Graph-based models"

    if "multimodal" in key:
        return "Multimodal-fusion models"

    if (
        key in {"ann", "artificial neural network"}
        or "neuro fuzzy" in key
        or key.startswith("ann ")
        or key.endswith(" ann")
        or "fuzzy" in key
    ):
        return "ANN/neuro-fuzzy models"

    if (
        "other" in key
        or "unclear" in key
        or "not reported" in key
    ):
        return "Other/unclear"

    if (
        "deep" in key
        or "lstm" in key
        or "gru" in key
        or "cnn" in key
        or "rnn" in key
        or "autoencoder" in key
    ):
        return "Deep-learning models"

    raise ValueError(
        "Unrecognized principal method-family value: "
        f"{value!r}"
    )


def table_family(
    standardized_family: str,
) -> str:
    """Combine ANN/neuro-fuzzy and other/unclear for Table 18."""

    if standardized_family in {
        "ANN/neuro-fuzzy models",
        "Other/unclear",
    }:
        return "ANN/neuro-fuzzy/other"

    return standardized_family


def validate_exact_counts(
    observed: dict[str, int],
    expected: dict[str, int],
    label: str,
) -> None:
    """Fail with a useful comparison when counts do not match."""

    rows = []

    for category, expected_count in expected.items():
        observed_count = int(
            observed.get(category, 0)
        )

        if observed_count != expected_count:
            rows.append(
                {
                    "Category": category,
                    "Expected": expected_count,
                    "Observed": observed_count,
                }
            )

    unexpected = sorted(
        set(observed) - set(expected)
    )

    for category in unexpected:
        rows.append(
            {
                "Category": category,
                "Expected": 0,
                "Observed": observed[category],
            }
        )

    if rows:
        comparison = pd.DataFrame(rows)

        raise AssertionError(
            f"{label} counts do not match the frozen taxonomy:\n\n"
            + comparison.to_string(index=False)
        )


# ------------------------------------------------------------
# 8. LOAD RECONCILED AUDIT
# ------------------------------------------------------------

audit_file = find_existing_file(
    AUDIT_CANDIDATES,
    RECONCILED_AUDIT_NAME,
)

print("\nReconciled audit:")
print(audit_file)

audit = pd.read_csv(
    audit_file,
    dtype=str,
    keep_default_na=False,
)

audit.columns = [
    clean(column)
    for column in audit.columns
]

for column in audit.columns:
    audit[column] = (
        audit[column]
        .fillna("")
        .astype(str)
        .map(clean)
    )

if len(audit) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} audit rows; "
        f"found {len(audit)}."
    )

if "Paper_ID" not in audit.columns:
    raise KeyError(
        "The reconciled audit does not contain Paper_ID."
    )

if audit["Paper_ID"].eq("").any():
    raise AssertionError(
        "Blank Paper_ID values were found in the audit."
    )

if not audit["Paper_ID"].is_unique:
    duplicate_ids = (
        audit.loc[
            audit["Paper_ID"].duplicated(keep=False),
            "Paper_ID",
        ]
        .sort_values()
        .unique()
        .tolist()
    )

    raise AssertionError(
        "Duplicate Paper_ID values were found in the audit:\n"
        f"{duplicate_ids[:30]}"
    )


# ------------------------------------------------------------
# 9. OBTAIN PRINCIPAL METHOD FAMILY
# ------------------------------------------------------------

family_column = find_column(
    audit,
    FAMILY_COLUMN_CANDIDATES,
)

if family_column is not None:
    analysis = audit.copy()

    analysis["_Family_Source"] = (
        analysis[family_column]
    )

    print(
        "\nMethod-family column found in reconciled audit:"
    )
    print(family_column)

else:
    workbook_file = find_existing_file(
        WORKBOOK_CANDIDATES,
        WORKBOOK_NAME,
    )

    print("\nCoding workbook:")
    print(workbook_file)

    coding = pd.read_excel(
        workbook_file,
        sheet_name=CODING_SHEET_NAME,
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )

    coding.columns = [
        clean(column)
        for column in coding.columns
    ]

    for column in coding.columns:
        coding[column] = (
            coding[column]
            .fillna("")
            .astype(str)
            .map(clean)
        )

    status_column = find_column(
        coding,
        STATUS_COLUMN_CANDIDATES,
    )

    if status_column is not None:
        included_mask = (
            coding[status_column]
            .map(normalized_key)
            .isin(
                {
                    "included high priority",
                    "included",
                    "include",
                }
            )
        )

        if int(included_mask.sum()) == EXPECTED_STUDIES:
            coding = coding.loc[
                included_mask
            ].copy()

    if len(coding) != EXPECTED_STUDIES:
        raise AssertionError(
            "The coding sheet did not resolve to 493 included rows. "
            f"Rows found: {len(coding)}.\n"
            "Check the inclusion-status field."
        )

    if "Paper_ID" not in coding.columns:
        raise KeyError(
            "The coding sheet does not contain Paper_ID."
        )

    if not coding["Paper_ID"].is_unique:
        raise AssertionError(
            "Paper_ID is not unique in the coding sheet."
        )

    family_column = find_column(
        coding,
        FAMILY_COLUMN_CANDIDATES,
    )

    if family_column is None:
        raise KeyError(
            "No principal method-family column was found.\n\n"
            "Checked candidates:\n"
            f"{FAMILY_COLUMN_CANDIDATES}\n\n"
            "Available coding columns:\n"
            f"{list(coding.columns)}"
        )

    coding_family = coding[
        [
            "Paper_ID",
            family_column,
        ]
    ].rename(
        columns={
            family_column: "_Family_Source",
        }
    )

    analysis = audit.merge(
        coding_family,
        on="Paper_ID",
        how="left",
        validate="one_to_one",
    )

    if analysis["_Family_Source"].eq("").any():
        missing_ids = analysis.loc[
            analysis["_Family_Source"].eq(""),
            "Paper_ID",
        ].tolist()

        raise AssertionError(
            "Principal method family was missing after the merge "
            f"for {len(missing_ids)} studies:\n"
            f"{missing_ids[:30]}"
        )

    print(
        "\nMethod-family column obtained from coding sheet:"
    )
    print(family_column)


# ------------------------------------------------------------
# 10. STANDARDIZE AND VERIFY METHOD FAMILIES
# ------------------------------------------------------------

analysis["Method_Family_Standardized"] = (
    analysis["_Family_Source"]
    .map(family_from_value)
)

family_counts_uncombined = (
    analysis["Method_Family_Standardized"]
    .value_counts()
    .to_dict()
)

validate_exact_counts(
    observed={
        key: int(value)
        for key, value in family_counts_uncombined.items()
    },
    expected=EXPECTED_FAMILY_COUNTS_UNCOMBINED,
    label="Uncombined method-family",
)

analysis["Table18_Method_Family"] = (
    analysis["Method_Family_Standardized"]
    .map(table_family)
)

table_family_counts = (
    analysis["Table18_Method_Family"]
    .value_counts()
    .to_dict()
)

validate_exact_counts(
    observed={
        key: int(value)
        for key, value in table_family_counts.items()
    },
    expected=EXPECTED_TABLE_FAMILY_COUNTS,
    label="Table 18 method-family",
)


# ------------------------------------------------------------
# 11. REQUIRED AUDIT COLUMNS
# ------------------------------------------------------------

required_audit_columns = {
    "Validation_Design",
    "Preprocessing_Boundary",
    "Leakage_Risk",
    "Economic_Evaluation_Claimed",
    "Statistical_Testing",
    "Code_Available",
}

missing_audit_columns = sorted(
    required_audit_columns - set(analysis.columns)
)

if missing_audit_columns:
    raise KeyError(
        "Required reconciled-audit columns are missing:\n"
        f"{missing_audit_columns}\n\n"
        "Available columns:\n"
        f"{list(analysis.columns)}"
    )


# ------------------------------------------------------------
# 12. CREATE STUDY-LEVEL RELIABILITY FLAGS
# ------------------------------------------------------------

analysis["Flag_Temporally_Ordered"] = (
    analysis["Validation_Design"]
    .isin(TEMPORALLY_ORDERED_DESIGNS)
)

analysis["Flag_Training_Only_Preprocessing"] = (
    analysis["Preprocessing_Boundary"]
    .map(normalized_key)
    .eq("training only")
)

analysis["Flag_Explicit_High_Leakage_Risk"] = (
    analysis["Leakage_Risk"]
    .map(normalized_key)
    .eq("high")
)

analysis["Flag_Economic_Evaluation"] = (
    analysis["Economic_Evaluation_Claimed"]
    .map(affirmative)
)

analysis["Flag_Formal_Statistical_Testing"] = (
    analysis["Statistical_Testing"]
    .map(affirmative)
)

analysis["Flag_Code_Available"] = (
    analysis["Code_Available"]
    .map(affirmative)
)


FLAG_COLUMNS: Final[dict[str, str]] = {
    "Temporally ordered":
        "Flag_Temporally_Ordered",

    "Training-only preprocessing":
        "Flag_Training_Only_Preprocessing",

    "Explicit high leakage risk":
        "Flag_Explicit_High_Leakage_Risk",

    "Economic evaluation":
        "Flag_Economic_Evaluation",

    "Formal statistical testing":
        "Flag_Formal_Statistical_Testing",

    "Code available":
        "Flag_Code_Available",
}


# ------------------------------------------------------------
# 13. VERIFY RECONCILED TOTALS
# ------------------------------------------------------------

observed_totals = {
    label:
        int(analysis[column].sum())
    for label, column in FLAG_COLUMNS.items()
}

print("\nObserved reconciled totals:")

for label in INDICATOR_ORDER:
    count = observed_totals[label]

    print(
        f"  {label:34s}: "
        f"{count:3d} "
        f"({percent(count, EXPECTED_STUDIES):.1f}%)"
    )

validate_exact_counts(
    observed=observed_totals,
    expected=EXPECTED_RECONCILED_TOTALS,
    label="Reconciled reliability-total",
)


# ------------------------------------------------------------
# 14. GENERATE TABLE 18
# ------------------------------------------------------------

raw_rows = []
formatted_rows = []

for family in TABLE_FAMILY_ORDER:

    subset = analysis.loc[
        analysis["Table18_Method_Family"]
        .eq(family)
    ]

    studies = int(len(subset))

    raw_row: dict[str, object] = {
        "Method family": family,
        "Studies": studies,
    }

    formatted_row: dict[str, object] = {
        "Method family": family,
        "Studies": studies,
    }

    for label in INDICATOR_ORDER:
        flag_column = FLAG_COLUMNS[label]

        count = int(
            subset[flag_column].sum()
        )

        raw_row[f"{label} n"] = count
        raw_row[f"{label} %"] = round(
            percent(count, studies),
            1,
        )

        formatted_row[label] = (
            formatted_cell(
                count,
                studies,
            )
        )

    raw_rows.append(raw_row)
    formatted_rows.append(formatted_row)


# Total row
raw_total_row: dict[str, object] = {
    "Method family": "Total",
    "Studies": EXPECTED_STUDIES,
}

formatted_total_row: dict[str, object] = {
    "Method family": "Total",
    "Studies": EXPECTED_STUDIES,
}

for label in INDICATOR_ORDER:
    count = observed_totals[label]

    raw_total_row[f"{label} n"] = count
    raw_total_row[f"{label} %"] = round(
        percent(
            count,
            EXPECTED_STUDIES,
        ),
        1,
    )

    formatted_total_row[label] = (
        formatted_cell(
            count,
            EXPECTED_STUDIES,
        )
    )

raw_rows.append(raw_total_row)
formatted_rows.append(formatted_total_row)

raw_table = pd.DataFrame(raw_rows)
formatted_table = pd.DataFrame(formatted_rows)


# ------------------------------------------------------------
# 15. CHANGE LOG AGAINST OLD TABLE 18
# ------------------------------------------------------------

change_rows = []

for family in TABLE_FAMILY_ORDER:

    new_row = raw_table.loc[
        raw_table["Method family"].eq(family)
    ].iloc[0]

    for indicator in [
        "Temporally ordered",
        "Explicit high leakage risk",
    ]:
        old_count = int(
            OLD_TABLE_VALUES[family][indicator]
        )

        new_count = int(
            new_row[f"{indicator} n"]
        )

        change_rows.append(
            {
                "Method family": family,
                "Indicator": indicator,
                "Old count": old_count,
                "New count": new_count,
                "Change": new_count - old_count,
            }
        )

change_log = pd.DataFrame(change_rows)

changed_only = change_log.loc[
    change_log["Change"].ne(0)
].copy()


# ------------------------------------------------------------
# 16. LATEX OUTPUT
# ------------------------------------------------------------

latex_lines = [
    r"\begin{landscape}",
    r"\begin{table}[!p]",
    r"\centering",
    (
        r"\caption{Method-family profile of evidence-supported "
        r"reliability practices in the \(493\)-study "
        r"technical-synthesis subset.}"
    ),
    r"\label{tab:family-reliability}",
    "",
    r"\footnotesize",
    r"\setlength{\tabcolsep}{3.2pt}",
    r"\renewcommand{\arraystretch}{1.14}",
    "",
    r"\begin{tabularx}{\linewidth}{",
    r"@{}",
    r">{\RaggedRight\arraybackslash}p{3.4cm}",
    r">{\centering\arraybackslash}p{1.0cm}",
    r"*{6}{>{\centering\arraybackslash}X}",
    r"@{}",
    r"}",
    r"\toprule",
    (
        r"\textbf{Method family} & "
        r"\textbf{Studies} & "
        r"\textbf{Temporally ordered} & "
        r"\textbf{Training-only preprocessing} & "
        r"\textbf{Explicit high leakage risk} & "
        r"\textbf{Economic evaluation} & "
        r"\textbf{Formal statistical testing} & "
        r"\textbf{Code available} \\"
    ),
    r"\midrule",
]

for family in TABLE_FAMILY_ORDER:

    subset = analysis.loc[
        analysis["Table18_Method_Family"]
        .eq(family)
    ]

    studies = int(len(subset))

    cells = []

    for label in INDICATOR_ORDER:
        count = int(
            subset[
                FLAG_COLUMNS[label]
            ].sum()
        )

        cells.append(
            latex_cell(
                count,
                studies,
            )
        )

    family_latex = family.replace(
        "&",
        r"\&",
    )

    latex_lines.extend(
        [
            family_latex,
            (
                f"& {studies} "
                + " ".join(
                    f"& {cell}"
                    for cell in cells
                )
                + r" \\"
            ),
            "",
        ]
    )

latex_lines.append(r"\midrule")

total_cells = [
    latex_cell(
        observed_totals[label],
        EXPECTED_STUDIES,
    )
    for label in INDICATOR_ORDER
]

latex_lines.extend(
    [
        r"\textbf{Total}",
        (
            f"& {EXPECTED_STUDIES} "
            + " ".join(
                f"& {cell}"
                for cell in total_cells
            )
            + r" \\"
        ),
        r"\bottomrule",
        r"\end{tabularx}",
        "",
        r"\vspace{1.5mm}",
        "",
        r"\begin{minipage}{\linewidth}",
        r"\footnotesize",
        r"\textit{Notes.}",
        (
            r"Values are \(n\) (row percentage), except in the total "
            r"row, where percentages use all \(493\) studies as the "
            r"denominator."
        ),
        "",
        (
            r"Temporally ordered validation comprises chronological "
            r"holdout, walk-forward, rolling-window, expanding-window, "
            r"and blocked temporal cross-validation."
        ),
        "",
        (
            r"Training-only preprocessing was counted only when the "
            r"preprocessing boundary was explicitly classified as "
            r"\texttt{Training\_Only} in the reconciled audit."
        ),
        "",
        (
            r"Explicit high leakage risk denotes studies classified "
            r"as \texttt{High} in the final study-level leakage-risk "
            r"assessment. It is not the complement of low leakage risk "
            r"because most studies retained an \texttt{Unclear} "
            r"classification."
        ),
        "",
        (
            r"The indicators are not mutually exclusive. A study may "
            r"contribute to more than one reliability column."
        ),
        "",
        (
            r"Zero indicates that no study in the corresponding method "
            r"family had the practice explicitly established in the "
            r"available evidence; it should not be interpreted as "
            r"definitive proof that the practice was absent."
        ),
        "",
        (
            r"The ANN/neuro-fuzzy/other group contains three studies "
            r"and should not be compared directly with larger method "
            r"families."
        ),
        r"\end{minipage}",
        r"\end{table}",
        r"\end{landscape}",
        "",
    ]
)

latex_text = "\n".join(latex_lines)


# ------------------------------------------------------------
# 17. SAVE OUTPUTS
# ------------------------------------------------------------

raw_csv = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled_Raw.csv"
)

formatted_csv = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled_Formatted.csv"
)

excel_file = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled.xlsx"
)

latex_file = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled.tex"
)

detail_file = (
    OUTPUT_DIR
    / "Table18_Study_Level_Flags_Reconciled.csv"
)

change_file = (
    OUTPUT_DIR
    / "Table18_Old_vs_Reconciled_Changes.csv"
)

raw_table.to_csv(
    raw_csv,
    index=False,
    encoding="utf-8-sig",
)

formatted_table.to_csv(
    formatted_csv,
    index=False,
    encoding="utf-8-sig",
)

analysis[
    [
        "Paper_ID",
        "_Family_Source",
        "Method_Family_Standardized",
        "Table18_Method_Family",
        "Validation_Design",
        "Preprocessing_Boundary",
        "Leakage_Risk",
        "Economic_Evaluation_Claimed",
        "Statistical_Testing",
        "Code_Available",
        *FLAG_COLUMNS.values(),
    ]
].to_csv(
    detail_file,
    index=False,
    encoding="utf-8-sig",
)

change_log.to_csv(
    change_file,
    index=False,
    encoding="utf-8-sig",
)

latex_file.write_text(
    latex_text,
    encoding="utf-8",
)

with pd.ExcelWriter(
    excel_file,
    engine="openpyxl",
) as writer:
    raw_table.to_excel(
        writer,
        sheet_name="Raw counts",
        index=False,
    )

    formatted_table.to_excel(
        writer,
        sheet_name="Formatted Table 18",
        index=False,
    )

    changed_only.to_excel(
        writer,
        sheet_name="Changed cells",
        index=False,
    )

    change_log.to_excel(
        writer,
        sheet_name="Full comparison",
        index=False,
    )


# ------------------------------------------------------------
# 18. FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 100)
print("RECONCILED TABLE 18")
print("=" * 100)

print(
    formatted_table.to_string(
        index=False,
    )
)

print("\nCells changed from the old Table 18:")

if changed_only.empty:
    print("  None.")
else:
    print(
        changed_only.to_string(
            index=False,
        )
    )

print("\nCorrect reconciled total row:")

print(
    "Total "
    f"& {EXPECTED_STUDIES} "
    + " ".join(
        f"& {latex_cell(observed_totals[label], EXPECTED_STUDIES)}"
        for label in INDICATOR_ORDER
    )
    + r" \\"
)

print("\nCreated files:")

for output_file in [
    raw_csv,
    formatted_csv,
    excel_file,
    latex_file,
    detail_file,
    change_file,
]:
    print(f"  {output_file}")

print(
    "\nIMPORTANT: The reconciled temporally ordered total is "
    f"{observed_totals['Temporally ordered']} "
    f"({percent(observed_totals['Temporally ordered'], EXPECTED_STUDIES):.1f}%)."
)
