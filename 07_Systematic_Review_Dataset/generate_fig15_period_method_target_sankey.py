from __future__ import annotations

from pathlib import Path
import csv
import sys
from collections import Counter, defaultdict

PROJECT_ROOT = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

INPUT_CANDIDATES = [
    PROJECT_ROOT / "07_Systematic_Review_Dataset" /
    "Section7_Final_Study_Level_Sankey_Input.csv",
    PROJECT_ROOT / "Section7_Final_Study_Level_Sankey_Input.csv",
    PROJECT_ROOT / "07_Reference_Outputs_Web" /
    "Section7_Final_Study_Level_Sankey_Input.csv",
]

OUTPUT_DIR = PROJECT_ROOT / "08_Figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FROZEN_FAMILY_COUNTS = {
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

FROZEN_TARGET_COUNTS = {
    "Price level": 381,
    "Return": 17,
    "Direction": 48,
    "Trend or regime": 10,
    "Multi-target": 33,
    "Not reported": 4,
}

FROZEN_PERIOD_COUNTS = {
    "2016-2020": 27,
    "2021-2022": 36,
    "2023-2024": 49,
    "2025-2026": 381,
}

FAMILY_ALIASES = {
    "deep learning": "Deep-learning models",
    "deep_learning": "Deep-learning models",
    "deep-learning models": "Deep-learning models",
    "hybrid deep learning": "Hybrid deep-learning models",
    "hybrid_deep_learning": "Hybrid deep-learning models",
    "hybrid deep-learning models": "Hybrid deep-learning models",
    "sentiment nlp": "Sentiment/NLP-driven models",
    "sentiment_nlp": "Sentiment/NLP-driven models",
    "sentiment/nlp-driven models": "Sentiment/NLP-driven models",
    "transformer attention": "Transformer/attention-based models",
    "transformer_attention": "Transformer/attention-based models",
    "transformer/attention-based models": "Transformer/attention-based models",
    "metaheuristic optimized": "Metaheuristic-optimized models",
    "metaheuristic_optimized": "Metaheuristic-optimized models",
    "metaheuristic-optimized models": "Metaheuristic-optimized models",
    "ensemble tree based machine learning":
        "Ensemble/tree-based machine learning",
    "ensemble_tree_based_machine_learning":
        "Ensemble/tree-based machine learning",
    "ensemble/tree-based machine learning":
        "Ensemble/tree-based machine learning",
    "graph based": "Graph-based models",
    "graph_based": "Graph-based models",
    "graph-based models": "Graph-based models",
    "multimodal fusion": "Multimodal-fusion models",
    "multimodal_fusion": "Multimodal-fusion models",
    "multimodal-fusion models": "Multimodal-fusion models",
    "other": "Other/unclear",
    "other unclear": "Other/unclear",
    "other/unclear": "Other/unclear",
    "ann neuro fuzzy": "ANN/neuro-fuzzy models",
    "ann_neuro_fuzzy": "ANN/neuro-fuzzy models",
    "ann/neuro-fuzzy models": "ANN/neuro-fuzzy models",
}

TARGET_ALIASES = {
    "price": "Price level",
    "price level": "Price level",
    "return": "Return",
    "direction": "Direction",
    "trend_regime": "Trend or regime",
    "trend or regime": "Trend or regime",
    "multi_target": "Multi-target",
    "multi-target": "Multi-target",
    "not_reported": "Not reported",
    "not reported": "Not reported",
}

REQUIRED_COLUMNS = {
    "Paper_ID",
    "Year",
    "Principal_Method_Family",
    "Target_Primary",
}


def clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def key(value: object) -> str:
    return (
        clean(value)
        .lower()
        .replace("&", " and ")
        .replace("/", " ")
        .replace("-", " ")
    )


def period_from_year(year_text: str) -> str:
    try:
        year = int(float(clean(year_text)))
    except ValueError as exc:
        raise ValueError(f"Invalid year: {year_text!r}") from exc

    if 2016 <= year <= 2020:
        return "2016-2020"
    if 2021 <= year <= 2022:
        return "2021-2022"
    if 2023 <= year <= 2024:
        return "2023-2024"
    if 2025 <= year <= 2026:
        return "2025-2026"

    raise ValueError(f"Year outside frozen technical-subset periods: {year}")


def normalize_family(value: str) -> str:
    cleaned = clean(value)
    if cleaned in FROZEN_FAMILY_COUNTS:
        return cleaned

    normalized = FAMILY_ALIASES.get(key(cleaned))
    if normalized:
        return normalized

    raise ValueError(f"Unrecognized method family: {value!r}")


def normalize_target(value: str) -> str:
    cleaned = clean(value)
    if cleaned in FROZEN_TARGET_COUNTS:
        return cleaned

    normalized = TARGET_ALIASES.get(key(cleaned).replace(" ", "_"))
    if normalized:
        return normalized

    normalized = TARGET_ALIASES.get(key(cleaned))
    if normalized:
        return normalized

    raise ValueError(f"Unrecognized target: {value!r}")


def find_input() -> Path:
    for path in INPUT_CANDIDATES:
        if path.exists():
            return path

    matches = []
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
            "No 493-row Sankey input CSV was found. Export the final "
            "study-level register with exactly these columns:\n"
            "Paper_ID, Year, Principal_Method_Family, Target_Primary\n"
            "Save it as Section7_Final_Study_Level_Sankey_Input.csv."
        )

    raise RuntimeError(
        "More than one candidate Sankey input CSV was found:\n"
        + "\n".join(str(path) for path in matches)
    )


def assert_counts(
    label: str,
    observed: Counter,
    expected: dict[str, int],
) -> None:
    if dict(observed) != expected:
        print(f"\n{label} count mismatch")
        print("Observed:")
        for item, count in observed.items():
            print(f"  {item}: {count}")
        print("Expected:")
        for item, count in expected.items():
            print(f"  {item}: {count}")
        raise AssertionError(f"{label} counts do not match the frozen manuscript.")


def main() -> None:
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise RuntimeError(
            "Install Plotly and Kaleido first:\n"
            "%pip install plotly kaleido"
        ) from exc

    input_path = find_input()
    print("Input:", input_path)

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 493:
        raise AssertionError(f"Expected 493 rows; found {len(rows)}.")

    paper_ids = [clean(row["Paper_ID"]) for row in rows]

    if any(not paper_id for paper_id in paper_ids):
        raise AssertionError("One or more Paper_ID values are blank.")

    if len(set(paper_ids)) != 493:
        duplicates = [
            paper_id
            for paper_id, count in Counter(paper_ids).items()
            if count > 1
        ]
        raise AssertionError(
            "Paper_ID values are not unique: "
            + ", ".join(duplicates)
        )

    normalized_rows = []

    for row in rows:
        normalized_rows.append(
            {
                "Paper_ID": clean(row["Paper_ID"]),
                "Period": period_from_year(row["Year"]),
                "Method_Family": normalize_family(
                    row["Principal_Method_Family"]
                ),
                "Target": normalize_target(row["Target_Primary"]),
            }
        )

    period_counts = Counter(row["Period"] for row in normalized_rows)
    family_counts = Counter(row["Method_Family"] for row in normalized_rows)
    target_counts = Counter(row["Target"] for row in normalized_rows)

    assert_counts("Period", period_counts, FROZEN_PERIOD_COUNTS)
    assert_counts("Method-family", family_counts, FROZEN_FAMILY_COUNTS)
    assert_counts("Target", target_counts, FROZEN_TARGET_COUNTS)

    period_family = Counter(
        (row["Period"], row["Method_Family"])
        for row in normalized_rows
    )
    family_target = Counter(
        (row["Method_Family"], row["Target"])
        for row in normalized_rows
    )

    if sum(period_family.values()) != 493:
        raise AssertionError("Period-to-family flow does not total 493.")

    if sum(family_target.values()) != 493:
        raise AssertionError("Family-to-target flow does not total 493.")

    periods = list(FROZEN_PERIOD_COUNTS)
    families = list(FROZEN_FAMILY_COUNTS)
    targets = list(FROZEN_TARGET_COUNTS)

    period_labels = [
        f"{period}<br>(n={FROZEN_PERIOD_COUNTS[period]})"
        for period in periods
    ]
    family_labels = [
        f"{family}<br>(n={FROZEN_FAMILY_COUNTS[family]})"
        for family in families
    ]
    target_labels = [
        f"{target}<br>(n={FROZEN_TARGET_COUNTS[target]})"
        for target in targets
    ]

    labels = period_labels + family_labels + target_labels

    period_index = {
        period: index
        for index, period in enumerate(periods)
    }
    family_offset = len(periods)
    family_index = {
        family: family_offset + index
        for index, family in enumerate(families)
    }
    target_offset = family_offset + len(families)
    target_index = {
        target: target_offset + index
        for index, target in enumerate(targets)
    }

    sources = []
    targets_idx = []
    values = []
    customdata = []

    flow_rows = []

    for (period, family), count in sorted(period_family.items()):
        sources.append(period_index[period])
        targets_idx.append(family_index[family])
        values.append(count)
        customdata.append(f"{period} -> {family}")
        flow_rows.append(
            {
                "Stage": "Period_to_Method",
                "Source": period,
                "Target": family,
                "Studies": count,
            }
        )

    for (family, target), count in sorted(family_target.items()):
        sources.append(family_index[family])
        targets_idx.append(target_index[target])
        values.append(count)
        customdata.append(f"{family} -> {target}")
        flow_rows.append(
            {
                "Stage": "Method_to_Target",
                "Source": family,
                "Target": target,
                "Studies": count,
            }
        )

    figure = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                valueformat=".0f",
                node={
                    "pad": 16,
                    "thickness": 18,
                    "line": {"width": 0.5},
                    "label": labels,
                    "hovertemplate": (
                        "%{label}<extra></extra>"
                    ),
                },
                link={
                    "source": sources,
                    "target": targets_idx,
                    "value": values,
                    "customdata": customdata,
                    "hovertemplate": (
                        "%{customdata}<br>"
                        "Studies: %{value}<extra></extra>"
                    ),
                },
            )
        ]
    )

    figure.update_layout(
        width=1800,
        height=1050,
        margin={"l": 25, "r": 25, "t": 30, "b": 30},
        font={"size": 15},
    )

    pdf_path = (
        OUTPUT_DIR
        / "Fig15_Period_Method_Target_Sankey.pdf"
    )
    png_path = (
        OUTPUT_DIR
        / "Fig15_Period_Method_Target_Sankey.png"
    )
    html_path = (
        OUTPUT_DIR
        / "Fig15_Period_Method_Target_Sankey.html"
    )
    flow_path = (
        OUTPUT_DIR
        / "Fig15_Period_Method_Target_Flows.csv"
    )
    audit_path = (
        OUTPUT_DIR
        / "Fig15_Period_Method_Target_Audit.csv"
    )

    figure.write_html(
        html_path,
        include_plotlyjs="cdn",
    )

    try:
        figure.write_image(
            pdf_path,
            format="pdf",
            width=1800,
            height=1050,
            scale=1,
        )
        figure.write_image(
            png_path,
            format="png",
            width=1800,
            height=1050,
            scale=2,
        )
    except Exception as exc:
        print(
            "\nHTML and CSV outputs were generated, but PDF/PNG "
            "export failed. Install/update Kaleido:\n"
            "%pip install -U kaleido\n"
        )
        print("Export error:", exc)

    with flow_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Stage", "Source", "Target", "Studies"],
        )
        writer.writeheader()
        writer.writerows(flow_rows)

    with audit_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["Audit_Item", "Observed", "Required", "Status"])
        writer.writerow(
            ["Study rows", len(normalized_rows), 493, "PASS"]
        )
        writer.writerow(
            ["Unique Paper_ID", len(set(paper_ids)), 493, "PASS"]
        )
        writer.writerow(
            [
                "Period-to-method total",
                sum(period_family.values()),
                493,
                "PASS",
            ]
        )
        writer.writerow(
            [
                "Method-to-target total",
                sum(family_target.values()),
                493,
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

    print("\nSankey audit passed.")
    print("Flows:", flow_path)
    print("Audit:", audit_path)
    print("Interactive HTML:", html_path)
    if pdf_path.exists():
        print("PDF:", pdf_path)
    if png_path.exists():
        print("PNG:", png_path)


if __name__ == "__main__":
    main()
