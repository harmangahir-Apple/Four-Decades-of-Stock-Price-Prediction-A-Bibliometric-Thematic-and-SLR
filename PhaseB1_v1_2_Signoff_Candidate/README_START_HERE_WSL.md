# ARCO Phase B1 v1.2 — Version-Controlled Sign-off Candidate

**Status:** candidate for scientific author ratification; **not signed**. The 12 synthetic cases and their separate author review do **not** approve G03/G11 automatically. All 11 form decisions are intentionally blank. Historical chats/reviewer comments are context, not primary-study evidence.

## 1. Extract (from your WSL project directory)

```bash
cd ~/projects/Stock_Price_Prediction_SLR_ACME
conda activate Harman_GPU
unzip -o ARCO_PhaseB1_v1_2_Signoff_Candidate_20261029.zip -d PhaseB1_v1_2_Signoff_Candidate
```

## 2. Check current source and your genuine 12-case author-review record

```bash
python PhaseB1_v1_2_Signoff_Candidate/phaseB1_v1_2_signoff_gate.py \
  --frozen './Supplementary_Data_S1_485_FROZEN.xlsx' \
  --package-dir PhaseB1_v1_2_Signoff_Candidate \
  --calibration-review PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv \
  --output-dir PhaseB1_v1_2_Signoff_Audit
```

Expected if your local review file is the one shown in chat, and the source is unmodified:

```
TECHNICAL GATE: PASS
CALIBRATION: 12/12_SYNTHETIC_PASS__AUTHOR_ACCEPTANCE_DOCUMENTED
AUTHOR GATES: 0 /11 APPROVED
STATUS: AUTHOR_RATIFICATION_PENDING — NO APPROVAL RECEIPT ISSUED
```

This **does not** indicate failed calibration: the independent author approval form is still blank.

## 3. Scientific author review and sign-off of the entire B1 v1.2 protocol

Open the scientific addendum, updated codebook, and separate form:

```bash
code PhaseB1_v1_2_Signoff_Candidate/B1_v1_2_Scientific_Rule_Addendum_SIGNOFF_CANDIDATE.md
code PhaseB1_v1_2_Signoff_Candidate/PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv
code PhaseB1_v1_2_Signoff_Candidate/B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv
```

For each gate G01–G11: read its `Required_Approval_Statement`, the relevant dossier / v1.2 addendum, and source reviewer comments. If acceptable **to the actual author**, enter `APPROVE`, actual approving author name, actual date (`YYYY-MM-DD`), and concise rationale. If not acceptable, enter `REJECT` with a reason and amend the scientific protocol before later reconsideration. For G03 and G11, the comments must explicitly address the reviewer-facing crosswalk, non-reporting ≠ procedural non-use, source recoverability, and N/A handling. G05/G06/G07/G09 also have separate caveats in the addendum.

**Never prefill signatures or approve programmatically. Do not rewrite any source workbook, Phase A counts, or the original v1.1 package.** Only this new author form is editable. The entire v1.2 signed version is defined by v1.1 codebook + six v1.2 field guardrail enhancements + v1.2 addendum + versioned manifest; amended materials should require a new version number and rehashing, not in-place editing.

## 4. Verify again, then finalize only after all 11 genuine approvals

```bash
python PhaseB1_v1_2_Signoff_Candidate/phaseB1_v1_2_signoff_gate.py \
  --frozen './Supplementary_Data_S1_485_FROZEN.xlsx' \
  --package-dir PhaseB1_v1_2_Signoff_Candidate \
  --calibration-review PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv \
  --output-dir PhaseB1_v1_2_Signoff_Audit \
  --finalize
```

A receipt (`B1_v1_2_AUTHOR_RATIFICATION_RECEIPT.json`) is created **only** if all immutable data/protocol checks pass, synthetic calibration + author-review verification passes, and all eleven signed decisions are APPROVE. This is an author declaration, not cryptographic identity verification or a second-reviewer reliability study.

## 5. What is *not* authorized by this candidate

- No new 485-study evidence coding has been performed.
- No change to Phase A manuscript, supplement, tables, figures, original source register or percentages.
- No Phase C agreement statistics or error-adjusted intervals can be claimed without independent study-level coding.
- B2 working-register initialization becomes authorized only after true B1 author ratification, while Phase A stays immutable.

## File roles

| File | Function |
|---|---|
| `B1_v1_2_Scientific_Rule_Addendum_SIGNOFF_CANDIDATE.md` | crosswalk, risk, pilot and provenance safeguards |
| `PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv` | 45 original field IDs plus six new explicit guardrail notes |
| `B1_v1_2_Field_Rule_Change_Log.csv` | precise v1.1-to-v1.2 modifications |
| `B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv` | only author-editable file; deliberately blank |
| `phaseB1_v1_2_signoff_gate.py` | frozen source + immutable package + synthetic calibration + author approval verification |
| `B1_v1_2_File_Hash_Manifest.json` | SHA-256 hashes of immutable protocol components |
| `Calibration/` | read-only 12 synthetic scenarios, test logic and expected results |
