#!/usr/bin/env python3
"""ACME Phase A — figure: publication period -> method family -> forecasting target.

Recreates the author-designed 492-study Sankey visual language using the FINAL,
immutable 485-study technical register. The source is never a legacy compiled
workbook or an old Sankey map. Preserves the prior period/family/target palette,
three-column ribbons, proportional node heights and categorical ordering.

The matplotlib implementation keeps every label as a vector-font text object,
uses white backing for names over ribbons, and separates labels belonging to
very small nodes with thin leader lines. Counts are computed study by study.

Usage in WSL:
  python regenerate_period_method_target_sankey_485_original_style_READABLE.py \\
    --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
    --output-dir Figures_485 --dpi 600

Alternatively:
  python regenerate_period_method_target_sankey_485_original_style_READABLE.py \\
    --archive PhaseA_FROZEN_485_Sync_Inputs.zip --output-dir Figures_485

Outputs: vector PDF/SVG, 600-dpi PNG/TIFF, two independently computed edge
matrices, individual edge counts, manifest/hash/flow QA JSON and LaTeX snippet.

Optional --check-only runs frozen-source validation without producing images.
No diagram is generated if source hashes, category marginals or conservation
checks fail. Do NOT change expected counts merely to make failing checks pass.

Dependencies: matplotlib and Pillow (for LZW TIFF); standard-library otherwise.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle

N = 485
REGISTER_NAME = "Technical_Register_485_FROZEN.csv"
CATEGORIES_NAME = "Manuscript_Category_Counts_FROZEN.csv"
MANIFEST_NAME = "Final_Freeze_Manifest_v1.json"
REG_SHA = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
CAT_SHA = "3d8e77e50cf6565351aa1ebd3b35aa26e61f2378b8731a348323a71415e4c1b8"
EXCLUDED = frozenset({"P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"})
STEM = "Figure16_Period_Method_Target_Sankey_485_Original_Style_Readable"

# Display order follows the earlier, author-designed 492-study figure.
# These locked counts are assertions; individual FLOW counts are read from
# the hashed 485-row register and MUST NOT be imputed from marginals.
PERIOD_COUNTS = {
    "2016–2020": 27,
    "2021–2022": 36,
    "2023–2024": 47,
    "2025–2026": 375,
}
FAMILY_COUNTS = {
    "Hybrid deep-learning models": 109,
    "Transformer/attention-based models": 68,
    "Deep-learning models": 114,
    "Metaheuristic-optimized models": 51,
    "Sentiment/NLP-driven models": 77,
    "Multimodal-fusion models": 12,
    "Graph-based models": 16,
    "Other/unclear": 3,
    "Ensemble/tree-based machine learning": 32,
    "ANN/neuro-fuzzy models": 2,
    "Statistical/econometric models": 1,
}
TARGET_COUNTS = {
    "Price": 378,
    "Multi_Target": 32,
    "Direction": 47,
    "Return": 17,
    "Trend_Regime": 8,
    "Volatility": 1,
    "Not_Reported": 2,
}

PERIOD_COLORS = {
    "2016–2020": "#5B8CC0",
    "2021–2022": "#4CA6A8",
    "2023–2024": "#F28E6B",
    "2025–2026": "#9B6CE3",
}
FAMILY_COLORS = {
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
    "Statistical/econometric models": "#B79C78",
}
TARGET_COLORS = {
    "Price": "#6E6E6E",
    "Multi_Target": "#8A8A8A",
    "Direction": "#9C9C9C",
    "Return": "#ADADAD",
    "Trend_Regime": "#BDBDBD",
    "Volatility": "#C6C6C6",
    "Not_Reported": "#D0D0D0",
}

# Abbreviated names are *display only*, not substitutions for the underlying
# mutually exclusive coding. Full names are retained in the audit tables.
FAMILY_DISPLAY = {
    "Hybrid deep-learning models": "Hybrid deep-learning (109)",
    "Transformer/attention-based models": "Transformer/attention (68)",
    "Deep-learning models": "Deep-learning models (114)",
    "Metaheuristic-optimized models": "Metaheuristic-optimized (51)",
    "Sentiment/NLP-driven models": "Sentiment/NLP-driven (77)",
    "Multimodal-fusion models": "Multimodal-fusion (12)",
    "Graph-based models": "Graph-based models (16)",
    "Other/unclear": "Other/unclear (3)",
    "Ensemble/tree-based machine learning": "Ensemble/tree-based ML (32)",
    "ANN/neuro-fuzzy models": "ANN/neuro-fuzzy (2)",
    "Statistical/econometric models": "Statistical/econometric (1)",
}
TARGET_DISPLAY = {
    "Price": "Price (378)",
    "Multi_Target": "Multi-target (32)",
    "Direction": "Direction (47)",
    "Return": "Return (17)",
    "Trend_Regime": "Trend or regime (8)",
    "Volatility": "Volatility (1)",
    "Not_Reported": "Not reported (2)",
}

# Diagram geometry; physical canvas aspect ratio is chosen so source 15–16 pt
# text remains about 8–9 pt when the PDF is inserted at 17.2 cm (LaTeX text width).
FIGSIZE = (12.6, 8.5)
X_PERIOD = 0.126
X_FAMILY = 0.482
X_TARGET = 0.831
NODE_W = 0.009
Y_TOP = 0.865
Y_BOTTOM = 0.175
STAGE_GAPS = (0.030, 0.0115, 0.023)
LABEL_FONT = 14.1
HEADING_FONT = 17.0
FOOTNOTE_FONT = 10.5
MAIN_TEXT = "#222222"
BACKGROUND = "#FFFFFF"


def options():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--archive", type=Path, default=None, help="Read the authenticated frozen ZIP")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--check-only", action="store_true", help="Verify counts/hashes, export nothing")
    return p.parse_args()


def load_bytes(args):
    wanted = (REGISTER_NAME, CATEGORIES_NAME, MANIFEST_NAME)
    if args.archive:
        with zipfile.ZipFile(args.archive) as archive:
            lookup = {}
            for name in archive.namelist():
                if name.endswith("/"):
                    continue
                base = Path(name).name
                if base in lookup:
                    raise ValueError(f"Ambiguous duplicate basename in frozen archive: {base}")
                lookup[base] = name
            missing = set(wanted) - set(lookup)
            if missing:
                raise FileNotFoundError(f"Missing frozen archive files: {sorted(missing)}")
            raw = {name: archive.read(lookup[name]) for name in wanted}
        path = str(args.archive.resolve())
    else:
        raw = {name: (args.frozen_dir / name).read_bytes() for name in wanted}
        path = str(args.frozen_dir.resolve())
    return raw, path


def parse_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def period_for(year):
    if not str(year).strip().isdigit():
        raise ValueError(f"Non-numeric publication year: {year!r}")
    y = int(year)
    if 2016 <= y <= 2020:
        return "2016–2020"
    if 2021 <= y <= 2022:
        return "2021–2022"
    if 2023 <= y <= 2024:
        return "2023–2024"
    if 2025 <= y <= 2026:
        return "2025–2026"
    raise ValueError(f"Technical-study year outside approved period bins: {y}")


def normal_target(value):
    # Controlled codes in the 51-field frozen register, with formatting variants
    # only for the exact same concept. Unknown codes fail instead of being guessed.
    clean = "_".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())
    aliases = {
        "price": "Price", "price_level": "Price",
        "multi_target": "Multi_Target", "multitarget": "Multi_Target",
        "direction": "Direction", "return": "Return",
        "trend_regime": "Trend_Regime", "trend_or_regime": "Trend_Regime",
        "volatility": "Volatility", "not_reported": "Not_Reported",
    }
    if clean not in aliases:
        raise ValueError(f"Unrecognized frozen target code: {value!r}")
    return aliases[clean]


def check_counter(name, observed, expected):
    if dict(observed) != expected:
        lines = []
        for key in expected:
            if observed.get(key, 0) != expected[key]:
                lines.append(f"{key}: found {observed.get(key,0)}, expected {expected[key]}")
        for key in observed:
            if key not in expected:
                lines.append(f"Unexpected: {key}={observed[key]}")
        raise RuntimeError(f"{name} does not reconcile with approved frozen counts:\n" + "\n".join(lines))


def read_and_verify(args):
    raw, provenance = load_bytes(args)
    m = json.loads(raw[MANIFEST_NAME].decode("utf-8-sig"))
    if m.get("final_corpus_frozen") is not True or m.get("retained_studies") != N:
        raise RuntimeError("Not the immutable author-approved 485-study freeze")
    if m.get("primary_metric_sankey_released") is not False:
        raise RuntimeError("Frozen release has unexpected primary-metric flag")
    for name, expected in ((REGISTER_NAME, REG_SHA), (CATEGORIES_NAME, CAT_SHA)):
        observed = hashlib.sha256(raw[name]).hexdigest()
        if m.get("output_sha256", {}).get(name) != expected or observed != expected:
            raise RuntimeError(f"Frozen SHA-256 mismatch: {name}\nObserved: {observed}")

    table = parse_csv(raw[REGISTER_NAME])
    ids = [r.get("Paper_ID", "").strip() for r in table]
    if len(table) != N or len(set(ids)) != N or not all(ids):
        raise RuntimeError("Frozen register must contain exactly 485 unique nonempty IDs")
    if set(ids) & EXCLUDED:
        raise RuntimeError("Author-approved excluded study found in the release")
    needed = {"Paper_ID", "Year", "Principal_Method_Family", "Target_Primary"}
    if not needed.issubset(table[0]):
        raise KeyError(f"Frozen register lacks fields: {sorted(needed-set(table[0]))}")
    rows = []
    for r in table:
        family = r["Principal_Method_Family"].strip()
        if family not in FAMILY_COUNTS:
            raise ValueError(f"Unrecognized principal family, Paper_ID {r['Paper_ID']}: {family}")
        rows.append({
            "Paper_ID": r["Paper_ID"].strip(),
            "Period": period_for(r["Year"]),
            "Family": family,
            "Target": normal_target(r["Target_Primary"]),
        })

    check_counter("Period", Counter(r["Period"] for r in rows), PERIOD_COUNTS)
    check_counter("Method family", Counter(r["Family"] for r in rows), FAMILY_COUNTS)
    check_counter("Target", Counter(r["Target"] for r in rows), TARGET_COUNTS)

    # Independently crosscheck the precomputed marginal register released with
    # the frozen study-level CSV. No previous 492-era values are accepted.
    cat_rows = parse_csv(raw[CATEGORIES_NAME])
    if not cat_rows or not {"Field", "Category", "Count"}.issubset(cat_rows[0]):
        raise RuntimeError("Independent category-count release is missing standard columns")
    summary = defaultdict(dict)
    for r in cat_rows:
        if r["Field"] in ("Principal_Method_Family", "Target_Primary"):
            summary[r["Field"]][r["Category"]] = int(r["Count"])
    check_counter("Independent method-family marginal", summary["Principal_Method_Family"], FAMILY_COUNTS)
    # Compare raw target codes to the independent release: normalization is applied
    # to both, with duplicate normalized codes failing rather than overwriting.
    target_summary = {}
    for key, count in summary["Target_Primary"].items():
        code = normal_target(key)
        if code in target_summary:
            raise RuntimeError(f"Duplicate category aliases in frozen target marginal: {code}")
        target_summary[code] = count
    check_counter("Independent target marginal", target_summary, TARGET_COUNTS)

    pf = Counter((r["Period"], r["Family"]) for r in rows)
    ft = Counter((r["Family"], r["Target"]) for r in rows)
    for pair, counter in (("Period->Family", pf), ("Family->Target", ft)):
        if sum(counter.values()) != N:
            raise RuntimeError(f"{pair} flow conservation total != {N}")
    for fam, n in FAMILY_COUNTS.items():
        incoming = sum(pf[(p, fam)] for p in PERIOD_COUNTS)
        outgoing = sum(ft[(fam, t)] for t in TARGET_COUNTS)
        if incoming != n or outgoing != n:
            raise RuntimeError(f"Non-conserved intermediate node: {fam}")
    receipt = {
        "frozen_studies": N, "source": provenance, "sha256_register": REG_SHA,
        "sha256_category_counts": CAT_SHA, "author_excluded_ids_absent": True,
        "period_marginal_verified": True, "family_marginal_verified": True,
        "target_marginal_verified": True, "both_stages_conserve_485": True,
        "counted_links_period_family": len(pf), "counted_links_family_target": len(ft),
        "primary_metric_field_not_used": True,
    }
    return pf, ft, receipt


def color_rgba(value, alpha):
    h = value.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def make_spans(counts, gap):
    """Keep node proportions strictly proportional to integer study counts."""
    available = Y_TOP-Y_BOTTOM - gap*(len(counts)-1)
    if available <= 0:
        raise RuntimeError("Node gap exceeds diagram height")
    factor = available / sum(counts.values())
    top = Y_TOP
    spans = {}
    for key, n in counts.items():
        bottom = top - n*factor
        spans[key] = (bottom, top)
        top = bottom-gap
    return spans, factor


def shifted_label_positions(spans, min_gap, y_lo=Y_BOTTOM, y_hi=Y_TOP):
    """Prevent small-count labels from overprinting each other.

    Display positions move; ribbon endpoints and bar thicknesses NEVER move.
    """
    items = list(spans)
    anchors = [(spans[k][0]+spans[k][1])/2 for k in items]
    if (len(items)-1)*min_gap > (y_hi-y_lo):
        raise RuntimeError("Required label spacing exceeds available vertical domain")
    ys = []
    for index, anchor in enumerate(anchors):
        # Leave enough space below this label for every remaining label.
        lower = y_lo + (len(items)-1-index)*min_gap
        upper = y_hi-index*min_gap
        if ys:
            upper = min(upper, ys[-1]-min_gap)
        if upper+1e-9 < lower:
            raise RuntimeError("Cannot separate all label centers")
        ys.append(min(max(anchor, lower), upper))
    if any(ys[i]-ys[i+1] < min_gap-1e-6 for i in range(len(ys)-1)):
        raise RuntimeError("Overlapping labels after displacement")
    return dict(zip(items, ys))


def ribbons(ax, links, source_counts, target_counts, source_spans,
            target_spans, source_x, target_x, link_colors, alpha):
    """Curved, precisely area-proportional Sankey flows (cubic Bézier edges)."""
    src_factor = (source_spans[next(iter(source_counts))][1] -
                  source_spans[next(iter(source_counts))][0]) / source_counts[next(iter(source_counts))]
    tgt_factor = (target_spans[next(iter(target_counts))][1] -
                  target_spans[next(iter(target_counts))][0]) / target_counts[next(iter(target_counts))]
    # Spacings differ by stage; unequal source/target ribbon widths would appear
    # to create/destroy flow area. Convert to a shared link thickness factor.
    # We use the *smaller* of the two stage factors. Ribbons are anchored at the
    # source node and target node, leaving a thin unused side-edge for gap effects.
    source_offset = {name: source_spans[name][1] for name in source_counts}
    target_offset = {name: target_spans[name][1] for name in target_counts}
    for s in source_counts:
        for t in target_counts:
            n = int(links.get((s,t), 0))
            if n <= 0:
                continue
            sh = n*src_factor
            th = n*tgt_factor
            yt_s, yb_s = source_offset[s], source_offset[s]-sh
            yt_t, yb_t = target_offset[t], target_offset[t]-th
            source_offset[s] -= sh
            target_offset[t] -= th
            sx, tx = source_x + NODE_W/2, target_x-NODE_W/2
            span = tx-sx
            c1, c2 = sx+span*0.46, tx-span*0.46
            verts = [
                (sx, yt_s), (c1, yt_s), (c2, yt_t), (tx, yt_t),
                (tx, yb_t), (c2, yb_t), (c1, yb_s), (sx, yb_s), (sx, yt_s),
            ]
            codes = [MplPath.MOVETO] + [MplPath.CURVE4]*3 + [MplPath.LINETO] + \
                    [MplPath.CURVE4]*3 + [MplPath.CLOSEPOLY]
            patch = PathPatch(MplPath(verts, codes), facecolor=color_rgba(link_colors[t] if t in link_colors else link_colors[s], alpha),
                              edgecolor="none", zorder=2)
            ax.add_patch(patch)
    for key in source_counts:
        if abs(source_offset[key] - source_spans[key][0]) > 1e-7:
            raise AssertionError(f"Source allocations not conserved: {key}")
    for key in target_counts:
        if abs(target_offset[key] - target_spans[key][0]) > 1e-7:
            raise AssertionError(f"Target allocations not conserved: {key}")


def draw(pf, ft, destination, dpi):
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
        "font.size": 13,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=FIGSIZE, facecolor=BACKGROUND)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.axis("off")

    p_span,_ = make_spans(PERIOD_COUNTS, STAGE_GAPS[0])
    f_span,_ = make_spans(FAMILY_COUNTS, STAGE_GAPS[1])
    t_span,_ = make_spans(TARGET_COUNTS, STAGE_GAPS[2])

    # Same family-coloured, translucent ribbons as the 492-study predecessor.
    ribbons(ax, pf, PERIOD_COUNTS, FAMILY_COUNTS, p_span, f_span,
            X_PERIOD, X_FAMILY, FAMILY_COLORS, 0.34)
    ribbons(ax, ft, FAMILY_COUNTS, TARGET_COUNTS, f_span, t_span,
            X_FAMILY, X_TARGET, FAMILY_COLORS, 0.39)

    for xpos, spans, palette in (
        (X_PERIOD, p_span, PERIOD_COLORS),
        (X_FAMILY, f_span, FAMILY_COLORS),
        (X_TARGET, t_span, TARGET_COLORS),
    ):
        for key, (bottom, top) in spans.items():
            ax.add_patch(Rectangle((xpos-NODE_W/2, bottom), NODE_W, top-bottom,
                                   facecolor=palette[key], edgecolor="#666666",
                                   linewidth=0.7, zorder=4))

    # Column headings retain the source figure's clear three-stage arrangement.
    for x, name in (
        (0.125, "Publication period"),
        (0.523, "Principal method family"),
        (0.846, "Primary forecasting target"),
    ):
        ax.text(x, .946, name, ha="center", va="center", fontsize=HEADING_FONT,
                fontweight="bold", color=MAIN_TEXT, zorder=8)

    # Label plates deliberately placed above ribbons; do not blur / rasterize.
    plate = dict(facecolor=(1,1,1,.92), edgecolor="none", pad=1.05)
    period_y = shifted_label_positions(p_span, min_gap=.093)
    for key, n in PERIOD_COUNTS.items():
        y = period_y[key]
        label = f"{key} ({n})"
        ax.text(X_PERIOD-.010, y, label, ha="right", va="center",
                fontsize=LABEL_FONT, color=MAIN_TEXT, zorder=8,
                bbox=plate, clip_on=False)
        midpoint = sum(p_span[key])/2
        if abs(y-midpoint)>.01:
            ax.plot([X_PERIOD-.005, X_PERIOD-.020], [midpoint, y],
                    color="#777777", linewidth=.48, zorder=6)

    family_y = shifted_label_positions(f_span, min_gap=.054)
    for key in FAMILY_COUNTS:
        midpoint = sum(f_span[key])/2
        y = family_y[key]
        label = FAMILY_DISPLAY[key]
        ax.text(X_FAMILY+.011, y, label, ha="left", va="center",
                fontsize=LABEL_FONT-.25, color=MAIN_TEXT, zorder=8,
                bbox=plate, clip_on=False)
        if abs(y-midpoint)>.010:
            ax.plot([X_FAMILY+.004, X_FAMILY+.010], [midpoint, y],
                    color="#717171", linewidth=.6, zorder=7)

    target_y = shifted_label_positions(t_span, min_gap=.070)
    for key in TARGET_COUNTS:
        midpoint = sum(t_span[key])/2
        y = target_y[key]
        ax.text(X_TARGET+.010, y, TARGET_DISPLAY[key], ha="left", va="center",
                fontsize=LABEL_FONT, color=MAIN_TEXT, zorder=8,
                bbox=plate, clip_on=False)
        if abs(y-midpoint)>.01:
            ax.plot([X_TARGET+.004, X_TARGET+.009], [midpoint, y],
                    color="#777777", linewidth=.58, zorder=7)

    ax.text(.500, .073,
            "Ribbon widths represent study counts; each stage conserves the frozen technical corpus (n = 485).",
            ha="center", va="center", fontsize=FOOTNOTE_FONT,
            color="#424242", zorder=9)

    destination.mkdir(parents=True, exist_ok=True)
    results = {}
    for ext in ("pdf", "svg", "png", "tiff"):
        target = destination / f"{STEM}.{ext}"
        kw = {"format": ext, "bbox_inches": "tight", "pad_inches": .045}
        if ext in ("png", "tiff"):
            kw["dpi"] = dpi
        if ext == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(target, **kw)
        results[ext] = target
    plt.close(fig)
    return results


def export(pf, ft, receipt, dest):
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{STEM}_Flow_Audit.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Stage", "Source", "Destination", "Count"])
        for p in PERIOD_COUNTS:
            for fam in FAMILY_COUNTS:
                n = pf.get((p,fam), 0)
                if n:
                    writer.writerow(["Period_to_Family",p,fam,n])
        for fam in FAMILY_COUNTS:
            for tgt in TARGET_COUNTS:
                n = ft.get((fam,tgt), 0)
                if n:
                    writer.writerow(["Family_to_Target",fam,tgt,n])
    for filename, left, right, values in (
        (f"{STEM}_Period_x_Family.csv", PERIOD_COUNTS, FAMILY_COUNTS, pf),
        (f"{STEM}_Family_x_Target.csv", FAMILY_COUNTS, TARGET_COUNTS, ft),
    ):
        with (dest / filename).open("w", encoding="utf-8-sig", newline="") as file:
            w=csv.writer(file)
            w.writerow(["Category", *right.keys(), "Row_Total"])
            for src in left:
                counts = [values.get((src,t),0) for t in right]
                w.writerow([src,*counts,sum(counts)])
            w.writerow(["Column_Total", *[sum(values.get((s,t),0) for s in left) for t in right],N])
    (dest / f"{STEM}_QA.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    tex = r'''\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{Figures_485/''' + STEM + r'''.pdf}
    \caption{Evolution of principal computational-intelligence method families
    and forecasting targets across publication periods in the frozen technical
    synthesis ($n=485$). Ribbon widths represent study counts. The three
    stages are publication period, mutually exclusive principal method family,
    and primary forecasting target. Flow counts are calculated from individual
    studies in the authenticated frozen register; each stage conserves 485
    studies. Node labels are displaced where necessary to keep rare categories
    legible, without changing proportional ribbons. Ribbons show adjacent-stage
    pairwise counts and should not be interpreted as individually identifiable
    three-stage trajectories. The 2026 publication data represent partial-year
    database coverage.}
    \label{fig:period-method-target-sankey}
\end{figure*}
'''
    (dest / f"{STEM}_LaTeX.tex").write_text(tex,encoding="utf-8")


def main():
    args=options()
    if args.dpi < 100:
        raise ValueError("DPI must be >= 100 (600 recommended)")
    pf,ft,receipt = read_and_verify(args)
    print("PASS | SHA-256, 485 unique studies, all three marginals, both-stage conservation")
    if args.check_only:
        print(json.dumps(receipt,indent=2,ensure_ascii=False))
        return
    files=draw(pf,ft,args.output_dir,args.dpi)
    export(pf,ft,receipt,args.output_dir)
    for name,path in files.items():
        print(f"{name.upper()}: {path.resolve()}")
    print("QA: ", (args.output_dir / f"{STEM}_QA.json").resolve())
    print("SOURCE FILES WERE NOT ALTERED.")


if __name__=="__main__":
    main()
