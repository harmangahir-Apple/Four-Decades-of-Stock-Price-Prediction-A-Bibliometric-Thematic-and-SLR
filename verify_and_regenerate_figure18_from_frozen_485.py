#!/usr/bin/env python3
"""ACME Phase A: VERIFY Figure 18 against the immutable 485-study register.

CRITICAL: Neither link matrix is inferred from its published margins.
Both are grouped directly from the *same individual frozen study rows*.

Default outputs (output directory):
  Figure18_Verified_Asset_to_Horizon.csv
  Figure18_Verified_Horizon_to_Utility.csv
  Figure18_Verified_ThreeWay_Flows.csv
  Figure18_Verified_Link_Comparison.csv  [if --existing-script provided]
  Figure18_Flow_Verification_Receipt.json
  Figure18_VERIFIED_LINKS.py  [copy-ready, but prefer --render]

Optional --render calls the original presentation script after REPLACING its
in-memory hand-entered link dictionaries with the empirically recovered links.
Its visual design is retained, without modifying the original Python file.

Usage:
 python verify_and_regenerate_figure18_from_frozen_485.py \\
   --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
   --existing-script regenerate_figure18_asset_horizon_utility_485_phaseA_values_serif.py \\
   --output-dir Figure18_Verification_485 --render --dpi 600

Run --inspect-only first if automatic discovery of source columns fails.
Requires only Python standard library for verification; pandas + plotly and
kaleido are required if --render is requested.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
from typing import Any

N = 485
REGISTER_FILE = "Technical_Register_485_FROZEN.csv"
MANIFEST_FILE = "Final_Freeze_Manifest_v1.json"
# Source-approved immutable hash, from Phase A lock receipt:
FROZEN_SHA = "601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f"
EXCLUDED = {"P00332", "P00384", "P00567", "P00681", "P00814", "P00928", "P01181"}

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

ASSET_FIELDS = ("Asset_Scope", "Asset_Scope_Primary", "Primary_Asset_Scope",
                "Asset_Scope_Category", "Asset_Type", "Market_Scope")
HORIZON_FIELDS = ("Forecast_Horizon", "Forecast_Horizon_Category",
                  "Forecast_Horizon_Primary", "Horizon_Reporting", "Horizon_Category",
                  "Prediction_Horizon", "Horizon_Status")
ECON_FIELDS = ("Economic_Evaluation", "Economic_Evaluation_Reported",
               "Economic_Evaluation_Performed", "Economic_Utility_Evaluation")
ROBUST_FIELDS = ("Robustness_Analysis", "Robustness_Evaluation",
                 "Robustness_Testing", "Robustness_Checks", "Robustness_Test",
                 "Robustness_Reported")


def norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(x).casefold())


def pick_field(columns: list[str], aliases: tuple[str, ...], specified: str | None, purpose: str) -> str:
    by_norm = {norm(c): c for c in columns}
    if len(by_norm) != len(columns):
        raise RuntimeError("CSV columns have indistinguishable normalized names; specify/reconcile header names")
    if specified:
        if specified not in columns:
            raise RuntimeError(f"{purpose}: --{purpose}-field {specified!r} not found; choose one of {columns}")
        return specified
    for a in aliases:
        if norm(a) in by_norm:
            return by_norm[norm(a)]
    raise RuntimeError(
        f"Cannot detect {purpose} source column. Fields available:\n" + "\n".join(columns) +
        f"\nSpecify --{purpose}-field EXACT_HEADER after inspecting the frozen register."
    )


def normalize_asset(raw: str, paper_id: str) -> str:
    v = norm(raw)
    map_ = {
        "multiplestocks": "Multiple Stocks", "multiplestock": "Multiple Stocks",
        "notreported": "Not Reported", "unclear": "Not Reported", "unknown": "Not Reported",
        "singlestock": "Single Stock", "singlestockindex": "Stock Index",
        "stockindex": "Stock Index", "singleindex": "Stock Index",
        "multipleindices": "Multiple Indices", "multipleindexes": "Multiple Indices",
        "crossmarket": "Cross Market", "crossmarkets": "Cross Market",
        "portfolio": "Portfolio",
    }
    if v not in map_:
        raise RuntimeError(f"Unknown asset scope code {raw!r} in {paper_id}; please map explicitly, not by guessing")
    return map_[v]


def normalize_horizon(raw: str, paper_id: str) -> str:
    v = norm(raw)
    missing = {"", "notreported", "unclear", "notrecoverable", "unknown",
               "notavailable", "notstated", "notspecified", "nr"}
    if v in missing:
        return "Horizon not reported"
    multi = {"multi", "multiple", "multihorizon", "multiplehorizon",
             "multiplehorizons", "multiplereportedhorizons", "multiforecasthorizon",
             "multiforecasthorizons", "severalhorizons"}
    if v in multi:
        return "Multiple horizons"
    singled = {"single", "singlereportedhorizon", "singlehorizon",
               "singlereported", "oneday", "1day", "1d", "day1", "intraday",
               "shortmultiday", "2to5days", "2to5day", "weekly", "6to10days",
               "monthly", "11to22days", "longerthanonemonth", "longerthanmonth",
               "longterm", "overnight", "onetradingday", "quarterly", "yearly",
               "annual", "multiweek", "1week", "1month"}
    if v in singled or re.fullmatch(r"\d+(day|days|d|week|weeks|month|months|hour|hours|h|min|minutes|m)", v):
        return "Single reported horizon"
    raise RuntimeError(f"Unmapped forecast horizon {raw!r} in {paper_id}; do not infer the category. "
                       "Inspect frozen codes and extend normalize_horizon explicitly.")


def confirmed_yes(raw: str, paper_id: str, colname: str) -> bool:
    v = norm(raw)
    yes = {"yes", "y", "true", "1", "present", "documented", "established"}
    nonyes = {"no", "n", "false", "0", "unclear", "notreported", "notrecoverable",
              "notdocumented", "unknown", "notspecified", "", "na", "notapplicable"}
    if v in yes:
        return True
    if v in nonyes:
        return False
    raise RuntimeError(f"Unrecognized {colname} coding {raw!r} for {paper_id}. "
                       "A negative/unknown must not be silently recoded as an affirmative result.")


def compare_exact(expected: dict[str, int], actual: Counter, title: str) -> None:
    if dict(expected) == dict(actual):
        print(f"PASS: {title} marginals reconcile with frozen Phase A ({sum(actual.values())})")
        return
    keys = list(dict.fromkeys([*expected, *actual]))
    diffs = [f"  {key}: expected={expected.get(key, 0)} actual={actual.get(key, 0)}"
             for key in keys if expected.get(key, 0) != actual.get(key, 0)]
    raise RuntimeError(f"FAIL: {title} marginals do not match Phase A:\n" + "\n".join(diffs))


def read_frozen(directory: Path):
    regpath, manifestpath = directory / REGISTER_FILE, directory / MANIFEST_FILE
    raw = regpath.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FROZEN_SHA:
        raise RuntimeError("STOP: frozen register SHA-256 mismatch. Do not use a modified file.\n"
                           f"Expected {FROZEN_SHA}\nObserved {digest}")
    manifest = json.loads(manifestpath.read_text(encoding="utf-8-sig"))
    if manifest.get("final_corpus_frozen") is not True or int(manifest.get("retained_studies", -1)) != N:
        raise RuntimeError("STOP: source manifest does not mark the 485-study frozen release")
    if manifest.get("output_sha256", {}).get(REGISTER_FILE) != digest:
        raise RuntimeError("STOP: manifest hash differs from authenticated register")
    with io.StringIO(raw.decode("utf-8-sig")) as buf:
        reader = csv.DictReader(buf)
        data = list(reader)
        headers = reader.fieldnames or []
    ids = [r.get("Paper_ID", "").strip() for r in data]
    if len(data) != N or len(set(ids)) != N or "" in ids or set(ids) & EXCLUDED:
        raise RuntimeError("STOP: frozen 485 unique Paper_ID audit failed, or an excluded ID remains")
    return data, headers, digest


def write_csv(path: Path, headers: list[str], entries: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(entries)


def original_script_links(src: Path):
    """Safely parse hard-coded link mappings as literals: do NOT execute original script."""
    tree = ast.parse(src.read_text(encoding="utf-8-sig"), filename=str(src))
    dicts = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
            if name in {"STAGE1_LINKS", "STAGE2_LINKS"}:
                dicts[name] = ast.literal_eval(stmt.value)
    if set(dicts) != {"STAGE1_LINKS", "STAGE2_LINKS"}:
        raise RuntimeError("Existing figure source must define literal STAGE1_LINKS and STAGE2_LINKS dictionaries")
    return dicts


def run_render(source: Path, edges1: dict[tuple[str,str],int], edges2: dict[tuple[str,str],int],
               outdir: Path, dpi: int) -> None:
    spec = importlib.util.spec_from_file_location("figure18_original_styling", source)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot import figure styling script {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for label, correct in (("ASSET_COUNTS", ASSET_COUNTS),
                            ("HORIZON_COUNTS", HORIZON_COUNTS),
                            ("UTILITY_COUNTS", UTILITY_COUNTS)):
        if getattr(module, label, None) != correct:
            raise RuntimeError(f"Visual source has altered {label}; refuse unverified render")
    module.STAGE1_LINKS = edges1
    module.STAGE2_LINKS = edges2
    module.OUTPUT_STEM = "Figure18_Asset_Horizon_Utility_485_VERIFIED_StudyLevel_Flows"
    previous = sys.argv
    try:
        sys.argv = [str(source), "--output-dir", str(outdir), "--dpi", str(dpi)]
        module.main()
    finally:
        sys.argv = previous


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path("PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--output-dir", type=Path, default=Path("Figure18_Verification_485"))
    p.add_argument("--existing-script", type=Path, default=None, help="Earlier Figure 18 plot generator with hand-entered links")
    p.add_argument("--asset-field", default=None)
    p.add_argument("--horizon-field", default=None)
    p.add_argument("--economic-field", default=None)
    p.add_argument("--robustness-field", default=None)
    p.add_argument("--inspect-only", action="store_true", help="Display frozen field names and their categories; write nothing")
    p.add_argument("--render", action="store_true", help="Generate new publication figure with real links; requires --existing-script")
    p.add_argument("--dpi", type=int, default=600)
    args = p.parse_args()
    if args.output_dir.resolve() == args.frozen_dir.resolve():
        raise RuntimeError("Refusing to write outputs to frozen source directory")
    rows, cols, digest = read_frozen(args.frozen_dir)
    if args.inspect_only:
        print("Authenticated 485-study register columns and observed values:")
        for c in cols:
            values = Counter(r.get(c, "").strip() for r in rows)
            if (any(key in norm(c) for key in ["asset", "horizon", "robust", "economic", "scope"])):
                print(f"{c}: {values.most_common(30)}")
            else:
                print(c)
        return
    asset_col = pick_field(cols, ASSET_FIELDS, args.asset_field, "asset")
    horizon_col = pick_field(cols, HORIZON_FIELDS, args.horizon_field, "horizon")
    econ_col = pick_field(cols, ECON_FIELDS, args.economic_field, "economic")
    robust_col = pick_field(cols, ROBUST_FIELDS, args.robustness_field, "robustness")
    print("Frozen columns:", dict(asset=asset_col, horizon=horizon_col, economic=econ_col, robustness=robust_col))

    normalized = []
    for r in rows:
        pid = r["Paper_ID"].strip()
        a = normalize_asset(r[asset_col], pid)
        h = normalize_horizon(r[horizon_col], pid)
        economic = confirmed_yes(r[econ_col], pid, econ_col)
        robust = confirmed_yes(r[robust_col], pid, robust_col)
        u = ("Economic + robustness" if economic and robust else
             "Economic only" if economic else "Robustness only" if robust else "Neither established")
        normalized.append({"Paper_ID": pid, "Asset": a, "Horizon": h, "Utility": u})

    compare_exact(ASSET_COUNTS, Counter(x["Asset"] for x in normalized), "Asset scope")
    compare_exact(HORIZON_COUNTS, Counter(x["Horizon"] for x in normalized), "Horizon reporting")
    compare_exact(UTILITY_COUNTS, Counter(x["Utility"] for x in normalized), "Evidence-supported utility")

    s1 = Counter((x["Asset"], x["Horizon"]) for x in normalized)
    s2 = Counter((x["Horizon"], x["Utility"]) for x in normalized)
    triples = Counter((x["Asset"], x["Horizon"], x["Utility"]) for x in normalized)
    if not sum(s1.values()) == sum(s2.values()) == sum(triples.values()) == N:
        raise RuntimeError("Flow conservation failed")
    if any(sum(v for (a,h), v in s1.items() if a == a0) != n for a0,n in ASSET_COUNTS.items()):
        raise RuntimeError("Stage 1 source conservation failed")
    if any(sum(v for (h,u), v in s2.items() if u == u0) != n for u0,n in UTILITY_COUNTS.items()):
        raise RuntimeError("Stage 2 destination conservation failed")
    if any(sum(v for (a,h2), v in s1.items() if h2 == h) !=
           sum(v for (h2,u),v in s2.items() if h2 == h) for h in HORIZON_COUNTS):
        raise RuntimeError("Horizon incoming/outgoing conservation failed")
    print("PASS: both stages conserve n=485, including 3-way per-study provenance")

    if args.render and not args.existing_script:
        raise RuntimeError("--render requires --existing-script PATH to preserve your figure's style")
    if args.existing_script and not args.existing_script.exists():
        raise FileNotFoundError(f"Figure 18 original style script absent: {args.existing_script}")

    diff_rows: list[dict[str,Any]] = []
    exact_match = None
    if args.existing_script:
        source_links = original_script_links(args.existing_script)
        for st, original, actual in (("Asset to horizon", source_links["STAGE1_LINKS"], s1),
                                     ("Horizon to utility", source_links["STAGE2_LINKS"], s2)):
            for key in sorted(set(original) | set(actual)):
                old = int(original.get(key,0))
                new = int(actual.get(key,0))
                if old != new:
                    diff_rows.append({"Stage": st,"Source":key[0],"Target":key[1],
                                      "Original_Script_Count":old,"Frozen_Study_Level_Count":new,
                                      "Difference_Actual_Minus_Original":new-old})
        exact_match = not diff_rows
        print(f"{'PASS' if exact_match else 'FAIL'}: current plot-script ribbons vs actual register: "
              f"{len(diff_rows)} unequal links")

    args.output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(args.output_dir/"Figure18_Verified_Asset_to_Horizon.csv", ["Asset","Horizon","Studies"],
              [{"Asset":a,"Horizon":h,"Studies":v} for (a,h),v in sorted(s1.items())])
    write_csv(args.output_dir/"Figure18_Verified_Horizon_to_Utility.csv", ["Horizon","Utility","Studies"],
              [{"Horizon":h,"Utility":u,"Studies":v} for (h,u),v in sorted(s2.items())])
    write_csv(args.output_dir/"Figure18_Verified_ThreeWay_Flows.csv", ["Asset","Horizon","Utility","Studies"],
              [{"Asset":a,"Horizon":h,"Utility":u,"Studies":v} for (a,h,u),v in sorted(triples.items())])
    if args.existing_script:
        write_csv(args.output_dir/"Figure18_Verified_Link_Comparison.csv",
                  ["Stage","Source","Target","Original_Script_Count","Frozen_Study_Level_Count",
                   "Difference_Actual_Minus_Original"],diff_rows)
    linkspath = args.output_dir/"Figure18_VERIFIED_LINKS.py"
    def literal_edges(counter):
        return "{\n" + "".join(f"    {k!r}: {v},\n" for k,v in sorted(counter.items())) + "}"
    linkspath.write_text("# Derived ONLY from SHA-256 authenticated n=485 study-level register.\n"
                         "STAGE1_LINKS = " + literal_edges(s1) + "\n\n"
                         "STAGE2_LINKS = " + literal_edges(s2) + "\n",encoding="utf-8")
    receipt = {"overall":"PASS" if (exact_match is None or exact_match) else "SOURCE_SCRIPT_LINK_MISMATCH",
               "frozen_n":N,"frozen_sha256":digest,
               "source_columns":{"asset":asset_col,"horizon":horizon_col,
                                 "economic":econ_col,"robustness":robust_col},
               "marginals":{"asset":ASSET_COUNTS,"horizon":HORIZON_COUNTS,"utility":UTILITY_COUNTS},
               "stage1_flow_total":sum(s1.values()),"stage2_flow_total":sum(s2.values()),
               "three_way_total":sum(triples.values()),
               "existing_figure_ribbons_match":exact_match,
               "different_edges_in_existing_script":len(diff_rows),
               "frozen_data_modified":False,
               "warning":"A passing marginal count alone NEVER verifies individual Sankey ribbon counts."}
    (args.output_dir/"Figure18_Flow_Verification_Receipt.json").write_text(
        json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.render:
        run_render(args.existing_script,dict(s1),dict(s2),args.output_dir,args.dpi)
    print("\nReceipt:",args.output_dir/"Figure18_Flow_Verification_Receipt.json")
    print("Exact two-stage counts:",linkspath)
    if exact_match is False:
        print("ACTION: replace unverified figure with a --render re-export; "
              "do not publish the old ribbon allocation.")

if __name__ == "__main__":
    main()
