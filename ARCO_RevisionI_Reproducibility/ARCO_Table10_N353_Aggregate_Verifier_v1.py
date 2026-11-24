#!/usr/bin/env python3
"""ARCO Revision-I: reproduce Table 10 from PRE-AGGREGATED, author-approved N=353 counts.

This is an aggregate arithmetic/formatting verification, NOT independent source
re-coding, PDF review, participant-level data access, or a 475/485-study census.
Requires the companion CSV with the precise pinned SHA256. No network access.

Examples:
  python ARCO_Table10_N353_Aggregate_Verifier_v1.py --self-test
  python ARCO_Table10_N353_Aggregate_Verifier_v1.py --output-dir ./table10_verified_new
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

N = 353
CSV_NAME = "ARCO_Table10_N353_AuthorApproved_Aggregate_v1.csv"
CSV_SHA256 = "009bfa599ba4fb7de672603c06d279a54216473b17f93daed90627c3ccd13fe8"
FIELDS = (
    "Dimension", "Yes", "No_assessed_not_documented",
    "Unclear", "Not_recoverable", "Denominator",
)
# Independently pinned within the program for arithmetic and accidental-edit checks.
EXPECTED = (
    ("Nonstationarity_Acknowledged", 123, 203, 27, 0),
    ("Regime_Specific_Evaluation", 17, 316, 20, 0),
    ("Shock_Context_Mentioned", 69, 278, 6, 0),
    ("Shock_Period_Evaluation", 10, 332, 11, 0),
    ("Chronological_Split", 129, 24, 200, 0),
    ("Economic_Evaluation", 35, 305, 13, 0),
    ("Transaction_Costs", 9, 343, 1, 0),
    ("Statistical_Testing", 62, 277, 14, 0),
    ("Code_Available", 16, 334, 3, 0),
    ("Data_Available", 36, 267, 50, 0),
)
NAMES = {
    "Nonstationarity_Acknowledged": "Non-stationarity acknowledged",
    "Regime_Specific_Evaluation": "Regime-specific evaluation",
    "Shock_Context_Mentioned": "Shock context mentioned",
    "Shock_Period_Evaluation": "Shock-period evaluation",
    "Chronological_Split": "Chronological split",
    "Economic_Evaluation": "Economic evaluation",
    "Transaction_Costs": "Transaction costs",
    "Statistical_Testing": "Formal statistical testing",
    "Code_Available": "Code availability",
    "Data_Available": "Data availability",
}


def verify_table(p: Path) -> list[tuple[str, int, int, int, int]]:
    if not p.is_file():
        raise ValueError(f"Companion aggregate CSV not found: {p}")
    observed_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    if observed_hash != CSV_SHA256:
        raise ValueError(f"Aggregate input SHA256 mismatch: {observed_hash}")
    with p.open(encoding="utf-8-sig", newline="") as handle:
        rd = csv.DictReader(handle)
        if tuple(rd.fieldnames or ()) != FIELDS:
            raise ValueError("CSV schema or column order differs from approved aggregate contract")
        raw = list(rd)
    if len(raw) != 10:
        raise ValueError(f"Expected ten dimensions, got {len(raw)}")
    converted = []
    for rec in raw:
        dim = rec["Dimension"]
        vals = tuple(int(rec[key]) for key in FIELDS[1:])
        if any(v < 0 for v in vals):
            raise ValueError(f"Negative count in {dim}")
        yes, no, unclear, not_recoverable, total = vals
        if total != N or sum(vals[:4]) != N:
            raise ValueError(f"Denominator/four-state invariant failed for {dim}")
        converted.append((dim, yes, no, unclear, not_recoverable))
    if tuple(converted) != EXPECTED:
        raise ValueError("Dimension order or agreed four-state counts do not match pinned aggregate contract")
    return converted


def percent(x: int) -> str:
    return f"{100 * x / N:.1f}"


def render_csv(rows):
    import io
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(("Dimension", "Yes_n_pct", "No_assessed_n_pct", "Unclear_n_pct", "Not_recoverable_n_pct", "N"))
    for dim, *counts in rows:
        w.writerow([NAMES[dim]] + [f"{v} ({percent(v)}%)" for v in counts] + [N])
    return out.getvalue()


def render_tex(rows):
    lines = [
        "% ARCO Table 10: verified aggregates ONLY; not study-level independent reproduction.",
        "% Use within a journal-appropriate table environment. No additional table caption included.",
        r"\begin{tabular}{lrrrr}",
        r"\hline",
        r"Practice & Yes & No assessed & Unclear & Not recoverable \\",
        r"\hline",
    ]
    for dim, *counts in rows:
        label = NAMES[dim].replace("-", "-")
        cells = [f"{v} ({percent(v)}\\%)" for v in counts]
        lines.append(label + " & " + " & ".join(cells) + " " + r"\\")
    lines.extend([
        r"\hline",
        r"\end{tabular}",
        "% The zeros in Not recoverable are structural to N353 complete-profile selection,",
        "% not an assertion that all N475 candidate-eligible records were recoverable.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).resolve().with_name(CSV_NAME))
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Write-once new folder for validation report, CSV and TeX. Optional.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        if len(EXPECTED) != 10 or any(sum(row[1:]) != N for row in EXPECTED):
            raise ValueError("Internal four-state totals fail")
        print("PASS: embedded N353 aggregate invariants")
    rows = verify_table(args.input)
    print(f"PASS: CSV SHA256 verified ({CSV_SHA256})")
    print("PASS: 10 dimensions × 353 complete profiles; four states separate")
    print("DIMENSION | YES | NO_ASSESSED | UNCLEAR | NOT_RECOVERABLE")
    for dim, *counts in rows:
        print(dim + " | " + " | ".join(str(x) for x in counts))
    print("CAUTION: These are author-approved pre-aggregated counts, not raw-data recoding.")
    print("CAUTION: N353 is a nonrandom complete-profile subset of N475 provisionally eligible studies.")
    print("CAUTION: Historical N485 and N352 document-recovery sensitivity are NOT recalculated here.")
    if args.output_dir is not None:
        target = args.output_dir.expanduser().resolve()
        if target.exists():
            raise ValueError(f"STOP: output path already exists: {target}")
        target.mkdir(parents=True, exist_ok=False)
        (target / "Table10_N353_Aggregate_Reproduced.csv").write_text(render_csv(rows), encoding="utf-8")
        (target / "Table10_N353_Tabular_Fragment.tex").write_text(render_tex(rows), encoding="utf-8")
        report = {
            "status": "PASS_AGGREGATE_ONLY_NOT_SOURCE_LEVEL_REPRODUCTION",
            "input_name": CSV_NAME,
            "input_sha256": CSV_SHA256,
            "profile_n": N,
            "dimension_count": len(rows),
            "complete_profile_cells": N * len(rows),
            "four_state_totals": {dim: dict(zip(FIELDS[1:5], counts)) for dim, *counts in rows},
            "scope_note": "N353 complete profiles within N475 provisionally eligible, with N122 incomplete. No generalization.",
            "publication_release": "NOT_AUTHORIZED",
        }
        (target / "Table10_N353_Aggregate_Verification.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"CREATED 3 output files in {target}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        raise SystemExit(2)
