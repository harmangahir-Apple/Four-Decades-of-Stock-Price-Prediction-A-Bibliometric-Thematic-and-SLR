#!/usr/bin/env python3
"""ARCO Phase B1 reviewer-informed 11-gate audit (read-only, evidence anchored).

Inputs: current main/supplementary PDFs, original reviewer DOCX, optional handover DOCX,
         existing Phase B1 sign-off candidate package and frozen workbook.
Outputs: review-oriented CSV/JSON/Markdown only. NEVER edits approval form or source data.

This is a traceable retrieval/consistency assistant, NOT semantic certification, primary-paper
verification, author approval, independent second coding or manuscript revision.
Requires: pymupdf (fitz), python-docx. The existing signoff gate itself uses stdlib.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,importlib.util,json,re,sys
from collections import Counter
from pathlib import Path

GATES = {
 'G01': {'title':'Corpus integrity and immutable Phase A freeze','review':r'485|492|493|494|screening|curation|corpus|records|deduplicat',
         'main':r'frozen technical|485|eligibility|paper.id','supp':r'485|denominator|full.text evidence|frozen technical',
         'risk':'Ensure historical handovers (493/494/4,974) do not overwrite the current 485/4,975 freeze. Require exact workbook checksum and unique-ID audit.',
         'recommendation':'TECHNICAL_PASS_CONDITIONAL_AUTHOR_REVIEW'},
 'G02': {'title':'45-field codebook, evidence thresholds and all reviewer audit domains','review':r'baseline|explainabil|uncertainty|statistical|leakage|reproducib|economic|validation|method famil',
         'main':r'baseline|explainability|uncertainty|table 10|review methodology', 'supp':r'technical.extraction|methodological.audit|table s14|table s18',
         'risk':'Check field definitions for baselines, XAI, prediction uncertainty and experimental controls. A field existing in the codebook is not evidence that papers were recoded.',
         'recommendation':'REVIEW_THRESHOLDS_BEFORE_APPROVAL'},
 'G03': {'title':'Evidence outcomes and missingness','review':r'negative finding|split unclear|not recoverable|no column|no public code|not present|unclear|yes and unclear',
         'main':r'yes.*no.*unclear|negative classification|unclear denotes|evidence.supported methodological',
         'supp':r'unclear classification|evidence recoverability|abstract.only|metadata.only',
         'risk':'CRITICAL: Reviewer 1 requests a visible full-text-assessed-not-documented category. Distinguish observable documentary non-reporting from explicit non-use of a method. Agree reporting aggregation before G03 approval.',
         'recommendation':'AMEND_OR_DOCUMENT_REVIEWER_CROSSWALK'},
 'G04': {'title':'Source precedence, provenance, negative search log','review':r'query|screening rules|reproducib|recover|supplementary|evidence|full.text|source',
         'main':r'search strateg|coding|evidence|validation|data availability',
         'supp':r'search expression|coding verification|source|table s14|s2',
         'risk':'The review PDFs are secondary evidence for B1 design; actual full texts, archived pages, PDF page indices, URL checks and negative-search logs are still required for B4/B5.',
         'recommendation':'APPROVE_ONLY_IF_PROVENANCE_REQUIREMENTS_ACCEPTED'},
 'G05': {'title':'Leakage-risk rules and experiment-specific aggregation','review':r'leakage risk|global scaling|preprocessing|overlap|validation design|training.only',
         'main':r'low.risk|leakage|preprocessing boundary|data.dependent',
         'supp':r'leakage|training.only|methodological.audit',
         'risk':'LOW must require affirmative protection of applicable pathways; mixed primary/supporting experiments need a predeclared policy. Verify historical leakage signals only from authentic study-level evidence.',
         'recommendation':'REVIEW_AGGREGATION_AND_LOW_RISK_CRITERIA'},
 'G06': {'title':'Multi-experiment to study-level summary','review':r'multiple|method famil|assessment|comparison|classification',
         'main':r'multiple|study.level|experiment|primary|robustness',
         'supp':r'one.*study|study.level|method.family|coding',
         'risk':'Require an experiment selection plan before viewing performance; report primary-vs-any-positive sensitivity and preserve conflicts. A paper-level YES cannot automatically represent all experiments.',
         'recommendation':'APPROVE_ONLY_AFTER_PREDEFINING_EXPERIMENT_POLICY'},
 'G07': {'title':'Stratified B3 pilot and independent sampling','review':r'sample|second verification|stratif|100 records|unverified|kappa|coding reliab',
         'main':r'40.study|stratified|sample|verification',
         'supp':r'40.*verification|coding verification|37.*40|sample',
         'risk':'Proposed 40-study B3 pilot is NOT the ~100 previously-unverified second-reviewer sample requested by Reviewer 1. Pilot IDs, eligible strata, seed and deviation logs remain to be generated.',
         'recommendation':'PILOT_PROVISIONAL__PHASE_C_SAMPLE_SEPARATE'},
 'G08': {'title':'B2 schema, source-to-ID mappings, audit and change tracking','review':r'coding dictionary|categorization|ruleset|tie.break|supplementary|screening|data',
         'main':r'study.level|data availability|coding|audit',
         'supp':r'supplementary data s1|field group|extracted or audited|verification|register',
         'risk':'Confirm complete 51-column map; 45 fields with experiment-level records; new blank B2 outcomes; Paper_ID and source hashes; raw text and adjudication logs. Do not equate Table S14 description with a populated B2 register.',
         'recommendation':'TECHNICAL_SCHEMA_REVIEW_REQUIRED'},
 'G09': {'title':'Phase C independent coding and reliability boundaries','review':r'kappa|independent|second reviewer|coding reliability|chance.corrected|100 records|error.adjusted',
         'main':r'independent|kappa|agreement|limitations|verification',
         'supp':r'absence of formal inter|37/40|independent coding|coding.verification',
         'risk':'The original 37/40 check is NOT Cohen kappa. Phase C needs an actual independent coding set, sampling design and dimension-wise chance-corrected agreement; do not mark reviewer request completed at B1.',
         'recommendation':'APPROVE_PHASE_C_BOUNDARY_NOT_COMPLETION'},
 'G10': {'title':'Publication freeze, revision control and denominator governance','review':r'cross.reference|percentages|summary|no.*available|full.*register|revis|supplementary',
         'main':r'485|5,022|4,975|reproducibility|supplementary data',
         'supp':r'4,975|4,972|485|supplementary data s1',
         'risk':'Maintain current Phase A counts until B and C close. Historical 493/4,974 snapshots must be flagged as archival, not reconciled by silently changing current numbers.',
         'recommendation':'APPROVE_ONLY_WITH_EXPLICIT_VERSION_CONTROL'},
 'G11': {'title':'Scientific scope and negative evidence safeguards','review':r'unclear|negative|not recoverable|metadata.only|not present|bias|full.text',
         'main':r'unclear|not interpret|not representative|subset|reporting',
         'supp':r'insufficient recoverable|metadata.only|full.text|limitations',
         'risk':'Mandatory reviewer-response crosswalk must specify: full-text assessed-not-documented is a reporting negative, NOT verified non-performance. Limited-access cases stay not recoverable absent direct evidence.',
         'recommendation':'AMEND_OR_DOCUMENT_REVIEWER_CROSSWALK'}
}

# Exact claims are extracted only if regex matches actual uploaded text; no fabricated quotations.
DIRECT_ISSUES = [
 ('Reviewer 1 missingness challenge','G03','reviewer1',r'Table 10|No column|negative finding'),
 ('Reviewer 1 code availability challenge','G11','reviewer1',r'public code|code availability'),
 ('Reviewer 1 independent second reviewer request','G09','reviewer1',r'about 100 records|report kappa|second verification'),
 ('Reviewer 1 baseline and XAI request','G02','reviewer1',r'baseline selection|Explainability and uncertainty'),
 ('Reviewer 1 coding rules complaint','G04','reviewer1',r'rules appear nowhere|rules are unstated'),
 ('Reviewer 2 evidence provenance concern','G04','reviewer2',r'queries used for the review'),
 ('Current Table 10 retains 3 columns','G03','manuscript',r'Table 10 Evidence.supported methodological practices'),
 ('Current Table 10 interpretation','G11','manuscript',r'Unclear, n'),
 ('Supplement S18 contains family table','G02','supplementary',r'Table S18'),
 ('Supplement reports historical verification','G09','supplementary',r'37.*confirmed|Thirty.seven classifications'),
 ('Supplement records interreviewer limitation','G09','supplementary',r'Absence of formal inter.reviewer'),
 ('Phase B1 pilot not completed by past 40 sample','G07','supplementary',r'Stratified forecasting.target verification sample'),
 ('Historical count may differ from current frozen denominator','G10','handover',r'4,974|n=493|494.study')
]


def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def docs(path:Path,role:str):
 """Return actual page-/paragraph-located items; no OCR or inferred pagination."""
 if not path.exists():raise FileNotFoundError(path)
 if path.suffix.lower()=='.pdf':
  import fitz
  obj=fitz.open(path)
  try:
   return [dict(role=role,file=path.name,locator=f'PDF page {i+1}',location_number=i+1,
               text=' '.join(p.get_text(sort=True).split())) for i,p in enumerate(obj)]
  finally:obj.close()
 if path.suffix.lower()=='.docx':
  from docx import Document
  obj=Document(path)
  arr=[]
  for i,p in enumerate(obj.paragraphs,1):
   text=' '.join(p.text.split())
   if text: arr.append(dict(role=role,file=path.name,locator=f'DOCX paragraph {i}',location_number=i,text=text))
  k=len(obj.paragraphs)
  for ti,t in enumerate(obj.tables,1):
   for ri,row in enumerate(t.rows,1):
    text=' | '.join(' '.join(c.text.split()) for c in row.cells)
    if text:arr.append(dict(role=role,file=path.name,locator=f'DOCX table {ti} row {ri}',location_number=k+ti*1000+ri,text=text))
  return arr
 raise ValueError(f'Unsupported document: {path}')

def quote(text,pattern,maxlength=245):
 m=re.search(pattern,text,re.I)
 if not m:return None
 a=max(0,m.start()-75); b=min(len(text),m.end()+175)
 sample=text[a:b]
 return ('…' if a else '')+sample[:maxlength]+('…' if b<len(text) else '')

def writercsv(path,headers,rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=headers,extrasaction='ignore');w.writeheader();w.writerows(rows)

def extract_source(srcdict, gate_id, category, pattern, limit=2):
 pool=srcdict.get(category,[])
 hits=[]
 for item in pool:
  q=quote(item['text'],pattern)
  if q:
   hits.append(dict(gate_id=gate_id,source_role=category,file=item['file'],location=item['locator'],
                    source_sha256=srcdict['_hashes'][item['file']],excerpt=q,pattern=pattern,
                    evidence_type=('REVIEWER_REQUEST' if category.startswith('reviewer') else
                                   'HISTORICAL_CONTEXT' if category=='handover' else 'CURRENT_DOCUMENT')))
 return hits[:limit]

def audit_technical(args):
 out={'status':'UNVERIFIED_NO_FROZEN_SOURCE','details':{}}
 if not args.frozen or not args.frozen.exists():return out
 out['sha256']=sha(args.frozen)
 if not (args.package_dir/'phaseB1_signoff_gate.py').exists():
  return {'status':'MISSING_SIGNOFF_SCRIPT','sha256':out['sha256']}
 spec=importlib.util.spec_from_file_location('b1signoff',args.package_dir/'phaseB1_signoff_gate.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 try:
  hard,pending,info=mod.check_issues(args.frozen,args.package_dir)
  return {'status':'PASS' if not hard else 'FAILED','hard_errors':hard,'pending':pending,'details':info}
 except Exception as exc:
  return {'status':'FAILED','error':str(exc),'sha256':out['sha256']}

def main():
 pa=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 pa.add_argument('--package-dir',type=Path,required=True)
 pa.add_argument('--frozen',type=Path,required=True)
 pa.add_argument('--manuscript',type=Path,required=True)
 pa.add_argument('--supplementary',type=Path,required=True)
 pa.add_argument('--reviewer1',type=Path,required=True)
 pa.add_argument('--reviewer2',type=Path,required=True)
 pa.add_argument('--handover',type=Path,nargs='*',default=[])
 pa.add_argument('--output-dir',type=Path,required=True)
 a=pa.parse_args()
 for field in ('frozen','manuscript','supplementary','reviewer1','reviewer2'):
  if not getattr(a,field).exists():pa.error(f'File not found: --{field} {getattr(a,field)}')
 a.output_dir.mkdir(parents=True,exist_ok=True)
 approved=a.package_dir/'B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv'
 if not approved.exists():pa.error('Sign-off author CSV missing from package dir')
 with approved.open(encoding='utf-8-sig',newline='') as f:author=list(csv.DictReader(f))
 if [r['Gate_ID'] for r in author]!=[f'G{i:02d}' for i in range(1,12)]:
  pa.error('Unexpected gate IDs; do not modify sign-off source')
 sources={'_hashes':{}}
 paths={ 'manuscript':[a.manuscript],'supplementary':[a.supplementary],
   'reviewer1':[a.reviewer1],'reviewer2':[a.reviewer2], 'handover':a.handover }
 for role,docs_paths in paths.items():
  sources[role]=[]
  for f in docs_paths:
   sources['_hashes'][f.name]=sha(f)
   sources[role].extend(docs(f,role))

 tech=audit_technical(a)
 evidence=[];gate_rows=[];issues=[]
 for rec in author:
  gid=rec['Gate_ID'];g=GATES[gid];support=[]
  for role,pattern in [('reviewer1',g['review']),('reviewer2',g['review']),('manuscript',g['main']),('supplementary',g['supp'])]:
   support.extend(extract_source(sources,gid,role,pattern,limit=2))
  if sources['handover'] and gid in ('G01','G05','G07','G10'):
   support.extend(extract_source(sources,gid,'handover',r'493|494|4,974|full.text|coding',limit=1))
  evidence.extend(support)
  rolecounts=Counter(x['source_role'] for x in support)
  decision=rec.get('Author_Decision','').strip().upper()
  flags=[]
  if gid in ('G03','G11'):flags.append('REVIEWER_1_NEGATIVE_CODING_CONFLICT_REQUIRES_RESPONSE')
  if gid=='G02':flags.append('FIELD_PRESENT_NOT_EQUIVALENT_TO_STUDY_LEVEL_COUNT')
  if gid=='G07':flags.append('PILOT_NOT_SECOND_INDEPENDENT_PHASE_C_SAMPLE')
  if gid=='G09':flags.append('NO_INDEPENDENT_AGREEMENT_YET')
  if gid=='G04':flags.append('PRIMARY_STUDY_SOURCE_VALIDATION_PENDING')
  if gid=='G10':flags.append('HISTORICAL_HANDOVERS_CAN_CONTAIN_OBSOLETE_DENOMINATORS')
  if gid=='G01' and tech['status']!='PASS':flags.append('TECHNICAL_SOURCE_GATE_NOT_PASSED')
  if not rolecounts.get('reviewer1') and not rolecounts.get('reviewer2'):
   flags.append('REVIEWER_MATCH_NOT_LOCATED_BY_PATTERN__MANUAL_REVIEW')
  gate_rows.append({'Gate_ID':gid,'Scientific_Approval_Gate':rec['Scientific_Approval_Gate'],
   'Proposed_Independent_Assessment':g['recommendation'],
   'Current_Author_Decision':decision or 'BLANK',
   'Reviewer1_Matches':rolecounts.get('reviewer1',0),'Reviewer2_Matches':rolecounts.get('reviewer2',0),
   'Main_PDF_Matches':rolecounts.get('manuscript',0),'Supplementary_PDF_Matches':rolecounts.get('supplementary',0),
   'Issue_Flags':'; '.join(flags), 'Required_Author_Check':g['risk'],
   'Approval_May_Be_Automated':'NO','Author_Action':'Read evidence passages, dossier and amendment ledger; approve/reject manually'})
  for f in flags:issues.append({'Gate_ID':gid,'Issue_Flag':f,'Description':g['risk'],'Disposition':'AUTHOR_REVIEW_REQUIRED'})
 for title,gid,role,regex in DIRECT_ISSUES:
  hits=extract_source(sources,gid,role,regex,limit=2)
  for item in hits:issues.append({'Gate_ID':gid,'Issue_Flag':title,'Description':item['excerpt'],
    'Location':item['file']+' '+item['location'], 'Disposition':'EVIDENCE_FOUND__CHECK_IF_RESOLVED'})
  if not hits:issues.append({'Gate_ID':gid,'Issue_Flag':title,'Description':'Anchor passage not located automatically; manual inspection needed',
                             'Location':'','Disposition':'NOT_LOCATED_BY_PATTERN'})

 eheaders=['gate_id','source_role','file','location','source_sha256','excerpt','pattern','evidence_type']
 writercsv(a.output_dir/'B1_11Gate_Evidence_Trace.csv',eheaders,evidence)
 writercsv(a.output_dir/'B1_11Gate_Review_Recommendations.csv',list(gate_rows[0]),gate_rows)
 writercsv(a.output_dir/'B1_Reviewer_And_Protocol_Issue_Log.csv',['Gate_ID','Issue_Flag','Description','Location','Disposition'],issues)

 # Human-facing text with concise provenance; note DOCX paragraphs are not printed page numbers.
 report=['# ARCO Phase B1 — Reviewer-informed scientific sign-off review','',
  '**Output type:** evidence-assisted recommendations, NOT author ratification.','',
  f'**Audit UTC:** {datetime.datetime.now(datetime.timezone.utc).isoformat()}','',
  f'**Frozen technical gate:** {tech["status"]}.','',
  '**Evidence discipline:** current manuscript and supplementary take precedence for present claims; '
  'reviewer documents are reviewer demands; historical handovers are provenance only and may contain stale counts.','',
  '**Automatic gate approval:** prohibited. No source or approval form was edited.','',
  '## Executive findings','',
  '1. Reviewer 1 requests a more informative full-text documentary absence classification. '
  'G03/G11 must define a response-compatible crosswalk without asserting actual non-use.',
  '2. The current main Table 10 remains a Yes/No/Unclear table; the new Phase B reporting design is not yet applied.',
  '3. Supplement S18 already provides historical method-family audit marginal counts; B1 fields are not verified recoding results.',
  '4. Reviewer 1 calls for independent checks including a sample of approximately 100 previously unverified records. '
  'The 40-study B3 pilot serves a different purpose. Phase C is pending.',
  '5. Older handover files describe superseded corpus sizes; do not let them change the frozen Phase A workbook.','',
  '## Gate-by-gate review','']
 for r in gate_rows:
  gid=r['Gate_ID'];g=GATES[gid]
  report += [f'### {gid}: {g["title"]}',
    f'**Proposed disposition:** `{r["Proposed_Independent_Assessment"]}` (not an author decision).',
    f'**Critical check:** {g["risk"]}',
    f'**Reviewer matches:** R1={r["Reviewer1_Matches"]}, R2={r["Reviewer2_Matches"]}; '
    f'current main={r["Main_PDF_Matches"]}, supplement={r["Supplementary_PDF_Matches"]}.','']
  for item in [x for x in evidence if x['gate_id']==gid][:5]:
   report += [f'- {item["source_role"]}: `{item["file"]}`, {item["location"]} — “{item["excerpt"]}”']
  report += ['']
 report += ['## Interpretation safeguards','',
    '- Keyword/text matches are **leads**, not proof of methodological compliance or reviewer satisfaction.',
    '- DOCX locators refer to paragraph or table row, never presumed printed page numbers.',
    '- Reviewer comments refer to the original manuscript; they can contain superseded 493/379 values.',
    '- This audit cannot verify original papers or recorded quotations because a complete 375-paper full-text library is not supplied.',
    '- The working B1 author approval form remains untouched. After genuine review, fill its gates and run the original sign-off gate.',
    '- No manuscript counts, codebook fields, or frozen 485-study classifications have been changed.']
 (a.output_dir/'B1_11Gate_Critical_Review.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
 receipt={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'technical_gate_status':tech['status'],'technical_gate':tech,'gates_reviewed':11,
  'author_decisions_written':0,'phaseA_mutated':False,
  'sources':[{'role':role,'name':p.name,'sha256':sources['_hashes'][p.name]} for role,paths2 in paths.items() for p in paths2],
  'evidence_traces':len(evidence),'issues':len(issues),'limitations':['Not an automated reviewer','Not full-text coding of 375 original studies',
  'Does not authorize approval','Does not substitute Phase C independence']}
 (a.output_dir/'B1_11Gate_Audit_Receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
 print('B1 reviewer-informed audit complete')
 print('Technical gate:',tech['status'])
 print('Gate assessments:',len(gate_rows),'evidence excerpts:',len(evidence),'issue rows:',len(issues))
 print('Author approvals changed: 0; source workbooks modified: 0')
 print('Outputs:',a.output_dir)

if __name__=='__main__':main()
