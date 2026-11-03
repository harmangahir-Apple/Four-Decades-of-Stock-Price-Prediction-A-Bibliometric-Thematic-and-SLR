#!/usr/bin/env python3
"""Regenerate ACME Figure 3 from the thesis-retained geographical evidence base.

Inputs are the author's original document-level FULL-COUNTING country totals or the
updated 4,972-geocodable-record totals. If USA is 392, the script adds exactly one
verified UCLA institutional participation for P05017 and writes a NEW derivative
CSV (never overwriting the source). If USA is already 393, it does not add again.

Optional independent verification: --audit Country_Record_Level_Audit_4975.csv.
The count 4,972 refers to unique geocodable records, NOT sum of country counts.

Natural Earth (public-domain) 1:110m Admin-0 boundaries are needed to plot.
The script accepts a local .shp/.geojson/.zip via --world or downloads/caches the
official Natural Earth ZIP at first use.

Dependencies: pandas, geopandas, matplotlib, numpy, shapely, pyogrio (or fiona).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import ScalarFormatter
import pandas as pd

EXPECTED_APPLICATION = 4975
EXPECTED_GEOCODABLE = 4972
EXPECTED_COUNTRIES = 107
EXPECTED_USA_OLD, EXPECTED_USA_NEW = 392, 393
EXPECTED_IND, EXPECTED_CHN = 1839, 1016
EXPECTED_COUNTRY_ASSIGNMENTS = 5929  # full counting, NOT unique publications

# Map display only: these territories are not separate polygons at 1:110m.
# Do not modify the underlying country-by-country audit CSV.
VISUAL_ONLY_TERRITORY_MAP = {"HKG": "CHN", "MAC": "CHN"}
# Approximate geographic centres for very small states absent as polygons at 1:110m.
# These display-only coordinates DO NOT affect bibliometric country counts.
SMALL_STATE_MARKERS = {
    "BHR": (50.56, 26.07),   # Bahrain
    "LIE": (9.55, 47.16),    # Liechtenstein
    "MLT": (14.38, 35.94),   # Malta
    "SGP": (103.82, 1.35),   # Singapore
}
NAME_CORRECTIONS = {"France": "FRA", "Norway": "NOR", "Kosovo": "XKX", "N. Cyprus": "CYP", "Somaliland": "SOM"}

PRETTY_NAMES = {
    "IND": "India", "CHN": "China", "USA": "United States",
    "IDN": "Indonesia", "GBR": "United Kingdom", "MYS": "Malaysia",
    "PAK": "Pakistan", "SAU": "Saudi Arabia", "KOR": "South Korea",
    "TWN": "Taiwan", "BGD": "Bangladesh", "IRN": "Iran", "THA": "Thailand",
    "AUS": "Australia", "CAN": "Canada", "DEU": "Germany", "VNM": "Vietnam",
    "JPN": "Japan", "BRA": "Brazil", "FRA": "France", "ARE": "United Arab Emirates"
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def detect_country_input(base: Path) -> Path:
    candidates = [
        base / "02_Merged_Data" / "World_Map_Heatmap_Output" / "Country_Publication_Counts_Full_Counting_4972.csv",
        base / "02_Merged_Data" / "World_Map_Heatmap_Output" / "Country_Publication_Counts_Full_Counting.csv",
        base / "Country_Publication_Counts_Full_Counting_4972.csv",
        base / "Country_Publication_Counts_Full_Counting.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Cannot locate country totals. Pass --country-csv with the actual CSV path.\n" +
                            "Checked:\n" + "\n".join(map(str, candidates)))


def load_country_counts(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    if not {"ISO3", "Publications"}.issubset(df.columns):
        raise ValueError(f"Missing ISO3/Publications in {path}. Found {list(df.columns)}")
    df = df[["ISO3", "Publications"]].copy()
    df["ISO3"] = df["ISO3"].astype(str).str.strip().str.upper()
    if df["ISO3"].duplicated().any():
        raise ValueError("Duplicated ISO3 country rows; the input must contain one row per country")
    df["Publications"] = pd.to_numeric(df["Publications"], errors="raise")
    if (df["Publications"] < 0).any() or not (df["Publications"] % 1 == 0).all():
        raise ValueError("Country counts must be nonnegative whole numbers")
    df["Publications"] = df["Publications"].astype(int)
    by_iso = df.set_index("ISO3")["Publications"]
    for key, expected in {"IND": EXPECTED_IND, "CHN": EXPECTED_CHN}.items():
        if key not in by_iso or int(by_iso[key]) != expected:
            raise AssertionError(f"{key} should equal {expected}; found {by_iso.get(key)}. Inspect file provenance")
    if len(df) != EXPECTED_COUNTRIES:
        raise AssertionError(f"Expected {EXPECTED_COUNTRIES} country/territory rows; got {len(df)}")
    usa = int(by_iso.get("USA", -1))
    if usa == EXPECTED_USA_OLD:
        # P05017 is a verified 2024 UCLA master's thesis in the 4975 study subset.
        # Add one USA country participation ONCE, with no other changes.
        df.loc[df["ISO3"].eq("USA"), "Publications"] += 1
        procedure = "Original 4,971-geocodable source totals + one P05017/UCLA USA affiliation"
    elif usa == EXPECTED_USA_NEW:
        procedure = "Already thesis-corrected 4,972-geocodable source; no increment"
    else:
        raise AssertionError(f"Unexpected USA={usa}; expected 392 (original) or 393 (revised). Stop to avoid double counting.")
    if int(df["Publications"].sum()) != EXPECTED_COUNTRY_ASSIGNMENTS:
        raise AssertionError(f"Country full-counting total mismatch: {df['Publications'].sum()} != 5,929")
    return df.sort_values("Publications", ascending=False).reset_index(drop=True), procedure


def verify_record_audit(path: Path, counts: pd.DataFrame) -> dict:
    """Recompute 4,972 unique geocodable studies and 5,929 country participations."""
    d = pd.read_csv(path, keep_default_na=False, low_memory=False)
    needed = {"Paper_ID", "Country_ISO3_List", "Map_Eligible"}
    if not needed.issubset(d.columns):
        raise ValueError(f"Audit missing: {sorted(needed - set(d.columns))}")
    if len(d) != EXPECTED_APPLICATION or d["Paper_ID"].nunique() != EXPECTED_APPLICATION:
        raise AssertionError("Audit must contain 4,975 distinct application-area study IDs")
    eligible = d["Map_Eligible"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    if int(eligible.sum()) != EXPECTED_GEOCODABLE:
        raise AssertionError(f"Geocodable record count is {int(eligible.sum())}, expected 4,972")
    p05017 = d.loc[d["Paper_ID"].astype(str).eq("P05017")]
    if len(p05017) != 1 or str(p05017.iloc[0]["Country_ISO3_List"]).strip() != "USA" or not bool(eligible.loc[p05017.index[0]]):
        raise AssertionError("P05017 must appear exactly once and be attributed to USA")
    expected = Counter()
    for record in d.itertuples(index=False):
        for code in str(getattr(record, "Country_ISO3_List")).split(";"):
            code = code.strip().upper()
            if code: expected[code] += 1
    actual = dict(zip(counts["ISO3"], counts["Publications"].astype(int)))
    if dict(expected) != actual:
        diff = {k: (expected.get(k, 0), actual.get(k, 0)) for k in set(expected) | set(actual) if expected.get(k, 0) != actual.get(k, 0)}
        raise AssertionError(f"Country file disagrees with study-level full counting: {diff}")
    return {"rows": len(d), "geocodable": int(eligible.sum()), "nongeocodable": int((~eligible).sum()),
            "unique_ids": d["Paper_ID"].nunique(), "country_participations": sum(expected.values()),
            "P05017_country": "USA"}


def load_boundaries(world_option: str | None, base: Path, outdir: Path) -> gpd.GeoDataFrame:
    if world_option:
        p = Path(world_option).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(p)
        return gpd.read_file(f"zip://{p}" if p.suffix.lower() == ".zip" else p)
    candidates = [
        base / "Natural_Earth" / "ne_110m_admin_0_countries.shp",
        base / "02_Merged_Data" / "Natural_Earth" / "ne_110m_admin_0_countries.shp",
        base / "World_Map_Heatmap_Output_Separate_Figures" / "Natural_Earth" / "ne_110m_admin_0_countries.shp",
        outdir / "Natural_Earth" / "ne_110m_admin_0_countries.shp",
        outdir / "Natural_Earth" / "ne_110m_admin_0_countries.zip",
        base / "World_Map_Heatmap_Output_Separate_Figures" / "Natural_Earth" / "ne_110m_admin_0_countries.zip",
        base / "02_Merged_Data" / "World_Map_Heatmap_Output_Separate_Figures" / "Natural_Earth" / "ne_110m_admin_0_countries.zip",
    ]
    for p in candidates:
        if p.exists():
            return gpd.read_file(f"zip://{p}" if p.suffix.lower() == ".zip" else p)
    cache = outdir / "Natural_Earth"
    cache.mkdir(parents=True, exist_ok=True)
    zp = cache / "ne_110m_admin_0_countries.zip"
    url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    print(f"Natural Earth boundaries not found locally; downloading {url}")
    try:
        urllib.request.urlretrieve(url, zp)
    except Exception as err:
        raise RuntimeError("Download failed. Supply --world /path/to/ne_110m_admin_0_countries.shp or ZIP; "
                           "the 110m Admin-0 Countries data are available from naturalearthdata.com") from err
    return gpd.read_file(f"zip://{zp}")


def make_map(world: gpd.GeoDataFrame, country: pd.DataFrame, output: Path) -> list[str]:
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.linewidth": 0.55, "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    w = world.copy()
    iso_col = next((c for c in ("ADM0_A3", "ISO_A3_EH", "ISO_A3", "iso_a3") if c in w.columns), None)
    name_col = next((c for c in ("ADMIN", "NAME", "NAME_EN", "name") if c in w.columns), None)
    if not iso_col or not name_col:
        raise ValueError("Natural Earth data missing a supported ISO3 or name column")
    w["ISO3"] = w[iso_col].astype(str).str.strip().str.upper()
    w.loc[w[name_col].isin(NAME_CORRECTIONS), "ISO3"] = w.loc[w[name_col].isin(NAME_CORRECTIONS), name_col].map(NAME_CORRECTIONS)
    map_counts = country.copy()
    map_counts["ISO3"] = map_counts["ISO3"].replace(VISUAL_ONLY_TERRITORY_MAP)
    map_counts = map_counts.groupby("ISO3", as_index=False)["Publications"].sum()
    unmapped = sorted(set(map_counts["ISO3"]) - set(w["ISO3"]))
    if unmapped:
        print("NOTE: ISO-3 codes without 1:110m polygons; mapped as small-state markers where coordinates are available:", ", ".join(unmapped))
    w = w.merge(map_counts, on="ISO3", how="left", validate="many_to_one")
    w["Publications"] = w["Publications"].fillna(0).astype(int)
    cmap = mpl.colormaps["viridis"]
    norm = LogNorm(vmin=1, vmax=int(w["Publications"].max()))
    fig = plt.figure(figsize=(13.0, 5.3), layout="constrained")
    gridspec = fig.add_gridspec(nrows=2, ncols=2, height_ratios=[12, 1], width_ratios=[3.45, 1.32],
                               wspace=0.08, hspace=0.05)
    ax = fig.add_subplot(gridspec[0, 0]); ranking_ax = fig.add_subplot(gridspec[0, 1]); cax = fig.add_subplot(gridspec[1, 0]); note_ax = fig.add_subplot(gridspec[1, 1])
    w.loc[w.Publications.eq(0)].plot(ax=ax, color="#e8edf1", edgecolor="#cdd4da", linewidth=0.25)
    w.loc[w.Publications.gt(0)].plot(ax=ax, column="Publications", cmap=cmap, norm=norm,
                                     edgecolor="#53616c", linewidth=0.25)
    # Show absent tiny states as coloured map points, with approximate centroids.
    original_country_counts = country.set_index("ISO3")["Publications"].to_dict()
    for iso in unmapped:
        if iso not in SMALL_STATE_MARKERS:
            continue
        longitude, latitude = SMALL_STATE_MARKERS[iso]
        ax.scatter([longitude], [latitude], s=20, c=[cmap(norm(original_country_counts[iso]))],
                   marker="o", edgecolors="white", linewidths=0.55, zorder=8)
    ax.set_xlim(-180, 180); ax.set_ylim(-59, 86); ax.set_axis_off()
    ax.set_title("A  Global affiliation-country distribution", fontsize=11, weight="bold", loc="left", pad=7)
    ranks = country.nlargest(10, "Publications").sort_values("Publications")
    names = [PRETTY_NAMES.get(iso, iso) for iso in ranks["ISO3"]]
    bars = ranking_ax.barh(names, ranks["Publications"], color=[cmap(norm(x)) for x in ranks["Publications"]], height=0.65)
    ranking_ax.set_title("B  Leading contributing countries", fontsize=10.4, weight="bold", loc="left", pad=8)
    ranking_ax.set_xlim(0, float(ranks["Publications"].max()) * 1.26)
    ranking_ax.set_xticks([])
    ranking_ax.tick_params(axis="y", length=0, labelsize=8.7, pad=5)
    ranking_ax.spines[["top", "left", "right", "bottom"]].set_visible(False)
    for bar, count in zip(bars, ranks["Publications"]):
        ranking_ax.text(bar.get_width() + 12, bar.get_y() + bar.get_height()/2, f"{count:,}",
                        va="center", fontsize=8.5, color="#202a35")
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_ticks([1, 10, 100, 1000])
    cb.ax.xaxis.set_major_formatter(ScalarFormatter())
    cb.ax.tick_params(labelsize=8, length=2)
    cb.set_label("Country-level publications (logarithmic scale)", fontsize=8.8, labelpad=1)
    cb.outline.set_linewidth(0.5)
    note_ax.set_axis_off()
    note_ax.text(0, 0.70, "4,972 unique geocodable records", fontsize=9, weight="bold", ha="left", va="center")
    note_ax.text(0, 0.18, "Full counting; country totals are non-additive", fontsize=8, ha="left", va="center", color="#4a5763")
    # The polygon-resolution limitation is stated in the accompanying manuscript caption;
    # placing a footnote here would overlap the bottom colour bar at print size.
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg"):
        fig.savefig(output.with_suffix("." + ext), bbox_inches="tight", pad_inches=0.07)
    fig.savefig(output.with_suffix(".png"), dpi=600, bbox_inches="tight", pad_inches=0.07)
    plt.close(fig)
    return unmapped


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="Project root (defaults to directory containing this script)")
    parser.add_argument("--country-csv", type=Path, default=None,
                        help="Original (USA=392) or corrected (USA=393) country full-counting CSV")
    parser.add_argument("--audit", type=Path, default=None,
                        help="Optional Country_Record_Level_Audit_4975.csv for independent validation")
    parser.add_argument("--world", type=str, default=None,
                        help="Optional Natural Earth .shp/.geojson/.zip to avoid downloading boundaries")
    parser.add_argument("--outdir", type=Path, default=None, help="Figure output directory")
    args = parser.parse_args()
    base = args.project_dir.expanduser().resolve()
    csv_file = (args.country_csv.expanduser().resolve() if args.country_csv else detect_country_input(base))
    outdir = (args.outdir.expanduser().resolve() if args.outdir else base / "08_Figures" / "Figure3_World_Publication_Map")
    outdir.mkdir(parents=True, exist_ok=True)
    country, procedure = load_country_counts(csv_file)
    revision_csv = outdir / "Country_Publication_Counts_Full_Counting_4972_VERIFIED.csv"
    country.to_csv(revision_csv, index=False)
    audit_result = None
    if args.audit:
        audit_path = args.audit.expanduser().resolve()
        audit_result = verify_record_audit(audit_path, country)
    w = load_boundaries(args.world, base, outdir)
    stem = outdir / "Fig_World_Publication_Map"
    unmatched = make_map(w, country, stem)
    report = {
        "input_csv": str(csv_file), "input_sha256": sha256(csv_file),
        "revision_procedure": procedure, "updated_csv": str(revision_csv),
        "updated_csv_sha256": sha256(revision_csv),
        "unique_geocodable_records": EXPECTED_GEOCODABLE,
        "application_area_records": EXPECTED_APPLICATION,
        "country_assignments_full_counting": int(country.Publications.sum()),
        "USA": int(country.set_index('ISO3').loc['USA', 'Publications']),
        "India": int(country.set_index('ISO3').loc['IND', 'Publications']),
        "China": int(country.set_index('ISO3').loc['CHN', 'Publications']),
        "number_of_country_codes": len(country),
        "unmapped_1_110m_country_codes": unmatched,
        "record_level_audit": audit_result,
        "files": {ext: str(stem.with_suffix('.'+ext)) for ext in ("pdf", "svg", "png")},
    }
    (outdir / "Fig3_Reconciliation_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nFigure 3 successfully regenerated")
    print("Country source:", csv_file)
    print("Procedure:", procedure)
    print("USA:", report['USA'], "| IND:", report['India'], "| CHN:", report['China'])
    print("Country assignments:", report['country_assignments_full_counting'], "(not unique publications)")
    print("Geocodable records: 4,972; application-area records: 4,975")
    if audit_result: print("Study-level record audit: PASS", audit_result)
    else: print("Study-level audit: not supplied; 4,972 is the locked denominator, not derivable from aggregated country totals")
    print("Vector PDF:", report['files']['pdf'])
    print("600 DPI PNG:", report['files']['png'])
    print("Report:", outdir / 'Fig3_Reconciliation_Report.json')


if __name__ == '__main__':
    main()
