#!/usr/bin/env python3
"""Independent Phase A release QA and fail-closed technical-corpus freeze.

Run from ~/projects/Stock_Price_Prediction_SLR_ACME with the existing Harman_GPU
conda environment. Read-only against all source and v1-v4 files. Writes a NEW
versioned freeze folder only if all release gates pass.
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
V1 = ROOT / 'PhaseA_Eligibility_Approved_v1_485'
V2 = ROOT / 'PhaseA_Methodological_Corrections_v2_485'
V3 = ROOT / 'PhaseA_Reconciliation_v3_485_DRAFT'
V4 = ROOT / 'PhaseA_Finalization_Candidate_v4_485'
FREEZE = ROOT / 'PhaseA_Technical_Corpus_FROZEN_v1_485'
COMPILED = Path('PhaseA_Source/Compiled Files.xlsx')
CANONICAL = Path('PhaseA_Source/Supplementary_Data_S1_492_Study_Technical_Register.xlsx')
EXCLUDED = {'P00332','P00384','P00567','P00681','P00814','P00928','P01181'}
RETAIN = {'P00401','P00620'}
IDENTITY_FLAGS = {'P00057','P00211','P00401','P00661','P00826',
                  'P00909','P01551','P02642','P03446'}
INCORRECT_PDF_FLAGS = {'P00663','P00841'}

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)

def write_csv(path, columns, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='raise')
        writer.writeheader()
        writer.writerows(rows)

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def norm_title(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').casefold())

def norm_doi(s):
    return re.sub(r'^doi\s*:\s*', '', str(s or '').strip().casefold()).removeprefix('https://doi.org/').strip()

def formula_status(design):
    if design in {'Chronological_Holdout','Walk_Forward','Rolling_Window',
                  'Expanding_Window','Blocked_CV'}:
        return 'Temporally ordered'
    if design == 'Random_Shuffled':
        return 'Random/shuffled'
    return 'Unclear'

def signed_files(directory, manifest_name):
    path = directory / manifest_name
    require(path.is_file(), f'Missing provenance manifest: {path}')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    hashes = manifest.get('output_sha256')
    require(isinstance(hashes, dict) and hashes, f'Invalid manifest output hashes: {path}')
    for filename, expected in hashes.items():
        item = directory / filename
        require(item.is_file() and digest(item) == expected,
                f'Hash or existence failure: {item}')
    return manifest


def main():
    print('=' * 91)
    print('STEP 16T — INDEPENDENT PHASE A RELEASE QA / FAIL-CLOSED FREEZE')
    print('=' * 91)
    require(not FREEZE.exists(), f'Existing freeze directory preserved: {FREEZE}')
    m1 = signed_files(V1, 'Eligibility_Manifest_v1.json')
    m2 = signed_files(V2, 'Correction_Manifest_v2.json')
    m3 = signed_files(V3, 'Reconciliation_Manifest_v3.json')
    m4 = signed_files(V4, 'Finalization_Manifest_v4.json')
    require(m1.get('retained_count') == 485 and m1.get('excluded_count') == 7,
            'Eligibility-manifest denominator mismatch')
    require(m2.get('applied_field_changes') == 27, 'v2 amendment count mismatch')
    require(m3.get('technical_corpus') == 485, 'v3 denominator mismatch')
    require(m4.get('retained_studies') == 485 and m4.get('new_field_changes') == 9,
            'v4 denominator/amendment mismatch')
    for name, expected in m4.get('input_sha256', {}).items():
        p = Path(name)
        require(p.is_file() and digest(p) == expected,
                f'Changed or missing v4 input: {p}')
    require(digest(CANONICAL) == m1['source_workbook_sha256'], 'Canonical 492 source changed')
    require(digest(V1 / 'Technical_Register_485_ELIGIBILITY_ONLY.csv') == m2['base_register_sha256'],
            'Eligibility-only baseline changed')
    require(digest(V2 / 'Technical_Register_485_CORRECTED_v2_DRAFT.csv') == m3['source_v2_register_sha256'],
            'v2 source changed')
    print('[1] Source, provenance, and v1–v4 output fingerprints: PASS')

    base_cols, base = read_csv(V1 / 'Technical_Register_485_ELIGIBILITY_ONLY.csv')
    v2_cols, v2 = read_csv(V2 / 'Technical_Register_485_CORRECTED_v2_DRAFT.csv')
    v4_path = V4 / 'Technical_Register_485_FINALIZATION_CANDIDATE_v4.csv'
    v4_cols, current = read_csv(v4_path)
    require(base_cols == v2_cols == v4_cols and len(v4_cols) == 51, 'Schema drift')
    ids = [r['Paper_ID'] for r in base]
    require(len(base) == len(v2) == len(current) == len(ids) == 485, '485-study count mismatch')
    require(len(set(ids)) == 485 and not set(ids) & EXCLUDED, 'Membership collision')
    require([r['Paper_ID'] for r in v2] == [r['Paper_ID'] for r in current] == ids,
            'Study order or membership changed')
    require(RETAIN.issubset(ids), 'Approved retained study missing')
    for row in current:
        require(row['Validation_Status'] == formula_status(row['Validation_Design']),
                f'Formula-status semantics drift: {row["Paper_ID"]}')
        require(row['Technical_Indicators'] in {'Yes','No'},
                f'Technical_Indicators domain violation: {row["Paper_ID"]}')
    print('[2] 485-study membership, 51 fields, row order, formula semantics: PASS')

    # Independent membership check against the unchanged 492-study workbook.
    workbook = load_workbook(CANONICAL, read_only=True, data_only=True)
    sheet = workbook['Study_Register_492']
    excel_headers = [str(c.value or '').strip() for c in sheet[2][:51]]
    require(excel_headers == base_cols, 'Workbook header mismatch')
    from_workbook = {}
    for cells in sheet.iter_rows(min_row=3, max_col=51, values_only=True):
        if not any(v is not None for v in cells):
            continue
        values = ['' if v is None else str(v) for v in cells]
        sid = values[0]
        require(sid and sid not in from_workbook, f'Duplicate/empty canonical ID: {sid}')
        from_workbook[sid] = dict(zip(base_cols, values))
    workbook.close()
    require(len(from_workbook) == 492, 'Canonical workbook does not contain 492 studies')
    require(set(from_workbook) - set(ids) == EXCLUDED,
            'Author-approved seven exclusions are not the exact membership difference')
    for row in base:
        require(row == from_workbook[row['Paper_ID']],
                f'485 eligibility baseline differs from workbook: {row["Paper_ID"]}')
    print('[3] Independent 492 → 485 source-row and approved exclusion comparison: PASS')

    _, ledger = read_csv(V2 / 'Correction_Change_Ledger_v2.csv')
    _, plus = read_csv(V4 / 'Additional_Field_Changes_v4.csv')
    _, held = read_csv(V3 / 'Outstanding_17_Held_Proposals_v3.csv')
    _, closed = read_csv(V4 / 'Closed_17_Holds_v4.csv')
    require(Counter(r['Action'] for r in ledger) == Counter(
        {'APPLIED':27,'HOLD':17,'UNCHANGED':2}), 'v2 ledger status mismatch')
    require(len(plus) == 9 and len(held) == len(closed) == 17,
            'v4 changes or disposition count mismatch')
    b = {r['Paper_ID']: r for r in base}
    mid = {r['Paper_ID']: r for r in v2}
    now = {r['Paper_ID']: r for r in current}
    first_changes = {}
    for r in ledger:
        if r['Action'] == 'APPLIED':
            key = (r['Study_ID'],r['Field'])
            require(key not in first_changes, f'Duplicate v2 change: {key}')
            first_changes[key] = (r['Original_Value'],r['Proposed_Value'])
    second_changes = {}
    for r in plus:
        key = (r['Study_ID'],r['Field'])
        require(key not in second_changes, f'Duplicate v4 change: {key}')
        second_changes[key] = (r['Original_Value'],r['Corrected_Value'])
    diff1, diff2 = {}, {}
    for sid in ids:
        for field in base_cols:
            if b[sid][field] != mid[sid][field]:
                diff1[sid,field] = (b[sid][field],mid[sid][field])
            if mid[sid][field] != now[sid][field]:
                diff2[sid,field] = (mid[sid][field],now[sid][field])
    require(diff1 == first_changes, 'v2 actual changes differ from 27-change ledger')
    require(diff2 == second_changes, 'v4 actual changes differ from 9-change ledger')
    hmap = {(r['Study_ID'],r['Field']):r for r in held}
    cmap = {(r['Study_ID'],r['Field']):r for r in closed}
    require(len(hmap) == len(cmap) == 17 and set(hmap) == set(cmap),
            '17 held proposals not all uniquely dispositioned')
    for key, item in cmap.items():
        sid,field = key
        require(item['Final_Value'] == now[sid][field],f'Final disposition differs from register: {key}')
        if item['Disposition'] == 'PRESERVE_EVIDENCE_LIMITATION':
            require(mid[sid][field] == now[sid][field],f'Preserve disposition changed data: {key}')
        elif item['Disposition'] == 'APPLY_SOURCE_SUPPORTED':
            require(item['Outcome'] in {'APPLIED','ALREADY_MATCHES'},
                    f'Unexpected application outcome: {key}')
        else:
            raise RuntimeError(f'Unknown hold disposition: {key}')
    unique_net = sum(b[sid][field] != now[sid][field] for sid in ids for field in base_cols)
    print(f'[4] 27 + 9 logged amendment operations: PASS; unique net changed fields: {unique_net}')
    print('[5] Seventeen hold dispositions reconciled: PASS')

    family = {r['Paper_ID']:r['Principal_Method_Family'] for r in current}
    require(family['P00211']=='Statistical/econometric models', 'P00211 ARIMA family drift')
    require(family['P00425']=='Other/unclear', 'P00425 comparison family drift')
    require(family['P00661']=='Deep-learning models', 'P00661 family drift')
    require(family['P00401']=='Hybrid deep-learning models', 'P00401 hybrid family drift')
    require(family['P00826']=='Sentiment/NLP-driven models', 'P00826 family drift')
    require(now['P00661']['Sampling_Frequency']=='Monthly', 'P00661 frequency drift')
    require(now['P00661']['Asset_Scope']=='Single_Stock', 'P00661 stock scope drift')
    require('NVIDIA' in now['P00661']['Dataset_Source'].upper(), 'P00661 dataset source drift')
    bad_alias = re.compile(r'Chinese stocks|600[, ]?719\.SS|000679\.SZ',re.I)
    for col,val in now['P00661'].items():
        require(not bad_alias.search(val),f'P00661 stale Chinese-stock label: {col}')
    require(sum(Counter(family.values()).values()) == 485,'Family totals do not reconcile')
    print('[6] Source-sensitive methodological taxonomy and P00661 provenance: PASS')

    # Re-evaluate the known wrong-PDF cases rather than relying on a past incorrect PDF.
    evidence_status = {}
    blockers = []
    for sid in sorted(INCORRECT_PDF_FLAGS):
        require(sid in now, f'Prior wrong-PDF record absent unexpectedly: {sid}')
        scope = now[sid]['Evidence_Scope']
        evidence_status[sid] = scope
        if scope == 'Full_Text':
            blockers.append(f'{sid}: Evidence_Scope=Full_Text, but prior associated PDF was for a different publication; a correct matching PDF is not yet authenticated.')
    print('[7] Known incorrect-PDF evidence scopes:', evidence_status)

    # Independently reconstruct metric identity mapping from compiled source.
    require(COMPILED.is_file(),'Compiled Files.xlsx not found')
    wb = load_workbook(COMPILED,read_only=True,data_only=True)
    ws = wb['Section5_Coding_Consolidated']
    header = [str(v or '').strip() for v in next(ws.iter_rows(min_row=1,max_row=1,values_only=True))]
    idx = {k:i for i,k in enumerate(header) if k}
    idcol = next((idx[x] for x in ('Paper_ID','Study_ID') if x in idx),None)
    titlecol = next((idx[x] for x in ('Title','Study_Title') if x in idx),None)
    metriccol = idx.get('Primary_Metric')
    require(None not in (idcol,titlecol,metriccol), 'Compiled workbook lacks identity/metric columns')
    doicol = idx.get('DOI')
    compiled_rows = defaultdict(list)
    for rn,values in enumerate(ws.iter_rows(min_row=2,values_only=True),start=2):
        sid = str(values[idcol] or '').strip()
        if sid in now:
            compiled_rows[sid].append((rn,values))
    wb.close()
    _, metric_audit = read_csv(V4 / 'Primary_Metric_Identity_Audit_v4.csv')
    require(len(metric_audit)==485 and len({r['Paper_ID'] for r in metric_audit})==485,
            'Metric audit is not 485 unique study IDs')
    metrics_by_id = {r['Paper_ID']:r for r in metric_audit}
    reconstructed = Counter()
    nonmissing_metric = 0
    doi_verified = 0
    title_only = 0
    for sid in ids:
        r = now[sid]
        hits = []
        for rn,values in compiled_rows.get(sid,[]):
            if norm_title(values[titlecol]) != norm_title(r['Title']):
                continue
            registered = norm_doi(r['DOI'])
            comparison = norm_doi(values[doicol]) if doicol is not None else ''
            if registered and comparison and registered != comparison:
                continue
            hits.append((rn,values,registered,comparison))
        require(len(hits) == 1, f'Nonunique/missing identity-qualified metric record: {sid} hits={len(hits)}')
        rn,values,canonical_doi,compiled_doi = hits[0]
        metric = str(values[metriccol] or '').strip() or 'Not_Reported'
        a = metrics_by_id[sid]
        require(a['Status']=='IDENTITY_VERIFIED' and a['Primary_Metric']==metric and str(a['Compiled_Row'])==str(rn),
                f'Metric value/row disagreement for {sid}')
        if canonical_doi and compiled_doi:
            doi_verified += 1
        else:
            title_only += 1
            if sid in IDENTITY_FLAGS:
                blockers.append(f'{sid}: legacy identity flag has no DOI-confirmed linkage to compiled metrics (title match only).')
        if metric.strip().casefold() not in {'not_reported','not reported','unknown','unclear'}:
            nonmissing_metric += 1
        formulation = r['Learning_Formulation'] or 'Not_Reported'
        target = r['Target_Primary'] or 'Not_Reported'
        reconstructed['Target_to_Formulation','Target::'+target,'Formulation::'+formulation] += 1
        reconstructed['Formulation_to_Metric','Formulation::'+formulation,'Metric::'+metric] += 1
    require(len(reconstructed) > 0 and sum(reconstructed.values())==970,'Sankey conservation failed')
    _, sankey = read_csv(V4 / 'Figure_Target_Formulation_Metric_v4_VERIFIED_SUBSET.csv')
    from_file = Counter()
    for r in sankey:
        key = (r['Stage'],r['Source'],r['Target'])
        require(key not in from_file, f'Duplicate Sankey edge: {key}')
        from_file[key] = int(r['Count'])
    require(from_file==reconstructed,'Reconstructed primary-metric Sankey differs from v4 flows')
    print(f'[8] Primary-metric linkage and Sankey: PASS — 485/485, DOI-confirmed={doi_verified}, title-only={title_only}, specified metrics={nonmissing_metric}')

    # Verify all category counts and year/other cross-tabs directly against the v4 records.
    _, categories = read_csv(V4 / 'Manuscript_Category_Counts_v4.csv')
    category_truth = Counter()
    for row in categories:
        col = row['Field']
        require(col in v4_cols,'Unknown category field')
        key = (col,row['Category'])
        require(key not in category_truth, f'Duplicate distribution category: {key}')
        cnt = int(row['Count'])
        require(int(row['Denominator']) == 485,'Wrong category denominator')
        require(abs(float(row['Percentage']) - 100*cnt/485)<0.00011,
                f'Incorrect percentage: {key}')
        category_truth[key] = cnt
    expected = Counter()
    for col in {r['Field'] for r in categories}:
        for r in current:
            expected[col,r[col] or '[Blank]']+=1
    require(expected == category_truth,'Category statistics differ from study-level records')
    pair_names = [p for p in V4.glob('FigureData_*_by_*_v4.csv')]
    require(len(pair_names) == 6,'Expected six year/target/method/formulation cross-tabs')
    for file in pair_names:
        heads, contents = read_csv(file)
        require(len(heads)==3 and heads[-1]=='Count','Figure cross-tab schema error')
        a,b = heads[:2]
        require(a in v4_cols and b in v4_cols,'Unknown cross-tab column')
        actual = Counter((r[a] or '[Blank]',r[b] or '[Blank]') for r in current)
        observed = Counter()
        for r in contents:
            key = (r[a],r[b])
            require(key not in observed,f'Duplicate cross-tab key: {file.name}: {key}')
            observed[key]=int(r['Count'])
        require(actual==observed,f'Cross-tab count mismatch: {file.name}')
    print('[9] Corpus-wide category counts and six cross-tab datasets: PASS')

    _, stale = read_csv(V4 / 'Residual_Source_Contamination_v4.csv')
    require(not stale,'Residual source-contamination warnings still present')
    if blockers:
        print('\nRELEASE BLOCKERS:')
        for i,issue in enumerate(blockers,1):
            print(f'  {i}. {issue}')
        print('\nNo freeze folder was created. All v1–v4 outputs remain unchanged.')
        print('STATUS: RELEASE BLOCKED — EVIDENCE INTEGRITY REQUIRES SOURCE-BASED RESOLUTION')
        return 2

    # SHA-256 lock of every input used by this independent audit.
    snapshot_inputs = [CANONICAL,COMPILED,base_file(V1),
                       V2/'Technical_Register_485_CORRECTED_v2_DRAFT.csv',
                       v4_path, V2/'Correction_Change_Ledger_v2.csv',
                       V4/'Additional_Field_Changes_v4.csv',
                       V4/'Closed_17_Holds_v4.csv',
                       V4/'Primary_Metric_Identity_Audit_v4.csv',
                       V4/'Figure_Target_Formulation_Metric_v4_VERIFIED_SUBSET.csv',
                       V4/'Manuscript_Category_Counts_v4.csv']
    snapshots = {str(x):digest(x) for x in snapshot_inputs}
    stage = Path(tempfile.mkdtemp(prefix='.phaseA_freeze_stage_',dir=ROOT))
    try:
        copies = [v4_path,V4/'Manuscript_Category_Counts_v4.csv',
                  V4/'Figure_Target_Formulation_Metric_v4_VERIFIED_SUBSET.csv',
                  V4/'Primary_Metric_Identity_Audit_v4.csv',
                  V4/'Additional_Field_Changes_v4.csv',
                  V4/'Closed_17_Holds_v4.csv',
                  V2/'Correction_Change_Ledger_v2.csv',
                  V1/'Eligibility_Decisions_9_AUTHOR_APPROVED.csv'] + sorted(pair_names)
        for p in copies:
            require(not (stage/p.name).exists(),f'Copy name collision: {p.name}')
            shutil.copy2(p,stage/p.name)
        release_notes = '\n'.join([
            'PHASE A — TECHNICAL SYNTHESIS DATASET: AUTHORITATIVE FREEZE',
            'Technical studies: 485; original canonical: 492; author-approved exclusions: 7',
            'Independent input and output hash validation: PASS',
            'Previous correction operations: 27; additional operations: 9',
            f'Unique original-to-frozen field differences: {unique_net}',
            'Seventeen earlier held proposals: all dispositioned',
            'Validation_Status: cached spreadsheet calculation independently verified previously',
            'Source workbook and all predecessor output folders: UNCHANGED',
            f'Primary metric identity linkage: 485/485; DOI confirmed {doi_verified}; title-only {title_only}',
            f'Primary metric meaningfully reported: {nonmissing_metric}/485',
            'Historical legacy source mismatches: superseded legacy mappings, not evidence of change to final canonical identities',
            'Wrong-PDF flags P00663/P00841 not coded as Full_Text without correct authenticated source',
            'Comparative-only ARIMA/LSTM P00425 classified Other/unclear; ARIMA-only P00211 statistical/econometric',
            'Technical_Indicators remains binary Yes/No; ambiguous original reporting recorded in disposition ledger',
            'Forecast horizon and financial outcome uncertainty preserved as Not_Reported / Unclear where unsupported',
            'The 485-study synthesis does not replace the broader bibliometric record totals',
            'Publication-ready plots, revised manuscript text, and journal submission are downstream work',
            'Dataset-level freeze status: PASS',
            ''
        ])
        report = stage/'PhaseA_Final_Freeze_QA_Report.txt'
        report.write_text(release_notes,encoding='utf-8')
        deliverables = [p for p in stage.iterdir() if p.is_file()]
        freeze_manifest = {
            'freeze_scope':'485-study technical-synthesis dataset and figure-ready statistical source tables',
            'frozen':True,
            'frozen_at':datetime.now().astimezone().isoformat(),
            'source_count':492,'author_approved_exclusions':sorted(EXCLUDED),
            'frozen_study_count':485,'amendment_operations':36,
            'net_field_changes_from_eligibility_baseline':unique_net,
            'held_proposals_dispositioned':17,
            'primary_metric_matches':485,'primary_metric_doi_confirmed':doi_verified,
            'primary_metric_title_only':title_only,
            'primary_metric_reported':nonmissing_metric,
            'incorrect_pdf_record_scopes':evidence_status,
            'statistics_checked':'category distributions + six cross-tabs + metric sankey',
            'source_sha256':snapshots,
            'outputs_sha256':{p.name:digest(p) for p in deliverables}
        }
        (stage/'PhaseA_FROZEN_Manifest_v1.json').write_text(
            json.dumps(freeze_manifest,indent=2,sort_keys=True),encoding='utf-8')
        require(all(digest(p)==hashed for p,hashed in [(Path(k),v) for k,v in snapshots.items()]),
                'An input changed while building freeze')
        os.replace(stage,FREEZE)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print('[10] Atomic authoritative freeze package: CREATED')
    print('\nLocation:',FREEZE)
    print('Studies:',len(current))
    print('Amendment operations: 36; net changed study-field pairs:',unique_net)
    print('Evidence scopes:',evidence_status)
    print('Original canonical/source folders: UNCHANGED')
    print('STATUS: PASS — PHASE A TECHNICAL DATASET FROZEN')
    return 0


def base_file(directory):
    return directory/'Technical_Register_485_ELIGIBILITY_ONLY.csv'


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('\nSTATUS: FAIL-CLOSED — NO AUTHORITATIVE FREEZE RELEASED')
        print(f'{type(exc).__name__}: {exc}')
        sys.exit(1)
