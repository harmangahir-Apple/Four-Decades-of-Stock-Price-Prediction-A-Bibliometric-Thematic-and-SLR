from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import csv
import re

import plotly.graph_objects as go


# ============================================================
# 1. PROJECT AND FILE SETTINGS
# ============================================================

PROJECT_ROOT = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

INPUT_CANDIDATES = [
    PROJECT_ROOT
    / "07_Systematic_Review_Dataset"
    / "Section7_Final_Study_Level_Sankey_Input.csv",

    PROJECT_ROOT
    / "Section7_Final_Study_Level_Sankey_Input.csv",

    PROJECT_ROOT
    / "07_Reference_Outputs_Web"
    / "Section7_Final_Study_Level_Sankey_Input.csv",
]

OUTPUT_DIR = PROJECT_ROOT / "Figure17_Output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SHOW_FIGURE = True


# ============================================================
# 2. FROZEN MANUSCRIPT COUNTS
# ============================================================

FROZEN_PERIOD_COUNTS = {
    "2016-2020": 27,
    "2021-2022": 36,
    "2023-2024": 49,
    "2025-2026": 381,
}

FROZEN_FAMILY_COUNTS = {
    "Hybrid deep-learning models": 110,
    "Transformer/attention-based models": 68,
    "Deep-learning models": 117,
    "Metaheuristic-optimized models": 51,
    "Sentiment/NLP-driven models": 81,
    "Multimodal-fusion models": 13,
    "Graph-based models": 16,
    "Other/unclear": 2,
    "Ensemble/tree-based machine learning": 34,
    "ANN/neuro-fuzzy models": 1,
}

FROZEN_TARGET_COUNTS = {
    "Price level": 381,
    "Multi-target": 33,
    "Direction": 48,
    "Return": 17,
    "Trend or regime": 10,
    "Not reported": 4,
}

PERIOD_ORDER = list(FROZEN_PERIOD_COUNTS)
FAMILY_ORDER = list(FROZEN_FAMILY_COUNTS)
TARGET_ORDER = list(FROZEN_TARGET_COUNTS)

REQUIRED_COLUMNS = {
    "Paper_ID",
    "Year",
    "Principal_Method_Family",
    "Target_Primary",
}


# ============================================================
# 3. NORMALIZATION ALIASES
# ============================================================

FAMILY_ALIASES = {
    "deep learning": "Deep-learning models",
    "deep learning models": "Deep-learning models",

    "hybrid deep learning": "Hybrid deep-learning models",
    "hybrid deep learning models":
        "Hybrid deep-learning models",

    "sentiment nlp": "Sentiment/NLP-driven models",
    "sentiment nlp driven models":
        "Sentiment/NLP-driven models",

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
    "multimodal fusion models":
        "Multimodal-fusion models",

    "other": "Other/unclear",
    "other unclear": "Other/unclear",

    "ann neuro fuzzy": "ANN/neuro-fuzzy models",
    "ann neuro fuzzy models":
        "ANN/neuro-fuzzy models",
}

TARGET_ALIASES = {
    "price": "Price level",
    "price level": "Price level",

    "return": "Return",
    "direction": "Direction",

    "trend regime": "Trend or regime",
    "trend or regime": "Trend or regime",

    "multi target": "Multi-target",

    "not reported": "Not reported",
}


# ============================================================
# 4. SCIE Q1 FIGURE SETTINGS
# ============================================================

FIGURE_WIDTH = 1800
FIGURE_HEIGHT = 1100
PNG_SCALE = 3

FONT_FAMILY = "Arial"

REGULAR_LABEL_FONT_SIZE = 20
SMALL_FAMILY_FONT_SIZE = 17
SMALL_TARGET_FONT_SIZE = 18

COUNT_FONT_PERCENT = 68
COLUMN_HEADING_FONT_SIZE = 27

NODE_THICKNESS = 18
NODE_LINE_WIDTH = 0.75

# Relative locations within the Sankey domain.
PERIOD_X = 0.025
FAMILY_X = 0.505
TARGET_X = 0.975

# Domain within the complete figure.
DOMAIN_X0 = 0.060
DOMAIN_X1 = 0.940
DOMAIN_Y0 = 0.035
DOMAIN_Y1 = 0.915

NODE_TOP = 0.025
NODE_BOTTOM = 0.975

PERIOD_GAP = 0.050
FAMILY_GAP = 0.017
TARGET_GAP = 0.038

PERIOD_LINK_ALPHA = 0.27
TARGET_LINK_ALPHA = 0.39

LABEL_BACKGROUND_ALPHA = 0.58
LABEL_BORDER_PAD = 0.60

CONNECTOR_ALPHA = 0.24
CONNECTOR_WIDTH = 0.55

HEADING_SPECS = [
    {
        "text": "Publication<br>period",
        "x": 0.145,
    },
    {
        "text": "Principal method<br>family",
        "x": 0.510,
    },
    {
        "text": "Primary forecasting<br>target",
        "x": 0.855,
    },
]


# ============================================================
# 5. FIXED LABEL POSITIONS
# ============================================================
# These values control annotation positions only.
# Sankey nodes and ribbon geometry remain unchanged.

PERIOD_LABEL_Y = {
    "2016-2020": 0.055,
    "2021-2022": 0.175,
    "2023-2024": 0.305,
    "2025-2026": 0.680,
}

FAMILY_LABEL_Y = {
    "Hybrid deep-learning models": 0.050,
    "Transformer/attention-based models": 0.185,
    "Deep-learning models": 0.325,
    "Metaheuristic-optimized models": 0.475,
    "Sentiment/NLP-driven models": 0.595,
    "Multimodal-fusion models": 0.715,
    "Graph-based models": 0.780,
    "Other/unclear": 0.840,
    "Ensemble/tree-based machine learning": 0.905,
    "ANN/neuro-fuzzy models": 0.965,
}

TARGET_LABEL_Y = {
    "Price level": 0.310,
    "Multi-target": 0.630,
    "Direction": 0.725,
    "Return": 0.815,
    "Trend or regime": 0.895,
    "Not reported": 0.965,
}


# ============================================================
# 6. COLOUR PALETTE
# ============================================================

PERIOD_COLOURS = {
    "2016-2020": "#5B8CC0",
    "2021-2022": "#4CA6A8",
    "2023-2024": "#F28E6B",
    "2025-2026": "#9164D8",
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
    "Price level": "#F4A261",
    "Multi-target": "#D96BC6",
    "Direction": "#E76F91",
    "Return": "#4CC9E8",
    "Trend or regime": "#8BC34A",
    "Not reported": "#E9B44C",
}


# ============================================================
# 7. COMPACT DISPLAY LABELS
# ============================================================

DISPLAY_LABELS = {
    "Hybrid deep-learning models":
        "Hybrid deep-learning<br>models",

    "Transformer/attention-based models":
        "Transformer/attention<br>models",

    "Deep-learning models":
        "Deep-learning",

    "Metaheuristic-optimized models":
        "Metaheuristic-optimized",

    "Sentiment/NLP-driven models":
        "Sentiment/NLP-driven",

    "Multimodal-fusion models":
        "Multimodal",

    "Graph-based models":
        "Graph-based",

    "Other/unclear":
        "Other/unclear",

    "Ensemble/tree-based machine learning":
        "Ensemble/tree ML",

    "ANN/neuro-fuzzy models":
        "ANN/neuro-fuzzy",

    "Trend or regime":
        "Trend/regime",
}

SMALL_FAMILY_LABELS = {
    "Multimodal-fusion models",
    "Graph-based models",
    "Other/unclear",
    "Ensemble/tree-based machine learning",
    "ANN/neuro-fuzzy models",
}

SMALL_TARGET_LABELS = {
    "Return",
    "Trend or regime",
    "Not reported",
}


# ============================================================
# 8. GENERAL HELPERS
# ============================================================

def clean(value: object) -> str:
    """Remove leading, trailing, and repeated whitespace."""

    return " ".join(
        str(value or "").strip().split()
    )


def normalized_key(value: object) -> str:
    """Create a punctuation-independent normalization key."""

    text = clean(value).lower()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(text.split())


def display_period(period: str) -> str:
    """Convert range hyphens to manuscript-ready en dashes."""

    return period.replace("-", "–")


def hex_to_rgba(
    hexadecimal: str,
    alpha: float,
) -> str:
    """Convert a hexadecimal colour into Plotly RGBA notation."""

    text = hexadecimal.strip().lstrip("#")

    if not re.fullmatch(
        r"[0-9A-Fa-f]{6}",
        text,
    ):
        raise ValueError(
            f"Invalid hexadecimal colour: {hexadecimal!r}"
        )

    red = int(text[0:2], 16)
    green = int(text[2:4], 16)
    blue = int(text[4:6], 16)

    return (
        f"rgba({red},{green},{blue},{alpha:.3f})"
    )


def period_from_year(year_text: str) -> str:
    """Assign a publication year to a frozen review period."""

    try:
        year = int(float(clean(year_text)))

    except (TypeError, ValueError) as error:
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
    """Normalize a principal method-family value."""

    cleaned = clean(value)

    if cleaned in FROZEN_FAMILY_COUNTS:
        return cleaned

    lookup = normalized_key(cleaned)

    if lookup in FAMILY_ALIASES:
        return FAMILY_ALIASES[lookup]

    raise ValueError(
        f"Unrecognized principal method family: {value!r}"
    )


def normalize_target(value: str) -> str:
    """Normalize a primary forecasting-target value."""

    cleaned = clean(value)

    if cleaned in FROZEN_TARGET_COUNTS:
        return cleaned

    lookup = normalized_key(cleaned)

    if lookup in TARGET_ALIASES:
        return TARGET_ALIASES[lookup]

    raise ValueError(
        f"Unrecognized primary target: {value!r}"
    )


def display_name(item: str) -> str:
    """Return a compact manuscript display label."""

    if item in FROZEN_PERIOD_COUNTS:
        return display_period(item)

    return DISPLAY_LABELS.get(
        item,
        item,
    )


def journal_label(
    item: str,
    count: int,
) -> str:
    """Create a label with a smaller study-count line."""

    return (
        f"{display_name(item)}"
        f"<br>"
        f"<span style='font-size:{COUNT_FONT_PERCENT}%'>"
        f"(n={count:,})"
        f"</span>"
    )


# ============================================================
# 9. INPUT DISCOVERY
# ============================================================

def find_input() -> Path:
    """Find the final study-level Sankey input CSV."""

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
            "No valid study-level Sankey input CSV was found.\n\n"
            "Required columns:\n"
            "Paper_ID, Year, Principal_Method_Family, "
            "Target_Primary\n\n"
            "Expected filename:\n"
            "Section7_Final_Study_Level_Sankey_Input.csv"
        )

    raise RuntimeError(
        "More than one candidate input CSV was found:\n"
        + "\n".join(
            str(path)
            for path in matches
        )
    )


# ============================================================
# 10. COUNT VALIDATION
# ============================================================

def assert_counts(
    label: str,
    observed: Counter[str],
    expected: dict[str, int],
) -> None:
    """Compare observed counts with frozen manuscript values."""

    if Counter(observed) == Counter(expected):
        return

    print(f"\n{label} count mismatch")

    print("\nObserved:")

    for item in expected:
        print(
            f"  {item}: "
            f"{observed.get(item, 0)}"
        )

    print("\nExpected:")

    for item, count in expected.items():
        print(f"  {item}: {count}")

    unexpected = {
        item: count
        for item, count in observed.items()
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
# 11. NODE-POSITION CALCULATION
# ============================================================

def calculate_column_centres(
    order: list[str],
    counts: dict[str, int],
    gap: float,
) -> dict[str, float]:
    """
    Calculate node centres proportional to category counts.

    Plotly Sankey coordinates increase from top to bottom.
    """

    node_count = len(order)

    total_span = NODE_BOTTOM - NODE_TOP

    total_gap = (
        gap * max(node_count - 1, 0)
    )

    available_height = (
        total_span - total_gap
    )

    if available_height <= 0:
        raise ValueError(
            "Vertical gap is too large for "
            "the selected Sankey column."
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


# ============================================================
# 12. COORDINATE CONVERSION
# ============================================================

def sankey_to_paper_x(
    node_x: float,
) -> float:
    """Convert Sankey-domain x to complete-figure x."""

    return (
        DOMAIN_X0
        + node_x
        * (
            DOMAIN_X1 - DOMAIN_X0
        )
    )


def sankey_to_paper_y(
    node_y: float,
) -> float:
    """Convert top-origin Sankey y to bottom-origin figure y."""

    return (
        DOMAIN_Y0
        + (
            1.0 - node_y
        )
        * (
            DOMAIN_Y1 - DOMAIN_Y0
        )
    )


# ============================================================
# 13. CUSTOM NODE ANNOTATIONS
# ============================================================

def add_node_annotation(
    annotations: list[dict[str, Any]],
    connector_shapes: list[dict[str, Any]],
    node_x: float,
    node_y: float,
    label_y: float,
    text: str,
    stage: str,
    font_size: int,
) -> None:
    """
    Add a manually positioned node label.

    The corresponding Sankey node is not moved. A subtle connector
    is shown only when the annotation is displaced vertically.
    """

    node_paper_x = sankey_to_paper_x(
        node_x
    )

    node_paper_y = sankey_to_paper_y(
        node_y
    )

    label_paper_y = sankey_to_paper_y(
        label_y
    )

    if stage == "target":

        label_x = node_paper_x - 0.013

        x_anchor = "right"
        alignment = "right"

        connector_x0 = (
            node_paper_x - 0.004
        )

        connector_x1 = (
            label_x + 0.003
        )

    else:

        label_x = node_paper_x + 0.013

        x_anchor = "left"
        alignment = "left"

        connector_x0 = (
            node_paper_x + 0.004
        )

        connector_x1 = (
            label_x - 0.003
        )

    if abs(label_y - node_y) >= 0.018:

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
                        f"rgba(75,75,75,"
                        f"{CONNECTOR_ALPHA:.3f})"
                    ),

                    "width":
                        CONNECTOR_WIDTH,
                },

                "layer": "above",
            }
        )

    annotations.append(
        {
            "x": label_x,
            "y": label_paper_y,

            "xref": "paper",
            "yref": "paper",

            "text": text,
            "showarrow": False,

            "xanchor": x_anchor,
            "yanchor": "middle",

            "align": alignment,

            "font": {
                "family":
                    FONT_FAMILY,

                "size":
                    font_size,

                "color":
                    "#303030",
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


# ============================================================
# 14. MAIN WORKFLOW
# ============================================================

def main() -> None:

    input_path = find_input()

    print("\nInput file:")
    print(input_path)

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    if len(rows) != 493:
        raise AssertionError(
            f"Expected 493 study rows; "
            f"found {len(rows)}."
        )

    paper_ids = [
        clean(row["Paper_ID"])
        for row in rows
    ]

    if any(
        not paper_id
        for paper_id in paper_ids
    ):
        raise AssertionError(
            "One or more Paper_ID values are blank."
        )

    duplicate_ids = sorted(
        paper_id
        for paper_id, count
        in Counter(paper_ids).items()
        if count > 1
    )

    if duplicate_ids:
        raise AssertionError(
            "Paper_ID values are not unique:\n"
            + "\n".join(duplicate_ids)
        )

    normalized_rows: list[
        dict[str, str]
    ] = []

    for row in rows:

        normalized_rows.append(
            {
                "Paper_ID":
                    clean(row["Paper_ID"]),

                "Period":
                    period_from_year(
                        row["Year"]
                    ),

                "Method_Family":
                    normalize_family(
                        row[
                            "Principal_Method_Family"
                        ]
                    ),

                "Target":
                    normalize_target(
                        row["Target_Primary"]
                    ),
            }
        )


    # ========================================================
    # 15. VERIFY FROZEN DISTRIBUTIONS
    # ========================================================

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
        "Publication period",
        period_counts,
        FROZEN_PERIOD_COUNTS,
    )

    assert_counts(
        "Method family",
        family_counts,
        FROZEN_FAMILY_COUNTS,
    )

    assert_counts(
        "Forecasting target",
        target_counts,
        FROZEN_TARGET_COUNTS,
    )


    # ========================================================
    # 16. BUILD STUDY FLOWS
    # ========================================================

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

    if sum(period_family.values()) != 493:
        raise AssertionError(
            "Period-to-method flows do not total 493."
        )

    if sum(family_target.values()) != 493:
        raise AssertionError(
            "Method-to-target flows do not total 493."
        )


    # ========================================================
    # 17. DEFINE NODES
    # ========================================================

    node_items = (
        PERIOD_ORDER
        + FAMILY_ORDER
        + TARGET_ORDER
    )

    node_stages = (
        ["Publication period"]
        * len(PERIOD_ORDER)

        + ["Principal method family"]
        * len(FAMILY_ORDER)

        + ["Primary forecasting target"]
        * len(TARGET_ORDER)
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

    node_index = {
        item: index
        for index, item
        in enumerate(node_items)
    }


    # ========================================================
    # 18. CALCULATE NODE POSITIONS
    # ========================================================

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

    # Copies avoid accidental modification of global settings.
    period_label_y = PERIOD_LABEL_Y.copy()
    family_label_y = FAMILY_LABEL_Y.copy()
    target_label_y = TARGET_LABEL_Y.copy()

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

    node_customdata = [
        [
            item,
            stage,
            count,
        ]
        for item, stage, count
        in zip(
            node_items,
            node_stages,
            node_counts,
        )
    ]


    # ========================================================
    # 19. DEFINE LINKS
    # ========================================================

    sources: list[int] = []
    targets_idx: list[int] = []
    values: list[int] = []

    link_colours: list[str] = []

    link_customdata: list[
        list[Any]
    ] = []

    flow_rows: list[
        dict[str, Any]
    ] = []


    # Period -> method-family flows.
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

            targets_idx.append(
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
                    display_period(period),
                    family,
                    count,
                    (
                        "Publication period "
                        "→ method family"
                    ),
                ]
            )

            flow_rows.append(
                {
                    "Stage":
                        "Period_to_Method",

                    "Source":
                        period,

                    "Target":
                        family,

                    "Studies":
                        count,
                }
            )


    # Method-family -> target flows.
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

            targets_idx.append(
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
                    (
                        "Method family "
                        "→ forecasting target"
                    ),
                ]
            )

            flow_rows.append(
                {
                    "Stage":
                        "Method_to_Target",

                    "Source":
                        family,

                    "Target":
                        target,

                    "Studies":
                        count,
                }
            )


    # ========================================================
    # 20. BUILD SANKEY
    # ========================================================

    figure = go.Figure(
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
                "pad": 18,

                "thickness":
                    NODE_THICKNESS,

                "line": {
                    "color":
                        "rgba(45,45,45,0.72)",

                    "width":
                        NODE_LINE_WIDTH,
                },

                # Native labels are disabled to avoid overlap.
                "label": [
                    ""
                ] * len(node_items),

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
                    targets_idx,

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
                    "%{customdata[3]}<br>"
                    "Studies: %{customdata[2]:,}"
                    "<extra></extra>"
                ),
            },
        )
    )


    # ========================================================
    # 21. ADD COLUMN HEADINGS
    # ========================================================

    annotations: list[
        dict[str, Any]
    ] = []

    connector_shapes: list[
        dict[str, Any]
    ] = []

    for heading in HEADING_SPECS:

        annotations.append(
            {
                "x":
                    heading["x"],

                "y":
                    0.968,

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


    # ========================================================
    # 22. ADD PERIOD LABELS
    # ========================================================

    for item in PERIOD_ORDER:

        add_node_annotation(
            annotations=annotations,

            connector_shapes=
                connector_shapes,

            node_x=
                PERIOD_X,

            node_y=
                period_y[item],

            label_y=
                period_label_y[item],

            text=
                journal_label(
                    item,
                    FROZEN_PERIOD_COUNTS[item],
                ),

            stage=
                "period",

            font_size=
                REGULAR_LABEL_FONT_SIZE,
        )


    # ========================================================
    # 23. ADD METHOD-FAMILY LABELS
    # ========================================================

    for item in FAMILY_ORDER:

        family_font_size = (
            SMALL_FAMILY_FONT_SIZE
            if item in SMALL_FAMILY_LABELS
            else REGULAR_LABEL_FONT_SIZE
        )

        add_node_annotation(
            annotations=annotations,

            connector_shapes=
                connector_shapes,

            node_x=
                FAMILY_X,

            node_y=
                family_y[item],

            label_y=
                family_label_y[item],

            text=
                journal_label(
                    item,
                    FROZEN_FAMILY_COUNTS[item],
                ),

            stage=
                "family",

            font_size=
                family_font_size,
        )


    # ========================================================
    # 24. ADD TARGET LABELS
    # ========================================================

    for item in TARGET_ORDER:

        target_font_size = (
            SMALL_TARGET_FONT_SIZE
            if item in SMALL_TARGET_LABELS
            else REGULAR_LABEL_FONT_SIZE
        )

        add_node_annotation(
            annotations=annotations,

            connector_shapes=
                connector_shapes,

            node_x=
                TARGET_X,

            node_y=
                target_y[item],

            label_y=
                target_label_y[item],

            text=
                journal_label(
                    item,
                    FROZEN_TARGET_COUNTS[item],
                ),

            stage=
                "target",

            font_size=
                target_font_size,
        )


    # ========================================================
    # 25. FINAL LAYOUT
    # ========================================================

    figure.update_layout(
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
                "#303030",
        },

        margin={
            "l": 5,
            "r": 5,
            "t": 35,
            "b": 5,
        },

        annotations=
            annotations,

        shapes=
            connector_shapes,
    )


    # ========================================================
    # 26. OUTPUT FILES
    # ========================================================

    base_name = (
        "Figure17_Period_Method_Target_"
        "Sankey_SCIE_Q1_Final"
    )

    html_path = (
        OUTPUT_DIR
        / f"{base_name}.html"
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

    flow_path = (
        OUTPUT_DIR
        / f"{base_name}_Flows.csv"
    )

    audit_path = (
        OUTPUT_DIR
        / f"{base_name}_Audit.csv"
    )


    # ========================================================
    # 27. INTERACTIVE HTML
    # ========================================================

    figure.write_html(
        html_path,

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


    # ========================================================
    # 28. STATIC EXPORTS
    # ========================================================

    static_export_ok = True

    try:

        figure.write_image(
            pdf_path,

            format="pdf",

            width=
                FIGURE_WIDTH,

            height=
                FIGURE_HEIGHT,

            scale=1,
        )

        figure.write_image(
            svg_path,

            format="svg",

            width=
                FIGURE_WIDTH,

            height=
                FIGURE_HEIGHT,

            scale=1,
        )

        figure.write_image(
            png_path,

            format="png",

            width=
                FIGURE_WIDTH,

            height=
                FIGURE_HEIGHT,

            scale=
                PNG_SCALE,
        )

    except Exception as error:

        static_export_ok = False

        print(
            "\nHTML and CSV outputs were generated, "
            "but PDF/PNG/SVG export failed."
        )

        print(
            "\nInstall or update Kaleido:"
        )

        print(
            "    pip install -U kaleido"
        )

        print(
            "\nRecent Kaleido versions "
            "may require Chrome:"
        )

        print(
            "    plotly_get_chrome"
        )

        print(
            f"\nExport error:\n{error}"
        )


    # ========================================================
    # 29. FLOW AUDIT CSV
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
    # 30. VALIDATION AUDIT CSV
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

        audit_rows = [
            (
                "Study rows",
                len(normalized_rows),
                493,
            ),
            (
                "Unique Paper_ID",
                len(set(paper_ids)),
                493,
            ),
            (
                "Period-to-method total",
                sum(period_family.values()),
                493,
            ),
            (
                "Method-to-target total",
                sum(family_target.values()),
                493,
            ),
            (
                "Period counts",
                str(dict(period_counts)),
                str(FROZEN_PERIOD_COUNTS),
            ),
            (
                "Method-family counts",
                str(dict(family_counts)),
                str(FROZEN_FAMILY_COUNTS),
            ),
            (
                "Target counts",
                str(dict(target_counts)),
                str(FROZEN_TARGET_COUNTS),
            ),
        ]

        for (
            audit_item,
            observed,
            required,
        ) in audit_rows:

            writer.writerow(
                [
                    audit_item,
                    observed,
                    required,
                    "PASS",
                ]
            )


    # ========================================================
    # 31. DISPLAY AND SUMMARY
    # ========================================================

    if SHOW_FIGURE:
        figure.show()

    print(
        "\nFigure 17 generation completed."
    )

    print(
        "All frozen-count audits passed."
    )

    print("\nInput:")
    print(input_path)

    print("\nOutput directory:")
    print(OUTPUT_DIR)

    print("\nInteractive HTML:")
    print(html_path)

    print("\nFlow audit:")
    print(flow_path)

    print("\nValidation audit:")
    print(audit_path)

    if static_export_ok:

        print("\nVector PDF:")
        print(pdf_path)

        print("\nVector SVG:")
        print(svg_path)

        print("\nHigh-resolution PNG:")
        print(png_path)


if __name__ == "__main__":
    main()