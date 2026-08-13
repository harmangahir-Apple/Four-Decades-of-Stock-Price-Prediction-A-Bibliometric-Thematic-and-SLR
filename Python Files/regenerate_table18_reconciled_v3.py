from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Final
import csv
import re


# ============================================================
# TABLE 18 — RECONCILED METHOD-FAMILY RELIABILITY PROFILE
#
# Correct data architecture:
#   1. Section5_5_Methodological_Audit_Reconciled.csv
#      supplies the six reconciled reliability indicators.
#
#   2. Section7_Final_Study_Level_Sankey_Input.csv
#      supplies the already frozen Principal_Method_Family
#      classification for the same 493 Paper_ID values.
#
# The Section5 workbook is deliberately NOT used for method family,
# because its Model_Family field is blank for the included records.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_DIR: Final[Path] = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

AUDIT_NAME: Final[str] = (
    "Section5_5_Methodological_Audit_Reconciled.csv"
)

FAMILY_NAME: Final[str] = (
    "Section7_Final_Study_Level_Sankey_Input.csv"
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
    PROJECT_DIR / AUDIT_NAME,
    PROJECT_DIR / "06_Quality_Assessment" / AUDIT_NAME,
    PROJECT_DIR / "Methodological_Reliability_Figure_Output"
    / AUDIT_NAME,
    Path("/mnt/data") / AUDIT_NAME,
]

FAMILY_CANDIDATES: Final[list[Path]] = [
    PROJECT_DIR / FAMILY_NAME,
    PROJECT_DIR / "07_Systematic_Review_Dataset" / FAMILY_NAME,
    PROJECT_DIR / "07_Reference_Outputs_Web" / FAMILY_NAME,
    PROJECT_DIR / "Figure17_Output" / FAMILY_NAME,
    Path("/mnt/data") / FAMILY_NAME,
]


# ------------------------------------------------------------
# 3. FROZEN METHOD-FAMILY TAXONOMY
# ------------------------------------------------------------

FROZEN_FAMILY_COUNTS: Final[dict[str, int]] = {
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

TABLE_FAMILY_COUNTS: Final[dict[str, int]] = {
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


FAMILY_ALIASES: Final[dict[str, str]] = {
    "deep learning": "Deep-learning models",
    "deep learning models": "Deep-learning models",

    "hybrid deep learning": "Hybrid deep-learning models",
    "hybrid deep learning models": "Hybrid deep-learning models",

    "sentiment nlp": "Sentiment/NLP-driven models",
    "sentiment nlp driven models": "Sentiment/NLP-driven models",

    "transformer attention":
        "Transformer/attention-based models",
    "transformer attention based models":
        "Transformer/attention-based models",

    "metaheuristic optimized":
        "Metaheuristic-optimized models",
    "metaheuristic optimized models":
        "Metaheuristic-optimized models",

    "ensemble tree based machine learning":
        "Ensemble/tree-based machine learning",

    "graph based": "Graph-based models",
    "graph based models": "Graph-based models",

    "multimodal fusion": "Multimodal-fusion models",
    "multimodal fusion models": "Multimodal-fusion models",

    "other": "Other/unclear",
    "other unclear": "Other/unclear",

    "ann neuro fuzzy": "ANN/neuro-fuzzy models",
    "ann neuro fuzzy models": "ANN/neuro-fuzzy models",
}


# ------------------------------------------------------------
# 4. RELIABILITY INDICATORS
# ------------------------------------------------------------

TEMPORALLY_ORDERED_DESIGNS: Final[set[str]] = {
    "Chronological_Holdout",
    "Walk_Forward",
    "Rolling_Window",
    "Expanding_Window",
    "Blocked_CV",
}

INDICATORS: Final[list[tuple[str, str]]] = [
    (
        "Temporally ordered",
        "Flag_Temporally_Ordered",
    ),
    (
        "Training-only preprocessing",
        "Flag_Training_Only_Preprocessing",
    ),
    (
        "Explicit high leakage risk",
        "Flag_Explicit_High_Leakage_Risk",
    ),
    (
        "Economic evaluation",
        "Flag_Economic_Evaluation",
    ),
    (
        "Formal statistical testing",
        "Flag_Formal_Statistical_Testing",
    ),
    (
        "Code available",
        "Flag_Code_Available",
    ),
]

EXPECTED_RECONCILED_TOTALS: Final[dict[str, int]] = {
    "Temporally ordered": 78,
    "Training-only preprocessing": 21,
    "Explicit high leakage risk": 31,
    "Economic evaluation": 38,
    "Formal statistical testing": 48,
    "Code available": 7,
}


# ------------------------------------------------------------
# 5. OLD TABLE 18 — USED ONLY FOR CHANGE REPORTING
# ------------------------------------------------------------

OLD_TABLE: Final[dict[str, dict[str, int]]] = {
    "Deep-learning models": {
        "Studies": 117,
        "Temporally ordered": 11,
        "Training-only preprocessing": 3,
        "Explicit high leakage risk": 5,
        "Economic evaluation": 5,
        "Formal statistical testing": 7,
        "Code available": 1,
    },
    "Hybrid deep-learning models": {
        "Studies": 110,
        "Temporally ordered": 12,
        "Training-only preprocessing": 3,
        "Explicit high leakage risk": 9,
        "Economic evaluation": 10,
        "Formal statistical testing": 13,
        "Code available": 2,
    },
    "Sentiment/NLP-driven models": {
        "Studies": 81,
        "Temporally ordered": 15,
        "Training-only preprocessing": 6,
        "Explicit high leakage risk": 5,
        "Economic evaluation": 7,
        "Formal statistical testing": 7,
        "Code available": 0,
    },
    "Transformer/attention-based models": {
        "Studies": 68,
        "Temporally ordered": 18,
        "Training-only preprocessing": 5,
        "Explicit high leakage risk": 6,
        "Economic evaluation": 8,
        "Formal statistical testing": 7,
        "Code available": 3,
    },
    "Metaheuristic-optimized models": {
        "Studies": 51,
        "Temporally ordered": 8,
        "Training-only preprocessing": 2,
        "Explicit high leakage risk": 2,
        "Economic evaluation": 2,
        "Formal statistical testing": 5,
        "Code available": 0,
    },
    "Ensemble/tree-based machine learning": {
        "Studies": 34,
        "Temporally ordered": 8,
        "Training-only preprocessing": 0,
        "Explicit high leakage risk": 4,
        "Economic evaluation": 2,
        "Formal statistical testing": 5,
        "Code available": 1,
    },
    "Graph-based models": {
        "Studies": 16,
        "Temporally ordered": 4,
        "Training-only preprocessing": 2,
        "Explicit high leakage risk": 1,
        "Economic evaluation": 2,
        "Formal statistical testing": 3,
        "Code available": 0,
    },
    "Multimodal-fusion models": {
        "Studies": 13,
        "Temporally ordered": 0,
        "Training-only preprocessing": 0,
        "Explicit high leakage risk": 1,
        "Economic evaluation": 2,
        "Formal statistical testing": 1,
        "Code available": 0,
    },
    "ANN/neuro-fuzzy/other": {
        "Studies": 3,
        "Temporally ordered": 1,
        "Training-only preprocessing": 0,
        "Explicit high leakage risk": 0,
        "Economic evaluation": 0,
        "Formal statistical testing": 0,
        "Code available": 0,
    },
}


# ------------------------------------------------------------
# 6. HELPERS
# ------------------------------------------------------------

def clean(value: object) -> str:
    """Remove leading, trailing, and repeated whitespace."""

    return " ".join(
        str(value or "").strip().split()
    )


def normalized_key(value: object) -> str:
    """Create a punctuation-independent lookup key."""

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        clean(value).casefold(),
    ).strip()


def find_file(
    candidates: list[Path],
    filename: str,
    required_columns: set[str],
) -> Path:
    """Locate one CSV with the required schema."""

    for path in candidates:
        if path.is_file():
            return path

    matches: list[Path] = []

    for path in PROJECT_DIR.rglob("*.csv"):
        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                header = next(
                    csv.reader(file),
                    [],
                )
        except Exception:
            continue

        if required_columns.issubset(set(header)):
            matches.append(path)

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise FileNotFoundError(
            f"Could not find {filename}.\n\n"
            "Required columns:\n"
            + ", ".join(sorted(required_columns))
            + "\n\nChecked:\n"
            + "\n".join(str(path) for path in candidates)
        )

    raise RuntimeError(
        "More than one matching CSV was found:\n"
        + "\n".join(str(path) for path in matches)
        + "\n\nSet the intended path explicitly in the script."
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read and clean a CSV file."""

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    return [
        {
            clean(key): clean(value)
            for key, value in row.items()
        }
        for row in rows
    ]


def normalize_family(value: str) -> str:
    """Normalize a frozen principal method-family value."""

    cleaned = clean(value)

    if cleaned in FROZEN_FAMILY_COUNTS:
        return cleaned

    lookup = normalized_key(cleaned)

    if lookup in FAMILY_ALIASES:
        return FAMILY_ALIASES[lookup]

    raise ValueError(
        "Unrecognized Principal_Method_Family value: "
        f"{value!r}"
    )


def table_family(value: str) -> str:
    """Combine the two smallest manuscript categories."""

    if value in {
        "ANN/neuro-fuzzy models",
        "Other/unclear",
    }:
        return "ANN/neuro-fuzzy/other"

    return value


def yes(value: object) -> bool:
    """Identify explicit affirmative audit coding."""

    return normalized_key(value) in {
        "yes",
        "true",
        "1",
    }


def percentage(
    count: int,
    denominator: int,
) -> float:
    """Calculate a percentage."""

    return (
        100.0
        * count
        / denominator
        if denominator
        else 0.0
    )


def formatted_cell(
    count: int,
    denominator: int,
) -> str:
    """Return manuscript-style n (row percentage)."""

    if count == 0:
        return "0"

    return (
        f"{count} "
        f"({percentage(count, denominator):.1f}%)"
    )


def latex_cell(
    count: int,
    denominator: int,
) -> str:
    """Return manuscript-style LaTeX n (row percentage)."""

    if count == 0:
        return "0"

    return (
        f"{count} "
        f"({percentage(count, denominator):.1f}\\%)"
    )


def assert_counter(
    name: str,
    observed: Counter[str],
    expected: dict[str, int],
) -> None:
    """Verify a frozen categorical distribution."""

    if Counter(observed) == Counter(expected):
        return

    categories = list(expected)

    extra = [
        category
        for category in observed
        if category not in expected
    ]

    rows = []

    for category in categories + extra:
        rows.append(
            (
                category,
                expected.get(category, 0),
                observed.get(category, 0),
            )
        )

    lines = [
        f"{category}: expected={expected_count}, "
        f"observed={observed_count}"
        for category, expected_count, observed_count in rows
        if expected_count != observed_count
    ]

    raise AssertionError(
        f"{name} does not match the frozen manuscript:\n"
        + "\n".join(lines)
    )


# ------------------------------------------------------------
# 7. LOAD INPUTS
# ------------------------------------------------------------

audit_path = find_file(
    AUDIT_CANDIDATES,
    AUDIT_NAME,
    {
        "Paper_ID",
        "Validation_Design",
        "Preprocessing_Boundary",
        "Leakage_Risk",
        "Economic_Evaluation_Claimed",
        "Statistical_Testing",
        "Code_Available",
    },
)

family_path = find_file(
    FAMILY_CANDIDATES,
    FAMILY_NAME,
    {
        "Paper_ID",
        "Principal_Method_Family",
    },
)

print("\nReconciled audit:")
print(audit_path)

print("\nFrozen method-family register:")
print(family_path)

audit_rows = read_csv_rows(
    audit_path
)

family_rows = read_csv_rows(
    family_path
)

if len(audit_rows) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} audit rows; "
        f"found {len(audit_rows)}."
    )

if len(family_rows) != EXPECTED_STUDIES:
    raise AssertionError(
        f"Expected {EXPECTED_STUDIES} method-family rows; "
        f"found {len(family_rows)}."
    )


# ------------------------------------------------------------
# 8. VERIFY PAPER_ID INTEGRITY
# ------------------------------------------------------------

audit_ids = [
    row["Paper_ID"]
    for row in audit_rows
]

family_ids = [
    row["Paper_ID"]
    for row in family_rows
]

if any(not paper_id for paper_id in audit_ids):
    raise AssertionError(
        "Blank Paper_ID found in reconciled audit."
    )

if any(not paper_id for paper_id in family_ids):
    raise AssertionError(
        "Blank Paper_ID found in method-family register."
    )

if len(set(audit_ids)) != EXPECTED_STUDIES:
    raise AssertionError(
        "Paper_ID is not unique in reconciled audit."
    )

if len(set(family_ids)) != EXPECTED_STUDIES:
    raise AssertionError(
        "Paper_ID is not unique in method-family register."
    )

missing_from_family = sorted(
    set(audit_ids) - set(family_ids)
)

missing_from_audit = sorted(
    set(family_ids) - set(audit_ids)
)

if missing_from_family or missing_from_audit:
    raise AssertionError(
        "Paper_ID sets do not match.\n\n"
        f"Missing from family register: "
        f"{missing_from_family[:30]}\n"
        f"Missing from reconciled audit: "
        f"{missing_from_audit[:30]}"
    )


# ------------------------------------------------------------
# 9. NORMALIZE METHOD FAMILIES
# ------------------------------------------------------------

family_by_id: dict[str, str] = {}

for row in family_rows:
    family_by_id[row["Paper_ID"]] = normalize_family(
        row["Principal_Method_Family"]
    )

family_counts = Counter(
    family_by_id.values()
)

assert_counter(
    "Principal method-family distribution",
    family_counts,
    FROZEN_FAMILY_COUNTS,
)

table_family_counts = Counter(
    table_family(value)
    for value in family_by_id.values()
)

assert_counter(
    "Table 18 method-family distribution",
    table_family_counts,
    TABLE_FAMILY_COUNTS,
)


# ------------------------------------------------------------
# 10. BUILD RECONCILED STUDY-LEVEL FLAGS
# ------------------------------------------------------------

study_rows: list[dict[str, object]] = []

for row in audit_rows:

    paper_id = row["Paper_ID"]

    principal_family = family_by_id[
        paper_id
    ]

    combined_family = table_family(
        principal_family
    )

    validation_design = row[
        "Validation_Design"
    ]

    flags = {
        "Flag_Temporally_Ordered":
            validation_design
            in TEMPORALLY_ORDERED_DESIGNS,

        "Flag_Training_Only_Preprocessing":
            row["Preprocessing_Boundary"]
            == "Training_Only",

        "Flag_Explicit_High_Leakage_Risk":
            row["Leakage_Risk"]
            == "High",

        "Flag_Economic_Evaluation":
            yes(
                row["Economic_Evaluation_Claimed"]
            ),

        "Flag_Formal_Statistical_Testing":
            yes(
                row["Statistical_Testing"]
            ),

        "Flag_Code_Available":
            yes(
                row["Code_Available"]
            ),
    }

    study_rows.append(
        {
            **row,
            "Principal_Method_Family":
                principal_family,
            "Table18_Method_Family":
                combined_family,
            **flags,
        }
    )


# ------------------------------------------------------------
# 11. VERIFY RECONCILED TOTALS
# ------------------------------------------------------------

observed_totals: dict[str, int] = {}

for label, flag_column in INDICATORS:
    observed_totals[label] = sum(
        bool(row[flag_column])
        for row in study_rows
    )

print("\nReconciled totals:")

for label, _ in INDICATORS:
    count = observed_totals[label]

    print(
        f"  {label:34s}: "
        f"{count:3d} "
        f"({percentage(count, EXPECTED_STUDIES):.1f}%)"
    )

if observed_totals != EXPECTED_RECONCILED_TOTALS:
    raise AssertionError(
        "Reconciled reliability totals differ from the "
        "updated Figure 13 values.\n\n"
        f"Observed: {observed_totals}\n"
        f"Expected: {EXPECTED_RECONCILED_TOTALS}"
    )


# ------------------------------------------------------------
# 12. GENERATE METHOD-FAMILY TABLE
# ------------------------------------------------------------

raw_rows: list[dict[str, object]] = []
formatted_rows: list[dict[str, object]] = []

for family in TABLE_FAMILY_ORDER:

    subset = [
        row
        for row in study_rows
        if row["Table18_Method_Family"] == family
    ]

    studies = len(subset)

    raw_row: dict[str, object] = {
        "Method family": family,
        "Studies": studies,
    }

    formatted_row: dict[str, object] = {
        "Method family": family,
        "Studies": studies,
    }

    for label, flag_column in INDICATORS:

        count = sum(
            bool(row[flag_column])
            for row in subset
        )

        raw_row[f"{label} n"] = count
        raw_row[f"{label} %"] = round(
            percentage(count, studies),
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


total_raw: dict[str, object] = {
    "Method family": "Total",
    "Studies": EXPECTED_STUDIES,
}

total_formatted: dict[str, object] = {
    "Method family": "Total",
    "Studies": EXPECTED_STUDIES,
}

for label, _ in INDICATORS:
    count = observed_totals[label]

    total_raw[f"{label} n"] = count
    total_raw[f"{label} %"] = round(
        percentage(
            count,
            EXPECTED_STUDIES,
        ),
        1,
    )

    total_formatted[label] = (
        formatted_cell(
            count,
            EXPECTED_STUDIES,
        )
    )

raw_rows.append(total_raw)
formatted_rows.append(total_formatted)


# ------------------------------------------------------------
# 13. BUILD CHANGE LOG
# ------------------------------------------------------------

change_rows: list[dict[str, object]] = []

for new_row in raw_rows[:-1]:

    family = str(
        new_row["Method family"]
    )

    old_row = OLD_TABLE[family]

    for label, _ in INDICATORS:

        old_count = int(
            old_row[label]
        )

        new_count = int(
            new_row[f"{label} n"]
        )

        change_rows.append(
            {
                "Method family": family,
                "Indicator": label,
                "Old count": old_count,
                "New count": new_count,
                "Change": new_count - old_count,
            }
        )


# ------------------------------------------------------------
# 14. WRITE CSV OUTPUTS
# ------------------------------------------------------------

RAW_FILE = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled_Raw.csv"
)

FORMATTED_FILE = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled_Formatted.csv"
)

DETAIL_FILE = (
    OUTPUT_DIR
    / "Table18_Study_Level_Flags_Reconciled.csv"
)

CHANGE_FILE = (
    OUTPUT_DIR
    / "Table18_Old_vs_Reconciled_Changes.csv"
)

LATEX_FILE = (
    OUTPUT_DIR
    / "Table18_Method_Family_Reliability_Reconciled.tex"
)


raw_fieldnames = list(
    raw_rows[0].keys()
)

with RAW_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=raw_fieldnames,
    )
    writer.writeheader()
    writer.writerows(raw_rows)


formatted_fieldnames = list(
    formatted_rows[0].keys()
)

with FORMATTED_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=formatted_fieldnames,
    )
    writer.writeheader()
    writer.writerows(formatted_rows)


detail_columns = [
    "Paper_ID",
    "Title",
    "Principal_Method_Family",
    "Table18_Method_Family",
    "Validation_Design",
    "Preprocessing_Boundary",
    "Leakage_Risk",
    "Economic_Evaluation_Claimed",
    "Statistical_Testing",
    "Code_Available",
    *[
        flag_column
        for _, flag_column in INDICATORS
    ],
]

with DETAIL_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=detail_columns,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(study_rows)


with CHANGE_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "Method family",
            "Indicator",
            "Old count",
            "New count",
            "Change",
        ],
    )
    writer.writeheader()
    writer.writerows(change_rows)


# ------------------------------------------------------------
# 15. WRITE LATEX TABLE
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

for row in raw_rows[:-1]:

    family = str(
        row["Method family"]
    )

    family_latex = family.replace(
        "&",
        r"\&",
    )

    studies = int(
        row["Studies"]
    )

    cells = [
        latex_cell(
            int(row[f"{label} n"]),
            studies,
        )
        for label, _ in INDICATORS
    ]

    latex_lines.append(
        family_latex
        + f" & {studies} "
        + " ".join(
            f"& {cell}"
            for cell in cells
        )
        + r" \\"
    )

latex_lines.append(
    r"\midrule"
)

total_cells = [
    latex_cell(
        observed_totals[label],
        EXPECTED_STUDIES,
    )
    for label, _ in INDICATORS
]

latex_lines.append(
    r"\textbf{Total}"
    + f" & {EXPECTED_STUDIES} "
    + " ".join(
        f"& {cell}"
        for cell in total_cells
    )
    + r" \\"
)

latex_lines.extend(
    [
        r"\bottomrule",
        r"\end{tabularx}",
        "",
        r"\vspace{1.5mm}",
        r"\begin{minipage}{\linewidth}",
        r"\footnotesize",
        r"\textit{Notes.}",
        (
            r"Values are \(n\) (row percentage), except in the "
            r"total row, where percentages use all \(493\) studies "
            r"as the denominator."
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
            r"assessment. It is not the complement of low leakage "
            r"risk because most studies retained an "
            r"\texttt{Unclear} classification."
        ),
        "",
        (
            r"The indicators are not mutually exclusive. A study may "
            r"contribute to more than one reliability column."
        ),
        "",
        (
            r"Zero indicates that no study in the corresponding "
            r"method family had the practice explicitly established "
            r"in the available evidence; it should not be interpreted "
            r"as definitive proof that the practice was absent."
        ),
        "",
        (
            r"The ANN/neuro-fuzzy/other group contains three studies "
            r"and should not be compared directly with larger "
            r"method families."
        ),
        r"\end{minipage}",
        r"\end{table}",
        r"\end{landscape}",
        "",
    ]
)

LATEX_FILE.write_text(
    "\n".join(latex_lines),
    encoding="utf-8",
)


# ------------------------------------------------------------
# 16. FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 108)
print("RECONCILED TABLE 18")
print("=" * 108)

headers = [
    "Method family",
    "Studies",
    *[
        label
        for label, _ in INDICATORS
    ],
]

widths = {
    "Method family": 42,
    "Studies": 7,
    "Temporally ordered": 20,
    "Training-only preprocessing": 28,
    "Explicit high leakage risk": 26,
    "Economic evaluation": 20,
    "Formal statistical testing": 27,
    "Code available": 16,
}

print(
    " | ".join(
        header.ljust(widths[header])
        for header in headers
    )
)

print("-" * 190)

for row in formatted_rows:
    print(
        " | ".join(
            str(row[header]).ljust(
                widths[header]
            )
            for header in headers
        )
    )

print("\nChanged cells from the old Table 18:")

changed = [
    row
    for row in change_rows
    if int(row["Change"]) != 0
]

if not changed:
    print("  None.")
else:
    for row in changed:
        sign = (
            "+"
            if int(row["Change"]) > 0
            else ""
        )

        print(
            f"  {row['Method family']} | "
            f"{row['Indicator']}: "
            f"{row['Old count']} -> {row['New count']} "
            f"({sign}{row['Change']})"
        )

print("\nCorrect reconciled total row:")

print(
    "Total "
    f"& {EXPECTED_STUDIES} "
    + " ".join(
        f"& {latex_cell(observed_totals[label], EXPECTED_STUDIES)}"
        for label, _ in INDICATORS
    )
    + r" \\"
)

print("\nCreated files:")

for path in [
    RAW_FILE,
    FORMATTED_FILE,
    DETAIL_FILE,
    CHANGE_FILE,
    LATEX_FILE,
]:
    print(f"  {path}")
