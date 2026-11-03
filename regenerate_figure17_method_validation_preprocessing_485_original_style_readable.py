#!/usr/bin/env python3
"""Figure 17 — ACME Phase A, methodological Sankey, final frozen n=485.

Restores the traditional three-column Sankey visual style used by the author:
principal method family -> validation design -> preprocessing boundary.
Text: serif, single-line labels with counts, no pointing arrows/leader lines.
Preserves all 11 principal method families (rather than collapsing them).

Everything numerical is read from the immutable 485-study, 51-field register.
Legacy 492/493-study workbooks, labels, edges, and Sankey files are NOT used.

Install: pip install matplotlib pillow

Run:
    python regenerate_figure17_method_validation_preprocessing_485_original_style_readable.py \\
        --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
        --output-dir Figures_485 --dpi 600

Or read the ZIP directly (without extracting it):
    python regenerate_figure17_method_validation_preprocessing_485_original_style_readable.py \\
        --archive PhaseA_FROZEN_485_Sync_Inputs.zip \\
        --output-dir Figures_485 --dpi 600

Exports vector PDF + SVG, 600-dpi PNG + LZW TIFF, edge/triple-flow audits,
category QA JSON and manuscript-ready LaTeX snippet.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle

STUDIES = 485
CSV_REGISTER = "Technical_Register_485_FROZEN.csv"
CSV_COUNTS = "Manuscript_Category_Counts_FROZEN.csv"
MANIFEST = "Final_Freeze_Manifest_v1.json"
SHA_REGISTER = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
SHA_COUNTS = "3d8e77e50cf6565351aa1ebd3b35aa26e61f2378b8731a348323a71415e4c1b8"
EXCLUDED = {"P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"}
BASENAME = "Figure17_Method_Validation_Preprocessing_485_Original_Style_Readable"

# The order and palette follow the updated original-style chart. In this
# 485-study figure the additional statistical/econometric family MUST remain.
METHOD_COUNTS = {
    "Deep-learning models": 114,
    "Hybrid deep-learning models": 109,
    "Sentiment/NLP-driven models": 77,
    "Transformer/attention-based models": 68,
    "Metaheuristic-optimized models": 51,
    "Ensemble/tree-based machine learning": 32,
    "Graph-based models": 16,
    "Multimodal-fusion models": 12,
    "Other/unclear": 3,
    "ANN/neuro-fuzzy models": 2,
    "Statistical/econometric models": 1,
}
VALIDATION_COUNTS = {
    "Unclear": 398,
    "Temporally ordered": 81,
    "Random/shuffled": 6,
}
PREPROCESSING_COUNTS = {
    "Unclear": 447,
    "Training only": 21,
    "Full dataset": 17,
}
assert all(sum(x.values()) == STUDIES for x in
           (METHOD_COUNTS, VALIDATION_COUNTS, PREPROCESSING_COUNTS))

# These colours intentionally preserve the appearance of the Phase-A figure.
METHOD_COLORS = {
    "Deep-learning models": "#1F77B4",
    "Hybrid deep-learning models": "#AEC7E8",
    "Sentiment/NLP-driven models": "#FFBB78",
    "Transformer/attention-based models": "#98DF8A",
    "Metaheuristic-optimized models": "#FF9896",
    "Ensemble/tree-based machine learning": "#C5B0D5",
    "Graph-based models": "#8C564B",
    "Multimodal-fusion models": "#E377C2",
    "Other/unclear": "#7F7F7F",
    "ANN/neuro-fuzzy models": "#BCBD22",
    "Statistical/econometric models": "#17BECF",
}
VALIDATION_COLORS = {
    "Unclear": "#1F77B4", "Temporally ordered": "#AEC7E8",
    "Random/shuffled": "#FFBB78",
}
PREPROCESSING_COLORS = {
    "Unclear": "#1F77B4", "Training only": "#AEC7E8",
    "Full dataset": "#FFBB78",
}

# Abbreviations change only the displayed TEXT, not the frozen category codes.
METHOD_DISPLAY = {
    "Deep-learning models": "Deep learning",
    "Hybrid deep-learning models": "Hybrid DL",
    "Sentiment/NLP-driven models": "Sentiment/NLP",
    "Transformer/attention-based models": "Transformer/attention",
    "Metaheuristic-optimized models": "Metaheuristic",
    "Ensemble/tree-based machine learning": "Ensemble/tree ML",
    "Graph-based models": "Graph-based models",
    "Multimodal-fusion models": "Multimodal-fusion",
    "Other/unclear": "Other/unclear",
    "ANN/neuro-fuzzy models": "ANN/neuro-fuzzy",
    "Statistical/econometric models": "Statistical/econometric",
}
VALIDATION_DISPLAY = {
    "Unclear": "Unclear", "Temporally ordered": "Temporally ordered",
    "Random/shuffled": "Random/shuffled",
}
PREPROCESSING_DISPLAY = {
    "Unclear": "Unclear", "Training only": "Training only",
    "Full dataset": "Full dataset",
}

# Compact, publication-friendly proportions. Text sizes are intentionally
# larger than the Phase-A preview; preserve FIGSIZE:font ratio in LaTeX.
FIGSIZE = (11.7, 7.65)
X_METHOD, X_VALIDATION, X_PREPROCESS = 0.270, 0.563, 0.840
NODE_WIDTH = 0.012
TOP, BOTTOM = 0.845, 0.158
GAPS = (0.0065, 0.016, 0.024)
FONT_FAMILY = "serif"
FONT_PT = 12.9
HEADING_PT = 15.2
TITLE_PT = 15.5
NOTE_PT = 10.4
TEXT_COLOR = "#292929"


def options():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--archive", type=Path, default=None,
                   help="Use PhaseA_FROZEN_485_Sync_Inputs.zip instead of --frozen-dir")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--check-only", action="store_true",
                   help="Run all source/count/link verifications without exporting")
    return p.parse_args()


def load_source(args):
    names = (CSV_REGISTER, CSV_COUNTS, MANIFEST)
    if args.archive is None:
        return {n: (args.frozen_dir / n).read_bytes() for n in names}, str(args.frozen_dir)
    with zipfile.ZipFile(args.archive) as z:
        members = {}
        for member in z.namelist():
            if member.endswith("/"):
                continue
            base = Path(member).name
            if base in members:
                raise ValueError(f"Duplicate filename inside frozen archive: {base}")
            members[base] = member
        if not set(names).issubset(members):
            raise FileNotFoundError(f"Frozen archive missing: {set(names)-set(members)}")
        return {n: z.read(members[n]) for n in names}, str(args.archive)


def csv_rows(blob):
    return list(csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))))


def verify_count(label, found, expected):
    actual = dict(found)
    if actual != expected:
        detail = [f"{k}: expected={n}, found={actual.get(k, 0)}"
                  for k, n in expected.items() if actual.get(k, 0) != n]
        detail.extend(f"Unexpected {k}: {n}" for k, n in actual.items() if k not in expected)
        raise RuntimeError(f"{label} disagrees with frozen release:\n" + "\n".join(detail))


def validation_code(row):
    name = row["Validation_Design"].strip()
    ordered = {"Chronological_Holdout", "Walk_Forward", "Rolling_Window",
               "Expanding_Window", "Blocked_CV"}
    if name in ordered:
        return "Temporally ordered"
    if name == "Random_Shuffled":
        return "Random/shuffled"
    if name == "Unclear":
        return "Unclear"
    raise ValueError(f"Unrecognized frozen Validation_Design: {name}")


def preprocessing_code(row):
    code = row["Preprocessing_Boundary"].strip()
    return {"Unclear": "Unclear", "Training_Only": "Training only",
            "Full_Dataset": "Full dataset"}[code]


def load_and_validate(args):
    raw, source = load_source(args)
    manifest = json.loads(raw[MANIFEST].decode("utf-8-sig"))
    if manifest.get("final_corpus_frozen") is not True or manifest.get("retained_studies") != STUDIES:
        raise RuntimeError("This is not the approved immutable frozen 485-study register")
    for filename, required_hash in ((CSV_REGISTER, SHA_REGISTER), (CSV_COUNTS, SHA_COUNTS)):
        observed = hashlib.sha256(raw[filename]).hexdigest()
        if observed != required_hash or manifest.get("output_sha256", {}).get(filename) != observed:
            raise RuntimeError(f"SHA256 check failed for {filename}: {observed}")

    data = csv_rows(raw[CSV_REGISTER])
    if len(data) != STUDIES or len({r["Paper_ID"] for r in data}) != STUDIES:
        raise RuntimeError("Expected 485 unique Paper_ID values")
    if any(not r["Paper_ID"].strip() for r in data):
        raise RuntimeError("Empty study ID in frozen register")
    if set(r["Paper_ID"] for r in data) & EXCLUDED:
        raise RuntimeError("Author-approved excluded Paper_ID detected")

    required_cols = {"Paper_ID", "Principal_Method_Family", "Validation_Design",
                     "Validation_Status", "Preprocessing_Boundary"}
    if not required_cols.issubset(data[0]):
        raise KeyError(f"Missing frozen field(s): {sorted(required_cols-set(data[0]))}")

    rows = []
    for r in data:
        family = r["Principal_Method_Family"].strip()
        if family not in METHOD_COUNTS:
            raise ValueError(f"Unknown family {family}, study {r['Paper_ID']}")
        validation = validation_code(r)
        try:
            prep = preprocessing_code(r)
        except KeyError as error:
            raise ValueError(f"Unrecognized preprocessing code in {r['Paper_ID']}: "
                             f"{r['Preprocessing_Boundary']!r}") from error
        # Independently verify coded status and design category. Some register
        # releases use 'Random or shuffled' instead of 'Random/shuffled'.
        status = " ".join(r["Validation_Status"].strip().lower().replace("/", " ").split())
        allowed = {
            "Temporally ordered": {"temporally ordered"},
            "Random/shuffled": {"random shuffled", "random or shuffled"},
            "Unclear": {"unclear"},
        }[validation]
        if status not in allowed:
            raise RuntimeError(f"Validation_Status/design mismatch for {r['Paper_ID']}: "
                               f"{r['Validation_Status']!r} vs {r['Validation_Design']!r}")
        rows.append({"Paper_ID": r["Paper_ID"], "Family": family,
                     "Validation": validation, "Preprocessing": prep})

    verify_count("Method family", Counter(r["Family"] for r in rows), METHOD_COUNTS)
    verify_count("Validation", Counter(r["Validation"] for r in rows), VALIDATION_COUNTS)
    verify_count("Preprocessing", Counter(r["Preprocessing"] for r in rows), PREPROCESSING_COUNTS)

    # Independent cross-check against the frozen category-count file.
    frozen_categories = csv_rows(raw[CSV_COUNTS])
    summary = defaultdict(dict)
    for r in frozen_categories:
        if r["Field"] in {"Principal_Method_Family", "Preprocessing_Boundary",
                          "Validation_Status"}:
            summary[r["Field"]][r["Category"]] = int(r["Count"])
    verify_count("Independent method-family marginal", summary["Principal_Method_Family"], METHOD_COUNTS)
    raw_prep = {"Unclear": 447, "Training_Only": 21, "Full_Dataset": 17}
    verify_count("Independent preprocessing marginal", summary["Preprocessing_Boundary"], raw_prep)
    # Validate design-based and status-based methodological categories.
    status_normalized = Counter()
    for key, count in summary["Validation_Status"].items():
        value = " ".join(key.strip().lower().replace("/", " ").split())
        if value == "temporally ordered": k = "Temporally ordered"
        elif value in {"random shuffled", "random or shuffled"}: k = "Random/shuffled"
        elif value == "unclear": k = "Unclear"
        else: raise RuntimeError(f"Unexpected category in validation summary: {key}")
        status_normalized[k] += count
    verify_count("Independent validation marginal", status_normalized, VALIDATION_COUNTS)

    fm = Counter((r["Family"], r["Validation"]) for r in rows)
    vp = Counter((r["Validation"], r["Preprocessing"]) for r in rows)
    fvp = Counter((r["Family"], r["Validation"], r["Preprocessing"]) for r in rows)
    for name, links in (("Family->Validation", fm),
                        ("Validation->Preprocessing", vp), ("Three-way", fvp)):
        if sum(links.values()) != STUDIES:
            raise RuntimeError(f"{name} flows do not conserve 485 studies")
    for family in METHOD_COUNTS:
        if sum(fm.get((family, v), 0) for v in VALIDATION_COUNTS) != METHOD_COUNTS[family]:
            raise RuntimeError(f"Outflow mismatch for family {family}")
    for val in VALIDATION_COUNTS:
        inbound = sum(fm.get((f, val), 0) for f in METHOD_COUNTS)
        outbound = sum(vp.get((val, p), 0) for p in PREPROCESSING_COUNTS)
        if inbound != VALIDATION_COUNTS[val] or outbound != VALIDATION_COUNTS[val]:
            raise RuntimeError(f"Middle-stage conservation failed for {val}")
    for p in PREPROCESSING_COUNTS:
        if sum(vp.get((v, p), 0) for v in VALIDATION_COUNTS) != PREPROCESSING_COUNTS[p]:
            raise RuntimeError(f"Preprocessing category conservation failed for {p}")
    return fm, vp, fvp, source


def make_spans(category_counts, gap):
    available = TOP - BOTTOM - gap * (len(category_counts)-1)
    if available <= 0:
        raise ValueError("Negative height remaining after node gaps")
    factor = available / sum(category_counts.values())
    top = TOP
    spans = {}
    for key, n in category_counts.items():
        bottom = top - n*factor
        spans[key] = (bottom, top)
        top = bottom-gap
    return spans


def avoid_overlap(spans, min_gap, low=BOTTOM, high=TOP):
    """Move text anchors only: node and link positions are not modified."""
    items = list(spans)
    anchors = [(spans[k][0]+spans[k][1])/2 for k in items]
    if min_gap*(len(items)-1) > high-low:
        raise ValueError("Text rows cannot fit into drawing region")
    # Guarantee each label receives its own vertical allocation.
    values = []
    for i, anchor in enumerate(anchors):
        lo = low + (len(items)-1-i)*min_gap
        hi = high-i*min_gap
        if values:
            hi = min(hi, values[-1]-min_gap)
        values.append(max(lo, min(anchor, hi)))
    for i in range(1, len(values)):
        if values[i-1]-values[i] < min_gap - 1e-7:
            raise RuntimeError("Label collision")
    return dict(zip(items, values))


def rgb(hexcolor, alpha):
    value = hexcolor.lstrip("#")
    return tuple(int(value[i:i+2], 16)/255 for i in (0, 2, 4)) + (alpha,)


def flow_ribbons(ax, edges, sources, destinations, srcspans, dstspans,
                 source_x, target_x, palette, alpha):
    """Ribbons have exact study-proportional endpoints; no arrows/leader lines."""
    # The destination factor can differ because its node padding differs.
    tgt_factor = (sum(hi-lo for lo,hi in dstspans.values())) / STUDIES
    src_factor = (sum(hi-lo for lo,hi in srcspans.values())) / STUDIES
    source_cursor = {k: srcspans[k][1] for k in sources}
    target_cursor = {k: dstspans[k][1] for k in destinations}
    for sk in sources:
        for tk in destinations:
            count = int(edges.get((sk, tk), 0))
            if count <= 0:
                continue
            sh, th = count*src_factor, count*tgt_factor
            top_s, bot_s = source_cursor[sk], source_cursor[sk]-sh
            top_t, bot_t = target_cursor[tk], target_cursor[tk]-th
            source_cursor[sk] -= sh
            target_cursor[tk] -= th
            sx = source_x + NODE_WIDTH/2
            tx = target_x - NODE_WIDTH/2
            bend = (tx-sx)*0.43
            path = MplPath(
                [(sx, top_s), (sx+bend, top_s), (tx-bend, top_t), (tx, top_t),
                 (tx, bot_t), (tx-bend, bot_t), (sx+bend, bot_s), (sx, bot_s),
                 (sx, top_s)],
                [MplPath.MOVETO] + [MplPath.CURVE4]*3 + [MplPath.LINETO] +
                [MplPath.CURVE4]*3 + [MplPath.CLOSEPOLY]
            )
            col = palette[sk]
            ax.add_patch(PathPatch(path, facecolor=rgb(col, alpha), edgecolor="none", zorder=2))
    for key in sources:
        if abs(source_cursor[key]-srcspans[key][0]) > 1e-8:
            raise RuntimeError(f"Source ribbon height mismatch: {key}")
    for key in destinations:
        if abs(target_cursor[key]-dstspans[key][0]) > 1e-8:
            raise RuntimeError(f"Target ribbon height mismatch: {key}")


def draw(fm, vp, output_dir, dpi):
    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "font.size": FONT_PT,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=FIGSIZE, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fam_spans = make_spans(METHOD_COUNTS, GAPS[0])
    val_spans = make_spans(VALIDATION_COUNTS, GAPS[1])
    pre_spans = make_spans(PREPROCESSING_COUNTS, GAPS[2])

    # First-stage ribbon colour follows its originating method family.
    flow_ribbons(ax, fm, METHOD_COUNTS, VALIDATION_COUNTS,
                 fam_spans, val_spans, X_METHOD, X_VALIDATION,
                 METHOD_COLORS, 0.36)
    # Second-stage ribbon colour follows the validation-design category.
    flow_ribbons(ax, vp, VALIDATION_COUNTS, PREPROCESSING_COUNTS,
                 val_spans, pre_spans, X_VALIDATION, X_PREPROCESS,
                 VALIDATION_COLORS, 0.40)

    for x, spans, palette in (
        (X_METHOD, fam_spans, METHOD_COLORS),
        (X_VALIDATION, val_spans, VALIDATION_COLORS),
        (X_PREPROCESS, pre_spans, PREPROCESSING_COLORS),
    ):
        for key, (bottom, top) in spans.items():
            ax.add_patch(Rectangle((x-NODE_WIDTH/2, bottom), NODE_WIDTH, top-bottom,
                                   facecolor=palette[key], linewidth=0.7,
                                   edgecolor="#6b6b6b", zorder=5))

    ax.text(0.50, 0.974, "Method family → validation → preprocessing (n = 485)",
            fontsize=TITLE_PT, fontweight="bold", ha="center", va="center",
            color="#242424", zorder=10)
    for x, title in ((0.145, "Principal method family"),
                     (0.565, "Validation design"),
                     (0.885, "Preprocessing boundary")):
        ax.text(x, 0.927, title, fontsize=HEADING_PT, fontweight="bold",
                ha="center", va="center", color="#242424", zorder=10)

    # Exactly the last Fig. 16 requested typography: serif, one line, inline n.
    # No connector/leader lines and no pointing arrows.
    methods_y = avoid_overlap(fam_spans, min_gap=0.046,
                              low=BOTTOM-0.017, high=TOP+0.011)
    validation_y = avoid_overlap(val_spans, min_gap=0.066,
                                 low=BOTTOM, high=TOP)
    preprocessing_y = avoid_overlap(pre_spans, min_gap=0.063,
                                    low=BOTTOM, high=TOP)

    for key, n in METHOD_COUNTS.items():
        ax.text(X_METHOD-0.011, methods_y[key],
                f"{METHOD_DISPLAY[key]} ({n})", fontsize=FONT_PT,
                ha="right", va="center", color=TEXT_COLOR, zorder=10)
    for key, n in VALIDATION_COUNTS.items():
        ax.text(X_VALIDATION+0.015, validation_y[key],
                f"{VALIDATION_DISPLAY[key]} ({n})", fontsize=FONT_PT,
                ha="left", va="center", color=TEXT_COLOR, zorder=10,
                bbox={"facecolor": (1, 1, 1, 0.35), "edgecolor": "none", "pad": 0.35})
    for key, n in PREPROCESSING_COUNTS.items():
        ax.text(X_PREPROCESS+0.012, preprocessing_y[key],
                f"{PREPROCESSING_DISPLAY[key]} ({n})", fontsize=FONT_PT,
                ha="left", va="center", color=TEXT_COLOR, zorder=10)

    # The footnote is supplementary: the explanatory caption is the authority.
    ax.text(0.50, 0.055,
            "Ribbon widths indicate study counts; each stage conserves n = 485.",
            fontsize=NOTE_PT, ha="center", va="center", color="#6b6b6b")

    output_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for ext in ("pdf", "svg", "png", "tiff"):
        path = output_dir / f"{BASENAME}.{ext}"
        kw = {"format": ext, "bbox_inches": "tight", "pad_inches": 0.08}
        if ext in ("png", "tiff"):
            kw["dpi"] = dpi
        if ext == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(path, **kw)
        result[ext] = path
    plt.close(fig)
    return result


def export_audits(fm, vp, fvp, source, directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"{BASENAME}_Flows.csv").open("w", encoding="utf-8-sig", newline="") as file:
        w = csv.writer(file)
        w.writerow(["Stage", "Source", "Destination", "Study_Count"])
        for family in METHOD_COUNTS:
            for validation in VALIDATION_COUNTS:
                count = fm.get((family, validation), 0)
                if count:
                    w.writerow(["Method_to_Validation", family, validation, count])
        for validation in VALIDATION_COUNTS:
            for preprocessing in PREPROCESSING_COUNTS:
                count = vp.get((validation, preprocessing), 0)
                if count:
                    w.writerow(["Validation_to_Preprocessing", validation, preprocessing, count])
    with (directory / f"{BASENAME}_Three_Way_Audit.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        w = csv.writer(file)
        w.writerow(["Method_Family", "Validation", "Preprocessing", "Studies"])
        for triple, n in sorted(fvp.items()):
            w.writerow([*triple, n])
    metadata = {
        "frozen_source": source, "N": STUDIES,
        "sha256_register": SHA_REGISTER, "sha256_category_counts": SHA_COUNTS,
        "method_marginals": METHOD_COUNTS,
        "validation_marginals": VALIDATION_COUNTS,
        "preprocessing_marginals": PREPROCESSING_COUNTS,
        "sum_method_validation_edges": sum(fm.values()),
        "sum_validation_preprocessing_edges": sum(vp.values()),
        "sum_three_way_counts": sum(fvp.values()),
        "phase_a_485_verified": True,
        "unknown_means_evidence_not_recoverable": True,
        "ribbon_coloring": {
            "first_stage": "originating principal method family",
            "second_stage": "validation design"
        },
        "no_pointing_arrows": True,
    }
    (directory / f"{BASENAME}_QA.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    caption = r"""\begin{figure*}[htbp]
    \centering
    \includegraphics[width=\textwidth]{Figures_485/Figure17_Method_Validation_Preprocessing_485_Original_Style_Readable.pdf}
    \caption{Study-level distribution of principal computational-intelligence
    method families across validation design and preprocessing boundary in the
    frozen technical-synthesis subset ($n=485$). Node heights and ribbon widths
    represent numbers of studies. Each study contributes one mutually exclusive
    method-family category, one validation category and one preprocessing
    category; consequently, each transition conserves the 485-study cohort.
    The 'Unclear' categories indicate that the relevant methodological
    information could not be verified from available reporting and should not
    be interpreted as evidence that a practice was absent.}
    \label{fig:method-validation-preprocessing}
\end{figure*}
\FloatBarrier
"""
    (directory / f"{BASENAME}_LaTeX.tex").write_text(caption, encoding="utf-8")


def main():
    args = options()
    if args.dpi < 100:
        raise ValueError("Use --dpi 600 for publication figures")
    fm, vp, fvp, source = load_and_validate(args)
    print(f"PASS: verified all SHA-256, frozen n={STUDIES}, category and flow checks")
    print("Method totals:", METHOD_COUNTS)
    print("Validation totals:", VALIDATION_COUNTS)
    print("Preprocessing totals:", PREPROCESSING_COUNTS)
    if args.check_only:
        return
    files = draw(fm, vp, args.output_dir, args.dpi)
    export_audits(fm, vp, fvp, source, args.output_dir)
    for fmt, path in files.items():
        print(f"{fmt.upper()}: {path.resolve()}")
    print("CSV, QA JSON, and LaTeX files also exported to", args.output_dir.resolve())


if __name__ == "__main__":
    main()
