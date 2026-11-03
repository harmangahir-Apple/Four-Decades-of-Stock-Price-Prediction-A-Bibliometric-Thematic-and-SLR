#!/usr/bin/env python3
"""ARCO Phase B2: provenance-safe INITIALIZATION ONLY.

Standard-library, dependency-free builder for reproducible CSV evidence-register
scaffolds. Requires the locally recorded author ratification receipt and validates
its hashes against the actual source files. Does NOT code any scientific claims.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

FROZEN_SHA='95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5'
RATIFIED_STATUS='B1_v1_2_AUTHOR_RATIFICATION_RECORDED__B2_INITIALIZATION_AUTHORIZED'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pr':'http://schemas.openxmlformats.org/package/2006/relationships'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for buf in iter(lambda:f.read(1024*1024),b''): h.update(buf)
    return h.hexdigest()


def csv_rows(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        return reader.fieldnames, list(reader)


def write_csv(path,fieldnames,rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='raise',lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def col_index(name):
    n=0
    for ch in name:
        n=n*26+(ord(ch)-ord('A')+1)
    return n-1


def read_xlsx_sheet(path,sheet_name):
    """Read original values from XLSX without third-party spreadsheet dependencies."""
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Frozen XLSX CRC check failed')
        workbook=ET.fromstring(archive.read('xl/workbook.xml'))
        relid=None
        for sh in workbook.findall('m:sheets/m:sheet',NS):
            if sh.get('name')==sheet_name:
                relid=sh.get('{'+NS['r']+'}id')
                break
        if relid is None:raise ValueError(f'Sheet not found: {sheet_name}')
        relationships=ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target=None
        for rel in relationships.findall('pr:Relationship',NS):
            if rel.get('Id')==relid:
                target=rel.get('Target');break
        if target is None:raise ValueError('Sheet relationship not found')
        target=target.lstrip('/')
        sheet_path=target if target.startswith('xl/') else 'xl/'+target
        sheet_xml=ET.fromstring(archive.read(sheet_path))
        shared=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            sst=ET.fromstring(archive.read('xl/sharedStrings.xml'))
            for si in sst.findall('m:si',NS):
                shared.append(''.join(x.text or '' for x in si.findall('.//m:t',NS)))
        records=[]
        for row in sheet_xml.findall('.//m:sheetData/m:row',NS):
            data={}
            for cell in row.findall('m:c',NS):
                addr=cell.get('r','')
                letter=re.match(r'[A-Z]+',addr)
                if letter is None:continue
                i=col_index(letter.group(0))
                kind=cell.get('t')
                if kind=='inlineStr':
                    value=''.join(x.text or '' for x in cell.findall('.//m:is//m:t',NS))
                else:
                    v=cell.find('m:v',NS)
                    value=v.text if v is not None and v.text is not None else ''
                    if kind=='s' and value:value=shared[int(value)]
                data[i]=str(value)
            if data:records.append(data)
        if not records:raise ValueError('Empty frozen worksheet')
        ncol=max(records[0])+1
        header=[records[0].get(i,'') for i in range(ncol)]
        result=[]
        for row in records[1:]:
            result.append({h:row.get(i,'') for i,h in enumerate(header)})
        return header,result


def verify_inputs(a):
    paths={'frozen':a.frozen,'b1':a.b1_package,'receipt':a.receipt,'calibration':a.calibration_review}
    for label,p in paths.items():
        if not p.exists():raise ValueError(f'{label} path does not exist: {p}')
    if not a.b1_package.is_dir():raise ValueError('B1 path must be directory')
    if digest(a.frozen)!=FROZEN_SHA:raise ValueError('Frozen workbook SHA-256 does not match ratified Phase A')
    receipt=json.loads(a.receipt.read_text(encoding='utf-8'))
    if receipt.get('status')!=RATIFIED_STATUS:
        raise ValueError('B1 author-ratification receipt not finalized / incorrect status')
    for key,exp in [('frozen_sha256',FROZEN_SHA),('frozen_records',485),('frozen_columns',51),('codebook_fields',45),('author_gates_approved',11),('phase_a_mutated',False),('independent_phase_c_completed',False)]:
        if receipt.get(key)!=exp:
            raise ValueError(f'B1 receipt mismatch {key}: {receipt.get(key)!r}, expected {exp!r}')
    if receipt.get('blocking_errors') or receipt.get('pending_author_actions'):
        raise ValueError('B1 receipt contains blocking/pending actions')
    files={
      'codebook':(a.b1_package/'PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv','codebook_v1_2_sha256'),
      'addendum':(a.b1_package/'B1_v1_2_Scientific_Rule_Addendum_SIGNOFF_CANDIDATE.md','addendum_sha256'),
      'approval':(a.b1_package/'B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv','approval_form_sha256'),
    }
    for label,(p,ref) in files.items():
        if not p.is_file():raise ValueError(f'Missing B1 {label}: {p}')
        if digest(p)!=receipt.get(ref):raise ValueError(f'B1 {label} differs from SIGNED receipt hash; do not alter signed files')
    if digest(a.calibration_review)!=receipt.get('calibration',{}).get('file_sha256'):
        raise ValueError('Completed calibration author review differs from signed B1 receipt')
    _, approvals=csv_rows(files['approval'][0])
    if len(approvals)!=11 or {r['Gate_ID'] for r in approvals}!={f'G{i:02d}' for i in range(1,12)} or any(r['Author_Decision'].strip()!='APPROVE' for r in approvals):
        raise ValueError('B1 signed approval form is not complete with 11 APPROVE decisions')
    _, calibration=csv_rows(a.calibration_review)
    if len(calibration)!=12 or any(r['Author_Decision_ACCEPT_or_REVISE'].strip()!='ACCEPT' for r in calibration):
        raise ValueError('Calibration review must have twelve author ACCEPT decisions')
    h,studies=read_xlsx_sheet(a.frozen,'Technical_Register_485')
    if len(h)!=51 or len(studies)!=485 or h[0]!='Paper_ID':
        raise ValueError('Frozen 485-by-51 study table mismatch')
    ids=[r['Paper_ID'] for r in studies]
    if len(set(ids))!=485 or any(not re.fullmatch(r'P\d{5}',pid) for pid in ids):
        raise ValueError('Frozen Paper_ID uniqueness or syntax mismatch')
    if Counter(x['Evidence_Scope'] for x in studies)!=Counter({'Full_Text':375,'Abstract_Only':85,'Metadata_Only':25}):
        raise ValueError('Frozen evidence-scope stratum mismatch')
    fheader,fields=csv_rows(files['codebook'][0])
    if len(fields)!=45 or len(set(x['Field_ID'] for x in fields))!=45:
        raise ValueError('Codebook does not have 45 unique fields')
    if Counter(f['Priority'] for f in fields)!=Counter({'CORE':27,'EXTENDED':18}):
        raise ValueError('Codebook 27 CORE / 18 EXTENDED mismatch')
    mapping=a.b1_package/'PhaseB1_PhaseA_Column_Mapping_51_SIGNOFF.csv'
    mh, mrows=csv_rows(mapping)
    if len(mrows)!=51 or [r['PhaseA_Column'] for r in mrows]!=h:
        raise ValueError('51-column mapping does not match actual Phase A column order')
    for f in fields:
        if f.get('PhaseA_exact_column'):
            for c in f['PhaseA_exact_column'].split(';'):
                if c.strip() not in h:
                    raise ValueError(f'Unrecognized original Phase A column in codebook: {f["Field_ID"]} => {c!r}')
    return receipt,h,studies,fheader,fields,mh,mrows


def initialize(a,verified):
    receipt,headers,studies,fheader,fields,mh,mrows=verified
    dest=a.output_dir
    if dest.exists() and any(dest.iterdir()):
        raise ValueError('Output directory must be new/empty; refusing overwrite: '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.B2_INIT_STAGE_',dir=str(dest.parent)))
    try:
        write_csv(stage/'B2_study_index_PHASEA_READONLY_51.csv',headers,studies)
        write_csv(stage/'B2_approved_field_dictionary_45.csv',fheader,fields)
        write_csv(stage/'B2_PhaseA_51_column_mapping.csv',mh,mrows)
        columns=['Paper_ID','Evidence_Scope','Field_ID','Field_Name','PhaseA_exact_column','Original_PhaseA_Value',
                 'Proposed_PhaseB_Value','Workflow_Status','Experiment_ID','Primary_Experiment_Selection_Status',
                 'Evidence_Assertion_IDs','Confidence','Coder','Coded_Date','Adjudication_Status','Coder_Notes']
        def decisions():
            for s in studies:
                for f in fields:
                    col=f.get('PhaseA_exact_column','')
                    yield dict(Paper_ID=s['Paper_ID'],Evidence_Scope=s['Evidence_Scope'],Field_ID=f['Field_ID'],
                          Field_Name=f['Field_Name'],PhaseA_exact_column=col,
                          Original_PhaseA_Value=(' | '.join(f'{c.strip()}={s.get(c.strip(), '')}' for c in col.split(';')) if ';' in col else s.get(col,'')) if col else '',Proposed_PhaseB_Value='',
                          Workflow_Status='NOT_ASSESSED',Experiment_ID='',Primary_Experiment_Selection_Status='UNSELECTED',
                          Evidence_Assertion_IDs='',Confidence='',Coder='',Coded_Date='',
                          Adjudication_Status='NOT_STARTED',Coder_Notes='')
        write_csv(stage/'B2_field_decisions_INITIAL_UNCODED_21825.csv',columns,decisions())
        empty_schemas={
          'B2_experiment_index.csv':['Paper_ID','Experiment_ID','Experiment_Role','Primary_Selection_Rule','Primary_Selection_Date','Forecasting_Target','Evaluation_Section','Evidence_Assertion_IDs','Selection_Status','Notes'],
          'B2_evidence_assertions.csv':['Assertion_ID','Paper_ID','Experiment_ID','Field_ID','Source_ID','Evidence_Role','Exact_Source_Quotation','PDF_Page_1_Based','Printed_Page_Label','Section_or_Table','Code_Path','Code_Line_Range','Assertion_Date','Verified_By','Verification_Status','Notes'],
          'B2_source_registry.csv':['Source_ID','Paper_ID','Source_Type','Version','DOI','URL','Local_Path','SHA256','Retrieved_YYYY_MM_DD','Source_Access_Status','Linked_Supplements_Checked','Notes'],
          'B2_negative_search_log.csv':['Search_Log_ID','Paper_ID','Experiment_ID','Field_ID','Source_ID','Search_Date','Search_Terms_or_Sections','Accessible_Sections_Reviewed','Linked_Material_Access_Status','Finding','Coder','Notes'],
          'B2_change_manifest.csv':['Change_ID','Paper_ID','Experiment_ID','Field_ID','Original_PhaseA_Value','Proposed_PhaseB_Value','Rationale','Evidence_Assertion_IDs','Proposer','Date','Adjudicator','Decision','Status'],
          'B2_unresolved.csv':['Issue_ID','Paper_ID','Experiment_ID','Field_ID','Issue_Type','Description','Required_Source_or_Action','Owner','Opened_YYYY_MM_DD','Resolution_Status','Resolution_Evidence_IDs'],
          'B2_protocol_amendments.csv':['Amendment_ID','From_Version','To_Version','Date','Rule_Affected','Proposed_Change','Scientific_Rationale','Author_Approval','B1_or_PhaseC_Implication','Receipt_SHA256'],
          'B2_study_level_derived_summaries.csv':['Paper_ID','Field_ID','Primary_Experiment_ID','Primary_Field_Value','Any_Experiment_YES','Any_Experiment_HIGH','Mixed_Experiment_Flag','Derivation_Method','Derivation_Reviewed','Evidence_IDs'],
        }
        for fname, cols in empty_schemas.items():write_csv(stage/fname,cols,[])
        schema_lines=['File_Name,Role,Editable,Initial_Rows,Notes']
        descriptions=[
          ('B2_study_index_PHASEA_READONLY_51.csv','Immutable Phase A reference',False,485,'Read only; 51 original columns; never change'),
          ('B2_field_decisions_INITIAL_UNCODED_21825.csv','Study-field initial workflow slots',True,21825,'Do not copy historical Phase A codes into new Phase B decisions'),
          ('B2_approved_field_dictionary_45.csv','B1 author-ratified field thresholds',False,45,'Read only; check YES/EXPLICIT_NO/N/A threshold per field'),
          ('B2_PhaseA_51_column_mapping.csv','Exact Phase A source mapping',False,51,'Read only'),
        ]+[(fname,'Empty schema for future evidence collection',True,0,'Use verified primary source assertions, not handover claims') for fname in empty_schemas]
        write_csv(stage/'B2_file_manifest.csv',['File_Name','Role','Editable','Initial_Rows','Notes'],
                  [dict(zip(['File_Name','Role','Editable','Initial_Rows','Notes'],[fn,role,'YES' if edit else 'NO',count,note])) for fn,role,edit,count,note in descriptions])
        doc=f'''# ARCO Phase B2 — Initialized but NOT coded

**Status: `B2_INITIALIZED_NOT_CODED`.** Source B1 v1.2 author ratification was checked against the **actual local receipt**. This package is an evidence-extraction workspace, not a scientific result.

## Locked inputs

- Frozen technical source: 485 studies x 51 original fields; SHA-256 `{FROZEN_SHA}`.
- B1 author receipt SHA-256 `{digest(a.receipt)}`; status `{receipt['status']}`.
- Ratified codebook: 45 fields, 27 CORE and 18 EXTENDED.
- Evidence scopes: 375 Full_Text, 85 Abstract_Only, 25 Metadata_Only.
- Initialized study × field workflow slots: **485 × 45 = 21,825**. They all begin `Workflow_Status=NOT_ASSESSED` and **blank `Proposed_PhaseB_Value`**.

## Beginner guide

1. **Never edit** `B2_study_index_PHASEA_READONLY_51.csv`, `B2_approved_field_dictionary_45.csv`, or `B2_PhaseA_51_column_mapping.csv`.
2. First build `B2_source_registry.csv` with actual original papers, supplements, dated repository snapshots and file hashes. The manuscript, reviewers' comments and chat handovers are research context, not original-study evidence.
3. During Phase B3, select the 40-case calibration pilot **using prespecified selection rules**. Do not treat this blank B2 register as completed coding.
4. For a specific field, locate the paper, capture the source paragraph, section and page in `B2_evidence_assertions.csv`. For well-supported non-reporting, maintain `B2_negative_search_log.csv`.
5. Keep each distinct experiment in `B2_experiment_index.csv`; use source-supported fields in a future experiment-level decision table. The 21,825 study-field rows are **initial placeholders** and must not overwrite experiment-specific evidence.
6. Only after assessing evidence may you enter a `Proposed_PhaseB_Value` into the working decisions; preserve the original Phase A value unchanged.
7. Any disagreement goes to `B2_unresolved.csv`, any revision to `B2_change_manifest.csv`, and any methodological rule modification to a new signed, versioned amendment.
8. Do not update manuscript headline percentages until Phase B evidence verification and Phase C independent reliability testing close.

**Important:** `NOT_REPORTED` needs a documented full-text search; it does not mean authors never performed the procedure. `INSUFFICIENT_ACCESS`, `AMBIGUOUS`, `EXPLICIT_NO`, and `NOT_APPLICABLE` are different evidence states. `PL11` leakage risk uses HIGH/LOW/INDETERMINATE/CONFLICTED/NOT_APPLICABLE, not a generic binary crosswalk.

## Next planned stage

B3: initialize a **deterministic 40-study pilot** (30 full text, 6 abstract, 4 metadata), with family/period representation, tracked seed and constraints. Phase C independent second-reviewer sample is separate and cannot be replaced by the B3 pilot.
'''
        (stage/'README_B2_INIT.md').write_text(doc,encoding='utf-8')
        hashes={p.name:digest(p) for p in sorted(stage.iterdir()) if p.is_file()}
        payload={'status':'B2_INITIALIZED_NOT_CODED','generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
               'origin':'ARCO Revision-I','frozen_sha256':FROZEN_SHA,
               'b1_author_receipt_sha256':digest(a.receipt),'b1_status':receipt['status'],
               'b1_codebook_sha256':digest(a.b1_package/'PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv'),
               'study_count':485,'original_columns':51,'codebook_fields':45,
               'field_decision_slots':21825,'new_evidence_assertions':0,'new_proposed_decisions':0,
               'independent_phase_c_completed':False,'input_source_unchanged':True,
               'generated_file_hashes':hashes}
        (stage/'B2_INITIALIZATION_RECEIPT.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
        # Exactly one immutable final initialization folder, without overwriting older outputs.
        if dest.exists():dest.rmdir()  # output directory was required empty
        stage.replace(dest)
        print('B2 INITIALIZATION: PASS')
        print('Frozen: 485 x 51 SHA-256',FROZEN_SHA)
        print('B1 AUTHOR RATIFICATION: verified locally')
        print('Fields: 45; new decision slots: 21825; NEW CODES: 0')
        print('STATUS: B2_INITIALIZED_NOT_CODED')
        print('OUTPUT:',dest)
        print('RECEIPT:',dest/'B2_INITIALIZATION_RECEIPT.json')
    finally:
        if stage.exists():shutil.rmtree(stage)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',type=Path,required=True)
    p.add_argument('--b1-package',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--calibration-review',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--preflight',action='store_true',help='validate signed inputs but create no outputs')
    a=p.parse_args()
    try:
        verified=verify_inputs(a)
        print('AUTHORIZATION CHECK: PASS')
        print('485-study frozen checksum, 45-field signed codebook, 11 author gates, 12-case calibration: PASS')
        if not a.preflight:initialize(a,verified)
        else:print('STATUS: PREFLIGHT_ONLY__NO_FILES_WRITTEN')
        return 0
    except Exception as err:
        print('BLOCKED:',type(err).__name__,str(err),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
