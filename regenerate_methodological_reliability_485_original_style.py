#!/usr/bin/env python3
"""Figure 13 — Phase-A frozen 485-study methodological reliability.

Recreates the ORIGINAL three-panel lollipop visual language:
  A. Validation-design reporting (summary bar + detailed lollipops)
  B. Explicitly documented methodological attributes (lollipops)
  C. Study-level leakage-signal classification (lollipops)

IMPORTANT SCIENTIFIC LIMITATION:
  The frozen 51-column technical register DOES NOT have a per-study list of
  particular leakage mechanisms. The old 492-study Panel C enumerated mechanisms
  from a separate methodological-audit source, so those old values cannot be
  silently reused for a 485-study figure. Panel C therefore reports the three
  verified study-level statuses in Leakage_Signal_Status. It is explicitly
  labelled differently and must not be described as mechanism-level prevalence.

Reads ONLY the frozen dataset and its manifest, never an obsolete 492-study
workbook. Supports either --frozen-dir (normal WSL setup) or --archive (zip).
Outputs vector PDF/SVG + 600 dpi PNG/TIFF + a machine-readable count CSV.

Usage, WSL:
  python regenerate_methodological_reliability_485_original_style.py \\
    --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
    --output-dir Figures_485 --dpi 600

Test with archive:
  python regenerate_methodological_reliability_485_original_style.py \\
    --archive PhaseA_FROZEN_485_Sync_Inputs.zip --output-dir Figures_485
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

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Rectangle

STUDIES = 485
FILENAME = "Figure13_Methodological_Reliability_485_Original_Style"
REGISTER = "Technical_Register_485_FROZEN.csv"
MANIFEST = "Final_Freeze_Manifest_v1.json"
CATEGORY_COUNTS = "Manuscript_Category_Counts_FROZEN.csv"

# Original-figure palette; light grey means evidence unavailable/unclear.
BLUE = "#3F83A6"
ORANGE = "#D99245"
GREEN = "#4F9A73"
RED = "#CB6C55"
GREY = "#B8BDC5"
BLACK = "#222222"
GRID = "#D3D7DA"

# (label, coding field, qualifying value) — correct frozen register names.
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
    ("At least one passage-verified signal (High)",
     "At least one passage-verified signal", 32, RED),
    ("No explicit verified signal identified (Low)",
     "No explicit passage-verified signal identified", 7, GREEN),
    ("Specific leakage mechanism not classifiable (Unclear)",
     "Specific leakage mechanism not classifiable", 446, GREY),
]
EXPECTED_PRACTICES = [110, 75, 58, 48, 37, 15, 14, 8, 7, 4]


def arguments():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--archive", type=Path, default=None,
                   help="Optional ZIP alternative to --frozen-dir")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--show", action="store_true")
    return p.parse_args()


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_inputs(args):
    if args.archive is not None:
        with zipfile.ZipFile(args.archive, "r") as z:
            nmap = {n.split("/")[-1]: n for n in z.namelist() if not n.endswith("/")}
            needed = (REGISTER, MANIFEST, CATEGORY_COUNTS)
            if not set(needed).issubset(nmap):
                raise RuntimeError(f"Archive missing: {set(needed)-set(nmap)}")
            raw = {name: z.read(nmap[name]) for name in needed}
        provenance = str(args.archive)
    else:
        raw = {name: (args.frozen_dir / name).read_bytes()
               for name in (REGISTER, MANIFEST, CATEGORY_COUNTS)}
        provenance = str(args.frozen_dir)

    manifest = json.loads(raw[MANIFEST].decode("utf-8-sig"))
    if manifest.get("retained_studies") != STUDIES or not manifest.get("final_corpus_frozen"):
        raise RuntimeError("Not an authenticated final 485-study freeze")
    for name in (REGISTER, CATEGORY_COUNTS):
        expected = manifest["output_sha256"].get(name)
        if not expected or sha256(raw[name]) != expected:
            raise RuntimeError(f"Frozen file SHA256 mismatch: {name}")

    def as_rows(name):
        return list(csv.DictReader(io.StringIO(raw[name].decode("utf-8-sig"))))

    rows = as_rows(REGISTER)
    count_rows = as_rows(CATEGORY_COUNTS)
    if len(rows) != STUDIES or len({r["Paper_ID"] for r in rows}) != STUDIES:
        raise RuntimeError("Frozen register membership failed")
    if len(rows[0]) != 51:
        raise RuntimeError("Expected 51-field technical register")
    for field in ("Validation_Design", "Validation_Status", "Leakage_Risk",
                  "Leakage_Signal_Status", *[p[1] for p in PRACTICES]):
        if field not in rows[0]:
            raise RuntimeError(f"Missing frozen field: {field}")
    return rows, count_rows, provenance


def count_field(rows, field, value):
    return sum(row[field] == value for row in rows)


def counts_and_checks(rows, category_rows):
    observed_validation = Counter(r["Validation_Design"] for r in rows)
    expected_validation = {key: n for _,key,n in VALIDATION}
    expected_validation["Unclear"] = 398
    if observed_validation != expected_validation:
        raise RuntimeError(f"Validation distribution mismatch: {observed_validation}")

    identified = STUDIES - observed_validation["Unclear"]
    if identified != 87:
        raise RuntimeError("Validation identified count must be 87")

    practices = [(label, count_field(rows, field, good))
                 for label, field, good in PRACTICES]
    if [n for _,n in practices] != EXPECTED_PRACTICES:
        raise RuntimeError(f"Methodological attribute counts unexpectedly changed: {practices}")

    signals = Counter(r["Leakage_Signal_Status"] for r in rows)
    risks = Counter(r["Leakage_Risk"] for r in rows)
    if risks != Counter({"High":32, "Low":7, "Unclear":446}):
        raise RuntimeError(f"Frozen risk reconciliation mismatch: {risks}")
    for name, key, n, color in RISK_STATUS:
        if signals.get(key,0) != n:
            raise RuntimeError(f"Leakage signal status mismatch: {key}")
    if sum(signals.values()) != STUDIES:
        raise RuntimeError("Leakage signal partition failed")

    # Independent frozen manuscript count summary agrees with the study-level values.
    marginal = {(r["Field"], r["Category"]):int(r["Count"])
                for r in category_rows}
    for col in ("Validation_Status", "Leakage_Risk"):
        for key,n in Counter(r[col] for r in rows).items():
            if marginal.get((col,key)) != n:
                raise RuntimeError(f"Independent frozen marginal mismatch: {col}/{key}")
    return observed_validation, identified, practices, signals


def configure_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "font.size": 11.2,
        "axes.titlesize": 12.0,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    })


def lollipop(ax, labels, values, colors, *, max_x, tick, font=10):
    y = np.arange(len(values), dtype=float)
    for yi, v, c in zip(y, values, colors):
        ax.hlines(yi, 0, v, color=c, linewidth=2.25, zorder=2)
        ax.scatter(v, yi, color=c, s=45, edgecolor="white", linewidth=0.75, zorder=3)
        ax.annotate(f"{v} ({v / STUDIES * 100:.1f}%)", (v, yi),
                    xytext=(5,0), textcoords="offset points",
                    va="center", ha="left", fontsize=font, color=BLACK)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max_x)
    ax.xaxis.set_major_locator(MultipleLocator(tick))
    ax.xaxis.grid(color=GRID, alpha=0.67, linestyle=(0,(2,3)), linewidth=0.65)
    ax.set_axisbelow(True)
    ax.spines[['left','top','right']].set_visible(False)
    ax.spines['bottom'].set_color('#666666')
    ax.spines['bottom'].set_linewidth(0.7)
    ax.tick_params(axis='y',length=0,pad=5)
    ax.tick_params(axis='x',direction='out',length=3)
    ax.set_xlabel('Number of studies',labelpad=7, fontsize=10.7)


def plot(observed_validation, identified, practices, *, output_dir, dpi):
    configure_style()
    fig = plt.figure(figsize=(14.7, 9.0), facecolor='white')
    # Layout replicates original figure: two upper panels, lower panel spans both.
    grid = fig.add_gridspec(2, 2, left=.185, right=.935, bottom=.11, top=.938,
                            wspace=.73, hspace=.48, height_ratios=[1.1,.85])
    left = grid[0,0].subgridspec(2,1,height_ratios=[.42, 2.8], hspace=.37)
    ax_summary = fig.add_subplot(left[0])
    ax_a = fig.add_subplot(left[1])
    ax_b = fig.add_subplot(grid[0,1])
    ax_c = fig.add_subplot(grid[1,:])

    # A, upper summary bar: design identified vs unclear.
    unknown = observed_validation['Unclear']
    ax_summary.set_xlim(0, STUDIES)
    ax_summary.set_ylim(0,1)
    ax_summary.add_patch(Rectangle((0,.16),identified,.66,color=BLUE,lw=0))
    ax_summary.add_patch(Rectangle((identified,.16),unknown,.66,color=GREY,lw=0))
    ax_summary.text(identified/2,.49, f"{identified}\n({identified/STUDIES*100:.1f}%)",
                    ha='center',va='center',color='white',fontsize=10.7,fontweight='bold')
    ax_summary.text(identified+unknown/2,.49,
                    f"{unknown}\n({unknown/STUDIES*100:.1f}%)",
                    ha='center',va='center',color=BLACK,fontsize=10.7)
    ax_summary.text(identified/2,-.03,'Design identified',ha='center',va='top',
                    fontsize=9.5,color=BLUE)
    ax_summary.text(identified+unknown/2,-.03,'Unclear',ha='center',va='top',
                    fontsize=9.5,color='#60676c')
    ax_summary.set_axis_off()
    ax_summary.set_title('A. Validation-design reporting',loc='left',
                         pad=16, fontweight='bold',fontsize=13.1)

    # A, lower detailed validation categories.
    labels = [label for label, _, _ in VALIDATION]
    values = [n for _,_,n in VALIDATION]
    cols = [ORANGE if key == 'Random_Shuffled' else BLUE
            for _, key, n in VALIDATION]
    lollipop(ax_a,labels,values,cols,max_x=72,tick=10,font=9.4)

    # B: all ten fields are explicitly present in the FROZEN 51-field register.
    labs_b = [label for label,n in practices]
    vals_b = [n for label,n in practices]
    lollipop(ax_b,labs_b,vals_b,[GREEN]*len(vals_b),max_x=134,tick=20,font=9.4)
    ax_b.set_title('B. Explicitly documented\nmethodological attributes',
                   loc='left',fontsize=13.1,fontweight='bold',pad=12)

    # C: frozen signal statuses, NOT an unsupported per-mechanism decomposition.
    labels_c = [label for label,key,n,c in RISK_STATUS]
    counts_c = [n for label,key,n,c in RISK_STATUS]
    colors_c = [c for label,key,n,c in RISK_STATUS]
    lollipop(ax_c,labels_c,counts_c,colors_c,max_x=490,tick=50,font=10.1)
    ax_c.set_title('C. Study-level leakage-signal classification',
                   loc='left',fontsize=13.1,fontweight='bold',pad=18)

    # Explicit limitation, essential when replacing the old mechanism-specific C.
    fig.text(.5,.037,
       'Percentages use n = 485. Panel C reports mutually exclusive study-level statuses; '
       'individual leakage mechanisms were not coded in the frozen register.',
       ha='center',va='bottom',fontsize=9.5,color='#4f4f4f')

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for ext in ('pdf','svg','png','tiff'):
        path = output_dir / (FILENAME+'.'+ext)
        kw = dict(bbox_inches='tight',pad_inches=.12)
        if ext in ('png','tiff'):
            kw['dpi'] = dpi
        if ext=='tiff':
            kw['pil_kwargs']={'compression':'tiff_lzw'}
        fig.savefig(path,**kw)
        paths[ext] = path
    return fig, paths


def save_summary(path, validation, identified, practices):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        w.writerow(['Panel','Category','Count','Percentage_of_485','Source_field'])
        for label,num,field in [
            ('Design identified',identified,'Validation_Design'),
            ('Unclear',validation['Unclear'],'Validation_Design')]:
            w.writerow(['A summary',label,num,f'{num/STUDIES*100:.4f}',field])
        for label,key,num in VALIDATION:
            w.writerow(['A validation',label,num,f'{num/STUDIES*100:.4f}','Validation_Design'])
        for (label,col,val),(_,num) in zip(PRACTICES,practices):
            w.writerow(['B methodology',label,num,f'{num/STUDIES*100:.4f}',col])
        for label,key,num,c in RISK_STATUS:
            w.writerow(['C signal status',label,num,f'{num/STUDIES*100:.4f}','Leakage_Signal_Status'])


def main():
    args = arguments()
    rows, counts, provenance = read_inputs(args)
    validation, identified, practices, statuses = counts_and_checks(rows,counts)
    fig, paths = plot(validation,identified,practices,output_dir=args.output_dir,dpi=args.dpi)
    counts_file=args.output_dir/(FILENAME+'_Verified_Counts.csv')
    save_summary(counts_file,validation,identified,practices)
    if args.show:
        plt.show()
    plt.close(fig)
    print('PASS — frozen SHA256 and 485-study membership')
    print('PASS — validation:', dict(validation))
    print('PASS — documented methodological attributes:', dict(practices))
    print('PASS — leakage-signal status:',dict(statuses))
    print('Source:', provenance)
    print('Original passage-specific leakage mechanisms: NOT RECONSTRUCTIBLE FROM FROZEN REGISTER')
    print('No change to original or frozen files.')
    for name,p in paths.items(): print(f'{name.upper():4s}: {p}')
    print('COUNT CSV:',counts_file)

if __name__ == '__main__':
    main()
