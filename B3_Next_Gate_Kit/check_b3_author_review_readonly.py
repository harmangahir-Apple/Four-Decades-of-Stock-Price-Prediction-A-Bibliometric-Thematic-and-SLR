#!/usr/bin/env python3
"""Read-only Phase B3 status/check; never creates author approvals or edits frozen data."""
import argparse
import csv
import hashlib
from collections import Counter
from datetime import date
from pathlib import Path

FROZEN_SHA = '95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5'
FLAGGED = {'P01112', 'P03446', 'P00584', 'P00853'}

def load(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path('.'))
    a=p.parse_args(); base=a.project
    selection=base/'PhaseB3_Pilot_Selected_v1/B3_pilot_40_SELECTION_LOCKED_PENDING_AUTHOR.csv'
    review=base/'PhaseB3_Pilot_Selected_v1/B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv'
    frozen=base/'Supplementary_Data_S1_485_FROZEN.xlsx'
    print('ARCO B3 AUTHOR-REVIEW STATUS — READ ONLY')
    if frozen.exists():
        got=hashlib.sha256(frozen.read_bytes()).hexdigest()
        print('Frozen SHA256:',got,'PASS' if got==FROZEN_SHA else 'MISMATCH')
        if got!=FROZEN_SHA:
            raise SystemExit('STOP: frozen source differs from signed Phase A source')
    else:
        print('Frozen workbook not present at expected path; SHA verification skipped')
    for f in (selection,review):
        if not f.is_file(): raise SystemExit(f'STOP: cannot locate {f}')
    sr,rr=load(selection),load(review)
    sid=[r.get('Paper_ID','') for r in sr]; rid=[r.get('Paper_ID','') for r in rr]
    if (len(sr),len(rr),len(set(sid)),len(set(rid)))!=(40,40,40,40):
        raise SystemExit('STOP: expected exactly 40 unique IDs in each file')
    if set(sid)!=set(rid):raise SystemExit('STOP: selection/review Paper_ID mismatch')
    for p_id in sid:
        s=next(r for r in sr if r['Paper_ID']==p_id)
        r=next(r for r in rr if r['Paper_ID']==p_id)
        if s['Pilot_ID']!=r['Pilot_ID']:
            raise SystemExit('STOP: Pilot_ID mismatch: '+p_id)
    stats=Counter((r.get('Pilot_Inclusion_Decision') or '').strip().upper() or 'BLANK' for r in rr)
    print('Selection and review IDs:',len(sr),'/ 40 — PASS')
    print('Author decisions:',dict(stats))
    problems=[]; incomplete=[]
    for r in rr:
        pid=r['Paper_ID']; d=(r.get('Pilot_Inclusion_Decision') or '').strip().upper()
        if d=='':
            incomplete.append(pid); continue
        if d not in {'APPROVE','REJECT'}:
            problems.append(f'{pid}: unknown decision value {d!r}');continue
        if not (r.get('Reviewer_Name') or '').strip():
            problems.append(f'{pid}: reviewer name blank')
        dt=(r.get('Review_Date_YYYY_MM_DD') or '').strip()
        try: date.fromisoformat(dt)
        except ValueError: problems.append(f'{pid}: invalid decision date {dt!r}')
        c=(r.get('Inclusion_Comments') or '').strip()
        if not c: problems.append(f'{pid}: comments blank')
        if pid in FLAGGED and ('remains pending' in c.lower() or 'pending investigation' in c.lower()):
            problems.append(f'{pid}: flagged decision recorded but comment still says pending investigation; reconcile')
    print('Flagged studies:',', '.join(sorted(FLAGGED)))
    print('Flagged without author decision:',', '.join(sorted(FLAGGED.intersection(incomplete))) or 'NONE')
    if problems:
        print('FORM ISSUES:',len(problems))
        for x in problems: print(' -',x)
    else: print('FORM STRUCTURAL/COMPLETENESS ISSUES: NONE DETECTED')
    if incomplete:
        print('GATE STATUS: PENDING_AUTHOR_SELECTION_DECISIONS')
        print('Unresolved review decisions:',len(incomplete))
    elif problems:
        print('GATE STATUS: HOLD__REVIEW_CONFLICTS')
    else:
        print('GATE STATUS: FORM_COMPLETE__SCIENTIFIC_REVIEW_AND_SOURCE_VERIFICATION_STILL_REQUIRED')
    print('This tool does NOT validate paper eligibility, source access, pilot quotas after replacement, or 45-field evidence coding.')

if __name__=='__main__': main()
