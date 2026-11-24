#!/usr/bin/env python3
"""ARCO Major 1: read-only, SHA-gated four-state COVERAGE audit.

Purpose: distinguish author-accounted decisions from study-dimension positions
requiring source assessment. This is NOT a re-coding, source-PDF verification,
publication release, or a replacement for the reviewer's complete census.

Input cohort must be the pinned 484-study NONPUBLICATION scenario. Staged 
records remain staging records. No existing inputs or outputs are overwritten.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

COHORT_SHA = 'a11488ee6fb3fcb75a167b245976226abfd4dbfa565365e509060fb79b4b438c'
LEDGER_SHA = 'db15c9774daa02b2b029804ed93e8d60149ca6d706fc37d35acd52ca0b8c91f3'
OVERLAY_SHA = '7841558057515a9aa02bca4607093443928cc20951a26a62b120d0c78f095a03'
STATES = ('Yes','No_assessed_not_documented','Unclear_ambiguous_full_text','Not_recoverable')
DIMENSIONS = (
    'Benchmark_Baseline_Reported', 'Chronological_Split','Code_Available',
    'Data_Available','Economic_Evaluation','Explainability_Method_Reported',
    'Nonstationarity_Acknowledged','Regime_Aware_Model','Regime_Specific_Evaluation',
    'Shock_Context_Mentioned','Shock_Period_Evaluation','Statistical_Testing',
    'Transaction_Costs','Uncertainty_Quantification_Reported')
TABLE10 = (
    'Nonstationarity_Acknowledged', 'Regime_Specific_Evaluation',
    'Shock_Context_Mentioned','Shock_Period_Evaluation','Chronological_Split',
    'Economic_Evaluation','Transaction_Costs','Statistical_Testing',
    'Code_Available','Data_Available')
TABLE2_DIRECT = ('Statistical_Testing', 'Economic_Evaluation', 'Code_Available')
TABLE2_NOT_DIRECT = ('Temporally ordered validation', 'Training-only preprocessing',
                     'High leakage-risk classification')


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_csv(p):
    with p.open('r',newline='',encoding='utf-8-sig') as f:
        r=csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError(f'CSV without header: {p}')
        return r.fieldnames, list(r)


def normalize_scope(raw):
    t=str(raw or '').strip().lower().replace('-','_').replace(' ','_')
    if not t: return 'SCOPE_NOT_RECORDED'
    if t in ('full_text','fulltext','full_text_verified','fulltext_verified'):
        return 'Full_Text'
    if t in ('abstract_only','abstract','abstract_only_evidence'):
        return 'Abstract_Only'
    if t in ('metadata_only','metadata','metadata_only_evidence'):
        return 'Metadata_Only'
    return 'SCOPE_UNMAPPED:'+str(raw)


def output_csv(path,fields,items):
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(items)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cohort',required=True,type=Path,
      help='Pinned B4 484-study SCENARIO_NOT_FOR_PUBLICATION CSV')
    p.add_argument('--ledger',required=True,type=Path,
      help='Stage17 1100 author-accounted ledger CSV')
    p.add_argument('--overlay',required=True,type=Path,
      help='Stage17 798 source overlay CSV (source references, not automatic verification)')
    p.add_argument('--outdir',required=True,type=Path,
      help='New output directory; preexisting path is a safety stop')
    a=p.parse_args()
    if a.outdir.exists():
        raise SystemExit(f'STOP: output already exists: {a.outdir}')
    for key,expected in [('cohort',COHORT_SHA),('ledger',LEDGER_SHA),('overlay',OVERLAY_SHA)]:
        value=getattr(a,key)
        if not value.is_file():
            raise SystemExit(f'STOP: missing {key}: {value}')
        observed=digest(value)
        if observed!=expected:
            raise SystemExit(f'STOP: {key} SHA mismatch: observed={observed}; expected={expected}')
    cohort_fields,cohort_rows=read_csv(a.cohort)
    ledger_fields,ledger_rows=read_csv(a.ledger)
    overlay_fields,overlay_rows=read_csv(a.overlay)
    if 'Paper_ID' not in cohort_fields:
        raise SystemExit('STOP: cohort Paper_ID field missing; do not infer identity')
    if any(x not in ledger_fields for x in ('Paper_ID','Dimension','Effective_Author_Approved_4State_STAGE9')):
        raise SystemExit('STOP: stage17 ledger required exact columns missing')
    if any(x not in overlay_fields for x in ('Paper_ID','Dimension','Source_PDF_SHA256','PDF_Evidence_Pages')):
        raise SystemExit('STOP: overlay required columns missing')
    if len(cohort_rows)!=484:
        raise SystemExit(f'STOP: expected 484 eligible rows; got {len(cohort_rows)}')
    ids=[r['Paper_ID'].strip() for r in cohort_rows]
    if not all(ids) or len(set(ids))!=len(ids):
        raise SystemExit('STOP: blank/duplicate cohort IDs')
    if 'P00752' in ids:
        raise SystemExit('STOP: P00752 remains in the 484 scenario')
    if len(ledger_rows)!=1100 or len(overlay_rows)!=798:
        raise SystemExit('STOP: Stage17 ledger/overlay row count unexpected')
    evidence_scope_column=next((x for x in (
        'Evidence_Scope','Evidence_Scope_Final','Full_Text_Status',
        'Source_Evidence_Scope','Evidence_Access_Scope') if x in cohort_fields),None)
    by_study={r['Paper_ID'].strip():r for r in cohort_rows}
    ledger={}
    for r in ledger_rows:
        key=(r['Paper_ID'].strip(),r['Dimension'].strip())
        if key in ledger or key[0] not in by_study or key[1] not in DIMENSIONS:
            raise SystemExit(f'STOP: duplicate/outside-cohort/unrecognized ledger key: {key}')
        state=r['Effective_Author_Approved_4State_STAGE9'].strip()
        if state not in STATES:
            raise SystemExit(f'STOP: not exact four-state value at {key}: {state!r}')
        ledger[key]=r
    if len(ledger)!=1100:
        raise SystemExit('STOP: expected 1100 distinct ledger keys')
    overlay={}
    for r in overlay_rows:
        key=(r['Paper_ID'].strip(),r['Dimension'].strip())
        if key in overlay:
            raise SystemExit(f'STOP: duplicate overlay key {key}')
        if key not in ledger:
            raise SystemExit(f'STOP: overlay not in author-accounted ledger {key}')
        overlay[key]=r
    coverage=[];queue=[];ten=[];scope_counts=Counter()
    states_by_dim=defaultdict(Counter)
    approved_studies=Counter()
    source_ref=Counter()
    for d in DIMENSIONS:
        st=Counter(); uncovered=0; refs=0
        for pid in ids:
            key=(pid,d)
            scope=normalize_scope(by_study[pid].get(evidence_scope_column,''))
            scope_counts[scope]+=1
            if key in ledger:
                lr=ledger[key];state=lr['Effective_Author_Approved_4State_STAGE9'].strip()
                st[state]+=1
                approved_studies[pid]+=1
                sha=lr.get('Source_SHA256_OR_BLANK','').strip()
                if not sha and key in overlay:
                    o=overlay[key]
                    sha=(o.get('Protected_Original_PDF_SHA256') or o.get('Source_PDF_SHA256') or '').strip()
                if sha:refs+=1;source_ref['SHA_REFERENCE_PRESENT_NOT_REVERIFIED']+=1
                else:source_ref['NO_SOURCE_SHA_IN_TWO_INPUTS']+=1
            else:
                uncovered+=1
                if d in TABLE10:
                    queue.append({
                     'Paper_ID':pid,'Dimension':d,
                     'Evidence_Scope_from_484_Register':scope,
                     'Action':'ORIGINAL_SOURCE_REVIEW_AND_AUTHOR_DECISION_REQUIRED',
                     'No_Imputed_State':'YES',
                     'Source_Hash_Reverification':'NOT_ASSESSED',
                     'Approval_Status':'NOT_AUTHOR_ACCOUNTED'})
        row={'Dimension':d,'Cohort_N':len(ids),
          'Author_Accounted':len(ids)-uncovered,'Not_Yet_Author_Accounted':uncovered,
          'Source_SHA_Reference_Present':refs}
        row.update({s:st[s] for s in STATES})
        if sum(st.values())+uncovered!=len(ids):
            raise SystemExit(f'STOP: denominator invariant broken: {d}')
        coverage.append(row);states_by_dim[d]=st
        if d in TABLE10:ten.append(row)
    full=sum(v==14 for v in approved_studies.values())
    partial=sum(0<v<14 for v in approved_studies.values())
    zero=sum(pid not in approved_studies for pid in ids)
    if (full,partial,zero)!=(78,6,400):
        raise SystemExit(f'STOP: stage17 78/6/400 invariant mismatch: {(full,partial,zero)}')
    if len(queue)!=sum(v['Not_Yet_Author_Accounted'] for v in ten):
        raise SystemExit('STOP: pending Table10 queue count mismatch')
    a.outdir.mkdir(parents=True,exist_ok=False)
    fields=['Dimension','Cohort_N','Author_Accounted','Not_Yet_Author_Accounted',
      *STATES,'Source_SHA_Reference_Present']
    output_csv(a.outdir/'ARCO_Major1_14Dimension_AuthorAccounted_Coverage_READONLY.csv',fields,coverage)
    output_csv(a.outdir/'ARCO_Major1_Table10_TenDimension_Coverage_READONLY.csv',fields,ten)
    output_csv(a.outdir/'ARCO_Major1_Table10_StillUnassessed_StudyDimension_QUEUE.csv',
      ['Paper_ID','Dimension','Evidence_Scope_from_484_Register','Action',
       'No_Imputed_State','Source_Hash_Reverification','Approval_Status'],queue)
    receipt={
      'status':'PASS_READ_ONLY_COVERAGE_NOT_FOUR_STATE_CENSUS',
      'cohort':'484_SCENARIO_NOT_PUBLICATION_FROZEN',
      'sha_pins':{'cohort':COHORT_SHA,'ledger':LEDGER_SHA,'overlay':OVERLAY_SHA},
      'study_count':len(ids),'dimensions_count':14,
      'ledger_author_accounted_positions':len(ledger),
      'full_14_dimension_studies':full,'partial_studies':partial,'zero_approved_studies':zero,
      'total_14_dimension_unaccounted':14*484-len(ledger),
      'Table10_dimensional_coverage':{
        'dimensions':len(TABLE10),'total_cells':len(TABLE10)*484,
        'author_accounted':sum(x['Author_Accounted'] for x in ten),
        'not_yet_assessed':len(queue),
        'source_sha_references_present_not_reverified':sum(x['Source_SHA_Reference_Present'] for x in ten)},
      'Table2_direct_dimension_matches':list(TABLE2_DIRECT),
      'Table2_not_same_as_14_dimension_fields':list(TABLE2_NOT_DIRECT),
      'Table9_validation_taxonomy':'NOT_DERIVABLE_FROM_CHRONOLOGICAL_SPLIT_FIELD',
      'Figure12':'REQUIRES_SOURCE_DATA_RECONCILIATION_NOT_AUTO_REDRAWN',
      'Scope_column_found':evidence_scope_column,
      'Scope_counts_across_14_dimensions':dict(scope_counts),
      'source_SHA_presence':'SOURCE_HASH_REFERENCE_ONLY_NOT_ORIGINAL_PDF_VERIFIED',
      'critical_limitations':[
        'Unaccounted positions were NOT classified as Not recoverable, No or Unclear.',
        'Four-state author-accounted status does NOT prove source evidence sufficient for every No.',
        'Source SHA references are NOT equivalent to checking original PDF bytes.',
        'No full 484-study four-state table, prevalence, manuscript edit or author approval is generated.',
        'Historical 485-study results and source-limited 484 scenario must not be silently mixed.'
      ],
      'new_approvals':0,'publication_release':'NOT_AUTHORIZED'
    }
    with (a.outdir/'ARCO_Major1_ReadOnly_CoverageReceipt.json').open('x',encoding='utf-8') as f:
        json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps({
      'status':receipt['status'],'full_partial_zero':(full,partial,zero),
      'not_yet_accounted_14_dim':receipt['total_14_dimension_unaccounted'],
      'table10':receipt['Table10_dimensional_coverage'],
      'scope_column':evidence_scope_column,
      'outdir':str(a.outdir)
      },indent=2))

if __name__=='__main__':
    try: main()
    except (ValueError, OSError) as e:
        print(f'STOP: {e}',file=sys.stderr)
        sys.exit(2)
