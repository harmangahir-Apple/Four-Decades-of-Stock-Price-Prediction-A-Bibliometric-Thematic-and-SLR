#!/usr/bin/env python3
"""Phase A 485-study conservative release repair, following Step 16V placeholder bug.

Run in Stock_Price_Prediction_SLR_ACME project root using the Harman_GPU environment.
Preserves canonical and v1-v4 inputs. Creates a new versioned freeze ONLY after QA.
Never interprets Not_Reported as a specified metric.
"""
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path('PhaseA_Freeze_Output_WSL')
V1 = ROOT/'PhaseA_Eligibility_Approved_v1_485'
V2 = ROOT/'PhaseA_Methodological_Corrections_v2_485'
V3 = ROOT/'PhaseA_Reconciliation_v3_485_DRAFT'
V4 = ROOT/'PhaseA_Finalization_Candidate_v4_485'
DEST = ROOT/'PhaseA_Technical_Corpus_FROZEN_v1_485'
CANONICAL = Path('PhaseA_Source/Supplementary_Data_S1_492_Study_Technical_Register.xlsx')
COMPILED = Path('PhaseA_Source/Compiled Files.xlsx')
EXCLUDED = {'P00332','P00384','P00567','P00681','P00814','P00928','P01181'}
SOURCES = {
    'P00663': {
        'doi':'10.1109/ICMI65310.2025.11141189',
        'title':'A Novel Lstm and Emotion-Driven Multimodal Model for Stock Price Prediction',
        'url':'https://www.linkedin.com/in/samiulislamniloy',
        'family':'Multimodal-fusion models',
        'raw_features':'Financial-news sentiment via FinBERT; other exact model inputs not specified',
        'note':'Author publication page describes FinBERT sentiment plus LSTM and 65.2% testing accuracy; no matching full text authenticated.'
    },
    'P00841': {
        'doi':'10.1109/ICCIT68739.2025.11489534',
        'title':'Enhanced Stock Trend Prediction Through Artificial Neural Networks',
        'url':'https://www.researchgate.net/publication/404082326_Enhanced_Stock_Trend_Prediction_through_Artificial_Neural_Networks',
        'family':'ANN/neuro-fuzzy models',
        'raw_features':'Not stated',
        'note':'Publication-matched abstract describes custom ANN and 97.08% accuracy; no matching full text authenticated.'
    },
}
UNCERTAINTY_FIELDS = [
    'Chronological_Split','Preprocessing_Boundary','Validation_Design',
    'Leakage_Risk','Regime_Aware_Model','Regime_Specific_Evaluation',
    'Shock_Period_Evaluation','Economic_Evaluation','Formal_Statistical_Tests',
    'Code_Available','Data_Available','Statistical_Testing','Transaction_Costs',
    'Training_Only_Preprocessing','Overlapping_Target_Control','Leakage_Control',
    'Nonstationarity_Acknowledged','Shock_Context_Mentioned',
]
UNKNOWN_METRICS = {'','not_reported','not reported','unclear','unknown','none','n/a','not stated','not specified'}
ORDERED = {'Chronological_Holdout','Walk_Forward','Rolling_Window','Expanding_Window','Blocked_CV'}

def require(test, message):
    if not test:
        raise RuntimeError(message)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''):
            h.update(part)
    return h.hexdigest()

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        d=csv.DictReader(f)
        return list(d.fieldnames or []),list(d)

def write_csv(path,fields,rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        d=csv.DictWriter(f,fieldnames=fields,extrasaction='raise')
        d.writeheader()
        d.writerows(rows)

def verify_signed(folder,filename):
    path=folder/filename
    m=json.loads(path.read_text(encoding='utf-8'))
    for name,sha in m['output_sha256'].items():
        p=folder/name
        require(p.is_file() and digest(p)==sha, f'Prior output changed: {p}')
    return m

def canonical_doi(s):
    return str(s or '').strip().casefold().removeprefix('https://doi.org/').removeprefix('doi:').strip()

def canonical_title(s):
    return re.sub(r'[^a-z0-9]', '',str(s or '').casefold())

def status_from_design(s):
    return 'Temporally ordered' if s in ORDERED else ('Random/shuffled' if s=='Random_Shuffled' else 'Unclear')

def main():
    print('='*88)
    print('STEP 16V.3 — FORECAST-TARGET TAXONOMY REPAIR / CONSERVATIVE RELEASE QA')
    print('='*88)
    require(not DEST.exists(), f'Existing freeze preserved: {DEST}')
    m1=verify_signed(V1,'Eligibility_Manifest_v1.json')
    m2=verify_signed(V2,'Correction_Manifest_v2.json')
    m3=verify_signed(V3,'Reconciliation_Manifest_v3.json')
    m4=verify_signed(V4,'Finalization_Manifest_v4.json')
    require(m1['retained_count']==485 and m1['excluded_count']==7,'v1 membership contract')
    require(m2['applied_field_changes']==27 and m4['new_field_changes']==9,'correction count contract')
    require(digest(CANONICAL)==m1['source_workbook_sha256'],'Canonical source changed')
    base=V1/'Technical_Register_485_ELIGIBILITY_ONLY.csv'
    v2=V2/'Technical_Register_485_CORRECTED_v2_DRAFT.csv'
    current=V4/'Technical_Register_485_FINALIZATION_CANDIDATE_v4.csv'
    metric_csv=V4/'Primary_Metric_Identity_Audit_v4.csv'
    fbase, rb=read_csv(base)
    f2,r2=read_csv(v2)
    fields,old=read_csv(current)
    fm, metric_audit=read_csv(metric_csv)
    require(fbase==f2==fields and len(fields)==51,'Schema mismatch')
    ids=[r['Paper_ID'] for r in old]
    require(len(ids)==len(set(ids))==len(rb)==len(r2)==485,'Cohort size/IDs wrong')
    require(ids==[r['Paper_ID'] for r in rb]==[r['Paper_ID'] for r in r2],'Row order changed')
    require(not set(ids)&EXCLUDED and {'P00401','P00620'}.issubset(ids),'Eligibility set drift')
    require(len(metric_audit)==485 and len({r['Paper_ID'] for r in metric_audit})==485,'Metric audit membership')
    require(set(r['Paper_ID'] for r in metric_audit)==set(ids),'Metric audit ID-set mismatch')
    require(all(r['Primary_Metric'].strip().casefold() in UNKNOWN_METRICS for r in metric_audit),
            'A specified primary metric exists; do not automatically omit the Sankey')
    print('[1] v1–v4 SHA-256 and 485-study membership: PASS')
    print('[2] Primary_Metric placeholders (including Not_Reported): 485/485 NON-SPECIFIED')

    # Independently verify that compiled Primary_Metric is BLANK, not merely placeholder-coded.
    wb=load_workbook(COMPILED,read_only=True,data_only=True)
    ws=wb['Section5_Coding_Consolidated']
    headers=[str(v or '').strip() for v in next(ws.iter_rows(min_row=1,max_row=1,values_only=True))]
    ci={h:i for i,h in enumerate(headers) if h}
    require({'Primary_Metric','Title'}.issubset(ci) and ('Paper_ID' in ci or 'Study_ID' in ci),
            'Compiled metric identity schema unexpected')
    idcol=ci.get('Paper_ID',ci.get('Study_ID'))
    tcol=ci['Title']
    pcol=ci['Primary_Metric']
    dcol=ci.get('DOI')
    by_id={r['Paper_ID']:r for r in old}
    matches=defaultdict(list)
    for nr,values in enumerate(ws.iter_rows(min_row=2,values_only=True),start=2):
        sid=str(values[idcol] or '').strip()
        if sid in by_id and canonical_title(values[tcol])==canonical_title(by_id[sid]['Title']):
            actual_doi=canonical_doi(values[dcol]) if dcol is not None else ''
            expected_doi=canonical_doi(by_id[sid]['DOI'])
            require(not actual_doi or not expected_doi or actual_doi==expected_doi,
                    f'Conflicting compiled DOI: {sid}')
            matches[sid].append((nr,str(values[pcol] or '').strip()))
    wb.close()
    require(len(matches)==485 and all(len(x)==1 for x in matches.values()),
            'Missing or duplicate compiled study/title identity match')
    require(all(not m[0][1] for m in matches.values()),'Compiled workbook contains primary metrics')
    print('[3] Original compiled Primary_Metric source independently verified blank: 485/485')

    # Source workbook identity and explicit v4 field-difference chain.
    wb=load_workbook(CANONICAL,read_only=True,data_only=True)
    ws=wb['Study_Register_492']
    eh=[str(c.value or '').strip() for c in ws[2][:51]]
    require(eh==fields,'Source schema mismatch')
    original_492={}
    for record in ws.iter_rows(min_row=3,max_col=51,values_only=True):
        if not any(v is not None for v in record):
            continue
        vals=['' if x is None else str(x) for x in record]
        sid=vals[0]
        require(sid not in original_492,'Duplicate source ID')
        original_492[sid]=dict(zip(fields,vals))
    wb.close()
    require(len(original_492)==492 and set(original_492)-set(ids)==EXCLUDED,
            'Original 492 → 485 eligibility membership not reconciled')
    require(all(r==original_492[r['Paper_ID']] for r in rb),'Eligibility baseline source drift')
    for sid,src in SOURCES.items():
        require(sid in by_id and canonical_doi(by_id[sid]['DOI'])==canonical_doi(src['doi']),
                f'Publication DOI mismatch: {sid}')
        require(canonical_title(by_id[sid]['Title'])==canonical_title(src['title']),
                f'Publication title mismatch: {sid}')
        require(by_id[sid]['Evidence_Scope']=='Full_Text',f'Expected wrong-PDF flag missing: {sid}')
    b={r['Paper_ID']:r for r in rb}
    v={r['Paper_ID']:r for r in old}
    old_net=sum(b[sid][f]!=v[sid][f] for sid in ids for f in fields)
    require(old_net==35,f'Unexpected pre-repair net changes: {old_net}')
    l2=read_csv(V2/'Correction_Change_Ledger_v2.csv')[1]
    l4=read_csv(V4/'Additional_Field_Changes_v4.csv')[1]
    require(Counter(r['Action'] for r in l2)==Counter({'APPLIED':27,'HOLD':17,'UNCHANGED':2}),
            '27+17+2 correction ledger drift')
    require(len(l4)==9,'Nine additional amendments not preserved')
    print('[4] Canonical eligibility and 27 + 9 prior corrections: PASS; net fields=35')

    records={sid:dict(v[sid]) for sid in ids}
    domain={name:{r[name] for r in old} for name in fields}

    # The observed categories are not the full controlled vocabulary.
    # Section 5's established forecasting-target taxonomy explicitly includes
    # Not_Reported even when this particular 485-study cohort has zero examples.
    # Permit ONLY that documented missing-target code, not arbitrary new classes.
    valid_target_codes={
        'Price','Return','Direction','Volatility','Trend_Regime',
        'Portfolio_Ranking','Multi_Target','Not_Reported'
    }
    require('Target_Primary' in domain,'Missing Target_Primary field')
    require(domain['Target_Primary'].issubset(valid_target_codes),
            'Unexpected existing Target_Primary code: '+
            repr(sorted(domain['Target_Primary']-valid_target_codes)))
    target_code_activated='Not_Reported' not in domain['Target_Primary']
    domain['Target_Primary'].add('Not_Reported')
    print('[5] Target taxonomy: PASS — established Not_Reported code '+
          ('activated (previous frequency 0)' if target_code_activated else 'already observed'))

    changes=[]
    retained_binary=[]
    def apply(sid,field,value,reason,url):
        require(field in fields,f'Unknown output field: {field}')
        require(field not in {'Paper_ID','Title','DOI'},f'Protected identity field: {field}')
        require(value is not None and not value.startswith('='),'Invalid proposed field value')
        old_value=records[sid][field]
        if old_value!=value:
            records[sid][field]=value
            changes.append({'Study_ID':sid,'Field':field,'Previous_Value':old_value,
                            'Final_Value':value,'Reason':reason,'Evidence_URL':url})

    def pick_unknown(field,desired):
        for value in desired:
            if value in domain[field]:
                return value
        raise RuntimeError(f'No defensible unknown code found for {field}')

    for sid,src in SOURCES.items():
        url=src['url']
        reason='Correct publication abstract; earlier associated PDF belonged to a different study'
        must={
            'Evidence_Scope':'Abstract_Only',
            'Evidence_Location':'Matching publication/author abstract; correct full text unavailable',
            'Principal_Method_Family':src['family'],
            'Target_Primary':pick_unknown('Target_Primary',['Not_Reported']),
            'Forecast_Horizon':pick_unknown('Forecast_Horizon',['Not_Reported']),
            'Asset_Scope':pick_unknown('Asset_Scope',['Not_Reported']),
            'Sampling_Frequency':pick_unknown('Sampling_Frequency',['Not_Reported']),
            'Market_Country':pick_unknown('Market_Country',['Not stated']),
            'Dataset_Source':'Not stated',
            'Raw_Input_Features':src['raw_features'],
            'Learning_Formulation':pick_unknown('Learning_Formulation',['Not_Reported','Unclear']),
        }
        for field,value in must.items():
            require(field in fields,f'Required register field absent: {field}')
            if field in {'Evidence_Scope','Principal_Method_Family','Target_Primary',
                         'Forecast_Horizon','Asset_Scope','Sampling_Frequency','Learning_Formulation'}:
                require(value in domain[field],f'Code not in register taxonomy: {field}={value}')
            apply(sid,field,value,reason,url)
        for field in UNCERTAINTY_FIELDS:
            if field not in fields:
                continue
            unknown=pick_unknown(field,['Unclear','Not_Reported','Not stated'])
            apply(sid,field,unknown,'Full-text-only methodological claim not supported by correct abstract',url)
        # Do not fabricate 'No' as a substantive scientific absence for a Yes/No-only field.
        retained_binary.append({'Study_ID':sid,'Field':'Technical_Indicators',
                                'Retained_Value':records[sid]['Technical_Indicators'],
                                'Limitation':'Binary Yes/No taxonomy cannot express evidence uncertainty; do not interpret No as verified absence'})
        apply(sid,'Validation_Status',status_from_design(records[sid]['Validation_Design']),
              'Independently recomputed Excel-derived status after conservative design coding',url)

    frozen=[records[sid] for sid in ids]
    require(len(frozen)==485 and not set(records)&EXCLUDED,'Post-repair cohort failure')
    require(all(frozen[i]['Paper_ID']==ids[i] for i in range(485)),'Post-repair row order failure')
    require(all(r['Validation_Status']==status_from_design(r['Validation_Design']) for r in frozen),
            'Derived validation-status inconsistency')
    require(all(r['Technical_Indicators'] in {'Yes','No'} for r in frozen),'Binary indicator domain')
    require(all(records[sid]['Evidence_Scope']=='Abstract_Only' for sid in SOURCES),
            'Known wrong-PDF evidence status not corrected')
    require(all(records[sid]==v[sid] for sid in ids if sid not in SOURCES),
            'Unrelated study modified')
    require(not re.search(r'Chinese stocks|600[, ]?719\.SS|000679\.SZ',str(records['P00661']),re.I),
            'P00661 retained stale legacy-dataset attribution')
    net=sum(b[sid][f]!=records[sid][f] for sid in ids for f in fields)
    require(changes,'No evidence repairs recorded')
    print(f'[5] Two wrong-PDF records conservatively repaired; operations={len(changes)}')
    print(f'[6] Final net changes relative to 485-study eligibility base: {net}')

    # Signed, independent category/cross-tab regeneration.
    inputs=[CANONICAL,COMPILED,base,v2,current,metric_csv,
            V2/'Correction_Change_Ledger_v2.csv',V4/'Additional_Field_Changes_v4.csv']
    inputs += [d/n for d,n in [(V1,'Eligibility_Manifest_v1.json'),
                               (V2,'Correction_Manifest_v2.json'),
                               (V3,'Reconciliation_Manifest_v3.json'),
                               (V4,'Finalization_Manifest_v4.json')]]
    inputs_sha={str(x):digest(x) for x in inputs}
    stage=Path(tempfile.mkdtemp(prefix='.phaseA_release_stage_',dir=ROOT))
    files=[]
    def export(filename,columns,rows):
        path=stage/filename
        write_csv(path,columns,rows)
        files.append(path)

    try:
        export('Technical_Register_485_FROZEN.csv',fields,frozen)
        export('Evidence_Repair_Changes_v1.csv',
               ['Study_ID','Field','Previous_Value','Final_Value','Reason','Evidence_URL'],changes)
        export('Binary_Field_Evidence_Limitations_v1.csv',
               ['Study_ID','Field','Retained_Value','Limitation'],retained_binary)
        sums=[]
        dimensions=['Evidence_Scope','Target_Primary','Learning_Formulation',
                    'Forecast_Horizon','Principal_Method_Family','Asset_Scope',
                    'Sampling_Frequency','Validation_Status','Technical_Indicators',
                    'Regime_Aware_Model','Leakage_Risk','Economic_Evaluation',
                    'Formal_Statistical_Tests','Code_Available']
        for field in dimensions:
            if field not in fields:
                continue
            ct=Counter(r[field] or '[Blank]' for r in frozen)
            require(sum(ct.values())==485,f'Distribution denominator failure: {field}')
            for value,num in sorted(ct.items()):
                sums.append({'Field':field,'Category':value,'Count':num,
                             'Percentage':f'{100*num/485:.4f}','Denominator':485})
        export('Manuscript_Category_Counts_FROZEN.csv',
               ['Field','Category','Count','Percentage','Denominator'],sums)
        pairs=[('Target_Primary','Principal_Method_Family'),
               ('Target_Primary','Forecast_Horizon'),
               ('Target_Primary','Learning_Formulation'),
               ('Principal_Method_Family','Validation_Status')]
        year=next((s for s in ('Publication_Year','PublicationYear','Year','Publication Year') if s in fields),None)
        if year:
            pairs.extend([(year,'Target_Primary'),(year,'Principal_Method_Family')])
        for left,right in pairs:
            ctr=Counter((r[left] or '[Blank]',r[right] or '[Blank]') for r in frozen)
            require(sum(ctr.values())==485,'Cross-tab mass balance failure')
            cross=[{left:l,right:r,'Count':n} for (l,r),n in sorted(ctr.items())]
            export(f'FigureData_{left}_by_{right}_FROZEN.csv',[left,right,'Count'],cross)
        copied=read_csv(stage/'Technical_Register_485_FROZEN.csv')
        require(copied==(fields,frozen),'Authoritative register round-trip failure')
        for p in files:
            require(p.is_file() and p.stat().st_size>0,f'Empty release output {p}')
        scope=Counter(r['Evidence_Scope'] for r in frozen)
        report=[
            'PHASE A TECHNICAL CORPUS — DATASET RELEASE QA',
            ('Established Target_Primary=Not_Reported category activated (previous frequency 0)'
             if target_code_activated else 'Established Target_Primary=Not_Reported already in input domain'),
            'Author-approved study denominator: 485 of 492; seven exclusions',
            'v1-v4 hashes: PASS; source workbook unchanged: PASS',
            '27+9 prior amendment operations validated; v4 net differences: 35',
            f'Additional source-sensitive repair operations: {len(changes)}',
            f'Final net changes from eligibility-only baseline: {net}',
            'Known mismatched original PDFs: P00663/P00841 (not treated as correct full texts)',
            'Both corresponding publication abstracts authenticated; Evidence_Scope=Abstract_Only',
            'Methodological positive claims without matching full text reset to uncertainty where supported',
            'Technical_Indicators is binary and does not encode uncertainty; limitations ledger supplied',
            'Primary_Metric: 485/485 genuinely blank in compiled workbook',
            'v4 audit Not_Reported tokens are PLACEHOLDERS, not specified metrics',
            'Target/Formulation/Primary-Metric Sankey: omitted from release',
            'Raw_Evaluation_Metrics not treated as coded primary metrics',
            'Missing DOIs in compiled workbook do not invalidate canonical record identities',
            'All category distributions and figure source cross-tabs re-derived from frozen records',
            'Current source data/earlier versions preserved as immutable audit trail',
            'Manuscript text and rendered figures still require synchronization',
            'Legacy register/source evidence must not be re-used as full-text evidence after identity flags',
            'Dataset release QA status: PASS',
            '', 'Evidence scopes:',
        ]+[f'{k}: {n}' for k,n in sorted(scope.items())]
        report_path=stage/'Release_QA_Report_v1.txt'
        report_path.write_text('\n'.join(report)+'\n',encoding='utf-8')
        files.append(report_path)
        for p,previous_sha in [(Path(k),v) for k,v in inputs_sha.items()]:
            require(digest(p)==previous_sha,f'Input changed during release: {p}')
        final_manifest={
            'freeze_scope':'Author-approved technical-synthesis dataset and figure-ready numerical tables',
            'final_corpus_frozen':True,
            'freeze_time':datetime.now().astimezone().isoformat(),
            'retained_studies':485,
            'excluded_ids':sorted(EXCLUDED),
            'v2_v4_operations':36,
            'v4_net_fields':35,
            'preexisting_target_values':sorted(set(r['Target_Primary'] for r in old)),
            'additional_repair_operations':len(changes),
            'final_net_differences':net,
            'abstract_only_evidence_repairs':sorted(SOURCES),
            'primary_metric_source_populated':0,
            'target_taxonomy_unknown_code':'Not_Reported',
            'target_taxonomy_code_activated':target_code_activated,
            'primary_metric_sankey_released':False,
            'rendered_figures_created':False,
            'manuscript_synchronized':False,
            'category_distributions':len(sums),
            'cross_tab_datasets':len(pairs),
            'source_sha256':inputs_sha,
            'output_sha256':{p.name:digest(p) for p in files},
        }
        (stage/'Final_Freeze_Manifest_v1.json').write_text(
            json.dumps(final_manifest,indent=2,sort_keys=True),encoding='utf-8')
        require(not DEST.exists(),'Freeze directory appeared during staging')
        os.replace(stage,DEST)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print('[7] Final output independent CSV reload and statistical reconciliation: PASS')
    print('[8] Source fingerprints and atomic commit: PASS')
    print('Freeze output:',DEST)
    print('Retained studies: 485 | exclusions: 7')
    print('Primary-metric Sankey: OMITTED — no reported source primary metrics')
    print('Original canonical and v1-v4 artifacts: UNCHANGED')
    print('STATUS: PASS — PHASE A TECHNICAL DATASET FROZEN')
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('STATUS: FAIL-CLOSED — NO NEW FREEZE RELEASED')
        print(f'{type(exc).__name__}: {exc}')
        sys.exit(1)
