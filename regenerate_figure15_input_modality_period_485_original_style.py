#!/usr/bin/env python3
"""
ACME Phase A — Figure 15: period-by-input-modality heatmap (frozen n=485).

REPLACES the legacy 492/493-study heatmap. All period denominators and cells
are recomputed from the frozen 51-field technical register; no old matrix is
loaded. The original 4-period × 10-category, serif, viridis heatmap design is
retained, with clearer labels, cell annotations, and a fixed 0–100% scale.

Run from the stock-SLR project root:

python regenerate_figure15_input_modality_period_485_original_style.py \
    --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \
    --output-dir Figures_485 --dpi 600

Alternatively, read the frozen ZIP directly without extracting it:
python regenerate_figure15_input_modality_period_485_original_style.py \
    --frozen-zip PhaseA_FROZEN_485_Sync_Inputs.zip \
    --output-dir Figures_485 --dpi 600

Output: PDF, SVG, PNG, TIFF, two audit matrices, long-form cell table,
        yearly denominator table, verification JSON, and LaTeX include code.

Requires pandas, numpy, matplotlib, and Pillow for the LZW TIFF export.
The script aborts before writing outputs if any frozen-source QA fails.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd

N = 485
REGISTER_SHA = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
CATEGORY_SHA = "3d8e77e50cf6565351aa1ebd3b35aa26e61f2378b8731a348323a71415e4c1b8"
REGISTER = "Technical_Register_485_FROZEN.csv"
MANIFEST = "Final_Freeze_Manifest_v1.json"
CATEGORIES = "Manuscript_Category_Counts_FROZEN.csv"
BASE = "Figure15_Input_Modality_Period_Heatmap_485_Original_Style"
PERIODS = ("2016–2020", "2021–2022", "2023–2024", "2025–2026")
PERIOD_YEAR_BOUNDS = ((2016, 2020), (2021, 2022), (2023, 2024), (2025, 2026))

# The first nine are multi-label indicators. The tenth is NOT a modality.
MODALITIES = (
    ("Historical_Market_Data", "Historical market data", 291),
    ("Technical_Indicators", "Technical indicators", 118),
    ("Financial_News_Text", "Financial news and textual information", 91),
    ("Decomposition_Transformation", "Decomposition or transformed representations", 62),
    ("Social_Media_Public_Opinion", "Social media or public-opinion information", 37),
    ("Relational_Cross_Market", "Index, sectoral, relational, or cross-market context", 27),
    ("Macroeconomic_Systemic", "Macroeconomic or systemic variables", 21),
    ("Fundamental_Accounting", "Fundamental or accounting information", 19),
    ("Alternative_Attention", "Alternative or attention-related information", 5),
)
UNKNOWN = ("Input_Modality_Not_Recoverable", "Input modality not recoverable", 34)
REQUIRED_EXCLUSIONS = {
    "P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"
}


def arguments():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    source = p.add_mutually_exclusive_group()
    source.add_argument("--frozen-dir", type=Path, default=None,
                        help="Directory containing frozen CSVs and manifest")
    source.add_argument("--frozen-zip", type=Path, default=None,
                        help="Frozen archive (no manual extraction necessary)")
    p.add_argument("--output-dir", type=Path, default=Path("Figures_485"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--show-title", action="store_true",
                   help="Add in-figure title; omit by default for journal LaTeX")
    p.add_argument("--check-all-hashes", action="store_true",
                   help="Verify every declared output_sha256 manifest artifact")
    return p.parse_args()


class FrozenSource:
    def __init__(self, directory: Path | None, archive: Path | None):
        self.directory = directory or Path(
            "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"
        )
        self.archive = archive
        if archive is not None:
            if not archive.is_file():
                raise FileNotFoundError(f"Frozen ZIP not found: {archive}")
            with zipfile.ZipFile(archive) as z:
                self.members = {}
                for member in z.namelist():
                    if member.endswith("/"):
                        continue
                    base = Path(member).name
                    if base in self.members:
                        raise ValueError(f"Ambiguous duplicate frozen ZIP file: {base}")
                    self.members[base] = member
        elif not self.directory.is_dir():
            raise FileNotFoundError(f"Frozen directory not found: {self.directory}")

    def get(self, basename: str) -> bytes:
        if self.archive is not None:
            member = self.members.get(basename)
            if member is None:
                raise FileNotFoundError(f"{basename} missing from {self.archive}")
            with zipfile.ZipFile(self.archive) as z:
                return z.read(member)
        target = self.directory / basename
        if not target.is_file():
            raise FileNotFoundError(f"Frozen file missing: {target}")
        return target.read_bytes()

    def describe(self) -> str:
        return str((self.archive or self.directory).resolve())


def verify_and_read(src: FrozenSource, verify_all: bool) -> tuple[pd.DataFrame, dict]:
    manifest_bytes = src.get(MANIFEST)
    release = json.loads(manifest_bytes.decode("utf-8-sig"))
    if release.get("final_corpus_frozen") is not True:
        raise ValueError("Frozen flag not true in release manifest")
    if int(release.get("retained_studies", -1)) != N:
        raise ValueError("Release manifest retained study count is not 485")
    if release.get("primary_metric_sankey_released") is not False:
        raise ValueError("Release manifest has an unexpected primary-metric release status")
    if int(release.get("final_net_differences", -1)) != 50:
        raise ValueError("Unexpected Phase A repair/reconciliation receipt")

    hashes = release.get("output_sha256")
    if not isinstance(hashes, dict):
        raise ValueError("Manifest has no output_sha256 mapping")
    if hashes.get(REGISTER) != REGISTER_SHA or hashes.get(CATEGORIES) != CATEGORY_SHA:
        raise ValueError("Manifest does not match author-approved frozen source hashes")

    checked_hashes = {}
    required = sorted(hashes) if verify_all else [REGISTER, CATEGORIES]
    for name in required:
        raw = src.get(name)
        observed = hashlib.sha256(raw).hexdigest()
        if observed != hashes[name]:
            raise ValueError(f"SHA-256 verification failed for {name}")
        checked_hashes[name] = observed

    df = pd.read_csv(io.BytesIO(src.get(REGISTER)), dtype=str,
                     keep_default_na=False, encoding="utf-8-sig")
    if len(df) != N:
        raise ValueError(f"Expected 485 source rows; found {len(df)}")
    required_fields = ["Paper_ID", "Year", "Input_Modality_Recoverable"] + [
        item[0] for item in MODALITIES
    ]
    missing = sorted(set(required_fields) - set(df.columns))
    if missing:
        raise KeyError(f"Required frozen fields unavailable: {missing}")
    if df["Paper_ID"].eq("").any() or df["Paper_ID"].nunique() != N:
        raise ValueError("Paper_ID null/duplicate; aborting")
    absent = REQUIRED_EXCLUSIONS.intersection(df["Paper_ID"])
    if absent:
        raise ValueError(f"Author-excluded technical study ID present: {sorted(absent)}")
    recorded_exclusions = set(release.get("excluded_ids", []))
    if recorded_exclusions and not REQUIRED_EXCLUSIONS.issubset(recorded_exclusions):
        raise ValueError("Manifest excluded IDs disagree with approved decision log")

    for col in [x[0] for x in MODALITIES] + ["Input_Modality_Recoverable"]:
        df[col] = df[col].str.strip()
        unexpected = sorted(set(df[col]) - {"Yes", "No"})
        if unexpected:
            raise ValueError(f"{col} contains non-binary values: {unexpected}")

    positive = np.column_stack(
        [df[col].eq("Yes").to_numpy() for col, _, _ in MODALITIES]
    )
    unknown = df["Input_Modality_Recoverable"].eq("No").to_numpy()
    if not np.array_equal(~positive.any(axis=1), unknown):
        raise ValueError("Recoverability field fails modality indicator reconciliation")

    for col, _label, correct_n in MODALITIES:
        got = int(df[col].eq("Yes").sum())
        if got != correct_n:
            raise ValueError(f"Frozen marginal for {col} is {got}, expected {correct_n}")
    if int(unknown.sum()) != UNKNOWN[2]:
        raise ValueError("Unrecoverable input modality count does not equal 34")

    cat = pd.read_csv(io.BytesIO(src.get(CATEGORIES)),
                      dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if not {"Field", "Category", "Count"}.issubset(cat.columns):
        raise ValueError("Frozen category counts CSV lacks expected structure")
    record = cat.loc[
        cat["Field"].eq("Technical_Indicators") & cat["Category"].eq("Yes"), "Count"
    ]
    if len(record) != 1 or int(record.iloc[0]) != 118:
        raise ValueError("Independent frozen Technical_Indicators total not 118")

    years = df["Year"].str.strip()
    if not years.str.fullmatch(r"\d{4}").all():
        raise ValueError("Publication years are nonnumeric/missing in frozen register")
    df["Publication_Year"] = years.astype(int)
    if not df["Publication_Year"].between(2016, 2026).all():
        unusual = df.loc[~df["Publication_Year"].between(2016, 2026),
                         ["Paper_ID", "Publication_Year"]]
        raise ValueError("Frozen year outside original plot bins:\n" +
                         unusual.to_string(index=False))
    return df, {
        "source": src.describe(),
        "register_sha256": checked_hashes[REGISTER],
        "category_counts_sha256": checked_hashes[CATEGORIES],
        "manifest_frozen": True,
        "retained_studies": N,
        "verified_artifact_hashes": checked_hashes,
    }


def summarize(df: pd.DataFrame):
    rows = list(MODALITIES) + [UNKNOWN]
    period_of = pd.Series(index=df.index, dtype="object")
    for label, (lo, hi) in zip(PERIODS, PERIOD_YEAR_BOUNDS):
        period_of.loc[df["Publication_Year"].between(lo, hi)] = label
    if period_of.isna().any():
        raise ValueError("At least one study could not be assigned to a period")
    df = df.assign(Publication_Period=period_of)

    period_n = df.groupby("Publication_Period", sort=False).size()
    period_n = period_n.reindex(PERIODS, fill_value=0).astype(int)
    if int(period_n.sum()) != N or (period_n <= 0).any():
        raise ValueError("Publication period denominators do not sum to 485 or include empty bins")

    counts = pd.DataFrame(index=[x[1] for x in rows], columns=PERIODS, dtype=int)
    for key, label, expected_total in rows:
        positive = (df[key].eq("Yes") if key != UNKNOWN[0]
                    else df["Input_Modality_Recoverable"].eq("No"))
        counts.loc[label] = [
            int((positive & df["Publication_Period"].eq(p)).sum()) for p in PERIODS
        ]
        if int(counts.loc[label].sum()) != expected_total:
            raise ValueError(f"Across-period counts for {label} fail marginal QA")
    counts = counts.astype(int)
    for period in PERIODS:
        if (counts[period] > period_n[period]).any() or (counts[period] < 0).any():
            raise ValueError(f"Invalid cell count in {period}")

    # Divide by each period size; rows are NOT supposed to sum to 100%.
    percentages = counts.div(period_n, axis=1).mul(100)
    years = (df.groupby("Publication_Year").size()
             .reindex(range(2016, 2027), fill_value=0).rename("Number_of_Studies"))
    years.index.name = "Publication_Year"

    records = []
    for key, label, _ in rows:
        for period in PERIODS:
            records.append({
                "Category_Key": key,
                "Category_Label": label,
                "Category_Type": ("Evidence recoverability" if key == UNKNOWN[0]
                                  else "Explicit input modality"),
                "Publication_Period": period,
                "Period_N": int(period_n[period]),
                "Studies": int(counts.loc[label, period]),
                "Within_Period_Percent": round(float(percentages.loc[label, period]), 4)
            })
    return counts, percentages, years, period_n, pd.DataFrame(records)


def draw_heatmap(counts, percentages, period_n, folder, dpi, show_title):
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
        "font.size": 11.0,
        "axes.labelsize": 11.2,
        "xtick.labelsize": 10.3,
        "ytick.labelsize": 10.3,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })
    values = percentages.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(11.3, 7.05))
    cmap = plt.get_cmap("viridis")
    image = ax.imshow(values, cmap=cmap, norm=Normalize(vmin=0, vmax=100),
                      aspect="auto", interpolation="nearest")

    ticklabels = [f"{p}\n(n={int(period_n[p])})" for p in PERIODS]
    ax.set_xticks(np.arange(len(PERIODS)), labels=ticklabels)
    ax.set_yticks(np.arange(len(counts)), labels=list(counts.index))
    ax.set_xlabel("Publication period", labelpad=9)
    ax.tick_params(axis="both", which="both", length=0, pad=9)

    if show_title:
        ax.set_title("Evolution of explicitly documented input modalities",
                     loc="left", fontweight="bold", fontsize=12, pad=18)

    # Light cell boundaries and a distinct separation for the evidence-status row.
    ax.set_xticks(np.arange(-0.5, len(PERIODS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(counts), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.7, alpha=0.78)
    ax.axhline(len(counts) - 1.5, linewidth=1.4, color="#D6D6D6",
               linestyle="--", zorder=5)

    for ridx in range(values.shape[0]):
        for cidx in range(values.shape[1]):
            percent = float(values[ridx, cidx])
            n = int(counts.iat[ridx, cidx])
            rgba = cmap(percent / 100.0)
            # Relative luminance: darker viridis cells require white text.
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            color = "#161616" if luminance >= 0.51 else "#FFFFFF"
            ax.text(cidx, ridx, f"{percent:.1f}%\n(n={n})",
                    ha="center", va="center", fontsize=9.2,
                    linespacing=1.55, fontweight="semibold", color=color)

    cbar = fig.colorbar(image, ax=ax, pad=0.022, fraction=0.047,
                        ticks=[0, 20, 40, 60, 80, 100])
    cbar.set_label("Studies within period (%)", labelpad=8)
    cbar.outline.set_linewidth(0.6)
    cbar.ax.tick_params(labelsize=9.2)

    for spine in ax.spines.values():
        spine.set_visible(False)
    # Wide label margin and generous row height, suitable for double-column figures.
    fig.subplots_adjust(left=0.465, right=0.89, bottom=0.135,
                        top=0.945 if show_title else 0.97)

    folder.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png", "tiff"):
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.10, "format": ext}
        if ext in ("png", "tiff"):
            kwargs["dpi"] = dpi
        if ext == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(folder / f"{BASE}.{ext}", **kwargs)
    plt.close(fig)


def export_outputs(counts, percentages, years, period_n, cells, audit, folder):
    folder.mkdir(parents=True, exist_ok=True)
    counts.index.name = "Input_Modality"
    percentages.index.name = "Input_Modality"
    counts.to_csv(folder / f"{BASE}_Counts.csv", encoding="utf-8-sig")
    percentages.round(3).to_csv(
        folder / f"{BASE}_Within_Period_Percentages.csv", encoding="utf-8-sig")
    years.to_csv(folder / f"{BASE}_Year_Denominators.csv", encoding="utf-8-sig")
    cells.to_csv(folder / f"{BASE}_Cell_Audit.csv",
                 index=False, encoding="utf-8-sig")
    audit["period_denominators"] = {k: int(v) for k, v in period_n.items()}
    audit["modalities_are_non_mutually_exclusive"] = True
    audit["unknown_is_evidence_recoverability_not_input_modality"] = True
    audit["verified_marginals"] = {
        key: count for key, _, count in list(MODALITIES) + [UNKNOWN]
    }
    (folder / f"{BASE}_QA.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    latex = r"""\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{Figures_485/""" + BASE + r""".pdf}
    \caption{Period-wise prevalence of explicitly documented input-data and
    feature-representation modalities in the frozen technical-synthesis
    corpus ($n=485$). Each annotated cell gives the proportion and count of
    studies within its publication period, with period-specific denominators
    displayed above the columns. Input modalities are non-mutually exclusive
    and therefore percentages do not sum to 100\% across rows. The separated
    final row records cases in which input-modality information was not
    recoverable; it is not an additional input modality. The 2026 records
    reflect partial-year coverage.}
    \label{fig:input-modality-period-heatmap}
\end{figure}
\FloatBarrier
"""
    (folder / f"{BASE}_LaTeX.tex").write_text(latex.lstrip(),
                                               encoding="utf-8")
    print("PASS: frozen 485-study register; source checks and modal totals verified.")
    print("Period denominators:", dict(period_n))
    print("Generated files:")
    for f in sorted(folder.glob(BASE + "*")):
        print(" ", f.resolve())


def main():
    a = arguments()
    if a.dpi < 100:
        raise ValueError("Use at least 100 dpi (recommended 600).")
    src = FrozenSource(a.frozen_dir, a.frozen_zip)
    df, audit = verify_and_read(src, a.check_all_hashes)
    counts, pct, years, period_n, cells = summarize(df)
    # Files are written only after all source, cross-tab and margin checks pass.
    draw_heatmap(counts, pct, period_n, a.output_dir, a.dpi, a.show_title)
    export_outputs(counts, pct, years, period_n, cells, audit, a.output_dir)


if __name__ == "__main__":
    main()
