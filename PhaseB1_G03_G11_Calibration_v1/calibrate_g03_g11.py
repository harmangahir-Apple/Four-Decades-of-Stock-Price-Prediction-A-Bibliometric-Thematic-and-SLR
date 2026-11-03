#!/usr/bin/env python3
"""Phase B1 synthetic rules calibration. DOES NOT verify any actual study or approve B1."""
import argparse,csv,json,hashlib,re
from collections import Counter
from datetime import date
from pathlib import Path

BOOL=('Direct_Yes','Direct_No','Ambiguous','Task_NA','Fulltext_Search_Complete',
 'Critical_Material_Missing','Primary_Material_Leak_Verified','Primary_All_Paths_Protected',
 'Secondary_Material_Leak_Verified','Repository_Link_Reported','Repository_Artifact_Verified',
 'Guard_Reject_Nominal_Ordinal')
GENERAL={'YES':'Yes','EXPLICIT_NO':'No / not documented','NOT_REPORTED':'No / not documented',
 'INSUFFICIENT_ACCESS':'Not recoverable','AMBIGUOUS':'Unclear','NOT_APPLICABLE':'Separate N/A'}
NOMINAL_OR_ORDINAL={'TV01','PL11'}

class CalibrationError(RuntimeError):pass

def yes(row,k):
 v=str(row.get(k,'')).strip().lower()
 if v not in ('0','1'):raise CalibrationError(f"{row['Case_ID']} invalid boolean {k}={v!r}")
 return v=='1'

def apply_reporting(state,field):
 if field in NOMINAL_OR_ORDINAL:
  raise CalibrationError(f'{field} is nominal/ordinal; a generic YES/NO table is invalid')
 if state not in GENERAL:raise CalibrationError(f'Unsupported state in yes/no table: {state}')
 return GENERAL[state]

def decide(row):
 fid=row['Field_ID']; scope=row['Evidence_Scope']; cid=row['Case_ID']
 if scope not in ('Full_Text','Abstract_Only','Metadata_Only'):
  raise CalibrationError(f'{cid}: unrecognized evidence scope {scope}')
 for k in BOOL:yes(row,k)
 if yes(row,'Guard_Reject_Nominal_Ordinal'):
  try:apply_reporting('HIGH',fid)
  except CalibrationError:return ('CROSSWALK_PROHIBITED','Crosswalk rejected','',{})
  raise CalibrationError('Ordinal/nominal crosswalk incorrectly allowed')
 if fid=='PL11':
  if yes(row,'Ambiguous'):state='CONFLICTED'
  elif yes(row,'Primary_Material_Leak_Verified'):state='HIGH'
  elif yes(row,'Primary_All_Paths_Protected'):state='LOW'
  else:state='INDETERMINATE'
  secondary=yes(row,'Secondary_Material_Leak_Verified')
  return (state,'Ordinal / separate','',{'mixed_experiment':bool(secondary and state=='LOW'),
     'any_experiment_high':bool(secondary or state=='HIGH'),'primary_risk':state})
 if yes(row,'Direct_Yes') and yes(row,'Direct_No'):return ('AMBIGUOUS','Unclear','',{})
 if yes(row,'Task_NA'):
  if not row.get('Task_NA_Reason','').strip():raise CalibrationError(f'{cid} N/A requires affirmative task reason')
  state='NOT_APPLICABLE'
 elif yes(row,'Ambiguous'):state='AMBIGUOUS'
 elif fid=='RP01':
  if yes(row,'Repository_Artifact_Verified'):state='YES'
  elif yes(row,'Direct_No'):state='EXPLICIT_NO'
  else:state='INSUFFICIENT_ACCESS'
 elif yes(row,'Direct_Yes'):state='YES'
 elif yes(row,'Direct_No'):state='EXPLICIT_NO'
 elif yes(row,'Critical_Material_Missing'):state='INSUFFICIENT_ACCESS'
 elif scope!='Full_Text':state='INSUFFICIENT_ACCESS'
 elif yes(row,'Fulltext_Search_Complete'):
  if not row['Negative_Search_Log'].strip():raise CalibrationError(f'{cid}: NOT_REPORTED needs a search log')
  state='NOT_REPORTED'
 else:state='INSUFFICIENT_ACCESS'
 subtype=state if state in ('EXPLICIT_NO','NOT_REPORTED') else ''
 aux={}
 if fid=='RP01':aux={'link_reported':yes(row,'Repository_Link_Reported'),
       'artifact_verified':yes(row,'Repository_Artifact_Verified')}
 return (state,apply_reporting(state,fid),subtype,aux)

def aggregate(statuses,field):
 # This function is ONLY for yes/no fields with complete Phase B/Phase C outcomes.
 if field in NOMINAL_OR_ORDINAL:raise CalibrationError(f'Forbidden aggregation for {field}')
 counts=Counter(statuses)
 if counts.get('NOT_ASSESSED',0):raise CalibrationError('Unassessed records block publication')
 for k in counts:
  if k not in GENERAL:raise CalibrationError(f'Unknown state {k}')
 n_total=sum(counts.values());na=counts['NOT_APPLICABLE'];n_app=n_total-na
 out={'n_total':n_total,'n_applicable':n_app,'n_not_applicable':na,
   'Yes':counts['YES'], 'No_not_documented':counts['EXPLICIT_NO']+counts['NOT_REPORTED'],
   'No_explicit_negative':counts['EXPLICIT_NO'], 'No_not_reported':counts['NOT_REPORTED'],
   'Not_recoverable':counts['INSUFFICIENT_ACCESS'],'Unclear':counts['AMBIGUOUS']}
 if sum(out[k] for k in ('Yes','No_not_documented','Not_recoverable','Unclear'))!=n_app:
  raise CalibrationError('Hidden denominator difference in reporting table')
 return out

def author_review(path):
 if not path: return {'status':'NOT_SUBMITTED','reviewed':0}
 rows=list(csv.DictReader(open(path,encoding='utf-8-sig',newline='')))
 if len(rows)!=12 or len({x['Case_ID'] for x in rows})!=12:raise CalibrationError('Author review needs 12 unique case IDs')
 n=0;revisions=[]
 for x in rows:
  decision=x.get('Author_Decision_ACCEPT_or_REVISE','').strip()
  if not decision:continue
  if decision not in ('ACCEPT','REVISE'):raise CalibrationError(f"Invalid author decision {x['Case_ID']}: {decision}")
  if not x.get('Author_Name','').strip():raise CalibrationError(f"{x['Case_ID']} lacks author name")
  ds=x.get('Review_Date_YYYY_MM_DD','').strip()
  try: date.fromisoformat(ds)
  except ValueError:raise CalibrationError(f"{x['Case_ID']} has invalid ISO date")
  if decision=='REVISE' and not x.get('Author_Comments','').strip():raise CalibrationError(f"{x['Case_ID']} revision needs explanation")
  n+=1
  if decision=='REVISE':revisions.append(x['Case_ID'])
 return {'status':'ALL_ACCEPTED_BY_REVIEWING_AUTHOR' if n==12 and not revisions else 'INCOMPLETE_OR_REVISIONS_REQUIRED',
   'reviewed':n,'revisions':revisions}

def main():
 ap=argparse.ArgumentParser(description='12 synthetic test scenarios; DOES NOT approve G03/G11')
 base=Path(__file__).resolve().parent
 ap.add_argument('--casebook',type=Path,default=base/'B1_12_Synthetic_Calibration_Cases.csv')
 ap.add_argument('--expected',type=Path,default=base/'B1_12_Case_Expected_Results.json')
 ap.add_argument('--output-dir',type=Path,default=Path('PhaseB1_G03_G11_Calibration_Results'))
 ap.add_argument('--author-review',type=Path,default=None)
 a=ap.parse_args()
 expected=json.loads(a.expected.read_text(encoding='utf-8'))
 rows=list(csv.DictReader(a.casebook.open(encoding='utf-8-sig',newline='')))
 if len(rows)!=12 or {r['Case_ID'] for r in rows}!=set(expected):raise CalibrationError('12-case ID inventory mismatch')
 out=[]
 for row in rows:
  state,display,subtype,aux=decide(row)
  exp=expected[row['Case_ID']]
  passed=(state,display,subtype)==(exp['expected_state'],exp['reporting_category'],exp['no_subtype'])
  out.append({'Case_ID':row['Case_ID'],'Field_ID':row['Field_ID'],
   'Evidence_Scope':row['Evidence_Scope'],'Expected_State':exp['expected_state'],
   'Actual_State':state,'Expected_Display':exp['reporting_category'],
   'Actual_Display':display,'No_Subtype':subtype,
   'Status':'PASS' if passed else 'FAIL',
   'Auxiliary_Controls_JSON':json.dumps(aux,sort_keys=True),
   'Synthetic_Scenario':row['Synthetic_Scenario']})
 if any(x['Status']!='PASS' for x in out):raise CalibrationError('The 12-case coding logic failed')
 # Extra invariants: mixed experiment retains both primary and sensitivity conclusions.
 mixed=json.loads(next(r for r in out if r['Case_ID']=='CAL10')['Auxiliary_Controls_JSON'])
 if mixed!={'any_experiment_high':True,'mixed_experiment':True,'primary_risk':'LOW'}:
  raise CalibrationError('Mixed experiment provenance failed')
 repo=json.loads(next(r for r in out if r['Case_ID']=='CAL11')['Auxiliary_Controls_JSON'])
 if repo!={'artifact_verified':False,'link_reported':True}:raise CalibrationError('Repository link/access separation failed')
 # Purely synthetic 485-record aggregate fixtures, NOT outcomes for actual studies.
 synthetic=['YES']*100+['EXPLICIT_NO']*5+['NOT_REPORTED']*200+['INSUFFICIENT_ACCESS']*130+['AMBIGUOUS']*40+['NOT_APPLICABLE']*10
 agg=aggregate(synthetic,'ST01')
 if agg['n_total']!=485 or agg['n_applicable']!=475 or agg['No_explicit_negative']!=5 or agg['No_not_reported']!=200:
  raise CalibrationError('Synthetic 485-record denominator fixture failed')
 rejected={}
 try:aggregate(synthetic+['NOT_ASSESSED'],'ST01')
 except CalibrationError as e:rejected['incomplete_workflow']=str(e)
 try:aggregate(synthetic,'PL11')
 except CalibrationError as e:rejected['ordinal_crosswalk']=str(e)
 if set(rejected)!={'incomplete_workflow','ordinal_crosswalk'}:
  raise CalibrationError('Mandatory publication safeguards failed')
 ar=author_review(a.author_review)
 a.output_dir.mkdir(parents=True,exist_ok=True)
 with (a.output_dir/'B1_12_Case_Automated_Results.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
 receipt={'purpose':'SYNTHETIC_PROTOCOL_LOGIC_ONLY','real_study_verifications':0,
  'b1_author_approvals_created':0,'phase_a_files_modified':0,
  'cases_passed':len(out),'cases_total':12,'result':'PASS_SYNTHETIC_LOGIC_ONLY',
  'source_casebook_sha256':hashlib.sha256(a.casebook.read_bytes()).hexdigest(),
  'source_expected_sha256':hashlib.sha256(a.expected.read_bytes()).hexdigest(),
  'synthetic_485_test_not_real_evidence':agg,'rejected_invalid_publication_cases':rejected,
  'author_calibration_review':ar,
  'gate_status':'NOT_APPROVED__AUTHOR_REVIEW_AND_VERSIONED_PROTOCOL_STILL_REQUIRED'}
 (a.output_dir/'B1_G03_G11_Calibration_Receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 md=['# G03/G11 12-case calibration (synthetic rules test)',
  '**No original study was assessed, no quotation or page number generated, no author approval recorded.**','',
  '| Case | Domain | Expected | Automated result | Test |', '|---|---|---|---|---|']
 for r in out:md.append(f"| {r['Case_ID']} | {r['Field_ID']} | {r['Expected_State']} | {r['Actual_State']} | {r['Status']} |")
 md+=['','## Synthetic 485-record reporting conservation (TEST DATA ONLY)',
   f"n = {agg['n_total']}; applicable = {agg['n_applicable']}; N/A = {agg['n_not_applicable']}; No explicitly negative = {agg['No_explicit_negative']}; No not documented = {agg['No_not_reported']}.",
  '','## Publication guards',f"- Unassessed values rejected: {rejected['incomplete_workflow']}",
   f"- Ordinal leakage risk rejected from YES/NO crosswalk: {rejected['ordinal_crosswalk']}",
   '','**Next gate:** independent author review of the proposed rules; any real-paper calibration requires authentic full texts, pages, and exact source locations. Phase B1 is not signed.']
 (a.output_dir/'B1_G03_G11_Calibration_Report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
 print(f'PASS: {len(out)}/12 synthetic evidence-state cases')
 print('PASS: both extra safeguards (NOT_ASSESSED gate; nominal/ordinal aggregation rejection)')
 print('PASS: synthetic 485-record conservation fixture (not actual 485 studies)')
 print(f"AUTHOR CALIBRATION REVIEW: {ar['status']} ({ar['reviewed']}/12)")
 print('G03 / G11: NOT APPROVED — genuine author review and versioned signoff still required')
 print('Results:',a.output_dir.resolve())

if __name__=='__main__':
 try:main()
 except (CalibrationError,FileNotFoundError) as e:
  raise SystemExit('FAIL: '+str(e))
