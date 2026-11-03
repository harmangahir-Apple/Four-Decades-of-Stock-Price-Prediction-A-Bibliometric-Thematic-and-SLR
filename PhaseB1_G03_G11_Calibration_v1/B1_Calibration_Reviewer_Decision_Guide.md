# How to decide G03 and G11 — beginner-friendly guide

**These 12 scenarios are synthetic examples, not source evidence from the 485 studies.** Do not use them for prevalence counts, real coding, or statements about original authors' practices.

**Rule:** `YES` = direct verified positive evidence; `EXPLICIT_NO` = direct verified non-use; `NOT_REPORTED` = full-text/source search completed but no affirmative documentation; `INSUFFICIENT_ACCESS` = critical sources unavailable; `AMBIGUOUS` = conflicting/underspecified; `NOT_APPLICABLE` = task-level exclusion evidenced. `NOT_ASSESSED` blocks publication.

| Test | Correct result | Why |
|---|---|---|
| CAL01 | YES | Named inferential test with actual result |
| CAL02 | EXPLICIT_NO | Authors specifically assume cost-free trades |
| CAL03 | NOT_REPORTED | Full-text search log completed, no test documented |
| CAL04 | AMBIGUOUS | Two methodological statements conflict |
| CAL05 | INSUFFICIENT_ACCESS | A critical cited appendix is missing |
| CAL06 | YES | Direct, specific evidence in accessible abstract |
| CAL07 | INSUFFICIENT_ACCESS | Abstract split percentage cannot determine chronology |
| CAL08 | INSUFFICIENT_ACCESS | Metadata lack method details |
| CAL09 | NOT_APPLICABLE | No strategy or trades to which costs apply |
| CAL10 | LOW for primary + any-experiment HIGH | Primary protected, secondary leaking; keep mixed flag |
| CAL11 | INSUFFICIENT_ACCESS for RP01 | Link mentioned but current executable artifact not verified; separate reported-link flag |
| CAL12 | CROSSWALK_PROHIBITED | PL11 risk is ordinal, not yes/no |

Reviewer-facing `No / not documented` aggregates two **separately retained** audit counts: `EXPLICIT_NO` and `NOT_REPORTED`. That display must state that documentary silence is not proof of non-performance.

A nominal or ordinal variable such as validation design (`TV01`) or leakage risk (`PL11`) MUST use its own category table. Treat `NOT_APPLICABLE` separately and change the applicable denominator; do not bury it in `No`. Never publish any table while a study is `NOT_ASSESSED` for that field.

## Reviewer action

In the review CSV, choose `ACCEPT` only if you agree the synthetic case follows these definitions. Choose `REVISE` and describe the concern otherwise. No actual author decision is pre-filled.
