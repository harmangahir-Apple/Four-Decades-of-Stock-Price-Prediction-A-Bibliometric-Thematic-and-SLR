#!/usr/bin/env python3
"""Recreate the ACME principal-method-family figure in its ORIGINAL visual style.

The 492-study predecessor used light-to-deep-blue, serif, horizontal bars.
This revised version retains that visual language and improves readability at
journal double-column width, while validating the Phase A FROZEN n=485 data.

SOURCE (no legacy 492/491/493 workbook):
  PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485/
    Technical_Register_485_FROZEN.csv
    Manuscript_Category_Counts_FROZEN.csv
    Final_Freeze_Manifest_v1.json

Run in WSL:
  python regenerate_method_family_485_original_style_readable.py \\
    --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
    --output-dir Figures_485 --dpi 600

Or read a ZIP containing these three files:
  python regenerate_method_family_485_original_style_readable.py \\
    --archive PhaseA_FROZEN_485_Sync_Inputs.zip --output-dir Figures_485

For layout-only review if source files are not present:
  python regenerate_method_family_485_original_style_readable.py \\
    --preview --output-dir Preview_485

The --preview flag uses explicitly locked published counts from the handoff;
it is NOT a substitute for source SHA-256 validation of an authenticated run.

Outputs: vector PDF and SVG, 600-dpi PNG and TIFF, verified counts CSV,
         LaTeX inclusion snippet, source receipt and figure-shape check.

Dependencies: matplotlib, numpy, Pillow (for LZW TIFF export).
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

N = 485
NAME = "Figure_Method_Family_Distribution_485_Original_Style_Readable"
REGISTER_NAME = "Technical_Register_485_FROZEN.csv"
COUNTS_NAME = "Manuscript_Category_Counts_FROZEN.csv"
MANIFEST_NAME = "Final_Freeze_Manifest_v1.json"
EXPECTED_REGISTER_SHA256 = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
EXPECTED_COUNTS_SHA256 = "3d8e77e50cf6565351aa1ebd3b35aa26e61f2378b8731a348323a71415e4c1b8"
EXCLUDED_IDS = frozenset({"P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"})

# Ordered as in the author-designed 492-study predecessor. Keep ALL 11 categories.
# The values below are fail-closed QA expectations, not the source of the figure
# in normal validated mode. Generated numbers are recomputed from per-study rows.
FAMILIES = [
    ("Deep-learning models", 114),
    ("Hybrid deep-learning models", 109),
    ("Sentiment/NLP-driven models", 77),
    ("Transformer/attention-based models", 68),
    ("Metaheuristic-optimized models", 51),
    ("Ensemble/tree-based machine learning", 32),
    ("Graph-based models", 16),
    ("Multimodal-fusion models", 12),
    ("Other/unclear", 3),
    ("ANN/neuro-fuzzy models", 2),
    ("Statistical/econometric models", 1),
]

# Match original gradient (pale blue at top, saturated medium blue at bottom).
TOP_BLUE = "#DFEBF2"
BOTTOM_BLUE = "#468FBE"
BAR_EDGE = "#6B8799"
TEXT = "#202020"
GRID = "#CDD3D9"


def options():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--archive", type=Path, default=None,
                   help="ZIP containing the exact frozen register, counts and manifest")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--preview", action="store_true", help="Layout preview ONLY using locked marginal counts")
    p.add_argument("--no-title", action="store_true", help="Omit plot title when LaTeX caption suffices")
    return p.parse_args()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_raw(args):
    needed = (REGISTER_NAME, COUNTS_NAME, MANIFEST_NAME)
    if args.archive:
        with zipfile.ZipFile(args.archive) as z:
            by_name = {}
            for entry in z.namelist():
                if entry.endswith("/"):
                    continue
                basename = Path(entry).name
                if basename in by_name:
                    raise RuntimeError("Duplicate archive basename: " + basename)
                by_name[basename] = entry
            missing = set(needed) - set(by_name)
            if missing:
                raise FileNotFoundError("Required frozen archive entries missing: " + str(missing))
            raw = {name: z.read(by_name[name]) for name in needed}
        return raw, str(args.archive.resolve())
    raw = {name: (args.frozen_dir / name).read_bytes() for name in needed}
    return raw, str(args.frozen_dir.resolve())


def csv_rows(blob: bytes):
    return list(csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))))


def validate_frozen(args):
    raw, path = load_raw(args)
    manifest = json.loads(raw[MANIFEST_NAME].decode("utf-8-sig"))
    if manifest.get("final_corpus_frozen") is not True or manifest.get("retained_studies") != N:
        raise RuntimeError("This is not the author-approved frozen 485-study release")
    declared = manifest.get("output_sha256", {})
    for name, expected in ((REGISTER_NAME, EXPECTED_REGISTER_SHA256),
                           (COUNTS_NAME, EXPECTED_COUNTS_SHA256)):
        if declared.get(name) != expected or sha256(raw[name]) != expected:
            raise RuntimeError("Fail-closed frozen-source SHA-256 mismatch: " + name)

    data = csv_rows(raw[REGISTER_NAME])
    if len(data) != N or len({r.get("Paper_ID", "") for r in data}) != N or any(not r.get("Paper_ID") for r in data):
        raise RuntimeError("485 unique study IDs required")
    if EXCLUDED_IDS.intersection({r["Paper_ID"] for r in data}):
        raise RuntimeError("Author-excluded study detected in frozen register")
    if any("Principal_Method_Family" not in r for r in data):
        raise KeyError("Principal_Method_Family field unavailable")

    observed = Counter(r["Principal_Method_Family"].strip() for r in data)
    expected = dict(FAMILIES)
    if observed != expected:
        unexpected = dict(sorted((set(observed.items()) ^ set(expected.items()))))
        raise RuntimeError("Method-family counts differ from frozen handoff. Differences: " + str(unexpected))

    marginals = csv_rows(raw[COUNTS_NAME])
    if not marginals or not {"Field", "Category", "Count"}.issubset(marginals[0]):
        raise RuntimeError("Category-counts source lacks expected columns")
    table = {r["Category"].strip(): int(r["Count"])
             for r in marginals if r["Field"].strip() == "Principal_Method_Family"}
    if table != expected:
        raise RuntimeError("Frozen independent category-count table does not reconcile")

    receipt = {"plot_provenance": "sha256-verified-frozen-register",
               "frozen_source": path,
               "n": N,
               "register_sha256": sha256(raw[REGISTER_NAME]),
               "category_counts_sha256": sha256(raw[COUNTS_NAME]),
               "manifest_final_corpus_frozen": True,
               "independent_category_marginal_reconciles": True}
    return observed, receipt


def rgb(hexcolor):
    return np.array([int(hexcolor[i:i+2], 16) for i in (1, 3, 5)], dtype=float)/255


def colors(n):
    start, end = rgb(TOP_BLUE), rgb(BOTTOM_BLUE)
    return [tuple(start*(1-t) + end*t) for t in np.linspace(0, 1, n)]


def plot(counts, path: Path, dpi: int, title: bool):
    # Relatively SMALL physical canvas: 11–12 pt source labels stay ~10 pt
    # after insertion at Springer two-column \textwidth. Avoid giant whitespace.
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
        "font.size": 11.4,
        "axes.titlesize": 12.6,
        "axes.labelsize": 11.5,
        "xtick.labelsize": 10.8,
        "ytick.labelsize": 11.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": "#656565",
        "axes.linewidth": 0.7,
    })
    names = [key for key, _ in FAMILIES]
    values = [int(counts[name]) for name in names]
    y = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(8.0, 5.65))
    barset = ax.barh(y, values, height=0.78, color=colors(len(y)),
                     edgecolor=BAR_EDGE, linewidth=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=11.15, color=TEXT)
    ax.invert_yaxis()
    ax.set_xlim(0, 136)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.set_xlabel("Number of studies", fontsize=11.5, labelpad=8)
    ax.set_ylabel("Principal computational-intelligence method family",
                  fontsize=10.85, labelpad=15)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.tick_params(axis="x", length=3, width=0.75, pad=5, colors=TEXT)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=GRID, linestyle=(0, (2, 3)), linewidth=0.8)
    ax.yaxis.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#5C5C5C")

    for patch, n in zip(barset.patches, values):
        ax.text(patch.get_width()+1.1, patch.get_y()+patch.get_height()/2,
                f"{n} ({n / N * 100:.1f}%)", ha="left", va="center",
                fontsize=10.65, color=TEXT, clip_on=False)

    if title:
        ax.set_title("Distribution of the 485-study technical-synthesis subset across\n"
                     "principal computational-intelligence method families",
                     pad=15, fontsize=12.4, fontweight="normal", color="#111111")

    ax.text(0.996, 0.012, r"$n=485$", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=10.4, color="#343434")

    # Left margin accounts for longest category label, avoiding x-coordinate
    # collision in PDF / PNG when the figure is inserted at journal width.
    fig.subplots_adjust(left=.437, right=.965, top=.83 if title else .96, bottom=.14)
    path.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "svg", "png", "tiff"):
        kw = dict(format=extension, bbox_inches="tight", pad_inches=0.10)
        if extension in ("png", "tiff"):
            kw["dpi"] = dpi
        if extension == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(path / f"{NAME}.{extension}", **kw)
    plt.close(fig)


def outputs(outdir: Path, counts, receipt):
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / f"{NAME}_Verified_Counts.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Principal_Method_Family", "Studies", "Percentage_of_485"])
        for label, _ in FAMILIES:
            writer.writerow([label, counts[label], f"{counts[label]/N*100:.4f}"])
    (outdir / f"{NAME}_QA.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    latex = r"""\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{Figures_485/Figure_Method_Family_Distribution_485_Original_Style_Readable.pdf}
    \caption{Distribution of the frozen technical-synthesis subset ($n=485$)
    across mutually exclusive principal computational-intelligence method
    families. Deep-learning models were the largest category ($n=114$, 23.5\%),
    followed by hybrid deep-learning models ($n=109$, 22.5\%),
    sentiment/NLP-driven models ($n=77$, 15.9\%), and
    transformer/attention-based models ($n=68$, 14.0\%).
    Percentages are calculated relative to the 485-study subset; minor
    differences from 100\% may arise from rounding.}
    \label{fig:method-family-distribution}
\end{figure}
\FloatBarrier
"""
    (outdir / f"{NAME}_LaTeX.tex").write_text(latex, encoding="utf-8")


def main():
    args = options()
    if args.dpi < 100:
        raise ValueError("DPI should be >=100 (600 recommended)")
    if args.preview:
        # Uses handoff-approved margins for LAYOUT testing; it is not a
        # re-verification of the frozen register.
        distribution = dict(FAMILIES)
        receipt = {"plot_provenance": "PREVIEW_ONLY_FROM_LOCKED_COUNTS",
                   "n": N,
                   "sha256_verified": False,
                   "note": "Run without --preview against the immutable freeze for source verification."}
    else:
        distribution, receipt = validate_frozen(args)
    if sum(distribution.values()) != N:
        raise RuntimeError("Method families must be mutually exclusive and total 485")
    plot(distribution, args.output_dir, args.dpi, title=not args.no_title)
    outputs(args.output_dir, distribution, receipt)
    print("PASS — counts:", list(distribution.items()))
    print("PASS — total study count:", sum(distribution.values()))
    print("Source status:", receipt["plot_provenance"])
    print("Output folder:", args.output_dir.resolve())
    print("No original workbook or frozen register has been changed")


if __name__ == "__main__":
    main()
