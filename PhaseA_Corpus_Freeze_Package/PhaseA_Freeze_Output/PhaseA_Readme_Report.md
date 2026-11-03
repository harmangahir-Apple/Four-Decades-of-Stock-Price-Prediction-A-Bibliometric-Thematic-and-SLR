# Phase A — Study-register freeze and lineage audit

**Status:** ID-level technical freeze verified. Modality flags and unresolved classification content are **not** certified.

## Key counts
- Final technical synthesis: **492**, unique `Paper_ID` values, identical across Compiled coding, Compiled audit, Supplementary Data S1 (492) and final family audit.
- Evidence scope: **379 full text**, **88 abstract only**, **25 metadata only**.
- Modality-applicable: **491**, excluding only `P00814` as `Not_Applicable` in the final supplementary register.
- Excluded coding records in Compiled workbook: **P00295**.
- Legacy 493-only IDs: **P04845**.
- Two 493-row sources have different records: compiled coding only **['P00295']**, legacy supplementary only **['P04845']**.
- Old modality CSV: contains excluded **P04845**, and omits **none** from the applicable set.
- Supplement-vs-compiled comparable field disagreements: **0**, requiring individual evidence review.
- Supplement-vs-legacy retained modality flag disagreements: **8**.

## Decisions and restrictions

1. Use the 492-study set in `PhaseA_Frozen492_Study_ID_Master.csv` as the authoritative technical-synthesis ID population.
2. Use `PhaseA_Modality491_Applicable_ID_Master.csv` for input-modality denominators. It does not validate every modality positive/negative code.
3. Do not use 493-study Table 18 or the 492-labelled legacy modality CSV as final manuscript results.
4. `PhaseA_Modality491_Legacy_Flags_CANDIDATE.csv` is a corrected-ID candidate only; reconcile flagged category values against supplementary evidence and full text.
5. The record P00814 has an apparent review-type title and remains included in technical synthesis. Its scientific eligibility requires human confirmation before final freeze.
6. Do not conflate 4,974 topical studies and 5,022 deduplicated records; those layers require a separate source-record-level audit.

## Gate status

| Gate | Status | Observation |
|---|---|---|
| Final study-ID congruence | PASS | Compiled included, Compiled audit, Supplement 492 and final family audit: same 492 IDs |
| Evidence-scope counts | PASS | {'Abstract_Only': 88, 'Metadata_Only': 25, 'Full_Text': 379} |
| Different 493-row register identities | REVIEW | Compiled-only ['P00295']; legacy-only ['P04845'] |
| Legacy 493 mapping | PASS | ['P04845'] |
| Modality applicability | PASS | ['P00814'] |
| Legacy 492-labelled modality input | FAIL | Extra vs applicable ['P04845']; Missing vs applicable [] |
| Same-named modality copy | PASS | Byte-identical |
| Authoritative field congruence | PASS | 0 field-level disagreements in comparable fields |
| Modality indicator congruence | REVIEW | 8 category disagreements between supplementary register and retained legacy modality flags |
| Legacy Table 18 compatibility | FAIL | Legacy audit 493 rows; final audit 492 rows |
| Eligibility of non-original P00814 | REVIEW | P00814 title indicates state-of-the-art analysis; currently Included_High_Priority and Not_Applicable for modalities |

## Reproducibility

- Input directory: `/mnt/data`
- Output directory: `/mnt/data/PhaseA_Freeze_Output`
- Source files are never overwritten; SHA-256 hashes are in `PhaseA_File_SHA256_Manifest.csv`.
- Re-run the script whenever an included `Paper_ID`, evidence-scope flag, or final coding decision changes.
