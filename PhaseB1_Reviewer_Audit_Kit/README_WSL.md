# ARCO Phase B1 — Reviewer-informed scientific gate audit

This read-only Python audit extracts evidence anchors from:
- both original reviewer Word documents;
- the **latest** manuscript and supplementary PDF;
- five historical handover Word documents (context only);
- frozen Phase A register and B1 sign-off candidate via the existing technical gate.

It writes **recommendations**, not approvals. It never edits the author approval CSV, manuscripts, or frozen data.

## Environment

```bash
conda activate Harman_GPU
python -m pip install pymupdf python-docx
```

## Folder setup in WSL

Place the nine uploaded Word/PDF files (two reviewers, two latest PDFs, five handovers) under:

`~/projects/Stock_Price_Prediction_SLR_ACME/PhaseB1_Review_Inputs/`

You may drag these files into the VS Code Explorer or copy them from `/mnt/c/Users/<WindowsUser>/Downloads/`.

The existing project should already have:

- `PhaseB1_Signoff_Candidate/` (unpacked B1 package),
- `Supplementary_Data_S1_485_FROZEN.xlsx` (approved original; read-only).

Extract this kit to `PhaseB1_Reviewer_Audit_Kit/` and run:

```bash
bash PhaseB1_Reviewer_Audit_Kit/run_b1_review.sh
```

Alternatively run `python PhaseB1_Reviewer_Audit_Kit/review_b1_11_gates.py --help` to supply custom file paths. All files are explicitly named; the runner refuses to substitute older documents.

## Outputs

In `PhaseB1_Reviewer_Audit_Results/`:

- `B1_11Gate_Critical_Review.md` — 11 decisions to review, source locators and matched excerpts;
- `B1_11Gate_Review_Recommendations.csv` — concise sign-off checklist;
- `B1_11Gate_Evidence_Trace.csv` — passage/paragraph-level retrieval log;
- `B1_Reviewer_And_Protocol_Issue_Log.csv` — unresolved issues and locations;
- `B1_11Gate_Audit_Receipt.json` — hashes, provenance, technical outcome, no edits.

## How to use scientific review output

1. Read the report and audit issues.
2. Review original reviewer comments and inspect context around evidence matches.
3. Make amendments to a **new version** of the B1 protocol if necessary (especially G03/G11).
4. Review each gate and populate `PhaseB1_Signoff_Candidate/B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv` **yourself**, not through this script.
5. Run original `phaseB1_signoff_gate.py` to verify author decisions; use `--finalize` only after genuine author approval.

### Important methodological distinction

Reviewer 1 requests a reporting-negative state for *full text inspected, practice not documented*. That is not equivalent to verified non-performance. The current six-state B1 evidence coding may be retained if a transparent reporting crosswalk is added. Decide this before signing G03/G11. The current main manuscript Table 10 has not yet been rewritten; that is future B/C integration work.

### Scope limitation

This tool searches text and records quotes only where the words appear. It does not interpret source code, retrieve 375 original full-text studies, adjudicate true methodological practice, verify a DOI, prove peer-review compliance, or compute independent agreement. A matched phrase does not constitute an approved gate.
