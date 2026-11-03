#!/usr/bin/env python3
"""Versioned ARCO B1 v1.2 sign-off; no automatic author approvals, read-only Phase A.

Stdlib-only. Checks the Phase A frozen SHA, all v1.1 core structure, extra
v1.2 codebook guardrails, immutable package assets, and independently re-runs
12 synthetic calibration scenarios against the actual *user-authored* review CSV.
Creates a sign-off receipt only after all eleven author gates are approved.
"""
import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

PATCH_IDS={'TV02','PL11','ST01','EC01','EC02','RP01'}
BASE_COLUMNS=['Field_ID','Domain','Field_Name','Operational_question','YES_threshold',
              'EXPLICIT_NO_threshold','NOT_APPLICABLE_rule','Priority','Source_sections',
              'PhaseA_exact_column','Common_ambiguity_and_guardrail']

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''):h.update(b)
    return h.hexdigest()

def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def load_legacy(path):
    spec=importlib.util.spec_from_file_location('b1_v11_readonly_validation',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def csv_integrity(package,errors):
    b=rows(package/'PhaseB1_Evidence_Codebook_v1_1_SIGNOFF_CANDIDATE.csv')
    v=rows(package/'PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv')
    if len(b)!=45 or len(v)!=45 or [x['Field_ID'] for x in b]!=[x['Field_ID'] for x in v]:
        errors.append('v1.2 codebook must preserve the same 45 ordered field IDs');return
    for prev,nxt in zip(b,v):
        fid=prev['Field_ID']
        for col in BASE_COLUMNS:
            if col=='Common_ambiguity_and_guardrail' and fid in PATCH_IDS:
                if not nxt[col].startswith(prev[col]+' v1.2:'):
                    errors.append(f'{fid} v1.2 guardrail must append transparently to v1.1')
            elif prev[col]!=nxt[col]:
                errors.append(f'Unapproved change in {fid}.{col}')
    changelog=rows(package/'B1_v1_2_Field_Rule_Change_Log.csv')
    if len(changelog)!=6 or {x['Field_ID'] for x in changelog}!=PATCH_IDS:
        errors.append('v1.2 addendum change log must describe 6 amended field guardrails')
    for g in changelog:
        if g['Author_Approval_Status']!='PENDING':
            errors.append('Immutable changelog may not claim automatic author approval')

def check_calibration(package,review,output,errors,pending):
    status={'review_file':str(review) if review else None,'case_count':0,'accepted_count':0}
    if not review:
        pending.append('Pass --calibration-review pointing to your completed 12-case AUTHOR review CSV')
        return status
    if not review.is_file():
        pending.append(f'Local 12-case author review CSV not found: {review}')
        return status
    try:
        r=rows(review)
        expected={f'CAL{i:02d}' for i in range(1,13)}
        if len(r)!=12 or {x.get('Case_ID') for x in r}!=expected:
            errors.append('Calibration review must have 12 unique IDs CAL01–CAL12');return status
        status['case_count']=len(r)
        for x in r:
            case=x.get('Case_ID','')
            decision=(x.get('Author_Decision_ACCEPT_or_REVISE','') or '').strip()
            if decision!='ACCEPT':
                pending.append(f'{case} is not author-ACCEPT: {decision or "blank"}')
                continue
            if not (x.get('Author_Name') or '').strip():
                errors.append(f'{case} accepted without reviewer name')
            try:
                day=dt.date.fromisoformat((x.get('Review_Date_YYYY_MM_DD') or '').strip())
                if day>dt.date.today():errors.append(f'{case} review date is in the future')
            except ValueError:errors.append(f'{case} review date invalid')
            if case in ('CAL10','CAL11') and not (x.get('Author_Comments') or '').strip():
                errors.append(f'{case} needs its accepted-with-clarification comment')
            status['accepted_count']+=1
        status['file_sha256']=digest(review)
        if any(x.startswith(('CAL','Invalid')) for x in errors) or status['accepted_count']!=12:
            return status
        cal_out=output/'Synthetic_Calibration_Verification'
        args=[sys.executable,str(package/'Calibration/calibrate_g03_g11.py'),
              '--casebook',str(package/'Calibration/B1_12_Synthetic_Calibration_Cases.csv'),
              '--expected',str(package/'Calibration/B1_12_Case_Expected_Results.json'),
              '--author-review',str(review),'--output-dir',str(cal_out)]
        res=subprocess.run(args,capture_output=True,text=True,timeout=45)
        status['test_stdout']=res.stdout.strip()
        if res.returncode:
            errors.append('12-case independent calibration rerun failed: '+(res.stderr or res.stdout)[-1500:]);return status
        receipt=json.loads((cal_out/'B1_G03_G11_Calibration_Receipt.json').read_text(encoding='utf-8'))
        if (receipt.get('result')!='PASS_SYNTHETIC_LOGIC_ONLY' or receipt.get('cases_passed')!=12
            or receipt.get('author_calibration_review',{}).get('status')!='ALL_ACCEPTED_BY_REVIEWING_AUTHOR'
            or set(receipt.get('rejected_invalid_publication_cases',{}))!={'incomplete_workflow','ordinal_crosswalk'}):
            errors.append('Synthetic calibration receipt does not match required 12/12 + safeguards')
        else:status['result']='12/12_SYNTHETIC_PASS__AUTHOR_ACCEPTANCE_DOCUMENTED'
    except (UnicodeError,KeyError,ValueError,TimeoutError,subprocess.TimeoutExpired) as e:
        errors.append('Calibration validation error: '+str(e))
    return status

def main():
    ap=argparse.ArgumentParser(description='ARCO B1 v1.2 signoff candidate; user decisions never prefilled')
    ap.add_argument('--frozen',type=Path,required=True)
    ap.add_argument('--package-dir',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--calibration-review',type=Path,help='Your local completed CAL01-CAL12 author CSV')
    ap.add_argument('--output-dir',type=Path,default=Path('PhaseB1_v1_2_Signoff_Audit'))
    ap.add_argument('--finalize',action='store_true')
    a=ap.parse_args()
    if not a.frozen.is_file():ap.error('Frozen XLSX not found: '+str(a.frozen))
    if not a.package_dir.is_dir():ap.error('Package directory not found')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    hard=[];pending=[]
    try:
        legacy=load_legacy(a.package_dir/'phaseB1_signoff_gate.py')
        old_hard,old_pending,base=legacy.check_issues(a.frozen,a.package_dir,False)
        hard.extend(old_hard);pending.extend(old_pending)
        integrity=json.loads((a.package_dir/'B1_v1_2_File_Hash_Manifest.json').read_text(encoding='utf-8'))
        for rel,expected in integrity.items():
            p=a.package_dir/rel
            if not p.is_file() or digest(p)!=expected:hard.append('Immutable v1.2 package component fails SHA-256: '+rel)
        csv_integrity(a.package_dir,hard)
        approvals=rows(a.package_dir/'B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv')
        for x in approvals:
            if x['Gate_ID'] in ('G03','G11') and x['Author_Decision'].strip().upper()=='APPROVE':
                if not (x['Author_Comments'] or '').strip():hard.append(x['Gate_ID']+' requires a rationale explicitly accepting v1.2 evidence-state rules')
        cal=check_calibration(a.package_dir,a.calibration_review,a.output_dir,hard,pending)
        meta={'protocol':'Phase B1 v1.2 author-ratification candidate','date_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'frozen_sha256':base.get('frozen_sha256'),'frozen_records':base.get('frozen_rows'),
              'frozen_columns':base.get('frozen_columns'),'codebook_fields':base.get('field_count'),
              'codebook_v1_2_sha256':digest(a.package_dir/'PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv'),
              'addendum_sha256':digest(a.package_dir/'B1_v1_2_Scientific_Rule_Addendum_SIGNOFF_CANDIDATE.md'),
              'approval_form_sha256':digest(a.package_dir/'B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv'),
              'calibration':cal,'author_gates_approved':base.get('author_gates_approved',0),
              'author_gates_rejected':base.get('author_gates_rejected',[]),
              'phase_a_mutated':False,'independent_phase_c_completed':False,
              'blocking_errors':hard,'pending_author_actions':pending}
        status='HARD_VALIDATION_FAILED' if hard else ('AUTHOR_RATIFICATION_PENDING' if pending else 'READY_TO_RECORD_RATIFICATION')
        meta['status']=status
        audit=a.output_dir/'B1_v1_2_Gate_Audit.json'
        audit.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print('FROZEN SHA-256:',meta['frozen_sha256'])
        print('FROZEN STUDIES / COLUMNS:',meta['frozen_records'],'/',meta['frozen_columns'])
        print('v1.2 CODEBOOK FIELDS:',meta['codebook_fields'],'(6 guardrails amended)')
        print('TECHNICAL GATE:', 'FAIL' if hard else 'PASS')
        print('CALIBRATION:',cal.get('result','PENDING (see messages)'))
        print('AUTHOR GATES:',base.get('author_gates_approved',0),'/11 APPROVED')
        for e in hard:print('ERROR:',e)
        for e in pending:print('PENDING:',e)
        if not hard and not pending and a.finalize:
            meta.update(status='B1_v1_2_AUTHOR_RATIFICATION_RECORDED__B2_INITIALIZATION_AUTHORIZED',
                  authority='Author-declared approval; not independently authenticated or equivalent to Phase C')
            receipt=a.output_dir/'B1_v1_2_AUTHOR_RATIFICATION_RECEIPT.json'
            receipt.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            print('STATUS:',meta['status'],'\nRECEIPT:',receipt)
        else:
            print('STATUS:',status,'— NO APPROVAL RECEIPT ISSUED')
        print('AUDIT:',audit)
        if hard:return 2
        if pending and a.finalize:return 3
        return 0
    except Exception as e:
        print('STOP: Could not authenticate the signoff package:',type(e).__name__,e,file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
