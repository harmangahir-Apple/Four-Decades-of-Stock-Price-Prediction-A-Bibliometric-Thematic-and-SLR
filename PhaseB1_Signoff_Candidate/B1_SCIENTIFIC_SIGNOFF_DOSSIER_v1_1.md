# ARCO Revision-I — Phase B1 Scientific Sign-off Candidate (v1.1)

**Status: SCIENTIFICALLY REVIEWED SIGN-OFF CANDIDATE — NOT YET AUTHOR-RATIFIED.**
**Date prepared:** 2026-10-29. **Corpus:** immutable `Supplementary_Data_S1_485_FROZEN(9).xlsx`, SHA-256 `95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5`.

## Decision sought

Approve the unchanged 45-field architecture (27 CORE, 18 EXTENDED) with the 12 field-specific clarifications logged separately in `B1_Proposed_Rule_Amendments_v1_to_v1_1.csv`. These are prospective B1 protocol refinements, **not retrospective amendments to Phase A empirical classifications**. Approval requires explicitly completing the 11 gates in `B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv`, not merely running a script.

## Scientific conventions now locked for ratification

1. **Audit estimand**: observable study-level reporting/evidence and independently verified procedural details, *not actual methodological quality inferred from silence*. Maintain separate statistical descriptions of YES, EXPLICIT_NO, NOT_REPORTED, INSUFFICIENT_ACCESS, AMBIGUOUS and NA. No unassessed rows in completed studies.
2. **Paper and experiment units**: one immutable `Paper_ID` per study; a separate `Experiment_ID` for materially distinct train/test dates, horizons, assets or pipelines. Collect passage-level data before paper-level synthesis. Primary experiment is article-declared main evaluation or predesignated principal table, never the best-performing outcome. A single leaky supporting experiment must not silently condemn all otherwise protected experiments; headline-claim dependence must be recorded. Any-YES and primary-YES summaries are separate sensitivity analyses.
3. **Evidence grading**: affirmative and negative claims require identifiable original source, exact quotation/line of code and page/section/path; the source must be independently accessible or archived, with SHA-256 where local. For PDF citations use both printed and PDF page indices when different. No filling missing quotations or page numbers by inference.
4. **Outcome-state logic**: `NOT_REPORTED` requires full-text plus available supplement and a logged search. `INSUFFICIENT_ACCESS` follows abstract-/metadata-limited evidence or unretrievable critical documentation. `AMBIGUOUS` captures unresolved or conflicting positive/negative details. `NOT_APPLICABLE` needs a positive reason, never merely no mention. `EXPLICIT_NO` needs a direct negation or genuinely comprehensive audited source that establishes non-use.
5. **Overall leakage**: PL11 is a distinct ordinal judgment. HIGH requires an identified material leakage mechanism in the evaluated protocol. LOW requires verified safe boundaries across **all materially applicable** paths; lack of a discovered signal alone implies INDETERMINATE. CONFLICTED documents source disagreements; if mixed primary vs supporting experiments, retain experiment-level results and use precommitted study aggregation. PL09 records mechanism-specific violations or safeguards, not a global proof of risk absence.
6. **Availability versus reproducibility**: public code URL and independently verifiable executable artifact are distinct. Public dataset identity and exact data reconstruction are distinct. Codebook's YES requires source-level evidence; keep extra binary metadata flags in B2.
7. **Economic evaluations**: no trading backtest does *not* automatically make EC01 NA for an empirical financial forecast. For EC02–EC05 NA requires that the underlying trading/decision evaluation is genuinely inapplicable and evidenced. Accuracy metrics are not economic utility.
8. **Statistical inference and uncertainty**: baseline implementation, paired tests, dependence control, multiplicity and predictive uncertainty are separate. Deterministic point forecasts can be assessed for whether uncertainty was quantified; EX03 does not become NA just because uncertainty is absent.
9. **Evidence scope**: 375 Full_Text prioritized, 85 Abstract_Only and 25 Metadata_Only remain separate. A narrow source may support YES if direct, but missing methods in an abstract or metadata record normally give INSUFFICIENT_ACCESS, not a negative finding.
10. **Timing**: B2 may initialize working files only after author sign-off. B3 selects a reproducible 40-study pilot (30/6/4) with quotas in v1 and targeted coverage of earlier periods, leakage flags and method families; B4 records pilot evidence. Phase C owns independent second-coder agreement. Publication-facing counts remain Phase A figures until B and C close.

## Proposed 40-study pilot

30 Full_Text across all eleven families: Deep 7, Hybrid 6, Sentiment 4, Transformer 4, Metaheuristic 3, and one each of Ensemble, Graph, Multimodal, Other/unclear, ANN/neuro-fuzzy, Statistical/econometric. Additionally 6 Abstract_Only and 4 Metadata_Only. Select with a deterministic seed and preserve exclusions and selection rationale. Attempt >=8 pre-2025 full-text cases where supported; if constraints conflict, log deviation instead of secretly replacing cohorts. No exact Paper_ID has yet been selected.

## Additional structural issue discovered and corrected in this candidate

The B1 v1 `PhaseB1_PhaseA_Column_Mapping.csv` lists **only 34 of the 51 frozen worksheet columns**. This was not a Phase A data error; it was an incomplete documentation map. The sign-off candidate includes an expanded **51-column map**, preserving all 34 previous mappings and adding 17 explicitly marked immutable-context fields. No Phase A values have been edited. Gate G08 covers approval of this complete mapping.

## Ratification and version freeze

Review `B1_Proposed_Rule_Amendments_v1_to_v1_1.csv` beside the original v1 file, amend the sign-off candidate if needed, and require all eleven gates marked `APPROVE` with an author name, date, and explicit comments where qualifications apply. Run the accompanying gate script using `--finalize` **only** after author decisions are entered. The machine checks the source and codebook and records an *author-declared* approval; it cannot authenticate the identity or actual review of the signatory. Any substantive change afterwards must create v1.2 and a new approval.

## Scientific references for designing an extraction protocol

- PRISMA 2020: https://www.bmj.com/content/372/bmj.n160 (report reviewer counts, independent extraction status and discrepancy resolution).
- Cochrane Handbook, Chapter 5: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05 (study versus report unit, raw passages and missingness, pilot and independent checking).

**Scope qualification**: This is a bespoke computational-finance reporting/evidence audit. It is **not** a validated risk-of-bias instrument, nor proof of inter-reviewer agreement. No publication claim can be revised on the basis of this sign-off alone.
