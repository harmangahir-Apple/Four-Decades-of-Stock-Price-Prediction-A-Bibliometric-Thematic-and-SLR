# ARCO Phase B2 — Initialized but NOT coded

**Status: `B2_INITIALIZED_NOT_CODED`.** Source B1 v1.2 author ratification was checked against the **actual local receipt**. This package is an evidence-extraction workspace, not a scientific result.

## Locked inputs

- Frozen technical source: 485 studies x 51 original fields; SHA-256 `95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5`.
- B1 author receipt SHA-256 `1a007071084ddf7dc6b3539c7e572c54708fbb39e4b398b2d0bfe5cce8c9c11e`; status `B1_v1_2_AUTHOR_RATIFICATION_RECORDED__B2_INITIALIZATION_AUTHORIZED`.
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
