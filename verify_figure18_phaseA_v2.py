#!/usr/bin/env python3
"""ACME Phase A Figure 18: authenticate the available study-level flows.

CRITICAL: The frozen 51-field register contains no robustness-analysis variable.
Default mode authenticates only asset-to-horizon flows. Full utility mode requires
a separately evidence-coded robustness table keyed by Paper_ID; NEVER infer links
from published node totals.

Outputs depend on --mode:
 stage1 (default): authentic asset-to-horizon flows, comparison, receipt
 economic-only: authentic horizon-to-economic-evaluation flows, receipt
 full: original four-group horizon-to-utility flows only if independently
       coded and checked robustness evidence CSV is supplied.

Optional --render is accepted only in full mode, after all evidence checks pass.
It calls the original presentation script with verified study-level links.
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
    missing = {"", "notreported", "horizonnotreported", "unclear", "notrecoverable", "unknown",
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



def robustness_status(raw: str, paper_id: str) -> bool:
    """Only passage-verified positive coding counts as robustness established."""
    v = norm(raw)
    if v in {"yes", "established", "documented", "true", "1"}:
        return True
    if v in {"no", "unclear", "notreported", "notestablished", "false", "0"}:
        return False
    raise RuntimeError(
        f"Robustness_Established for {paper_id} is {raw!r}; "
        "every study must have an explicit Yes / No / Unclear / Not_Reported decision "
        "before the full Figure 18 can be verified.")


def write_robustness_template(rows: list[dict[str,str]], output_dir: Path) -> Path:
    """Blank evidence collection template; does not populate conclusions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dst = output_dir / "Robustness_Evidence_Coding_Template.csv"
    if dst.exists():
        raise FileExistsError(
            f"Refusing to overwrite possibly coded evidence: {dst}")
    write_csv(dst,
              ["Paper_ID", "Robustness_Established", "Evidence_Location", "Coding_Note"],
              [{"Paper_ID": r["Paper_ID"].strip(), "Robustness_Established": "",
                "Evidence_Location": "", "Coding_Note": ""} for r in rows])
    return dst


def load_robustness(path: Path, expected_ids: set[str]) -> dict[str, bool]:
    if not path.is_file():
        raise FileNotFoundError(f"Robustness evidence CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"Paper_ID", "Robustness_Established", "Evidence_Location"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(f"Robustness CSV requires headers {sorted(required)}. "
                               "A generic evaluation proxy is unacceptable.")
        rows = list(reader)
    ids = [r["Paper_ID"].strip() for r in rows]
    if len(rows) != N or set(ids) != expected_ids or len(set(ids)) != N:
        raise RuntimeError(
            "Robustness CSV must have exactly 485 distinct Paper_ID values matching the frozen register. "
            f"Rows={len(rows)}, Missing={len(expected_ids-set(ids))}, "
            f"Unexpected={len(set(ids)-expected_ids)}")
    result = {}
    for r in rows:
        pid = r["Paper_ID"].strip()
        positive = robustness_status(r["Robustness_Established"], pid)
        if positive and not r["Evidence_Location"].strip():
            raise RuntimeError(
                f"Study {pid} is robustness=Yes but has no Evidence_Location. "
                "Record the actual source passage, page or extraction record.")
        result[pid] = positive
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen-dir", type=Path, default=Path(
        "PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485"))
    p.add_argument("--output-dir", type=Path, default=Path("Figure18_Verification_485"))
    p.add_argument("--existing-script", type=Path, default=None)
    p.add_argument("--asset-field", default=None)
    p.add_argument("--horizon-field", default=None)
    p.add_argument("--economic-field", default=None)
    p.add_argument("--mode", choices=("stage1", "economic-only", "full"), default="stage1")
    p.add_argument("--robustness-csv", type=Path,
                   help="485-ID independent robustness evidence table; required in full mode")
    p.add_argument("--write-robustness-template", action="store_true")
    p.add_argument("--inspect-only", action="store_true")
    p.add_argument("--render", action="store_true",
                   help="Only full mode, after a complete evidence-backed robustness audit")
    p.add_argument("--dpi", type=int, default=600)
    args = p.parse_args()
    if args.frozen_dir.resolve() == args.output_dir.resolve():
        raise RuntimeError("Never write outputs inside the immutable frozen folder")
    if args.render and args.mode != "full":
        raise RuntimeError(
            "--render requires --mode full and an audited --robustness-csv. "
            "Do not render the original four-category figure from incomplete evidence.")
    if args.render and args.existing_script is None:
        raise RuntimeError("--render requires --existing-script for original plot styling")
    rows, cols, digest = read_frozen(args.frozen_dir)
    if args.inspect_only:
        print("SHA-256 authenticated frozen register with 485 unique study IDs")
        for c in cols:
            if any(k in norm(c) for k in ("asset", "horizon", "economic", "robust", "shock", "regime")):
                print(c, Counter(r.get(c, "").strip() for r in rows))
        print("There is NO robustness field in the standard 51-field release.")
        return
    if args.write_robustness_template:
        dst = write_robustness_template(rows, args.output_dir)
        print("BLANK evidence template written:", dst)
        print("All 485 evidence decisions remain BLANK until externally assessed.")
        return
    asset_col = pick_field(cols, ASSET_FIELDS, args.asset_field, "asset")
    horizon_col = pick_field(cols, HORIZON_FIELDS, args.horizon_field, "horizon")
    econ_col = (pick_field(cols, ECON_FIELDS, args.economic_field, "economic")
                if args.mode != "stage1" else None)
    asset_horizon = []
    for r in rows:
        pid = r["Paper_ID"].strip()
        asset_horizon.append({"Paper_ID":pid,
                              "Asset":normalize_asset(r[asset_col],pid),
                              "Horizon":normalize_horizon(r[horizon_col],pid),
                              "Economic":(confirmed_yes(r[econ_col],pid,econ_col)
                                          if econ_col else None)})
    compare_exact(ASSET_COUNTS, Counter(x["Asset"] for x in asset_horizon), "Asset scope")
    compare_exact(HORIZON_COUNTS, Counter(x["Horizon"] for x in asset_horizon), "Horizon reporting")
    s1 = Counter((x["Asset"],x["Horizon"]) for x in asset_horizon)
    if sum(s1.values()) != N:
        raise RuntimeError("Stage 1 failed study-level conservation")
    old = None
    if args.existing_script:
        old = original_script_links(args.existing_script)
    mismatches = []
    if old is not None:
        for key in sorted(set(s1) | set(old["STAGE1_LINKS"])):
            previous, actual = int(old["STAGE1_LINKS"].get(key,0)), int(s1.get(key,0))
            if previous != actual:
                mismatches.append({"Asset":key[0], "Horizon":key[1],
                                  "Original_Script_Count":previous,
                                  "Frozen_Study_Level_Count":actual,
                                  "Difference":actual-previous})
        print(("PASS" if not mismatches else "FAIL"),
              f"original Figure 18 Stage-1 ribbon comparison: {len(mismatches)} mismatched edges")
    s2 = None
    triples = None
    status = "STAGE1_ONLY_VERIFIED; FULL_FIGURE_UNVERIFIED"
    utility_counts = None
    source_columns = {"asset":asset_col,"horizon":horizon_col,"economic":econ_col,
                      "robustness":"NOT_IN_FROZEN_REGISTER"}
    if args.mode == "economic-only":
        for row in asset_horizon:
            row["Utility"] = ("Economic evaluation established" if row["Economic"]
                              else "Economic evaluation not established in available evidence")
        utility_counts = {"Economic evaluation established":37,
                          "Economic evaluation not established in available evidence":448}
        status = "ECONOMIC_ONLY_FLOW_VERIFIED; ORIGINAL_4_CATEGORY_FIGURE_UNVERIFIED"
    elif args.mode == "full":
        if args.robustness_csv is None:
            raise RuntimeError(
                "The frozen 51-field register has NO robustness variable. "
                "Provide --robustness-csv with 485 Paper_ID evidence-coded decisions; "
                "or use --mode stage1 / --mode economic-only. "
                "Never equate shock/regime evaluation with general robustness.")
        robust_map = load_robustness(args.robustness_csv,
                                     {x["Paper_ID"] for x in asset_horizon})
        source_columns["robustness"] = str(args.robustness_csv)
        for row in asset_horizon:
            yes_e, yes_r = row["Economic"], robust_map[row["Paper_ID"]]
            row["Utility"] = ("Economic + robustness" if yes_e and yes_r else
                              "Economic only" if yes_e else
                              "Robustness only" if yes_r else "Neither established")
        utility_counts = UTILITY_COUNTS
        status = "FULL_FLOW_STUDY_LEVEL_VERIFIED_WITH_EXTERNAL_ROBUSTNESS_EVIDENCE"
    if utility_counts is not None:
        compare_exact(utility_counts, Counter(row["Utility"] for row in asset_horizon),
                      "Final-stage evidence statuses")
        s2 = Counter((row["Horizon"],row["Utility"]) for row in asset_horizon)
        triples = Counter((row["Asset"],row["Horizon"],row["Utility"])
                          for row in asset_horizon)
        if sum(s2.values()) != N or sum(triples.values()) != N:
            raise RuntimeError("Stage 2 or three-way flows failed conservation")
        if any(sum(v for (a,h),v in s1.items() if h == key) !=
               sum(v for (h,u),v in s2.items() if h == key)
               for key in HORIZON_COUNTS):
            raise RuntimeError("Inconsistent middle stage conservation")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(args.output_dir/"Figure18_Verified_Asset_to_Horizon.csv",
              ["Asset","Horizon","Studies"],
              [{"Asset":a,"Horizon":h,"Studies":n} for (a,h),n in sorted(s1.items())])
    if old is not None:
        write_csv(args.output_dir/"Figure18_Stage1_Link_Comparison.csv",
                  ["Asset","Horizon","Original_Script_Count",
                   "Frozen_Study_Level_Count","Difference"],mismatches)
    diff2 = None
    if s2 is not None:
        write_csv(args.output_dir/"Figure18_Verified_Horizon_to_FinalStage.csv",
                  ["Horizon","Final_Category","Studies"],
                  [{"Horizon":h,"Final_Category":u,"Studies":n}
                   for (h,u),n in sorted(s2.items())])
        write_csv(args.output_dir/"Figure18_Verified_ThreeWay_Flows.csv",
                  ["Asset","Horizon","Final_Category","Studies"],
                  [{"Asset":a,"Horizon":h,"Final_Category":u,"Studies":n}
                   for (a,h,u),n in sorted(triples.items())])
        if args.mode == "full" and old is not None:
            diff2 = []
            for key in sorted(set(s2) | set(old["STAGE2_LINKS"])):
                before, now = int(old["STAGE2_LINKS"].get(key,0)),int(s2.get(key,0))
                if before != now:
                    diff2.append({"Horizon":key[0],"Utility":key[1],
                                  "Original_Script_Count":before,
                                  "Verified_Study_Level_Count":now,"Difference":now-before})
            write_csv(args.output_dir/"Figure18_Stage2_Link_Comparison.csv",
                      ["Horizon","Utility","Original_Script_Count",
                       "Verified_Study_Level_Count","Difference"],diff2)
            print(("PASS" if not diff2 else "FAIL"),
                  f"original Figure 18 Stage-2 ribbon comparison: {len(diff2)} mismatched edges")
        if args.mode == "full":
            links = args.output_dir / "Figure18_VERIFIED_LINKS.py"
            def as_python(counter):
                return "{\n" + "".join(f"    {k!r}: {v},\n" for k,v in sorted(counter.items())) + "}"
            links.write_text("# SHA-256 checked frozen register + externally audited robustness by Paper_ID.\n"
                             + "STAGE1_LINKS = " + as_python(s1) + "\n\n"
                             + "STAGE2_LINKS = " + as_python(s2) + "\n",encoding="utf-8")
    receipt = {
        "status":status,"mode":args.mode,"frozen_n":N,"frozen_sha256":digest,
        "source_columns":source_columns,
        "stage1_total":sum(s1.values()),"stage1_marginals":ASSET_COUNTS,
        "horizon_marginals":HORIZON_COUNTS,
        "existing_stage1_mismatches":len(mismatches) if old is not None else None,
        "stage2_verified":s2 is not None,
        "stage2_total":sum(s2.values()) if s2 is not None else None,
        "final_stage_marginals":utility_counts,
        "existing_stage2_mismatches":len(diff2) if diff2 is not None else None,
        "critical_warning":("The frozen register has no robustness indicator; "
            "the older four-category Figure 18 is not authenticated by a 485 marginal count.")
    }
    receipt_path = args.output_dir/"Figure18_Flow_Verification_Receipt_v2.json"
    receipt_path.write_text(json.dumps(receipt, indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.render:
        run_render(args.existing_script,dict(s1),dict(s2),args.output_dir,args.dpi)
    print("\nSTATUS:",status)
    print("Audit receipt:",receipt_path)
    if args.mode == "stage1":
        print("Figure 18 Stage 2 was NOT verified. No robustness coding in frozen source.")
    if mismatches:
        print("The older Stage-1 ribbons are NOT authenticated: see Figure18_Stage1_Link_Comparison.csv")
    if diff2:
        print("The older Stage-2 ribbons are NOT authenticated: see Figure18_Stage2_Link_Comparison.csv")


if __name__ == "__main__":
    main()
