from __future__ import annotations

from pathlib import Path
import csv
import re
from collections import Counter
from typing import Any

import pandas as pd
import plotly.graph_objects as go


# ============================================================
# 1. PROJECT SETTINGS
# ============================================================

PROJECT_ROOT = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

LEGACY_SANKEY_FILENAME = "Section7_Final_Study_Level_Sankey_Input.csv"
COMPILED_FILENAME = "Compiled Files.xlsx"

# The legacy Sankey CSV supplies the previously finalized principal-family
# assignment.  The compiled workbook supplies the authoritative final
# 492-study inclusion boundary, publication year, and Target_Primary.
INPUT_CANDIDATES = [
    PROJECT_ROOT
    / "07_Systematic_Review_Dataset"
    / LEGACY_SANKEY_FILENAME,

    PROJECT_ROOT
    / "07_Reference_Outputs"
    / LEGACY_SANKEY_FILENAME,

    PROJECT_ROOT
    / "14_Sankey"
    / LEGACY_SANKEY_FILENAME,

    PROJECT_ROOT
    / LEGACY_SANKEY_FILENAME,

    PROJECT_ROOT
    / "07_Reference_Outputs_Web"
    / LEGACY_SANKEY_FILENAME,

    Path(LEGACY_SANKEY_FILENAME),
    Path("/mnt/data") / LEGACY_SANKEY_FILENAME,
]

COMPILED_CANDIDATES = [
    PROJECT_ROOT / COMPILED_FILENAME,
    Path(COMPILED_FILENAME),
    Path("/mnt/data") / COMPILED_FILENAME,
]

CODING_SHEET = "Section5_Coding_Consolidated"
INCLUDED_STATUS = "Included_High_Priority"

EXPECTED_STUDIES = 492
EXPECTED_LEGACY_ROWS = 493
EXPECTED_REMOVED_IDS = {"P04845"}

# Final manual adjudications established during manuscript reconciliation.
FINAL_FAMILY_OVERRIDES = {
    "P00057": "Deep-learning models",
    "P00909": "Hybrid deep-learning models",
    "P03446": "Other/unclear",
}

OUTPUT_DIR = PROJECT_ROOT / "Figure16_Output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SHOW_FIGURE = True


# ============================================================
# 2. FROZEN MANUSCRIPT COUNTS
# ============================================================

FROZEN_PERIOD_COUNTS = {
    "2016-2020": 27,
    "2021-2022": 36,
    "2023-2024": 47,
    "2025-2026": 382,
}

FROZEN_FAMILY_COUNTS = {
    "Hybrid deep-learning models": 110,
    "Transformer/attention-based models": 68,
    "Deep-learning models": 117,
    "Metaheuristic-optimized models": 51,
    "Sentiment/NLP-driven models": 80,
    "Multimodal-fusion models": 13,
    "Graph-based models": 16,
    "Other/unclear": 3,
    "Ensemble/tree-based machine learning": 33,
    "ANN/neuro-fuzzy models": 1,
}

FROZEN_TARGET_COUNTS = {
    "Price level": 381,
    "Multi-target": 32,
    "Direction": 48,
    "Return": 17,
    "Trend or regime": 9,
    "Volatility": 1,
    "Not reported": 4,
}

PERIOD_ORDER = list(FROZEN_PERIOD_COUNTS)
FAMILY_ORDER = list(FROZEN_FAMILY_COUNTS)
TARGET_ORDER = list(FROZEN_TARGET_COUNTS)


# ============================================================
# 3. INPUT COLUMN REQUIREMENTS
# ============================================================

REQUIRED_COLUMNS = {
    "Paper_ID",
    "Year",
    "Principal_Method_Family",
    "Target_Primary",
}

REQUIRED_COMPILED_COLUMNS = {
    "Paper_ID",
    "Year",
    "Target_Primary",
    "Systematic_Inclusion_Status",
}


# ============================================================
# 4. NORMALIZATION ALIASES
# ============================================================

FAMILY_ALIASES = {
    "deep learning": "Deep-learning models",
    "deep learning models": "Deep-learning models",

    "hybrid deep learning": "Hybrid deep-learning models",
    "hybrid deep learning models": "Hybrid deep-learning models",

    "sentiment nlp": "Sentiment/NLP-driven models",
    "sentiment nlp driven models": "Sentiment/NLP-driven models",

    "transformer attention": "Transformer/attention-based models",
    "transformer attention based models":
        "Transformer/attention-based models",

    "metaheuristic optimized": "Metaheuristic-optimized models",
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

TARGET_ALIASES = {
    "price": "Price level",
    "price level": "Price level",

    "return": "Return",

    "direction": "Direction",

    "trend regime": "Trend or regime",
    "trend or regime": "Trend or regime",

    "multi target": "Multi-target",

    "volatility": "Volatility",

    "not reported": "Not reported",
}


# ============================================================
# 5. JOURNAL FIGURE SETTINGS
# ============================================================

FIGURE_WIDTH = 1800
FIGURE_HEIGHT = 1200
PNG_SCALE = 3

FONT_FAMILY = "Arial"

REGULAR_LABEL_FONT_SIZE = 19
COUNT_FONT_PERCENT = 78
COLUMN_HEADING_FONT_SIZE = 24

NODE_THICKNESS = 18
NODE_LINE_WIDTH = 0.75

# Sankey-relative node locations
PERIOD_X = 0.020
FAMILY_X = 0.470
TARGET_X = 0.975

# Leave sufficient external space for labels.
DOMAIN_X0 = 0.055
DOMAIN_X1 = 0.945
DOMAIN_Y0 = 0.040
DOMAIN_Y1 = 0.900

PERIOD_GAP = 0.050
FAMILY_GAP = 0.017
TARGET_GAP = 0.038

NODE_TOP = 0.025
NODE_BOTTOM = 0.975

PERIOD_LINK_ALPHA = 0.34
TARGET_LINK_ALPHA = 0.44

LABEL_BACKGROUND_ALPHA = 0.20

# Heading locations in complete figure coordinates.
# These are intentionally independent of node locations.
HEADING_POSITIONS = {
    "Publication period": 0.135,
    "Principal method family": 0.515,
    "Primary forecasting target": 0.865,
}


# ============================================================
# 6. COLOUR PALETTE
# ============================================================

PERIOD_COLOURS = {
    "2016-2020": "#5B8CC0",
    "2021-2022": "#4CA6A8",
    "2023-2024": "#F28E6B",
    "2025-2026": "#9B6CE3",
}

FAMILY_COLOURS = {
    "Hybrid deep-learning models": "#4CC9E8",
    "Transformer/attention-based models": "#A6D854",
    "Deep-learning models": "#F4A261",
    "Metaheuristic-optimized models": "#D96BC6",
    "Sentiment/NLP-driven models": "#E76F91",
    "Multimodal-fusion models": "#E76F51",
    "Graph-based models": "#6C8CD5",
    "Other/unclear": "#A7A7A7",
    "Ensemble/tree-based machine learning": "#E9B44C",
    "ANN/neuro-fuzzy models": "#8A9A5B",
}

TARGET_COLOURS = {
    "Price level": "#6E6E6E",
    "Multi-target": "#8A8A8A",
    "Direction": "#9C9C9C",
    "Return": "#ADADAD",
    "Trend or regime": "#BDBDBD",
    "Volatility": "#C6C6C6",
    "Not reported": "#D0D0D0",
}


# ============================================================
# 7. DISPLAY LABELS
# ============================================================

DISPLAY_LABELS = {
    "Ensemble/tree-based machine learning":
        "Ensemble/tree-based ML",

    "Transformer/attention-based models":
        "Transformer/attention-based<br>models",

    "Hybrid deep-learning models":
        "Hybrid deep-learning<br>models",

    "Metaheuristic-optimized models":
        "Metaheuristic-optimized<br>models",

    "Sentiment/NLP-driven models":
        "Sentiment/NLP-driven<br>models",

    "Multimodal-fusion models":
        "Multimodal-fusion models",

    "ANN/neuro-fuzzy models":
        "ANN/neuro-fuzzy models",

    "Trend or regime":
        "Trend or regime",

    "Volatility":
        "Volatility",

    "Not reported":
        "Not reported",
}


# ============================================================
# 8. TEXT HELPERS
# ============================================================

def clean(value: object) -> str:
    """Normalize surrounding and repeated whitespace."""

    return " ".join(
        str(value or "").strip().split()
    )


def normalized_key(value: object) -> str:
    """Create a punctuation-independent lookup key."""

    text = clean(value).lower()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(text.split())


def hex_to_rgba(
    hexadecimal: str,
    alpha: float,
) -> str:
    """Convert #RRGGBB to Plotly rgba format."""

    text = hexadecimal.lstrip("#")

    if len(text) != 6:
        raise ValueError(
            f"Invalid hexadecimal colour: {hexadecimal}"
        )

    red = int(text[0:2], 16)
    green = int(text[2:4], 16)
    blue = int(text[4:6], 16)

    return (
        f"rgba({red},{green},{blue},{alpha:.3f})"
    )


def period_from_year(year_text: str) -> str:
    """Map publication year to the frozen review periods."""

    try:
        year = int(float(clean(year_text)))

    except ValueError as error:
        raise ValueError(
            f"Invalid publication year: {year_text!r}"
        ) from error

    if 2016 <= year <= 2020:
        return "2016-2020"

    if 2021 <= year <= 2022:
        return "2021-2022"

    if 2023 <= year <= 2024:
        return "2023-2024"

    if 2025 <= year <= 2026:
        return "2025-2026"

    raise ValueError(
        "Publication year lies outside the frozen "
        f"technical-synthesis periods: {year}"
    )


def normalize_family(value: str) -> str:
    """Normalize the principal method-family coding."""

    cleaned = clean(value)

    if cleaned in FROZEN_FAMILY_COUNTS:
        return cleaned

    lookup = normalized_key(cleaned)

    if lookup in FAMILY_ALIASES:
        return FAMILY_ALIASES[lookup]

    raise ValueError(
        f"Unrecognized method family: {value!r}"
    )


def normalize_target(value: str) -> str:
    """Normalize the primary target coding."""

    cleaned = clean(value)

    if cleaned in FROZEN_TARGET_COUNTS:
        return cleaned

    lookup = normalized_key(cleaned)

    if lookup in TARGET_ALIASES:
        return TARGET_ALIASES[lookup]

    raise ValueError(
        f"Unrecognized forecasting target: {value!r}"
    )


def journal_label(
    item: str,
    count: int,
) -> str:
    """Create a compact label with a smaller count line."""

    display = DISPLAY_LABELS.get(item, item)

    return (
        f"{display}<br>"
        f"<span style='font-size:{COUNT_FONT_PERCENT}%'>"
        f"(n={count:,})"
        f"</span>"
    )

DISPLAY_LABELS.update({
    "2016-2020": "2016–2020",
    "2021-2022": "2021–2022",
    "2023-2024": "2023–2024",
    "2025-2026": "2025–2026",
})


# ============================================================
# 9. INPUT DISCOVERY
# ============================================================

def find_input() -> Path:
    """Locate the legacy 493-row study-level Sankey input CSV."""

    for path in INPUT_CANDIDATES:
        if path.exists():
            return path

    matches: list[Path] = []

    for path in PROJECT_ROOT.rglob("*.csv"):

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.reader(file)
                header = next(reader, [])

        except Exception:
            continue

        if REQUIRED_COLUMNS.issubset(set(header)):
            matches.append(path)

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise FileNotFoundError(
            "No valid legacy Sankey input CSV was found.\n"
            "Required columns:\n"
            "Paper_ID, Year, Principal_Method_Family, "
            "Target_Primary\n\n"
            "Expected filename:\n"
            "Section7_Final_Study_Level_Sankey_Input.csv"
        )

    raise RuntimeError(
        "More than one valid Sankey input CSV was found:\n"
        + "\n".join(str(path) for path in matches)
    )



def find_compiled_workbook() -> Path:
    """Locate the authoritative compiled workbook."""

    for path in COMPILED_CANDIDATES:
        if path.is_file():
            return path

    matches = (
        sorted(PROJECT_ROOT.rglob(COMPILED_FILENAME))
        if PROJECT_ROOT.is_dir()
        else []
    )

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise RuntimeError(
            "More than one compiled workbook was found:\n"
            + "\n".join(str(path) for path in matches)
            + "\n\nSpecify the intended file explicitly in "
              "COMPILED_CANDIDATES."
        )

    raise FileNotFoundError(
        "Compiled Files.xlsx was not found.\n\nChecked:\n"
        + "\n".join(str(path) for path in COMPILED_CANDIDATES)
    )


# ============================================================
# 10. COUNT VALIDATION
# ============================================================

def assert_counts(
    label: str,
    observed: Counter,
    expected: dict[str, int],
) -> None:
    """Verify observed distributions against frozen counts."""

    observed_dict = dict(observed)

    if observed_dict == expected:
        return

    print(f"\n{label} count mismatch")

    print("\nObserved:")
    for item in expected:
        print(
            f"  {item}: "
            f"{observed_dict.get(item, 0)}"
        )

    print("\nExpected:")
    for item, count in expected.items():
        print(f"  {item}: {count}")

    unexpected = {
        item: count
        for item, count in observed_dict.items()
        if item not in expected
    }

    if unexpected:
        print("\nUnexpected categories:")
        for item, count in unexpected.items():
            print(f"  {item}: {count}")

    raise AssertionError(
        f"{label} counts do not match "
        "the frozen manuscript values."
    )


# ============================================================
# 11. NODE POSITIONING
# ============================================================

def calculate_column_centres(
    order: list[str],
    counts: dict[str, int],
    gap: float,
) -> dict[str, float]:
    """
    Calculate non-overlapping node centres proportional to
    node totals.

    Plotly Sankey uses y=0 at the top and y=1 at the bottom.
    """

    node_count = len(order)

    total_span = NODE_BOTTOM - NODE_TOP

    total_gap = (
        gap * max(node_count - 1, 0)
    )

    available_height = total_span - total_gap

    if available_height <= 0:
        raise ValueError(
            "The selected vertical gap is too large "
            "for this node column."
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

        cursor += node_height + gap

    return centres

def repel_label_positions(
    order: list[str],
    raw_positions: dict[str, float],
    minimum_gap: float,
    lower_limit: float = 0.035,
    upper_limit: float = 0.965,
) -> dict[str, float]:
    """
    Separate annotation positions without changing Sankey-node
    positions or ribbon values.

    Plotly Sankey coordinates increase from top to bottom.
    """

    ordered_items = sorted(
        order,
        key=lambda item: raw_positions[item],
    )

    adjusted = {
        item: min(
            max(raw_positions[item], lower_limit),
            upper_limit,
        )
        for item in ordered_items
    }

    # Forward pass
    for index in range(1, len(ordered_items)):

        previous_item = ordered_items[index - 1]
        current_item = ordered_items[index]

        minimum_position = (
            adjusted[previous_item]
            + minimum_gap
        )

        if adjusted[current_item] < minimum_position:
            adjusted[current_item] = minimum_position

    # Shift upward when the final label exceeds the limit.
    final_item = ordered_items[-1]

    if adjusted[final_item] > upper_limit:

        overflow = (
            adjusted[final_item]
            - upper_limit
        )

        for item in ordered_items:
            adjusted[item] -= overflow

    # Backward pass
    for index in range(
        len(ordered_items) - 2,
        -1,
        -1,
    ):

        current_item = ordered_items[index]
        next_item = ordered_items[index + 1]

        maximum_position = (
            adjusted[next_item]
            - minimum_gap
        )

        if adjusted[current_item] > maximum_position:
            adjusted[current_item] = maximum_position

    # Final lower-bound correction
    first_item = ordered_items[0]

    if adjusted[first_item] < lower_limit:

        underflow = (
            lower_limit
            - adjusted[first_item]
        )

        for item in ordered_items:
            adjusted[item] += underflow

    return adjusted


# ============================================================
# 12. CUSTOM ANNOTATIONS
# ============================================================

def add_node_annotation(
    annotations: list[dict[str, Any]],
    node_x: float,
    label_y: float,
    text: str,
    stage: str,
) -> None:
    """
    Add a manually positioned label without altering the
    underlying Sankey node or flow.
    """

    paper_x = (
        DOMAIN_X0
        + node_x
        * (DOMAIN_X1 - DOMAIN_X0)
    )

    paper_y = (
        DOMAIN_Y0
        + (1.0 - label_y)
        * (DOMAIN_Y1 - DOMAIN_Y0)
    )

    if stage == "period":

        label_x = paper_x + 0.012
        x_anchor = "left"
        alignment = "left"

    elif stage == "family":

        label_x = paper_x + 0.013
        x_anchor = "left"
        alignment = "left"

    elif stage == "target":

        label_x = paper_x - 0.012
        x_anchor = "right"
        alignment = "right"

    else:
        raise ValueError(
            f"Unsupported annotation stage: {stage}"
        )

    annotations.append(
        {
            "x": label_x,
            "y": paper_y,

            "xref": "paper",
            "yref": "paper",

            "text": text,
            "showarrow": False,

            "xanchor": x_anchor,
            "yanchor": "middle",
            "align": alignment,

            "font": {
                "family": FONT_FAMILY,
                "size": REGULAR_LABEL_FONT_SIZE,
                "color": "#303030",
            },

            "bgcolor": (
                "rgba(255,255,255,"
                f"{LABEL_BACKGROUND_ALPHA})"
            ),

            "bordercolor":
                "rgba(255,255,255,0)",

            "borderpad": 1.2,
        }
    )


# ============================================================
# 13. MAIN WORKFLOW
# ============================================================

def main() -> None:

    input_path = find_input()
    compiled_path = find_compiled_workbook()

    print("Legacy Sankey input:")
    print(input_path)

    print("\nAuthoritative compiled workbook:")
    print(compiled_path)

    # --------------------------------------------------------
    # Load the legacy 493-row Sankey map.
    # It is retained only as the baseline principal-family map.
    # --------------------------------------------------------

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        legacy_rows = list(
            csv.DictReader(file)
        )

    if len(legacy_rows) != EXPECTED_LEGACY_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_LEGACY_ROWS} legacy Sankey rows; "
            f"found {len(legacy_rows)}."
        )

    legacy_paper_ids = [
        clean(row["Paper_ID"])
        for row in legacy_rows
    ]

    if any(not paper_id for paper_id in legacy_paper_ids):
        raise AssertionError(
            "One or more Paper_ID values are blank in the legacy Sankey file."
        )

    if len(set(legacy_paper_ids)) != EXPECTED_LEGACY_ROWS:

        duplicates = sorted(
            paper_id
            for paper_id, count
            in Counter(legacy_paper_ids).items()
            if count > 1
        )

        raise AssertionError(
            "Legacy Sankey Paper_ID values are not unique:\n"
            + "\n".join(duplicates)
        )

    legacy_by_id = {
        clean(row["Paper_ID"]): row
        for row in legacy_rows
    }

    # --------------------------------------------------------
    # Load the authoritative compiled workbook.
    # Year and Target_Primary are taken from this workbook.
    # Only Included_High_Priority rows survive.
    # --------------------------------------------------------

    coding_all = pd.read_excel(
        compiled_path,
        sheet_name=CODING_SHEET,
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )

    coding_all.columns = [
        str(column).strip()
        for column in coding_all.columns
    ]

    missing_compiled_columns = sorted(
        REQUIRED_COMPILED_COLUMNS
        - set(coding_all.columns)
    )

    if missing_compiled_columns:
        raise KeyError(
            "Compiled workbook is missing required columns:\n"
            f"{missing_compiled_columns}\n\n"
            f"Available columns:\n{list(coding_all.columns)}"
        )

    for column in REQUIRED_COMPILED_COLUMNS:
        coding_all[column] = (
            coding_all[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    coding = coding_all.loc[
        coding_all[
            "Systematic_Inclusion_Status"
        ].eq(INCLUDED_STATUS)
    ].copy()

    if len(coding) != EXPECTED_STUDIES:
        raise AssertionError(
            f"Expected {EXPECTED_STUDIES} final included studies; "
            f"found {len(coding)}."
        )

    if coding["Paper_ID"].nunique() != EXPECTED_STUDIES:
        raise AssertionError(
            "The compiled final register does not contain "
            f"{EXPECTED_STUDIES} unique Paper_ID values."
        )

    if coding["Paper_ID"].eq("").any():
        raise AssertionError(
            "Blank Paper_ID values found in the compiled final register."
        )

    final_ids = set(coding["Paper_ID"])
    legacy_ids = set(legacy_by_id)

    missing_from_legacy = final_ids - legacy_ids
    obsolete_legacy_ids = legacy_ids - final_ids

    if missing_from_legacy:
        raise AssertionError(
            "Final included studies are missing from the legacy Sankey map:\n"
            f"{sorted(missing_from_legacy)}"
        )

    if obsolete_legacy_ids != EXPECTED_REMOVED_IDS:
        raise AssertionError(
            "Unexpected difference between the legacy Sankey map and "
            "the frozen compiled register.\n"
            f"Expected removed IDs: {sorted(EXPECTED_REMOVED_IDS)}\n"
            f"Observed removed IDs: {sorted(obsolete_legacy_ids)}"
        )

    print(
        "\nLegacy record removed by final reconciliation:",
        sorted(obsolete_legacy_ids),
    )

    # --------------------------------------------------------
    # Build the final 492 study-level Sankey rows.
    #
    # Source hierarchy:
    #   Paper_ID inclusion -> Compiled Files.xlsx
    #   Publication year   -> Compiled Files.xlsx
    #   Primary target     -> Compiled Files.xlsx
    #   Method family      -> legacy finalized Sankey family map
    #                         + final adjudication overrides
    # --------------------------------------------------------

    normalized_rows: list[dict[str, str]] = []

    for _, compiled_row in coding.iterrows():

        paper_id = clean(
            compiled_row["Paper_ID"]
        )

        legacy_row = legacy_by_id[
            paper_id
        ]

        baseline_family = normalize_family(
            legacy_row["Principal_Method_Family"]
        )

        final_family = FINAL_FAMILY_OVERRIDES.get(
            paper_id,
            baseline_family,
        )

        # Validate the manually overridden label through the same
        # normalization layer used for all other family labels.
        final_family = normalize_family(
            final_family
        )

        normalized_rows.append(
            {
                "Paper_ID": paper_id,

                "Period": period_from_year(
                    compiled_row["Year"]
                ),

                "Method_Family": final_family,

                "Target": normalize_target(
                    compiled_row["Target_Primary"]
                ),
            }
        )

    paper_ids = [
        row["Paper_ID"]
        for row in normalized_rows
    ]

    if len(normalized_rows) != EXPECTED_STUDIES:
        raise AssertionError(
            f"Final Sankey rows should total {EXPECTED_STUDIES}; "
            f"found {len(normalized_rows)}."
        )

    if len(set(paper_ids)) != EXPECTED_STUDIES:
        raise AssertionError(
            "Final Sankey Paper_ID values are not unique."
        )

    # Explicit checks for the three study-level adjudications.
    final_family_lookup = {
        row["Paper_ID"]: row["Method_Family"]
        for row in normalized_rows
    }

    for paper_id, expected_family in FINAL_FAMILY_OVERRIDES.items():

        observed_family = final_family_lookup.get(
            paper_id
        )

        if observed_family != expected_family:
            raise AssertionError(
                f"{paper_id}: expected final method family "
                f"{expected_family!r}, found {observed_family!r}."
            )

    if "P04845" in final_family_lookup:
        raise AssertionError(
            "P04845 must not remain in the frozen 492-study Sankey."
        )

    period_counts = Counter(
        row["Period"]
        for row in normalized_rows
    )

    family_counts = Counter(
        row["Method_Family"]
        for row in normalized_rows
    )

    target_counts = Counter(
        row["Target"]
        for row in normalized_rows
    )

    assert_counts(
        "Period",
        period_counts,
        FROZEN_PERIOD_COUNTS,
    )

    assert_counts(
        "Method-family",
        family_counts,
        FROZEN_FAMILY_COUNTS,
    )

    assert_counts(
        "Target",
        target_counts,
        FROZEN_TARGET_COUNTS,
    )

    period_family = Counter(
        (
            row["Period"],
            row["Method_Family"],
        )
        for row in normalized_rows
    )

    family_target = Counter(
        (
            row["Method_Family"],
            row["Target"],
        )
        for row in normalized_rows
    )

    if sum(period_family.values()) != EXPECTED_STUDIES:
        raise AssertionError(
            f"Period-to-method flows do not total {EXPECTED_STUDIES}."
        )

    if sum(family_target.values()) != EXPECTED_STUDIES:
        raise AssertionError(
            f"Method-to-target flows do not total {EXPECTED_STUDIES}."
        )


    # ========================================================
    # 14. NODE DEFINITIONS
    # ========================================================

    node_items = (
        PERIOD_ORDER
        + FAMILY_ORDER
        + TARGET_ORDER
    )

    node_stage = (
        ["period"] * len(PERIOD_ORDER)
        + ["family"] * len(FAMILY_ORDER)
        + ["target"] * len(TARGET_ORDER)
    )

    node_counts = (
        [
            FROZEN_PERIOD_COUNTS[item]
            for item in PERIOD_ORDER
        ]
        + [
            FROZEN_FAMILY_COUNTS[item]
            for item in FAMILY_ORDER
        ]
        + [
            FROZEN_TARGET_COUNTS[item]
            for item in TARGET_ORDER
        ]
    )

    node_colours = (
        [
            PERIOD_COLOURS[item]
            for item in PERIOD_ORDER
        ]
        + [
            FAMILY_COLOURS[item]
            for item in FAMILY_ORDER
        ]
        + [
            TARGET_COLOURS[item]
            for item in TARGET_ORDER
        ]
    )

    period_y = calculate_column_centres(
        PERIOD_ORDER,
        FROZEN_PERIOD_COUNTS,
        PERIOD_GAP,
    )

    family_y = calculate_column_centres(
        FAMILY_ORDER,
        FROZEN_FAMILY_COUNTS,
        FAMILY_GAP,
    )

    target_y = calculate_column_centres(
        TARGET_ORDER,
        FROZEN_TARGET_COUNTS,
        TARGET_GAP,
    )

    node_x = (
        [PERIOD_X] * len(PERIOD_ORDER)
        + [FAMILY_X] * len(FAMILY_ORDER)
        + [TARGET_X] * len(TARGET_ORDER)
    )

    node_y = (
        [
            period_y[item]
            for item in PERIOD_ORDER
        ]
        + [
            family_y[item]
            for item in FAMILY_ORDER
        ]
        + [
            target_y[item]
            for item in TARGET_ORDER
        ]
    )

    node_index = {
        item: index
        for index, item
        in enumerate(node_items)
    }

    node_customdata = [
        [
            item,
            stage,
            count,
        ]
        for item, stage, count
        in zip(
            node_items,
            node_stage,
            node_counts,
        )
    ]

    # Node positions determine ribbon geometry.
    # Label positions are independently separated to prevent overlap.

    period_label_y = repel_label_positions(
    order=PERIOD_ORDER,
    raw_positions=period_y,
    minimum_gap=0.100,
    )

    family_label_y = repel_label_positions(
    order=FAMILY_ORDER,
    raw_positions=family_y,
    minimum_gap=0.064,
    )

    target_label_y = repel_label_positions(
    order=TARGET_ORDER,
    raw_positions=target_y,
    minimum_gap=0.085,
    )


    # ========================================================
    # 15. LINK DEFINITIONS
    # ========================================================

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    link_colours: list[str] = []
    link_customdata: list[list[Any]] = []

    flow_rows: list[dict[str, Any]] = []

    for period in PERIOD_ORDER:

        for family in FAMILY_ORDER:

            count = period_family.get(
                (period, family),
                0,
            )

            if count <= 0:
                continue

            sources.append(
                node_index[period]
            )

            targets.append(
                node_index[family]
            )

            values.append(count)

            link_colours.append(
                hex_to_rgba(
                    FAMILY_COLOURS[family],
                    PERIOD_LINK_ALPHA,
                )
            )

            link_customdata.append(
                [
                    period,
                    family,
                    count,
                    "Publication period → method family",
                ]
            )

            flow_rows.append(
                {
                    "Stage": "Period_to_Method",
                    "Source": period,
                    "Target": family,
                    "Studies": count,
                }
            )

    for family in FAMILY_ORDER:

        for target in TARGET_ORDER:

            count = family_target.get(
                (family, target),
                0,
            )

            if count <= 0:
                continue

            sources.append(
                node_index[family]
            )

            targets.append(
                node_index[target]
            )

            values.append(count)

            link_colours.append(
                hex_to_rgba(
                    FAMILY_COLOURS[family],
                    TARGET_LINK_ALPHA,
                )
            )

            link_customdata.append(
                [
                    family,
                    target,
                    count,
                    "Method family → forecasting target",
                ]
            )

            flow_rows.append(
                {
                    "Stage": "Method_to_Target",
                    "Source": family,
                    "Target": target,
                    "Studies": count,
                }
            )


    # ========================================================
    # 16. BUILD THE SANKEY
    # ========================================================

    figure = go.Figure(
        go.Sankey(
            arrangement="fixed",
            orientation="h",

            domain={
                "x": [DOMAIN_X0, DOMAIN_X1],
                "y": [DOMAIN_Y0, DOMAIN_Y1],
            },

            node={
                "pad": 18,
                "thickness": NODE_THICKNESS,

                "line": {
                    "color":
                        "rgba(45,45,45,0.72)",

                    "width":
                        NODE_LINE_WIDTH,
                },

                # Labels are added as custom annotations.
                "label": [""] * len(node_items),

                "color": node_colours,
                "x": node_x,
                "y": node_y,

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
                "source": sources,
                "target": targets,
                "value": values,
                "color": link_colours,

                "customdata":
                    link_customdata,

                "hovertemplate": (
                    "<b>%{customdata[0]}</b>"
                    " → "
                    "<b>%{customdata[1]}</b><br>"
                    "%{customdata[3]}<br>"
                    "Studies: %{customdata[2]:,}"
                    "<extra></extra>"
                ),
            },
        )
    )


    # ========================================================
    # 17. COLUMN HEADINGS
    # ========================================================

    annotations: list[dict[str, Any]] = []

    heading_specs = [
        (
            PERIOD_X,
            "Publication period",
        ),
        (
            FAMILY_X,
            "Principal method family",
        ),
        (
            TARGET_X,
            "Primary forecasting target",
        ),
    ]

    for sankey_x, heading in heading_specs:

        paper_x = (
            DOMAIN_X0
            + sankey_x
            * (DOMAIN_X1 - DOMAIN_X0)
        )

        annotations.append(
            {
                "x": paper_x,
                "y": 0.975,

                "xref": "paper",
                "yref": "paper",

                "text": f"<b>{heading}</b>",

                "showarrow": False,

                "xanchor": "center",
                "yanchor": "middle",

                "font": {
                    "family": FONT_FAMILY,
                    "size":
                        COLUMN_HEADING_FONT_SIZE,
                    "color": "#252525",
                },
            }
        )


    # ========================================================
    # 18. CUSTOM NODE LABELS
    # ========================================================

    for item in PERIOD_ORDER:

        add_node_annotation(
            annotations=annotations,
            node_x=PERIOD_X,
            label_y=period_label_y[item],
            text=journal_label(
                item,
                FROZEN_PERIOD_COUNTS[item],
            ),
            stage="period",
        )

    for item in FAMILY_ORDER:

        add_node_annotation(
            annotations=annotations,
            node_x=FAMILY_X,
            label_y=family_label_y[item],
            text=journal_label(
                item,
                FROZEN_FAMILY_COUNTS[item],
            ),
            stage="family",
        )

    for item in TARGET_ORDER:

        add_node_annotation(
            annotations=annotations,
            node_x=TARGET_X,
            label_y=target_label_y[item],
            text=journal_label(
                item,
                FROZEN_TARGET_COUNTS[item],
            ),
            stage="target",
        )


    # ========================================================
    # 19. FINAL LAYOUT
    # ========================================================

    figure.update_layout(
        width=FIGURE_WIDTH,
        height=FIGURE_HEIGHT,

        paper_bgcolor="white",
        plot_bgcolor="white",

        font={
            "family": FONT_FAMILY,
            "size":
                REGULAR_LABEL_FONT_SIZE,
            "color": "#303030",
        },

        margin={
            "l": 30,
            "r": 42,
            "t": 55,
            "b": 28,
        },

        annotations=annotations,
    )


    # ========================================================
    # 20. OUTPUT PATHS
    # ========================================================

    base_name = (
        "Figure16_Period_Method_Target_"
        "Sankey_SCIE_Q1"
    )

    pdf_path = (
        OUTPUT_DIR
        / f"{base_name}.pdf"
    )

    svg_path = (
        OUTPUT_DIR
        / f"{base_name}.svg"
    )

    png_path = (
        OUTPUT_DIR
        / f"{base_name}.png"
    )

    html_path = (
        OUTPUT_DIR
        / f"{base_name}.html"
    )

    flow_path = (
        OUTPUT_DIR
        / f"{base_name}_Flows.csv"
    )

    audit_path = (
        OUTPUT_DIR
        / f"{base_name}_Audit.csv"
    )


    # ========================================================
    # 21. EXPORT INTERACTIVE HTML
    # ========================================================

    figure.write_html(
        html_path,

        include_plotlyjs=True,
        full_html=True,

        config={
            "displaylogo": False,
            "responsive": True,

            "toImageButtonOptions": {
                "format": "png",
                "filename": base_name,
                "width": FIGURE_WIDTH,
                "height": FIGURE_HEIGHT,
                "scale": PNG_SCALE,
            },
        },
    )


    # ========================================================
    # 22. EXPORT VECTOR AND RASTER FILES
    # ========================================================

    static_export_ok = True

    try:

        figure.write_image(
            pdf_path,
            format="pdf",
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
            scale=1,
        )

        figure.write_image(
            svg_path,
            format="svg",
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
            scale=1,
        )

        figure.write_image(
            png_path,
            format="png",
            width=FIGURE_WIDTH,
            height=FIGURE_HEIGHT,
            scale=PNG_SCALE,
        )

    except Exception as error:

        static_export_ok = False

        print(
            "\nHTML and audit files were generated, "
            "but static export failed."
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


    # ========================================================
    # 23. FLOW AUDIT CSV
    # ========================================================

    with flow_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "Stage",
                "Source",
                "Target",
                "Studies",
            ],
        )

        writer.writeheader()
        writer.writerows(flow_rows)


    # ========================================================
    # 24. VALIDATION AUDIT CSV
    # ========================================================

    with audit_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "Audit_Item",
                "Observed",
                "Required",
                "Status",
            ]
        )

        writer.writerow(
            [
                "Study rows",
                len(normalized_rows),
                EXPECTED_STUDIES,
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Unique Paper_ID",
                len(set(paper_ids)),
                EXPECTED_STUDIES,
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Period-to-method total",
                sum(period_family.values()),
                EXPECTED_STUDIES,
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Method-to-target total",
                sum(family_target.values()),
                EXPECTED_STUDIES,
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Period counts",
                str(dict(period_counts)),
                str(FROZEN_PERIOD_COUNTS),
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Method-family counts",
                str(dict(family_counts)),
                str(FROZEN_FAMILY_COUNTS),
                "PASS",
            ]
        )

        writer.writerow(
            [
                "Target counts",
                str(dict(target_counts)),
                str(FROZEN_TARGET_COUNTS),
                "PASS",
            ]
        )


    # ========================================================
    # 25. DISPLAY AND SUMMARY
    # ========================================================

    if SHOW_FIGURE:
        figure.show()

    print("\nFigure 16 Sankey audit passed.")

    print("\nInput:")
    print(input_path)

    print("\nOutput directory:")
    print(OUTPUT_DIR)

    print("\nFlow audit:")
    print(flow_path)

    print("\nValidation audit:")
    print(audit_path)

    print("\nInteractive HTML:")
    print(html_path)

    if static_export_ok:

        print("\nVector PDF:")
        print(pdf_path)

        print("\nVector SVG:")
        print(svg_path)

        print("\nHigh-resolution PNG:")
        print(png_path)


if __name__ == "__main__":
    main()