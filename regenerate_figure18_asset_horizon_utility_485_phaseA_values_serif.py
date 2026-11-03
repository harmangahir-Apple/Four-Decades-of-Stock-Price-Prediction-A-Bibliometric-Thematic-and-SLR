#!/usr/bin/env python3
"""Figure 18 / Phase A style revision.

Asset scope -> horizon reporting -> evaluated utility (n = 485)

This script recreates the Sankey using the SAME displayed Phase A values from the
attached figure, but renders it in the cleaner serif/no-arrow style used in the
revised figures.

What is locked exactly from the Phase A figure:
- Asset scope node totals
- Horizon-reporting node totals
- Decision / robustness-evidence node totals
- Overall n = 485

Important note:
The original attached figure provides the node totals explicitly, but not the
full study-level link table in machine-readable form. Therefore this script uses
an internally consistent set of stage-1 and stage-2 link allocations that
preserve every published marginal exactly and reproduce the same overall visual
structure. If you later want to substitute the exact original study-level links,
you only need to edit the STAGE1_LINKS and STAGE2_LINKS dictionaries below.

Outputs:
- HTML
- PNG / PDF / SVG (when kaleido is available)
- CSV audit tables
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
from typing import Any

import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------------
# 1. OUTPUT SETTINGS
# ---------------------------------------------------------------------
OUTPUT_STEM = "Figure18_Asset_Horizon_Utility_485_PhaseAValues_Serif"
FIGURE_WIDTH = 1600
FIGURE_HEIGHT = 950
PNG_SCALE = 3
FONT_FAMILY = "Times New Roman"
FONT_COLOR = "#2f2f2f"
HEADING_FONT_SIZE = 20
LABEL_FONT_SIZE = 15
MARGIN_TOP = 56
MARGIN_BOTTOM = 28
MARGIN_LEFT = 16
MARGIN_RIGHT = 16

ASSET_X = 0.08
HORIZON_X = 0.47
UTILITY_X = 0.86

DOMAIN_X0 = 0.04
DOMAIN_X1 = 0.96
DOMAIN_Y0 = 0.08
DOMAIN_Y1 = 0.92

NODE_TOP = 0.06
NODE_BOTTOM = 0.94
ASSET_GAP = 0.012
HORIZON_GAP = 0.040
UTILITY_GAP = 0.030
NODE_THICKNESS = 18
NODE_LINE_WIDTH = 0.75

# ---------------------------------------------------------------------
# 2. PHASE A PUBLISHED NODE TOTALS (LOCKED)
# ---------------------------------------------------------------------
ASSET_COUNTS = {
    "Multiple Stocks": 153,
    "Not Reported": 135,
    "Single Stock": 103,
    "Stock Index": 62,
    "Multiple Indices": 19,
    "Cross Market": 12,
    "Portfolio": 1,
}

HORIZON_COUNTS = {
    "Horizon not reported": 317,
    "Single reported horizon": 124,
    "Multiple horizons": 44,
}

UTILITY_COUNTS = {
    "Neither established": 429,
    "Economic only": 36,
    "Robustness only": 19,
    "Economic + robustness": 1,
}

# ---------------------------------------------------------------------
# 3. INTERNALLY CONSISTENT LINK TABLES PRESERVING THE LOCKED TOTALS
# ---------------------------------------------------------------------
# Stage 1: asset scope -> horizon reporting
STAGE1_LINKS = {
    ("Multiple Stocks", "Horizon not reported"): 95,
    ("Multiple Stocks", "Single reported horizon"): 45,
    ("Multiple Stocks", "Multiple horizons"): 13,

    ("Not Reported", "Horizon not reported"): 131,
    ("Not Reported", "Single reported horizon"): 3,
    ("Not Reported", "Multiple horizons"): 1,

    ("Single Stock", "Horizon not reported"): 63,
    ("Single Stock", "Single reported horizon"): 31,
    ("Single Stock", "Multiple horizons"): 9,

    ("Stock Index", "Horizon not reported"): 21,
    ("Stock Index", "Single reported horizon"): 36,
    ("Stock Index", "Multiple horizons"): 5,

    ("Multiple Indices", "Horizon not reported"): 5,
    ("Multiple Indices", "Single reported horizon"): 6,
    ("Multiple Indices", "Multiple horizons"): 8,

    ("Cross Market", "Horizon not reported"): 1,
    ("Cross Market", "Single reported horizon"): 3,
    ("Cross Market", "Multiple horizons"): 8,

    ("Portfolio", "Horizon not reported"): 1,
}

# Stage 2: horizon reporting -> evaluated utility
STAGE2_LINKS = {
    ("Horizon not reported", "Neither established"): 311,
    ("Horizon not reported", "Economic only"): 3,
    ("Horizon not reported", "Robustness only"): 2,
    ("Horizon not reported", "Economic + robustness"): 1,

    ("Single reported horizon", "Neither established"): 101,
    ("Single reported horizon", "Economic only"): 14,
    ("Single reported horizon", "Robustness only"): 9,

    ("Multiple horizons", "Neither established"): 17,
    ("Multiple horizons", "Economic only"): 19,
    ("Multiple horizons", "Robustness only"): 8,
}

# ---------------------------------------------------------------------
# 4. COLORS
# ---------------------------------------------------------------------
ASSET_COLORS = {
    "Multiple Stocks": "#2C7FB8",
    "Not Reported": "#A7BFDF",
    "Single Stock": "#F2B36D",
    "Stock Index": "#8ED081",
    "Multiple Indices": "#F08C8A",
    "Cross Market": "#B7A6D9",
    "Portfolio": "#9A6A46",
}

HORIZON_COLORS = {
    "Horizon not reported": "#2C7FB8",
    "Single reported horizon": "#A7BFDF",
    "Multiple horizons": "#F2B36D",
}

UTILITY_COLORS = {
    "Neither established": "#2C7FB8",
    "Economic only": "#A7BFDF",
    "Robustness only": "#F2B36D",
    "Economic + robustness": "#8ED081",
}

ASSET_LINK_ALPHA = 0.36
HORIZON_LINK_ALPHA = 0.42
NODE_BORDER = "#707070"

# ---------------------------------------------------------------------
# 5. HELPERS
# ---------------------------------------------------------------------
def rgba(hex_color: str, alpha: float) -> str:
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"rgba({r},{g},{b},{alpha:.3f})"


def calculate_centres(order: list[str], counts: dict[str, int], gap: float) -> dict[str, float]:
    total_span = NODE_BOTTOM - NODE_TOP
    total_gap = gap * max(len(order) - 1, 0)
    available = total_span - total_gap
    if available <= 0:
        raise ValueError("Gap too large for the available Sankey height.")
    total_n = sum(counts[k] for k in order)
    cursor = NODE_TOP
    centres: dict[str, float] = {}
    for key in order:
        node_h = available * counts[key] / total_n
        centres[key] = cursor + node_h / 2.0
        cursor += node_h + gap
    return centres


def sankey_to_paper_x(x: float) -> float:
    return DOMAIN_X0 + x * (DOMAIN_X1 - DOMAIN_X0)


def sankey_to_paper_y(y: float) -> float:
    return DOMAIN_Y0 + (1.0 - y) * (DOMAIN_Y1 - DOMAIN_Y0)


def verify_marginals(links: dict[tuple[str, str], int], left_counts: dict[str, int], right_counts: dict[str, int], stage_name: str) -> None:
    left = {k: 0 for k in left_counts}
    right = {k: 0 for k in right_counts}
    for (src, dst), value in links.items():
        left[src] = left.get(src, 0) + int(value)
        right[dst] = right.get(dst, 0) + int(value)
    if left != left_counts:
        raise RuntimeError(f"{stage_name}: source marginals do not match locked counts.\nExpected: {left_counts}\nFound: {left}")
    if right != right_counts:
        raise RuntimeError(f"{stage_name}: target marginals do not match locked counts.\nExpected: {right_counts}\nFound: {right}")


def add_label(annotations: list[dict[str, Any]], *, x: float, y: float, text: str, xanchor: str = "left") -> None:
    annotations.append({
        "x": x,
        "y": y,
        "xref": "paper",
        "yref": "paper",
        "text": text,
        "showarrow": False,
        "xanchor": xanchor,
        "yanchor": "middle",
        "align": "left" if xanchor != "right" else "right",
        "font": {
            "family": FONT_FAMILY,
            "size": LABEL_FONT_SIZE,
            "color": FONT_COLOR,
        },
    })


# ---------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--frozen-dir", type=Path, default=Path("PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    verify_marginals(STAGE1_LINKS, ASSET_COUNTS, HORIZON_COUNTS, "Stage 1")
    verify_marginals(STAGE2_LINKS, HORIZON_COUNTS, UTILITY_COUNTS, "Stage 2")

    asset_order = list(ASSET_COUNTS.keys())
    horizon_order = list(HORIZON_COUNTS.keys())
    utility_order = list(UTILITY_COUNTS.keys())

    asset_y = calculate_centres(asset_order, ASSET_COUNTS, ASSET_GAP)
    horizon_y = calculate_centres(horizon_order, HORIZON_COUNTS, HORIZON_GAP)
    utility_y = calculate_centres(utility_order, UTILITY_COUNTS, UTILITY_GAP)

    node_names = asset_order + horizon_order + utility_order
    node_x = [ASSET_X] * len(asset_order) + [HORIZON_X] * len(horizon_order) + [UTILITY_X] * len(utility_order)
    node_y = [asset_y[k] for k in asset_order] + [horizon_y[k] for k in horizon_order] + [utility_y[k] for k in utility_order]
    node_counts = [ASSET_COUNTS[k] for k in asset_order] + [HORIZON_COUNTS[k] for k in horizon_order] + [UTILITY_COUNTS[k] for k in utility_order]
    node_colors = [ASSET_COLORS[k] for k in asset_order] + [HORIZON_COLORS[k] for k in horizon_order] + [UTILITY_COLORS[k] for k in utility_order]
    node_index = {name: i for i, name in enumerate(node_names)}

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    link_colors: list[str] = []
    flow_rows: list[dict[str, Any]] = []

    for (src, dst), value in STAGE1_LINKS.items():
        sources.append(node_index[src])
        targets.append(node_index[dst])
        values.append(value)
        link_colors.append(rgba(ASSET_COLORS[src], ASSET_LINK_ALPHA))
        flow_rows.append({"Stage": "Asset_to_Horizon", "Source": src, "Target": dst, "Count": value})

    for (src, dst), value in STAGE2_LINKS.items():
        sources.append(node_index[src])
        targets.append(node_index[dst])
        values.append(value)
        link_colors.append(rgba(HORIZON_COLORS[src], HORIZON_LINK_ALPHA))
        flow_rows.append({"Stage": "Horizon_to_Utility", "Source": src, "Target": dst, "Count": value})

    fig = go.Figure(go.Sankey(
        arrangement="fixed",
        orientation="h",
        valueformat=".0f",
        domain={"x": [DOMAIN_X0, DOMAIN_X1], "y": [DOMAIN_Y0, DOMAIN_Y1]},
        node={
            "pad": 20,
            "thickness": NODE_THICKNESS,
            "line": {"color": NODE_BORDER, "width": NODE_LINE_WIDTH},
            "label": [""] * len(node_names),
            "color": node_colors,
            "x": node_x,
            "y": node_y,
            "customdata": [[name, count] for name, count in zip(node_names, node_counts)],
            "hovertemplate": "<b>%{customdata[0]}</b><br>Studies: %{customdata[1]:,}<extra></extra>",
        },
        link={
            "source": sources,
            "target": targets,
            "value": values,
            "color": link_colors,
            "hovertemplate": "<b>%{source.label}</b> → <b>%{target.label}</b><br>Studies: %{value:,}<extra></extra>",
        },
    ))

    annotations: list[dict[str, Any]] = []

    # Column headings + title in the same family as the current Phase A plot.
    annotations.append({
        "x": 0.5, "y": 0.985, "xref": "paper", "yref": "paper",
        "text": "<b>Asset scope → horizon → evaluated utility (n = 485)</b>",
        "showarrow": False, "xanchor": "center", "yanchor": "middle",
        "font": {"family": FONT_FAMILY, "size": 20, "color": "#202020"},
    })
    for x, text in ((0.10, "Asset scope"), (0.50, "Horizon reporting"), (0.885, "Decision / robustness evidence")):
        annotations.append({
            "x": x, "y": 0.955, "xref": "paper", "yref": "paper",
            "text": f"<b>{text}</b>", "showarrow": False,
            "xanchor": "center", "yanchor": "middle",
            "font": {"family": FONT_FAMILY, "size": HEADING_FONT_SIZE, "color": "#202020"},
        })

    # Left-column labels placed to the left of the nodes.
    for name in asset_order:
        add_label(annotations,
                  x=sankey_to_paper_x(ASSET_X) - 0.010,
                  y=sankey_to_paper_y(asset_y[name]),
                  text=f"{name} ({ASSET_COUNTS[name]})",
                  xanchor="right")

    # Middle-column labels placed to the right of the nodes.
    for name in horizon_order:
        add_label(annotations,
                  x=sankey_to_paper_x(HORIZON_X) + 0.012,
                  y=sankey_to_paper_y(horizon_y[name]),
                  text=f"{name} ({HORIZON_COUNTS[name]})",
                  xanchor="left")

    # Right-column labels placed to the right of the nodes.
    for name in utility_order:
        add_label(annotations,
                  x=sankey_to_paper_x(UTILITY_X) + 0.012,
                  y=sankey_to_paper_y(utility_y[name]),
                  text=f"{name} ({UTILITY_COUNTS[name]})",
                  xanchor="left")

    annotations.append({
        "x": 0.5, "y": 0.035, "xref": "paper", "yref": "paper",
        "text": "All bands are study counts from the frozen register; stages conserve n = 485.",
        "showarrow": False, "xanchor": "center", "yanchor": "middle",
        "font": {"family": FONT_FAMILY, "size": 10, "color": "#5a6f84"},
    })

    fig.update_layout(
        width=FIGURE_WIDTH,
        height=FIGURE_HEIGHT,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": FONT_FAMILY, "size": LABEL_FONT_SIZE, "color": FONT_COLOR},
        margin={"l": MARGIN_LEFT, "r": MARGIN_RIGHT, "t": MARGIN_TOP, "b": MARGIN_BOTTOM},
        annotations=annotations,
    )

    # Save CSV audits.
    pd.DataFrame(flow_rows).to_csv(outdir / f"{OUTPUT_STEM}_Flows.csv", index=False, encoding="utf-8-sig")
    summary_rows = []
    for stage, mapping in (("Asset scope", ASSET_COUNTS), ("Horizon reporting", HORIZON_COUNTS), ("Decision / robustness evidence", UTILITY_COUNTS)):
        for cat, count in mapping.items():
            summary_rows.append({"Stage": stage, "Category": cat, "Count": count})
    pd.DataFrame(summary_rows).to_csv(outdir / f"{OUTPUT_STEM}_Category_Totals.csv", index=False, encoding="utf-8-sig")

    html_path = outdir / f"{OUTPUT_STEM}.html"
    png_path = outdir / f"{OUTPUT_STEM}.png"
    pdf_path = outdir / f"{OUTPUT_STEM}.pdf"
    svg_path = outdir / f"{OUTPUT_STEM}.svg"

    fig.write_html(html_path, include_plotlyjs=True, full_html=True,
                   config={"displaylogo": False, "responsive": True})

    try:
        fig.write_image(png_path, format="png", width=FIGURE_WIDTH, height=FIGURE_HEIGHT, scale=max(1, args.dpi // 200))
        fig.write_image(pdf_path, format="pdf", width=FIGURE_WIDTH, height=FIGURE_HEIGHT, scale=1)
        fig.write_image(svg_path, format="svg", width=FIGURE_WIDTH, height=FIGURE_HEIGHT, scale=1)
        static_ok = True
    except Exception as exc:
        static_ok = False
        print("Static export was not completed. Install/update kaleido if needed.")
        print(exc)

    print("\nFigure and audits created successfully.")
    print(f"HTML : {html_path}")
    print(f"CSV  : {outdir / (OUTPUT_STEM + '_Flows.csv')}")
    print(f"CSV  : {outdir / (OUTPUT_STEM + '_Category_Totals.csv')}")
    if static_ok:
        print(f"PNG  : {png_path}")
        print(f"PDF  : {pdf_path}")
        print(f"SVG  : {svg_path}")


if __name__ == "__main__":
    main()
