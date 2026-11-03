# ARCO Phase B3 — 40-study author-selection review

**Purpose:** Help the author complete `B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv` using the 485-study frozen register, the exact 40-study selection, and cautious source verification. This is NOT an automatic scientific approval.

## Verified register facts

- Frozen XLSX SHA-256: `95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5`.
- The selection contains 40 unique IDs, all present in the frozen register.
- Every selected paper's title, DOI, year, original evidence scope, assigned method family, historical validation label and leakage-risk label exactly matches the frozen register.
- No selected DOI or normalized title is duplicated in the 485-record register.
- 30 Full_Text, 6 Abstract_Only, 4 Metadata_Only.
- All 40 have Finalization_Status=Finalized; all 40 source status fields in the pilot CSV still say NOT_VERIFIED.
- 36 candidates may be approved for sample *selection* after actual author review; FOUR require targeted investigation and MUST NOT be rubber-stamped.

## Files

- `B3_40_STUDY_RECOMMENDATIONS_AND_EVIDENCE.csv`: 40-row crosswalk, reasons, source URLs for selectively researched flags, and a suggested decision.
- `B3_4_FLAGGED_STUDIES_ISSUE_LOG.csv`: four records requiring additional checking.
- `B3_pilot_40_AUTHOR_SELECTION_REVIEW_PREFILLED_COMMENTS_DRAFT.csv`: exact 6-column author form with proposed comments but deliberately BLANK decisions, name, and date. Copy as a **new** working file; leave your originals untouched.
- `B3_40_Author_Review_Workbook.xlsx`: styled review summary and 40-row matrix.
- `B3_REGISTER_AUDIT_RECEIPT.json`: computational checks.
- `validate_b3_author_form.py`: read-only check to run on your original form after your own decisions.

## What to enter in author form

1. For the 36 `APPROVE_CANDIDATE__REGISTER_ONLY` rows: after examining the selection and frozen metadata, enter `APPROVE` in Pilot_Inclusion_Decision if you accept this *selection*. The comments already explain that source verification and 45-field coding are pending.
2. For P00584: **leave decision blank** while resolving DOI/title/year mismatch. Do not silently change frozen Phase A.
3. For P01112: **leave decision blank** while checking the singleton ANN/neuro-fuzzy family, which is atypical for the CNN-hybrid title.
4. For P00853: verify the one-primary-family tie-break on a multi-algorithm ensemble, then decide. Its publisher record supports an ensemble of ML algorithms including LSTM.
5. For P03446: verify the working-paper publication type and the review's eligibility of equity-volatility research; avoid treating SSRN content as peer-reviewed journal output.
6. In Reviewer_Name, enter your own actual name. In Review_Date_YYYY_MM_DD, enter the actual review date. Do not backdate or fabricate a signature.
7. If an issue is confirmed, record it in a change/adjudication log and revise the pilot under the approved sampling policy. Do not replace a rare-family study informally.

These flags concern whether the original Phase A metadata reliably supports the pilot strata. **There is no finding that any of the four papers is scientifically worthless or should automatically be excluded.**

## Selected external source verification

- P00584: https://ijrpr.com/uploads/V7ISSUE6/IJRPR66600.pdf (registered DOI associated with June 2026 title `From SMA to LSTM: ...`).
- P01112: https://eurekamag.com/research/104/038/104038454.php (title/DOI match, CNN-hybrid framing; complete method still requires primary paper).
- P00853: https://pure.southwales.ac.uk/en/publications/quantifying-market-signals-an-ensemble-iot-driven-approach-to-sto/ (seven-model ensemble).
- P03446: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3996169 (SSRN working paper, stock realized-volatility forecast).

**Source notes:** External checks are targeted, not a 40-paper publisher validation. The frozen workbook is immutable; author approval of pilot selection must remain independent of automatic recommendations.
