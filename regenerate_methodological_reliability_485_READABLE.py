#!/usr/bin/env python3
"""Journal-readable recreation of the Phase A methodological-reliability figure.

Uses the immutable 485-study technical corpus and original three-panel lollipop
visual language, reorganized into a full-width vertical layout so labels remain
readable when the figure is scaled to journal page width.

Panels:
 A — Validation-design reporting: identified vs unclear + six design categories
 B — Ten explicitly documented methodological attributes
 C — Study-level leakage-signal status (NOT individual leakage mechanisms)

Important: "Chronological split" is a separately coded attribute (n=110) and
must NOT be interpreted as the number with temporally ordered validation (n=81).
"Unclear" indicates that evidence was not classifiable/recoverable, not that the
methodological practice was absent or safe.

Usage:
  python regenerate_methodological_reliability_485_READABLE.py \\
    --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
    --output-dir Figures_485 --dpi 600

  python regenerate_methodological_reliability_485_READABLE.py \\
    --archive PhaseA_FROZEN_485_Sync_Inputs.zip --output-dir Figures_485

Creates vector PDF and SVG; PNG and LZW TIFF at 600 dpi; QA CSV; LaTeX code.
Requires: matplotlib, numpy, Pillow (for TIFF).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Rectangle

STUDIES = 485
FILENAME = "Figure13_Methodological_Reliability_485_Journal_Readable"
REGISTER = "Technical_Register_485_FROZEN.csv"
MANIFEST = "Final_Freeze_Manifest_v1.json"
CATEGORY_COUNTS = "Manuscript_Category_Counts_FROZEN.csv"
REGISTER_HASH = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
CATEGORY_HASH = "3d8e77e50cf6565351aa1ebd3b35aa26e61f2378b8731a348323a71415e4c1b8"
EXCLUDED = {"P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"}

# Restrained original palette. Darker grey is used for legible status marks.
BLUE = "#3F83A6"
ORANGE = "#D99245"
GREEN = "#4F9A73"
RED = "#CB6C55"
PALE_GREY = "#B8BDC5"
STATUS_GREY = "#838D98"
BLACK = "#20252A"
GRID = "#DBDFE2"

PRACTICES = [
    ("Chronological split", "Chronological_Split", "Yes"),
    ("Non-stationarity acknowledged", "Nonstationarity_Acknowledged", "Yes"),
    ("Shock context mentioned", "Shock_Context_Mentioned", "Yes"),
    ("Statistical testing", "Statistical_Testing", "Yes"),
    ("Economic evaluation", "Economic_Evaluation", "Yes"),
    ("Shock-period evaluation", "Shock_Period_Evaluation", "Yes"),
    ("Transaction costs", "Transaction_Costs", "Yes"),
    ("Regime-specific evaluation", "Regime_Specific_Evaluation", "Yes"),
    ("Code available", "Code_Available", "Yes"),
    ("Data available", "Data_Available", "Yes"),
]
VALIDATION = [
    ("Chronological holdout", "Chronological_Holdout", 61),
    ("Walk-forward", "Walk_Forward", 11),
    ("Rolling window", "Rolling_Window", 6),
    ("Expanding window", "Expanding_Window", 2),
    ("Blocked cross-validation", "Blocked_CV", 1),
    ("Random or shuffled", "Random_Shuffled", 6),
]
RISK_STATUS = [
    ("At least one passage-verified\nsignal (High)",
     "At least one passage-verified signal", 32, RED),
    ("No explicit verified signal\nidentified (Low)",
     "No explicit passage-verified signal identified", 7, GREEN),
    ("Specific leakage mechanism\nnot classifiable (Unclear)",
     "Specific leakage mechanism not classifiable", 446, STATUS_GREY),
]
EXPECTED_PRACTICES = [110, 75, 58, 48, 37, 15, 14, 8, 7, 4]


def parse_arguments():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    source = p.add_mutually_exclusive_group()
    source.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    source.add_argument("--archive", type=Path, default=None,
                        help="ZIP containing the frozen manifest and data files")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--show", action="store_true")
    return p.parse_args()


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def read_inputs(args):
    needed = (REGISTER, MANIFEST, CATEGORY_COUNTS)
    if args.archive is not None:
        with zipfile.ZipFile(args.archive) as z:
            members = {}
            for n in z.namelist():
                if not n.endswith("/"):
                    base = Path(n).name
                    if base in members:
                        raise RuntimeError(f"Ambiguous archive basename: {base}")
                    members[base] = n
            missing = set(needed) - set(members)
            if missing:
                raise FileNotFoundError(f"Missing archive files: {sorted(missing)}")
            raw = {n: z.read(members[n]) for n in needed}
        provenance = str(args.archive)
    else:
        raw = {n: (args.frozen_dir / n).read_bytes() for n in needed}
        provenance = str(args.frozen_dir)

    manifest = json.loads(raw[MANIFEST].decode("utf-8-sig"))
    if manifest.get("retained_studies") != STUDIES or manifest.get("final_corpus_frozen") is not True:
        raise RuntimeError("Not the approved immutable 485-study release")
    if manifest.get("final_net_differences") != 50:
        raise RuntimeError("Unexpected frozen-release provenance")
    for name, pinned in [(REGISTER, REGISTER_HASH), (CATEGORY_COUNTS, CATEGORY_HASH)]:
        expected = manifest.get("output_sha256", {}).get(name)
        if expected != pinned or sha256(raw[name]) != pinned:
            raise RuntimeError(f"Frozen source SHA-256 mismatch: {name}")

    def as_rows(name):
        return list(csv.DictReader(io.StringIO(raw[name].decode("utf-8-sig"))))
    rows, category_rows = as_rows(REGISTER), as_rows(CATEGORY_COUNTS)
    if len(rows) != STUDIES or len({r.get("Paper_ID", "") for r in rows}) != STUDIES:
        raise RuntimeError("Frozen study population is not 485 unique IDs")
    if len(rows[0]) != 51:
        raise RuntimeError(f"Expected 51 frozen register fields, found {len(rows[0])}")
    ids = {r["Paper_ID"] for r in rows}
    if "" in ids or (EXCLUDED & ids):
        raise RuntimeError("Empty or author-excluded Paper_ID in technical register")
    needed_fields = ["Validation_Design", "Validation_Status", "Leakage_Risk",
                     "Leakage_Signal_Status", *[item[1] for item in PRACTICES]]
    for field in needed_fields:
        if field not in rows[0]:
            raise RuntimeError(f"Missing frozen field: {field}")
    return rows, category_rows, provenance


def counts_and_checks(rows, category_rows):
    validation = Counter(r["Validation_Design"] for r in rows)
    expected_val = {key: count for _, key, count in VALIDATION}
    expected_val["Unclear"] = 398
    if validation != expected_val:
        raise RuntimeError(f"Unexpected validation-design distribution: {validation}")
    identified = STUDIES - validation["Unclear"]
    if identified != 87:
        raise RuntimeError("Identifiable validation-design total differs from 87")
    practices = [(label, sum(r[field] == yes for r in rows))
                 for label, field, yes in PRACTICES]
    if [v for _, v in practices] != EXPECTED_PRACTICES:
        raise RuntimeError(f"Methodological attributes do not match frozen counts: {practices}")
    risks = Counter(r["Leakage_Risk"] for r in rows)
    if risks != Counter({"High": 32, "Low": 7, "Unclear": 446}):
        raise RuntimeError(f"Frozen leakage-risk count mismatch: {risks}")
    signals = Counter(r["Leakage_Signal_Status"] for r in rows)
    for _label, key, expected, _color in RISK_STATUS:
        if signals.get(key, 0) != expected:
            raise RuntimeError(f"Frozen leakage-signal count mismatch: {key}")
    if sum(signals.values()) != STUDIES:
        raise RuntimeError("Leakage-signal statuses do not form a 485-study partition")

    marginal = {(r["Field"], r["Category"]): int(r["Count"])
                for r in category_rows}
    for field in ("Validation_Status", "Leakage_Risk"):
        for key, n in Counter(r[field] for r in rows).items():
            if marginal.get((field, key)) != n:
                raise RuntimeError(f"Independent frozen marginal failed: {field}/{key}")
    return validation, identified, practices, signals


def configure_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
        "font.size": 13.2,
        "axes.titlesize": 16.4,
        "axes.labelsize": 13.2,
        "xtick.labelsize": 12.1,
        "ytick.labelsize": 13.3,
        "pdf.fonttype": 42,     # Embedded searchable fonts in vector PDF
        "ps.fonttype": 42,
        "svg.fonttype": "none", # Editable SVG text
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def lollipop(ax, labels, values, colors, *, maximum, tick, value_font=12.3, x_label=False):
    y = np.arange(len(values), dtype=float)
    ax.set_xlim(0, maximum)
    # Add vertical separation for two-line category labels in Panel C.
    ax.set_ylim(len(values)-0.25, -0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=13.1, linespacing=1.16)
    ax.xaxis.set_major_locator(MultipleLocator(tick))
    ax.xaxis.grid(True, linestyle=(0, (2.0, 3.5)), color=GRID,
                  alpha=.95, linewidth=.85)
    ax.set_axisbelow(True)
    for yi, n, color in zip(y, values, colors):
        ax.hlines(yi, 0, n, color=color, linewidth=2.8, zorder=3)
        ax.scatter(n, yi, s=65, facecolor=color, edgecolor="white",
                   linewidth=1.0, zorder=4)
        ax.annotate(f"{n} ({100*n/STUDIES:.1f}%)", xy=(n, yi),
                    xytext=(7, 0), textcoords="offset points",
                    ha="left", va="center", color=BLACK,
                    fontsize=value_font, fontweight="semibold",
                    annotation_clip=False, zorder=5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#666666")
    ax.spines["bottom"].set_linewidth(.85)
    ax.tick_params(axis="y", which="major", length=0, pad=11)
    ax.tick_params(axis="x", which="major", length=4, width=.7, pad=5)
    if x_label:
        ax.set_xlabel("Number of studies", fontsize=13.3, labelpad=8)


def draw_plot(validation, identified, practices, *, out_dir, dpi, show):
    configure_style()
    # Narrower and taller than the legacy landscape image: at LaTeX width=\textwidth
    # the fonts undergo much less downscaling, even in two-column journals.
    fig = plt.figure(figsize=(9.2, 10.2))
    x0, right = .421, .903
    width = right - x0

    # Three stacked FULL-WIDTH data panels, avoiding the two mini-plots that
    # caused tiny labels in the earlier landscape arrangement.
    fig.text(x0, .969, "A. Validation-design reporting", ha="left",
             va="top", fontsize=16.6, fontweight="bold", color=BLACK)

    summary = fig.add_axes([x0, .884, width, .059])
    summary.set_xlim(0, STUDIES)
    summary.set_ylim(0, 1)
    summary.add_patch(Rectangle((0, .43), identified, .45, color=BLUE, lw=0))
    summary.add_patch(Rectangle((identified, .43), validation["Unclear"], .45,
                                color=PALE_GREY, lw=0))
    # The 17.9% blue segment is physically too narrow for a long label.
    # Place only its count inside the bar; show the percentage below.
    summary.text(identified/2, .65, f"{identified}", ha="center", va="center",
                 color="white", fontsize=14.0, fontweight="bold")
    summary.text(identified + validation["Unclear"]/2, .65,
                 f"{validation['Unclear']} (82.1%)", ha="center", va="center",
                 color=BLACK, fontsize=13.1, fontweight="semibold")
    summary.text(0, .15, "Design identified (17.9%)", ha="left", va="center",
                 color=BLUE, fontsize=11.4, fontweight="semibold")
    summary.text(STUDIES, .15, "Unclear (82.1%)", ha="right", va="center",
                 color="#5D646C", fontsize=11.4)
    summary.set_axis_off()

    ax_a = fig.add_axes([x0, .698, width, .166])
    lollipop(ax_a, [label for label, _, _ in VALIDATION],
             [n for _, _, n in VALIDATION],
             [ORANGE if key == "Random_Shuffled" else BLUE
              for _, key, _ in VALIDATION], maximum=84, tick=10)

    fig.text(x0, .653, "B. Explicitly documented methodological attributes",
             ha="left", va="top", fontsize=16.6, fontweight="bold", color=BLACK)
    ax_b = fig.add_axes([x0, .294, width, .320])
    lollipop(ax_b, [label for label, _ in practices],
             [n for _, n in practices], [GREEN]*len(practices),
             maximum=146, tick=20)

    fig.text(x0, .253, "C. Study-level leakage-signal classification",
             ha="left", va="top", fontsize=16.6, fontweight="bold", color=BLACK)
    ax_c = fig.add_axes([x0, .075, width, .137])
    lollipop(ax_c, [label for label, _, _, _ in RISK_STATUS],
             [count for _, _, count, _ in RISK_STATUS],
             [color for _, _, _, color in RISK_STATUS],
             maximum=565, tick=100, value_font=12.5, x_label=True)

    # Interpretation and denominator are in the LaTeX caption; no small footer.

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for ext in ("pdf", "svg", "png", "tiff"):
        path = out_dir / f"{FILENAME}.{ext}"
        options = dict(format=ext, bbox_inches="tight", pad_inches=.09)
        if ext in ("png", "tiff"):
            options["dpi"] = dpi
        if ext == "tiff":
            options["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(path, **options)
        paths[ext] = path
    if show:
        plt.show()
    plt.close(fig)
    return paths


def save_summary(path, validation, identified, practices):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Panel", "Category", "Count", "Percentage_of_485", "Source_field"])
        for label, n in [("Design identified", identified),
                         ("Unclear", validation["Unclear"])]:
            writer.writerow(["A summary", label, n, f"{100*n/STUDIES:.4f}",
                             "Validation_Design"])
        for label, field, n in VALIDATION:
            writer.writerow(["A validation", label, n, f"{100*n/STUDIES:.4f}",
                             "Validation_Design"])
        for (label, field, _yes), (_label, n) in zip(PRACTICES, practices):
            writer.writerow(["B methodology", label, n,
                             f"{100*n/STUDIES:.4f}", field])
        for label, status, n, _color in RISK_STATUS:
            writer.writerow(["C signal status", label.replace("\n", " "), n,
                             f"{100*n/STUDIES:.4f}", "Leakage_Signal_Status"])


def save_latex(path, figure_directory):
    latex = r"""\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{""" + str(figure_directory) + "/" + FILENAME + r""".pdf}
    \caption{Methodological reliability profile of the frozen 485-study technical-synthesis
    subset. (A) Validation-design recoverability and the six explicitly coded design
    categories. (B) Prevalence of explicitly documented methodological attributes.
    (C) Study-level leakage-signal status (high, low or unclear), not the prevalence
    of individual leakage mechanisms. All percentages have denominator $n=485$.
    Chronological splitting in panel B is a separately coded attribute and must
    not be equated with formally identified temporally ordered validation in panel A.
    An unclear classification denotes insufficient recoverable evidence, not a
    verified absence of the practice or leakage risk.}
    \label{fig:methodological-reliability}
\end{figure}
\FloatBarrier
"""
    path.write_text(latex, encoding="utf-8")


def main():
    args = parse_arguments()
    if args.dpi < 100:
        raise ValueError("Use at least 100 dpi; 600 recommended")
    rows, cats, provenance = read_inputs(args)
    validation, identified, practices, signals = counts_and_checks(rows, cats)
    paths = draw_plot(validation, identified, practices, out_dir=args.output_dir,
                      dpi=args.dpi, show=args.show)
    summary = args.output_dir / f"{FILENAME}_Verified_Counts.csv"
    save_summary(summary, validation, identified, practices)
    save_latex(args.output_dir / f"{FILENAME}_LaTeX.tex", args.output_dir)
    print("PASS: SHA-256 checked; unique frozen n=485, 51 fields, reconciled counts")
    print("Validation:", dict(validation))
    print("Practices:", dict(practices))
    print("Leakage statuses:", dict(signals))
    print("Frozen source:", provenance)
    print("WARNING: Individual leakage mechanisms are not available in the frozen 51-field register.")
    for ext, path in paths.items():
        print(f"{ext.upper()}: {path}")
    print("COUNT CSV:", summary)


if __name__ == "__main__":
    main()
