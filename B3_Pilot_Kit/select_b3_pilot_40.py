#!/usr/bin/env python3
"""ARCO Revision-I, Phase B3: deterministic pilot SELECTION (not evidence coding).

Requires validated B2 initialization and verifies B2's initial, uncoded state.
Does not alter B2, Phase A or B1. It creates a new output folder with the 40
study ID selection, provenance, source acquisition checklist and author decision.

This deliberately stratified *calibration* sample is NOT a probability sample for
prevalence estimates, nor the independent Phase C inter-rater agreement sample.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
import sys
import tempfile
import shutil
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

EXPECTED_FROZEN = '95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5'
EXPECTED_SCOPE = {'Full_Text':375,'Abstract_Only':85,'Metadata_Only':25}
FULL_QUOTAS = {
 'Deep-learning models':7,
 'Hybrid deep-learning models':6,
 'Sentiment/NLP-driven models':4,
 'Transformer/attention-based models':4,
 'Metaheuristic-optimized models':3,
 'Ensemble/tree-based machine learning':1,
 'Graph-based models':1,
 'Multimodal-fusion models':1,
 'Other/unclear':1,
 'ANN/neuro-fuzzy models':1,
 'Statistical/econometric models':1,
}
SCOPE_QUOTAS={'Full_Text':30,'Abstract_Only':6,'Metadata_Only':4}
SEED_DEFAULT=20261029
MAX_TRIALS=30000


def fail(msg):
    raise ValueError(msg)


def sha256(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            d.update(block)
    return d.hexdigest()


def read_csv(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:fail('Missing CSV header: '+str(path))
        return reader.fieldnames,list(reader)


def write_csv(path,columns,rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='raise',lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def check_inputs(b2):
    if not b2.is_dir():fail('B2 output folder missing: '+str(b2))
    rfile=b2/'B2_INITIALIZATION_RECEIPT.json'
    if not rfile.is_file():fail('B2 initialization receipt missing')
    receipt=json.loads(rfile.read_text(encoding='utf-8'))
    checks={
     'status':'B2_INITIALIZED_NOT_CODED','frozen_sha256':EXPECTED_FROZEN,
     'study_count':485,'original_columns':51,'codebook_fields':45,
     'field_decision_slots':21825,'new_evidence_assertions':0,
     'new_proposed_decisions':0,'independent_phase_c_completed':False,
     'input_source_unchanged':True,
    }
    for k,v in checks.items():
        if receipt.get(k)!=v:fail(f'B2 receipt mismatch: {k} {receipt.get(k)!r} != {v!r}')
    manifest=receipt.get('generated_file_hashes')
    if not isinstance(manifest,dict) or not manifest:fail('B2 receipt has no file hash manifest')
    for name,expected in manifest.items():
        p=b2/name
        if not p.is_file() or sha256(p)!=expected:
            fail('B2 source file missing or changed since initialization: '+name)
    if sum(FULL_QUOTAS.values())!=30:fail('Fixed full-text family quotas do not sum to 30')
    h,rows=read_csv(b2/'B2_study_index_PHASEA_READONLY_51.csv')
    if len(h)!=51 or len(rows)!=485:fail('B2 source study index dimensions invalid')
    required={'Paper_ID','Evidence_Scope','Principal_Method_Family','Year','Title', 'DOI','Leakage_Risk','Validation_Design'}
    if not required.issubset(h):fail('Required source columns missing: '+str(sorted(required-set(h))))
    ids=[r['Paper_ID'] for r in rows]
    if len(set(ids))!=485 or any(not p.startswith('P') for p in ids):fail('Study IDs missing or duplicated')
    if dict(Counter(r['Evidence_Scope'] for r in rows))!=EXPECTED_SCOPE:
        fail('Evidence scopes disagree with frozen 375/85/25')
    fh,fields=read_csv(b2/'B2_approved_field_dictionary_45.csv')
    if len(fields)!=45 or len({r['Field_ID'] for r in fields})!=45:fail('Invalid approved field dictionary')
    dh,decisions=read_csv(b2/'B2_field_decisions_INITIAL_UNCODED_21825.csv')
    if len(decisions)!=21825 or len({(r['Paper_ID'],r['Field_ID']) for r in decisions})!=21825:
        fail('Decision slot count/keys disagree with B2 initialization')
    if any(r.get('Workflow_Status')!='NOT_ASSESSED' or r.get('Proposed_PhaseB_Value') for r in decisions):
        fail('B2 initialized decision register is no longer blank; use a new working-copy workflow, do not overwrite')
    for fn in ['B2_evidence_assertions.csv','B2_experiment_index.csv','B2_source_registry.csv','B2_change_manifest.csv']:
        _,rr=read_csv(b2/fn)
        if rr:fail('Non-empty B2 initial schema; initial B2 state expected: '+fn)
    pools=defaultdict(list)
    for r in rows:pools[r['Evidence_Scope'],r['Principal_Method_Family']].append(r)
    for f,q in FULL_QUOTAS.items():
        have=len(pools['Full_Text',f])
        if have<q:fail(f'Insufficient Full_Text {f}: need {q}, have {have}')
    return receipt, sorted(rows,key=lambda x:x['Paper_ID']),pools,sha256(rfile),manifest


def metrics(selected):
    vals=Counter(r['Leakage_Risk'] for r in selected)
    validation=Counter(r['Validation_Design'] for r in selected)
    years=Counter(r['Year'] for r in selected)
    return {
      'pre_2025':sum(int(r['Year'])<2025 for r in selected),
      'phaseA_high':vals['High'],'phaseA_low':vals['Low'],
      'phaseA_random_shuffled':validation['Random_Shuffled'],
      'phaseA_temporal_validation':sum(n for v,n in validation.items() if v in {
         'Chronological_Holdout','Walk_Forward','Rolling_Window','Expanding_Window','Blocked_CV'}),
      'years':dict(sorted(years.items())),'phaseA_risk':dict(sorted(vals.items())),
      'phaseA_validation':dict(sorted(validation.items())),
    }


def choose(rows,pools,seed):
    # Fixed quotas, prospective hard calibration coverage constraints. First
    # feasible seeded draw wins; no selection based on study performance.
    required={'pre_2025':8,'phaseA_high':1,'phaseA_low':1,
              'phaseA_random_shuffled':1,'phaseA_temporal_validation':1}
    for trial in range(MAX_TRIALS):
        rng=random.Random(f'ARCO-B3-v1|{seed}|trial-{trial}')
        chosen=[]
        for family,q in FULL_QUOTAS.items():
            pool=sorted(pools['Full_Text',family],key=lambda x:x['Paper_ID'])
            chosen.extend(rng.sample(pool,q))
        for scope,q in [('Abstract_Only',6),('Metadata_Only',4)]:
            pool=sorted([r for r in rows if r['Evidence_Scope']==scope],key=lambda x:x['Paper_ID'])
            chosen.extend(rng.sample(pool,q))
        x=metrics(chosen)
        if all(x[key]>=val for key,val in required.items()):
            return sorted(chosen,key=lambda r:({'Full_Text':0,'Abstract_Only':1,'Metadata_Only':2}[r['Evidence_Scope']],r['Principal_Method_Family'],r['Paper_ID'])),trial,x,required
    fail('No pilot draw fulfilled all pre-registered constraints after '+str(MAX_TRIALS)+' attempts; amendment/exception required')


def output(a,receipt,rows,selected,trial,m,required,receipt_hash,manifest):
    out=a.output_dir
    if out.exists():fail('Output folder already exists; refusing overwrite: '+str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.B3_PILOT_STAGE_',dir=out.parent))
    try:
        columns=['Pilot_ID','Paper_ID','Evidence_Scope','Principal_Method_Family','Year','Title','DOI',
                 'PhaseA_Leakage_Risk_SAMPLING_ONLY','PhaseA_Validation_Design_SAMPLING_ONLY',
                 'Family_Selection_Quota','Selection_Type','Source_Status','Coding_Status','Notes']
        selected_rows=[];registry=[];review=[]
        for i,r in enumerate(selected,1):
            scope=r['Evidence_Scope'];fam=r['Principal_Method_Family'];pid=r['Paper_ID']
            selected_rows.append(dict(Pilot_ID=f'B3_{i:03d}',Paper_ID=pid,
              Evidence_Scope=scope,Principal_Method_Family=fam,Year=r['Year'],
              Title=r['Title'],DOI=r['DOI'],
              PhaseA_Leakage_Risk_SAMPLING_ONLY=r['Leakage_Risk'],
              PhaseA_Validation_Design_SAMPLING_ONLY=r['Validation_Design'],
              Family_Selection_Quota=str(FULL_QUOTAS[fam]) if scope=='Full_Text' else '',
              Selection_Type=('SINGLETON_CENSUS' if scope=='Full_Text' and fam in {
                'ANN/neuro-fuzzy models','Statistical/econometric models'} else 'SEEDED_STRATIFIED_RANDOM'),
              Source_Status='NOT_VERIFIED',Coding_Status='NOT_STARTED',Notes=''))
            registry.append(dict(Pilot_ID=f'B3_{i:03d}',Paper_ID=pid,Title=r['Title'],DOI=r['DOI'],
                Evidence_Scope_PhaseA=scope,Primary_Paper_Path='',Primary_Paper_SHA256='',
                Paper_Title_DOI_Match='',Linked_Supplements_Checked='',
                Access_Verification_Date='',Source_Verification_Status='NOT_STARTED',
                Retrieval_Issues='',Checked_By='',Notes=''))
            review.append(dict(Pilot_ID=f'B3_{i:03d}',Paper_ID=pid,
                Pilot_Inclusion_Decision='',Reviewer_Name='',Review_Date_YYYY_MM_DD='',
                Inclusion_Comments=''))
        write_csv(stage/'B3_pilot_40_SELECTION_LOCKED_PENDING_AUTHOR.csv',columns,selected_rows)
        write_csv(stage/'B3_pilot_40_SOURCE_ACQUISITION_CHECKLIST.csv',list(registry[0]),registry)
        write_csv(stage/'B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv',list(review[0]),review)
        strata=[]
        for scope in SCOPE_QUOTAS:
            c=Counter(r['Principal_Method_Family'] for r in selected if r['Evidence_Scope']==scope)
            allc=Counter(r['Principal_Method_Family'] for r in rows if r['Evidence_Scope']==scope)
            for fam in sorted(allc):
                strata.append(dict(Evidence_Scope=scope,Principal_Method_Family=fam,
                   Frozen_Stratum_Size=allc[fam],Selected_Studies=c[fam],
                   FullText_Predefined_Quota=FULL_QUOTAS[fam] if scope=='Full_Text' and fam in FULL_QUOTAS else ''))
        write_csv(stage/'B3_pilot_40_STRATA_SUMMARY.csv',
                  ['Evidence_Scope','Principal_Method_Family','Frozen_Stratum_Size','Selected_Studies','FullText_Predefined_Quota'],strata)
        provenance={'status':'B3_PILOT_SELECTION_PREPARED__AUTHOR_REVIEW_PENDING','method':'seeded-stratified-pilot-first-feasible-draw',
           'seed':a.seed,'trial_zero_based':trial,'max_trials':MAX_TRIALS,'algorithm_version':'ARCO-B3-v1',
           'selected_paper_ids':[r['Paper_ID'] for r in selected],
           'frozen_sha256':EXPECTED_FROZEN,'b2_initialization_receipt_sha256':receipt_hash,
           'b2_initialization_status':receipt['status'],
           'scope_quotas':SCOPE_QUOTAS,'fulltext_family_quotas':FULL_QUOTAS,
           'selection_constraints_minimum':required,'achieved_metrics':m,
           'selection_motivation':'Calibrate coding decisions across rare families/older years/legacy audit statuses; not a prevalence estimate.',
           'caution':'Phase A leakage/validation values used only for sampling. They are NOT verified Phase B labels.',
           'coding_completed':False,'phase_c_independent_coding_completed':False,
           'source_acquisition_complete':False,'author_selection_approved':False,
           'generated_utc':datetime.now(timezone.utc).isoformat()}
        provenance['output_sha256']={p.name:sha256(p) for p in sorted(stage.iterdir()) if p.is_file()}
        (stage/'B3_SELECTION_MANIFEST.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        readme='''# ARCO Phase B3 — 40-study pilot selection; NOT study coding\n\nThis is a *calibration* sample, not a randomly representative set for field-wide prevalence estimates and not an independent Phase C sample.\n\n- The original frozen Phase A register, B1 approvals and B2 output were read only.\n- Check B3_pilot_40_SELECTION_LOCKED_PENDING_AUTHOR.csv (40 studies).\n- Review B3_pilot_40_STRATA_SUMMARY.csv, B3_SELECTION_MANIFEST.json and sampling method.\n- Confirm/reject each paper using B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv (author review, not automatic approval).\n- Locate each actual original paper; verify title/DOI match before any coding. Enter source file, sha256, access date in B3_pilot_40_SOURCE_ACQUISITION_CHECKLIST.csv.\n- Phase A validation/leakage labels were sampling aids ONLY and are not new verified evidence.\n- The two singleton Full_Text family strata are census selections. B3 remains purposive stratified calibration.\n- Record all B3 evidence separately in B2 evidence/source/negative-search registers. Never fill all 21,825 decision slots from the study index or these pilot labels.\n- Phase C requires genuinely independent coders and a separately defined sample.\n- Keep manuscript numerical claims frozen until B evidence verification and Phase C are completed.\n'''
        (stage/'README_B3_PILOT.md').write_text(readme,encoding='utf-8')
        if out.exists():fail('Output changed during creation; refusing overwrite')
        stage.rename(out)
    finally:
        if stage.exists():shutil.rmtree(stage)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--b2-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--seed',type=int,default=SEED_DEFAULT)
    p.add_argument('--preflight',action='store_true')
    a=p.parse_args()
    try:
        receipt,rows,pools,receipt_hash,manifest=check_inputs(a.b2_dir)
        chosen,trial,m,required=choose(rows,pools,a.seed)
        print('B2 AUTHORIZATION AND INTEGRITY: PASS')
        print('B3 PILOT QUOTAS: Full_Text 30 / Abstract_Only 6 / Metadata_Only 4')
        print('FAMILY QUOTAS: 11 / 11 satisfied')
        print('SEED:',a.seed,'FIRST FEASIBLE DRAW TRIAL:',trial)
        print('LEGACY STRATIFICATION COVERAGE (not verified study findings):',
              'pre2025=',m['pre_2025'],'High=',m['phaseA_high'],
              'Low=',m['phaseA_low'],'Random_Shuffled=',m['phaseA_random_shuffled'])
        if a.preflight:
            print('STATUS: B3_PREFLIGHT_PASS__NO_FILES_WRITTEN')
        else:
            output(a,receipt,rows,chosen,trial,m,required,receipt_hash,manifest)
            print('STATUS: B3_PILOT_SELECTION_PREPARED__AUTHOR_REVIEW_PENDING')
            print('NEW EVIDENCE CODES: 0; AUTHOR APPROVAL: NOT RECORDED')
            print('OUTPUT:',a.output_dir)
        return 0
    except Exception as e:
        print('BLOCKED:',type(e).__name__,str(e),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
