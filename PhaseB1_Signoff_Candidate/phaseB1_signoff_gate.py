#!/usr/bin/env python3
"""Read-only frozen Phase-A and Phase-B1 author-ratification gate; standard library only.
No citation or author approval is fabricated. No original files are edited.
"""
import argparse, csv, datetime as dt, hashlib, json, re, sys, zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
EXPECTED_SHA = '95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5'
EXPECTED_SCOPE = {'Full_Text': 375, 'Abstract_Only': 85, 'Metadata_Only': 25}
EXPECTED_METHOD = {
'Deep-learning models':114,'Hybrid deep-learning models':109,'Sentiment/NLP-driven models':77,
'Transformer/attention-based models':68,'Metaheuristic-optimized models':51,
'Ensemble/tree-based machine learning':32,'Graph-based models':16,'Multimodal-fusion models':12,
'Other/unclear':3,'ANN/neuro-fuzzy models':2,'Statistical/econometric models':1}
EXPECTED_FIELD_GROUPS={'TV':7,'PL':11,'BL':5,'ST':4,'EC':5,'RB':4,'EX':4,'RP':5}
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def read_csv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def col_idx(address):
    letters=''.join(ch for ch in address if ch.isalpha());v=0
    for ch in letters:v=v*26+ord(ch.upper())-64
    return v-1

def read_frozen_xlsx(p):
    """Parse a read-only, ordinary XLSX using Python stdlib (no project dependency)."""
    with zipfile.ZipFile(p) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('m:si',NS):
                ss.append(''.join(t.text or '' for t in si.findall('.//m:t',NS)))
        wr=ET.fromstring(z.read('xl/workbook.xml'))
        shs=wr.findall('.//m:sheets/m:sheet',NS)
        if not shs or shs[0].get('name')!='Technical_Register_485':
            raise ValueError('Technical_Register_485 must be the first worksheet of this approved workbook')
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows=[]
        for row in root.findall('.//m:sheetData/m:row',NS):
            d={}
            for c in row.findall('m:c',NS):
                ref=c.get('r','');v=c.find('m:v',NS)
                if c.get('t')=='inlineStr':
                    raw=''.join(t.text or '' for t in c.findall('.//m:is//m:t',NS))
                elif c.get('t')=='s':raw=ss[int(v.text)] if v is not None and v.text is not None else ''
                else:raw=(v.text or '') if v is not None else ''
                if ref:d[col_idx(ref)] = raw
            rows.append(d)
    if not rows:raise ValueError('Empty frozen worksheet')
    width=max(rows[0])+1
    columns=[rows[0].get(i,'').strip() for i in range(width)]
    records=[dict(zip(columns,[r.get(i,'') for i in range(width)])) for r in rows[1:]]
    return columns,records

def check_issues(frozen, package, final=False):
    hard=[];pending=[];info={}
    fsha=sha(frozen);info['frozen_sha256']=fsha
    if fsha != EXPECTED_SHA:hard.append('Frozen SHA-256 does not match the approved source fingerprint; STOP')
    headers,records=read_frozen_xlsx(frozen)
    info.update(frozen_rows=len(records),frozen_columns=len(headers),paper_id_count=len({r.get('Paper_ID','').strip() for r in records}))
    if len(headers)!=51 or len(records)!=485:hard.append('Frozen row/column contract != 485 / 51')
    ids=[r.get('Paper_ID','').strip() for r in records]
    if len(set(ids))!=485 or any(not re.fullmatch(r'P\d{5}', x) for x in ids):hard.append('Paper_ID missing, duplicated, or not Pxxxxx')
    scope=dict(Counter(r['Evidence_Scope'].strip() for r in records));info['scope_counts']=scope
    if scope!=EXPECTED_SCOPE:hard.append(f'Evidence scopes disagree: {scope}')
    method=dict(Counter(r['Principal_Method_Family'].strip() for r in records));info['family_counts']=method
    if method!=EXPECTED_METHOD:hard.append(f'Method families disagree: {method}')
    expected_baseline={
    'Validation_Status':{'Temporally ordered':81,'Random/shuffled':6,'Unclear':398},
    'Preprocessing_Boundary':{'Training_Only':21,'Full_Dataset':17,'Unclear':447},
    'Leakage_Risk':{'High':32,'Low':7,'Unclear':446},
    }
    for key,counts in expected_baseline.items():
        found=dict(Counter(r.get(key,'').strip() for r in records));info[key+'_counts']=found
        if found!=counts:hard.append(f'{key}: expected {counts}; found {found}')
    fields=read_csv(package/'PhaseB1_Evidence_Codebook_v1_1_SIGNOFF_CANDIDATE.csv')
    info['field_count']=len(fields)
    if len(fields)!=45 or len({r['Field_ID'] for r in fields})!=45:hard.append('45 unique B1 codes not found')
    group=Counter(x['Field_ID'][:2] for x in fields);info['groups']=dict(group)
    if dict(group)!=EXPECTED_FIELD_GROUPS:hard.append('Field-group counts diverge from 45-field protocol')
    priority=Counter(x['Priority'].strip() for x in fields);info['priority_counts']=dict(priority)
    if priority!={'CORE':27,'EXTENDED':18}:hard.append('CORE/EXTENDED != 27/18')
    for r in fields:
        for fld in ['Domain','Field_Name','Operational_question','YES_threshold','EXPLICIT_NO_threshold','NOT_APPLICABLE_rule','Source_sections','Common_ambiguity_and_guardrail']:
            if not (r.get(fld,'') or '').strip():hard.append(f"Incomplete field {r['Field_ID']} : {fld}")
        for col in r.get('PhaseA_exact_column','').split(';'):
            if col and col not in headers:hard.append(f"Unknown Phase A column {col} in {r['Field_ID']}")
    mapped=read_csv(package/'PhaseB1_PhaseA_Column_Mapping_51_SIGNOFF.csv')
    if len(mapped)!=51 or {r['PhaseA_Column'] for r in mapped}!=set(headers):hard.append('Phase A column mapping differs from 51 frozen columns')
    amendment=read_csv(package/'B1_Proposed_Rule_Amendments_v1_to_v1_1.csv')
    info['rule_amendment_rows']=len(amendment)
    if not amendment:hard.append('Amendment ledger empty')
    amendment_ids={r['Field_ID'] for r in amendment}
    if not amendment_ids.issubset(set(r['Field_ID'] for r in fields)):hard.append('Amendment references unknown B1 ID')
    approved=read_csv(package/'B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv')
    expected_gates={'G%02d'%i for i in range(1,12)}
    if len(approved)!=11 or {r.get('Gate_ID','') for r in approved}!=expected_gates:hard.append('11 unique G01-G11 sign-off gates missing')
    filled=0;rejected=[]
    for row in approved:
        v=(row.get('Author_Decision','') or '').strip().upper()
        if v not in ('','APPROVE','REJECT'):hard.append(f"Invalid author decision {row.get('Gate_ID')}={v}")
        if v=='REJECT':rejected.append(row.get('Gate_ID'))
        if v=='APPROVE':
            filled+=1
            if not (row.get('Approving_Author') or '').strip():hard.append(f"{row.get('Gate_ID')} APPROVE lacks author name")
            try:
                when=dt.date.fromisoformat((row.get('Approval_Date_YYYY_MM_DD') or '').strip())
                if when > dt.date.today():hard.append(f"{row.get('Gate_ID')} has future approval date")
            except ValueError:hard.append(f"{row.get('Gate_ID')} APPROVE lacks valid ISO approval date")
    info['author_gates_approved']=filled;info['author_gates_rejected']=rejected
    if rejected:pending.append('Author explicitly rejected gate(s): '+', '.join(rejected))
    if filled<11:pending.append(f'Author ratification incomplete ({filled}/11 approved)')
    # Check package content integrity from a package-local manifest; no hidden source edits.
    manifests=json.loads((package/'B1_File_Hash_Manifest.json').read_text(encoding='utf-8'))
    for rel,expect in manifests.items():
        if not (package/rel).exists() or sha(package/rel)!=expect:hard.append(f'Sign-off candidate file altered without regenerated version/manifest: {rel}')
    info['package_file_checksums_match']=not any('altered' in v for v in hard)
    return hard,pending,info

def main():
    ap=argparse.ArgumentParser(description='ARCO Phase B1 read-only technical and author sign-off gate')
    ap.add_argument('--frozen',type=Path,required=True,help='Exact Phase A frozen XLSX file')
    ap.add_argument('--package-dir',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--finalize',action='store_true',help='Only after a real author has approved every gate')
    a=ap.parse_args()
    for p in [a.frozen,a.package_dir]:
        if not p.exists():ap.error(f'Path not found: {p}')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    try:hard,pending,info=check_issues(a.frozen,a.package_dir,a.finalize)
    except Exception as e:print('STOP: cannot authenticate source/protocol:',e,file=sys.stderr);sys.exit(2)
    info.update(phase='B1',date_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                status='HARD_VALIDATION_FAILED' if hard else ('AUTHOR_RATIFICATION_PENDING' if pending else 'AUTHOR_RATIFICATION_RECORDED'),
                blocking_errors=hard,pending_author_actions=pending,phaseA_mutated=False,
                note='Author declarations are not cryptographic identity verification. Phase C reliability not conducted.')
    output=a.output_dir/'PhaseB1_Signoff_Gate_Audit.json'
    output.write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Frozen:',a.frozen,'SHA-256',info['frozen_sha256'])
    print('Source:',info['frozen_rows'],'studies x',info['frozen_columns'],'columns; scopes',info['scope_counts'])
    print('Codebook:',info['field_count'],'fields; CORE',info['priority_counts'].get('CORE'),'EXTENDED',info['priority_counts'].get('EXTENDED'))
    print('Technical gate:', 'FAIL' if hard else 'PASS')
    for e in hard:print('ERROR:',e)
    print('Author gates:',info['author_gates_approved'],'of 11 approved')
    if hard:print('STATUS: HARD_VALIDATION_FAILED');sys.exit(2)
    if pending:
        for e in pending:print('PENDING:',e)
        print('STATUS: TECHNICAL_VALIDATION_PASS__AWAITING_AUTHOR_SIGNATURE')
        if a.finalize:sys.exit(3)
    else:
        if a.finalize:
            receipt=a.output_dir/'PhaseB1_AUTHOR_RATIFICATION_RECEIPT.json'
            receipt.write_text(json.dumps({**info,'authority':'Author-declared documented ratification; not independent identity verification.',
               'next_authorized_action':'B2 working register initialization; Phase A read-only'},indent=2),encoding='utf-8')
            print('STATUS: B1_AUTHOR_RATIFICATION_RECORDED__B2_AUTHORIZED');print('Receipt:',receipt)
        else:print('STATUS: TECHNICAL_VALIDATION_PASS__RATIFICATION_RECORD_READY (rerun --finalize)')
    print('Audit:',output)
if __name__=='__main__':main()
