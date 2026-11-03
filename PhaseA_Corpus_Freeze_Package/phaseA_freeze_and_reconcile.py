#!/usr/bin/env python3
"""Phase A: reproduce the study-ID freeze, version audit and denominator maps.

Run: python phaseA_freeze_and_reconcile.py --root '/home/harman/projects/SLR Stock Price Prediction/Stock_Price_Prediction_SLR_ACME'
Or, when uploads are colocated: python phaseA_freeze_and_reconcile.py --root /mnt/data

Only Python standard library is needed. Never alters inputs. This is an identity
and provenance audit, NOT a substitute for independent content adjudication.
"""
from __future__ import annotations
import argparse,collections,csv,datetime,hashlib,json,posixpath,re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

MAIN_NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL_NS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def read_xlsx_sheet(path:Path,name:str,header_row:int=1)->list[dict[str,str]]:
    """Read XLSX data using OOXML ZIP content without modifying workbooks."""
    with ZipFile(path,'r') as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            sr=ET.fromstring(z.read('xl/sharedStrings.xml'))
            strings=[''.join(t.text or '' for t in si.iter('{%s}t'%MAIN_NS)) for si in sr.findall('{%s}si'%MAIN_NS)]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        relationships=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={r.attrib['Id']:r.attrib['Target'] for r in relationships}
        target=None
        for sheet in wb.findall('.//{%s}sheet'%MAIN_NS):
            if sheet.get('name')==name:
                target=relmap[sheet.get('{%s}id'%REL_NS)]
                break
        if target is None:raise KeyError(f'{name!r} worksheet not found in {path}')
        part=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        root=ET.fromstring(z.read(part))
        records=[]
        for row in root.findall('.//{%s}sheetData/{%s}row'%(MAIN_NS,MAIN_NS)):
            cells={}
            for cell in row.findall('{%s}c'%MAIN_NS):
                m=re.match(r'([A-Z]+)',cell.attrib['r'])
                if not m:continue
                idx=0
                for ch in m.group(1):idx=idx*26+(ord(ch)-64)
                v=cell.find('{%s}v'%MAIN_NS)
                string=v.text if v is not None and v.text is not None else ''
                if cell.attrib.get('t')=='s' and string:string=strings[int(string)]
                elif cell.attrib.get('t')=='inlineStr':
                    i=cell.find('{%s}is'%MAIN_NS)
                    string=''.join(t.text or '' for t in i.iter('{%s}t'%MAIN_NS)) if i is not None else ''
                cells[idx-1]=string
            if cells:records.append((int(row.attrib['r']),cells))
        headers=None; output=[]
        for rownum,cells in records:
            if rownum==header_row:
                headers=[cells.get(c,'').strip() for c in range(max(cells)+1)]
                if 'Paper_ID' not in headers:raise ValueError(f'{name} header row {header_row} lacks Paper_ID')
            elif rownum>header_row and headers is not None:
                values={header:cells.get(i,'').strip() for i,header in enumerate(headers) if header}
                if any(values.values()):output.append(values)
        if headers is None:raise ValueError(f'Header row {header_row} missing in {name}')
        return output

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        return [{str(k).strip():(str(v).strip() if v is not None else '') for k,v in row.items() if k is not None} for row in csv.DictReader(f)]

def write_csv(path,rows,fields=None):
    rows=list(rows)
    if fields is None:
        fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def assert_ids(rows,label):
    ids=[r.get('Paper_ID','') for r in rows]
    if not ids or '' in ids:raise ValueError(f'Blank ID or empty {label}')
    dup=[sid for sid,count in collections.Counter(ids).items() if count>1]
    if dup:raise ValueError(f'Duplicate IDs in {label}: {dup[:20]}')
    return set(ids)

def normalized_text(s):return ' '.join(str(s).casefold().split())

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('/mnt/data'));p.add_argument('--out',type=Path,default=None)
    a=p.parse_args(); root=a.root.expanduser().resolve();out=(a.out or root/'PhaseA_Freeze_Output').resolve();out.mkdir(parents=True,exist_ok=True)
    files={
      'compiled':'Compiled Files.xlsx',
      'supp_final':'Supplementary_Data_S1_492_Study_Technical_Register.xlsx',
      'supp_legacy':'Supplementary_Data_S1_493_Study_Technical_Register.csv',
      'audit_legacy':'Section5_5_Methodological_Audit_Reconciled.csv',
      'method_legacy':'Section7_Final_Study_Level_Sankey_Input.csv',
      'method_final':'Principal_Method_Family_Distribution_492_SCIE_Q1_Final_Study_Level_Audit.csv',
      'modality_legacy':'Section6_Final_Applicable_Studies_492.csv',
      'modality_legacy_copy':'Section6_Final_Applicable_Studies_492 (1).csv',
      'modality_explicit':'Section6_Explicit_Modality_Analysis_492.csv',
      'table18_legacy':'Table18_Method_Family_Reliability_Reconciled_Raw.csv',
    }
    # When the project uses subdirectories, resolve a file only if there is
    # exactly one matching basename; never silently choose among versions.
    paths={}
    for key,name in files.items():
        direct=root/name
        if direct.is_file():
            paths[key]=direct
        else:
            matches=sorted(x for x in root.rglob(name) if x.is_file())
            if len(matches)==1:
                paths[key]=matches[0]
            elif len(matches)>1:
                raise RuntimeError(f'Ambiguous source {name}: {matches}. Place the authoritative copy directly in --root.')
            else:
                paths[key]=direct
    missing=[str(k)+': '+str(v) for k,v in paths.items() if not v.is_file()]
    if missing:raise FileNotFoundError('Missing required inputs:\n'+'\n'.join(missing))

    compiled_coding=read_xlsx_sheet(paths['compiled'],'Section5_Coding_Consolidated')
    compiled_audit=read_xlsx_sheet(paths['compiled'],'Section5_5_Methodological_Audit')
    final_supp=read_xlsx_sheet(paths['supp_final'],'Study_Register_492',header_row=2)
    leg_supp=read_csv(paths['supp_legacy'])
    leg_audit=read_csv(paths['audit_legacy']);leg_method=read_csv(paths['method_legacy'])
    final_method=read_csv(paths['method_final']);leg_mod=read_csv(paths['modality_legacy'])
    explicit_mod=read_csv(paths['modality_explicit']);table18=read_csv(paths['table18_legacy'])
    final_coding=[r for r in compiled_coding if r.get('Systematic_Inclusion_Status')=='Included_High_Priority']
    excluded_coding=[r for r in compiled_coding if r.get('Systematic_Inclusion_Status')!='Included_High_Priority']
    canonical=assert_ids(final_coding,'Compiled included'); audit_ids=assert_ids(compiled_audit,'Compiled audit')
    supp_ids=assert_ids(final_supp,'Supplementary Data S1 492'); meth_ids=assert_ids(final_method,'Final family register')
    if len(canonical)!=492 or canonical!=audit_ids or canonical!=supp_ids or canonical!=meth_ids:
        raise AssertionError('AUTHORITATIVE FREEZE FAILED: 492 count or ID-set disagreement')
    compiled_all_ids=assert_ids(compiled_coding,'Compiled coding (including excluded)')
    legacy_supp_ids=assert_ids(leg_supp,'Legacy supplementary 493')
    swap_rows=[{'Source':'Compiled coding / 493 rows','Paper_ID':sid,'Presence':'Not present in legacy 493','Status':next((r.get('Systematic_Inclusion_Status','') for r in compiled_coding if r['Paper_ID']==sid),'')} for sid in sorted(compiled_all_ids-legacy_supp_ids)]
    swap_rows += [{'Source':'Legacy supplementary / 493 rows','Paper_ID':sid,'Presence':'Not present in compiled coding 493','Status':'Legacy record; absent from final 492'} for sid in sorted(legacy_supp_ids-compiled_all_ids)]
    write_csv(out/'PhaseA_Different_493_Populations.csv',swap_rows,['Source','Paper_ID','Presence','Status'])
    final_by_id={r['Paper_ID']:r for r in final_supp}
    coding_by_id={r['Paper_ID']:r for r in final_coding}
    audit_by_id={r['Paper_ID']:r for r in compiled_audit}
    family_by_id={r['Paper_ID']:r for r in final_method}
    applicable={sid for sid,r in final_by_id.items() if r.get('Input_Modality_Recoverable')!='Not_Applicable'}
    na_ids=sorted(canonical-applicable)
    if len(applicable)!=491 or len(na_ids)!=1:
        raise AssertionError('Expected 491 applicable studies and 1 Not_Applicable in authoritative supplement')
    legacy_inputs={k:rows for k,rows in [('Supplement legacy',leg_supp),('Method legacy',leg_method),('Audit legacy',leg_audit),('Modality legacy',leg_mod),('Explicit modality',explicit_mod),('Final method',final_method)]}
    id_records=[]
    for k,rows in legacy_inputs.items():
        ids=assert_ids(rows,k)
        id_records.append({'Register':k,'Rows':len(rows),'Unique_Paper_IDs':len(ids),'Missing_vs_final_492':'|'.join(sorted(canonical-ids)), 'Extra_vs_final_492':'|'.join(sorted(ids-canonical)), 'Identity_match_final_492':str(ids==canonical)})
    write_csv(out/'PhaseA_Register_ID_Reconciliation.csv',id_records)

    base_methods={r['Paper_ID']:r for r in leg_method}
    legacy_supp={r['Paper_ID']:r for r in leg_supp}
    attr_rows=[]
    for sid in sorted(canonical):
        f=final_by_id[sid];c=coding_by_id[sid];aud=audit_by_id[sid];fm=family_by_id[sid]
        row={'Paper_ID':sid,'Title':f.get('Title',''),'Year':f.get('Year',''), 'Evidence_Scope':f.get('Evidence_Scope',''),
          'Inclusion_Status':c['Systematic_Inclusion_Status'],'Modality_Applicability':('Not_Applicable' if sid in na_ids else 'Applicable'),
          'Final_Method_Family':f.get('Principal_Method_Family',''),'Final_Method_Verified_Family_Audit':fm.get('Principal_Method_Family',''),
          'Final_Validation_Design':f.get('Validation_Design',''),'Compiled_Audit_Validation_Design':aud.get('Validation_Design',''),
          'Final_Preprocessing_Boundary':f.get('Preprocessing_Boundary',''),'Compiled_Audit_Preprocessing_Boundary':aud.get('Preprocessing_Boundary',''),
          'Final_Leakage_Risk':f.get('Leakage_Risk',''),'Compiled_Audit_Leakage_Risk':aud.get('Leakage_Risk',''),
          'Legacy_Method_Family':base_methods.get(sid,{}).get('Principal_Method_Family',''),
          'Legacy_Supplement_Title':legacy_supp.get(sid,{}).get('Title','')}
        attr_rows.append(row)
    write_csv(out/'PhaseA_Frozen492_Study_ID_Master.csv',attr_rows)
    applicable_rows=[x for x in attr_rows if x['Paper_ID'] in applicable]
    write_csv(out/'PhaseA_Modality491_Applicable_ID_Master.csv',applicable_rows)

    check_fields=[('Title','Title','coding'),('Year','Year','coding'),('Title','Title','audit'),('Year','Year','audit'),
      ('Target_Primary','Target_Primary','audit'),('Learning_Formulation','Learning_Formulation','audit'),
      ('Asset_Scope','Asset_Scope','audit'),('Principal_Method_Family','Principal_Method_Family','family'),
      ('Validation_Design','Validation_Design','audit'),('Preprocessing_Boundary','Preprocessing_Boundary','audit'),
      ('Leakage_Risk','Leakage_Risk','audit'),('Statistical_Testing','Statistical_Testing','audit'),
      ('Code_Available','Code_Available','audit'),('Data_Available','Data_Available','audit'),
      ('Transaction_Costs','Transaction_Costs','audit'),('Shock_Period_Evaluation','Shock_Period_Evaluation','audit'),
      ('Regime_Specific_Evaluation','Regime_Specific_Evaluation','audit'),('Chronological_Split','Chronological_Split','audit')]
    source_maps={'coding':coding_by_id,'audit':audit_by_id,'family':family_by_id}
    conflicts=[]
    for sid in sorted(canonical):
        master=final_by_id[sid]
        for leftkey,rightkey,source in check_fields:
            src=source_maps[source][sid]
            if leftkey in master and rightkey in src:
                a1=master[leftkey];a2=src[rightkey]
                if normalized_text(a1)!=normalized_text(a2):
                    conflicts.append({'Paper_ID':sid,'Field':leftkey,'Supplement492_Value':a1,'Comparison_Source':source,'Comparison_Value':a2,'Action':'Verify provenance; do not auto-overwrite'})
    write_csv(out/'PhaseA_Study_Field_Disagreements.csv',conflicts,['Paper_ID','Field','Supplement492_Value','Comparison_Source','Comparison_Value','Action'])

    modality_fields={'Historical_Market_Data':'Historical_Market_Data','Technical_Indicators':'Technical_Indicators',
    'Financial_News_Text':'Financial_News_Text','Social_Media_Public_Opinion':'Social_Media_Public_Opinion',
    'Fundamental_Accounting':'Fundamental_Accounting','Macroeconomic_Systemic':'Macroeconomic_Systemic',
    'Relational_Cross_Market':'Index_Sector_CrossMarket','Alternative_Attention':'Alternative_Attention_Data',
    'Decomposition_Transformation':'Decomposition_Transforms'}
    old_mod_by_id={r['Paper_ID']:r for r in leg_mod}
    modality_disagreements=[]
    for sid in sorted(applicable):
        old=old_mod_by_id.get(sid)
        if old is None:continue
        new=final_by_id[sid]
        for key,oldkey in modality_fields.items():
            a1=new.get(key,'');a2=old.get(oldkey,'')
            expected={'Yes':'1','No':'0','Unclear':'?','Not_Reported':'?','Not_Applicable':'NA'}.get(a1,a1)
            if expected!=a2:
                modality_disagreements.append({'Paper_ID':sid,'Category':key,'Final_Supplement_Value':a1,'Legacy_Modality_Value':a2,'Action':'Investigate evidence scope and adjudication; no automatic category override'})
    write_csv(out/'PhaseA_Modality_Flag_Disagreements.csv',modality_disagreements)
    # Retain 491 legacy modality rows as a *candidate* only; flags are NOT automatically approved.
    candidate=[r for r in leg_mod if r['Paper_ID'] in applicable]
    if {r['Paper_ID'] for r in candidate}!=applicable:raise AssertionError('491 candidate modality IDs inconsistent')
    write_csv(out/'PhaseA_Modality491_Legacy_Flags_CANDIDATE.csv',candidate,list(leg_mod[0]))

    exclusions=[{'Paper_ID':r['Paper_ID'],'Status':r.get('Systematic_Inclusion_Status',''),'Title':r.get('Title',''),'Origin':'Compiled Files / excluded row'} for r in excluded_coding]
    exclusions += [{'Paper_ID':sid,'Status':'Legacy-only; removed from final 492','Title':legacy_supp.get(sid,{}).get('Title',''),'Origin':'493-study legacy register'} for sid in sorted(set(legacy_supp)-canonical)]
    exclusions += [{'Paper_ID':sid,'Status':'Not applicable for modality analysis (still in final 492)','Title':final_by_id[sid].get('Title',''),'Origin':'Final supplementary register'} for sid in na_ids]
    write_csv(out/'PhaseA_Exclusion_and_Applicability_Log.csv',exclusions)
    counts=collections.Counter(x['Evidence_Scope'] for x in attr_rows)
    issues=[]
    def gate(name,status,observation,action):issues.append({'Gate':name,'Status':status,'Observed':observation,'Required_Action':action})
    gate('Final study-ID congruence','PASS','Compiled included, Compiled audit, Supplement 492 and final family audit: same 492 IDs','Freeze ID list and protect from overwrite')
    gate('Evidence-scope counts','PASS',str(dict(counts)),'Maintain full-text/abstract-only/metadata-only scope labels')
    gate('Different 493-row register identities','REVIEW',f'Compiled-only {sorted(compiled_all_ids-legacy_supp_ids)}; legacy-only {sorted(legacy_supp_ids-compiled_all_ids)}','Document both historical 493 populations explicitly; never equate counts with identical study sets')
    gate('Legacy 493 mapping','PASS' if {r['Paper_ID'] for r in leg_supp}-canonical=={'P04845'} else 'FAIL',str(sorted({r['Paper_ID'] for r in leg_supp}-canonical)),'Document excluded record; do not mix legacy counts')
    gate('Modality applicability','PASS' if na_ids==['P00814'] else 'FAIL',str(na_ids),'Exclude Not Applicable record from 491 denominator only')
    leg_mod_ids={r['Paper_ID'] for r in leg_mod}
    gate('Legacy 492-labelled modality input','FAIL' if leg_mod_ids!=applicable else 'PASS',f'Extra vs applicable {sorted(leg_mod_ids-applicable)}; Missing vs applicable {sorted(applicable-leg_mod_ids)}','Replace ID set; manually adjudicate divergent modality flags')
    gate('Same-named modality copy','PASS' if sha(paths['modality_legacy'])==sha(paths['modality_legacy_copy']) else 'REVIEW','Byte-identical' if sha(paths['modality_legacy'])==sha(paths['modality_legacy_copy']) else 'Different byte hashes','Do not mistake duplicate file for independent evidence')
    gate('Authoritative field congruence','REVIEW' if conflicts else 'PASS',f'{len(conflicts)} field-level disagreements in comparable fields','Resolve by field-level evidence hierarchy; do not bulk replace')
    gate('Modality indicator congruence','REVIEW' if modality_disagreements else 'PASS',f'{len(modality_disagreements)} category disagreements between supplementary register and retained legacy modality flags','Inspect the corresponding explicit/override evidence for each difference')
    gate('Legacy Table 18 compatibility','FAIL' if len(leg_audit)!=492 else 'PASS',f'Legacy audit {len(leg_audit)} rows; final audit {len(compiled_audit)} rows','Regenerate family-by-audit table from frozen 492, not 493')
    gate('Eligibility of non-original P00814','REVIEW','P00814 title indicates state-of-the-art analysis; currently Included_High_Priority and Not_Applicable for modalities','Manually confirm it meets technical-synthesis eligibility; do not silently exclude')
    write_csv(out/'PhaseA_QA_Gates.csv',issues)
    file_manifest=[]
    for key,path in sorted(paths.items()):
        file_manifest.append({'Role':key,'File':path.name,'Size_Bytes':path.stat().st_size,'SHA256':sha(path)})
    write_csv(out/'PhaseA_File_SHA256_Manifest.csv',file_manifest)

    family_counts=collections.Counter(r.get('Principal_Method_Family','') for r in final_supp)
    validation_counts=collections.Counter(r.get('Validation_Design','') for r in final_supp)
    summary={'freeze_date':datetime.date.today().isoformat(),'canonical_studies':len(canonical),'modality_applicable_studies':len(applicable),
    'not_applicable_ids':na_ids,'excluded_compiled_ids':[r['Paper_ID'] for r in excluded_coding],
    'legacy_only_ids':sorted(set(legacy_supp)-canonical),'evidence_scope':dict(counts),'method_families':dict(family_counts),
    'validation_design':dict(validation_counts),'study_field_disagreements':len(conflicts),'modality_flag_disagreements':len(modality_disagreements),
    'legacy_modality_extra_ids':sorted(leg_mod_ids-applicable),'legacy_modality_missing_ids':sorted(applicable-leg_mod_ids),'gates':issues}
    with (out/'PhaseA_Summary.json').open('w',encoding='utf-8') as f:json.dump(summary,f,indent=2,ensure_ascii=False)
    report=[
    '# Phase A — Study-register freeze and lineage audit','',
    '**Status:** ID-level technical freeze verified. Modality flags and unresolved classification content are **not** certified.','',
    '## Key counts',f'- Final technical synthesis: **{len(canonical)}**, unique `Paper_ID` values, identical across Compiled coding, Compiled audit, Supplementary Data S1 (492) and final family audit.',
    f'- Evidence scope: **{counts.get("Full_Text",0)} full text**, **{counts.get("Abstract_Only",0)} abstract only**, **{counts.get("Metadata_Only",0)} metadata only**.',
    f'- Modality-applicable: **{len(applicable)}**, excluding only `{", ".join(na_ids)}` as `Not_Applicable` in the final supplementary register.',
    f'- Excluded coding records in Compiled workbook: **{", ".join(r["Paper_ID"] for r in excluded_coding)}**.',
    f'- Legacy 493-only IDs: **{", ".join(sorted(set(legacy_supp)-canonical))}**.',
    f'- Two 493-row sources have different records: compiled coding only **{sorted(compiled_all_ids-legacy_supp_ids)}**, legacy supplementary only **{sorted(legacy_supp_ids-compiled_all_ids)}**.',
    f'- Old modality CSV: contains excluded **{", ".join(sorted(leg_mod_ids-applicable))}**, and omits **{", ".join(sorted(applicable-leg_mod_ids)) or "none"}** from the applicable set.',
    f'- Supplement-vs-compiled comparable field disagreements: **{len(conflicts)}**, requiring individual evidence review.',
    f'- Supplement-vs-legacy retained modality flag disagreements: **{len(modality_disagreements)}**.',
    '', '## Decisions and restrictions','',
    '1. Use the 492-study set in `PhaseA_Frozen492_Study_ID_Master.csv` as the authoritative technical-synthesis ID population.',
    '2. Use `PhaseA_Modality491_Applicable_ID_Master.csv` for input-modality denominators. It does not validate every modality positive/negative code.',
    '3. Do not use 493-study Table 18 or the 492-labelled legacy modality CSV as final manuscript results.',
    '4. `PhaseA_Modality491_Legacy_Flags_CANDIDATE.csv` is a corrected-ID candidate only; reconcile flagged category values against supplementary evidence and full text.',
    '5. The record P00814 has an apparent review-type title and remains included in technical synthesis. Its scientific eligibility requires human confirmation before final freeze.',
    '6. Do not conflate 4,974 topical studies and 5,022 deduplicated records; those layers require a separate source-record-level audit.',
    '', '## Gate status','',
    '| Gate | Status | Observation |','|---|---|---|']
    for x in issues:report.append(f'| {x["Gate"]} | {x["Status"]} | {x["Observed"]} |')
    report += ['', '## Reproducibility','',f'- Input directory: `{root}`',f'- Output directory: `{out}`',
    '- Source files are never overwritten; SHA-256 hashes are in `PhaseA_File_SHA256_Manifest.csv`.',
    '- Re-run the script whenever an included `Paper_ID`, evidence-scope flag, or final coding decision changes.']
    (out/'PhaseA_Readme_Report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['canonical_studies','modality_applicable_studies','not_applicable_ids','excluded_compiled_ids','legacy_only_ids','study_field_disagreements','modality_flag_disagreements','legacy_modality_extra_ids','legacy_modality_missing_ids']},indent=2))
    print('OUTPUT',out)

if __name__=='__main__':main()
