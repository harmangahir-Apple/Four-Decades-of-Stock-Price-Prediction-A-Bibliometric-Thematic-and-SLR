#!/usr/bin/env python3
"""Read-only completeness validator for Phase B3 author pilot-selection review.
Does not fill or approve decisions. Does not touch Phase A/B2 sources.
"""
import argparse, csv
from collections import Counter
from datetime import date
from pathlib import Path

def read(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

p=argparse.ArgumentParser()
p.add_argument("--review",default="PhaseB3_Pilot_Selected_v1/B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv")
p.add_argument("--selection",default="PhaseB3_Pilot_Selected_v1/B3_pilot_40_SELECTION_LOCKED_PENDING_AUTHOR.csv")
p.add_argument("--guide",default="B3_40_STUDY_RECOMMENDATIONS_AND_EVIDENCE.csv")
a=p.parse_args()
rev=read(a.review); sel=read(a.selection); guide=read(a.guide)
errors=[]
if len(rev)!=40 or len(sel)!=40:errors.append("Must contain 40 pilot rows.")
if len({r["Paper_ID"] for r in rev})!=40:errors.append("Duplicate Paper_ID in form.")
if [(r["Pilot_ID"],r["Paper_ID"]) for r in rev] != [(r["Pilot_ID"],r["Paper_ID"]) for r in sel]:
    errors.append("Form Pilot_ID/Paper_ID order differs from locked selection.")
issues={g['Paper_ID']:g for g in guide if not g["Recommendation"].startswith("APPROVE_CANDIDATE")}
counts=Counter()
for r in rev:
    d=r["Pilot_Inclusion_Decision"].strip().upper()
    counts[d or "BLANK"]+=1
    if d and d not in {"APPROVE","REJECT"}:
        errors.append(f"{r['Pilot_ID']}: invalid decision {d!r}.")
    if d:
        if not r['Reviewer_Name'].strip():errors.append(f"{r['Pilot_ID']}: reviewer name missing.")
        try:
            date.fromisoformat(r['Review_Date_YYYY_MM_DD'].strip())
        except ValueError:errors.append(f"{r['Pilot_ID']}: review date invalid.")
        if not r["Inclusion_Comments"].strip():errors.append(f"{r['Pilot_ID']}: comments blank.")
    if r["Paper_ID"] in issues and d=="APPROVE":
        print("FLAGGED APPROVAL REQUIRES DOCUMENTED RESOLUTION:",r['Pilot_ID'],r['Paper_ID'],issues[r["Paper_ID"]]["Recommendation"])
print("Review rows:",len(rev),"Selected rows:",len(sel))
print("Decisions:",dict(counts))
print("Flagged studies:",", ".join(sorted(issues)))
if errors:
    print("FORM VALIDATION: FAIL")
    for e in errors:print(" -",e)
else:
    print("FORM STRUCTURE: PASS")
    if counts.get("BLANK"):print("AUTHOR REVIEW: PENDING",counts["BLANK"],"blank decisions")
    elif counts.get("REJECT"):print("AUTHOR REVIEW: REJECTIONS REQUIRE ADJUDICATION")
    else:print("AUTHOR FORM: COMPLETED; actual scientific approval and flagged-issue resolution still require evidence")
