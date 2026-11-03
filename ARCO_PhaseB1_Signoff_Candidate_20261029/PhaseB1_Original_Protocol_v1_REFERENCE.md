# ARCO Revision-I — Phase B1 Methodological Evidence-Coding Protocol (Draft v1.0)

**Prepared:** 2026-10-29  
**Status:** B1 protocol drafted; requires author ratification before B2. No sources have been newly coded.  
**Frozen source:** `Supplementary_Data_S1_485_FROZEN(9).xlsx`, worksheet `Technical_Register_485`  
**SHA-256:** `95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5`  
**Dataset:** 485 study rows, 51 frozen columns; 485 unique Paper_IDs. Full_Text=375; Abstract_Only=85; Metadata_Only=25.  
**Historical bibliometric denominators:** 5,022 indexed rows; 4,975 application-area; 4,972 geocodable; 4,610 complete-year thematic. These are out of scope for Phase B recoding.

## A. Intent and jurisdiction

Phase B1 defines an evidence **reporting and verification audit**, not a retrospective claim to observe how studies were actually implemented. No original Phase A value may be overwritten. The first source-linked study-level recoding begins only after B1 approval (B2 establishes the working register; B3 pilot selection; B4 pilot verification; B5 full coding). Phase C, not B1 or B5, owns independent second-coder reliability and chance-corrected agreement. The author-approved 485-study eligibility set is invariant unless a separately authorized amendment is recorded.

The coding dictionary contains **45 item-level fields** across eight methodological domains: Temporal validation (7), Preprocessing and leakage (11), Baselines and ablations (5), Statistical inference (4), Economic utility (5), Robustness and generalization (4), Explainability and uncertainty (4), Reproducibility (5). Two priority tiers: **CORE** (27) and **EXTENDED** (18). Each coding question, YES/negative threshold, NA rule, relevant Phase A mapping and ambiguity caution are specified verbatim in the accompanying CSV/XLSX.

## B. Outcome states and guardrails

- `YES`: explicit affirmative evidence meets that field's operational threshold. The paper reports or demonstrably implements the practice; quote and page/section are mandatory.
- `EXPLICIT_NO`: direct negative evidence from authors or fully inspected executable implementation establishes non-use. **No mention ≠ explicit no.** An uninspected codebase cannot establish this state.
- `NOT_REPORTED`: the accessible full text and relevant supplementary materials were systematically searched, but no determining statement was located. Must cite **search log**, inspected source versions, searches and sections. This is a reporting state, not a negative methodological conclusion.
- `INSUFFICIENT_ACCESS`: only abstract, metadata, paywalled excerpt, invalid link, or incomplete material is available for the field. Positive evidence may nevertheless be verified from these sources if explicit. This is not interchangeable with NOT_REPORTED.
- `AMBIGUOUS`: relevant passages conflict or lack specificity, e.g. 'fivefold cross-validation' with no indication of whether folds were shuffled. Record both positive/negative passages and request adjudication.
- `NOT_APPLICABLE`: the question logically does not apply, with field-specific reason and explicit supporting study context. An empty results table or missing details does **not** by itself establish inapplicability.
- `NOT_ASSESSED`: temporary workflow state only; never a final analysis code. Blank proposed value means not assessed, not unclear.

**Risk-exception:** `PL11` uses the categorical values `HIGH`, `LOW`, `INDETERMINATE`, `CONFLICTED`, `NOT_APPLICABLE` instead of the above yes/no states. `HIGH` requires a specific verified material leakage mechanism. `LOW` requires positive coverage of all material applicable pipeline boundaries; absence of detected signals alone never justifies it. A mixed multi-experiment study is summarized only after experiment-specific evaluations are retained.

**Confidence, separate from outcome:** HIGH (primary text/code unambiguous, source identity verified); MODERATE (clear passage but limited procedural detail); LOW (source narrow, tentative evidence or indirect implication). LOW confidence YES must be flagged for review, not automatically accepted. A blank confidence is mandatory when not assessed.

## C. Source hierarchy and precedence

Hierarchy is **claim-specific** rather than a simplistic ranking of file types. For published methodology descriptions: (1) version-of-record text **as corrected by formal corrigenda/retractions**, (2) contemporaneous official supplements, (3) versioned article-linked repository/config/data dictionary, (4) accepted manuscript and identifiable preprint, (5) abstract, (6) publisher bibliographic metadata. Author correspondence may clarify but is dated and logged, never silently substituted. For what an implementation actually did, verifiable, time-appropriate code can rebut a textual claim, but differences MUST be retained as a conflict rather than silently adjudicated by source type. AI summaries, search snippets and citations to other studies are discovery aids, **never sufficient methodological evidence**.

Each document gets `Source_ID`, title/version, DOI/URL/local file URI, SHA-256 (for acquired files), publication/update date when known, access date, evidence scope and relation to Paper_ID. Page labels preserve both printed page and PDF page where they differ. A code assertion records repository commit/file path/line range. Do not invent any unavailable page or quote.

Recommended source search order: publisher version/corrigenda -> article supplementary methods/tables -> verified repository README/config and data snapshot -> accepted manuscript -> institutional abstract -> bibliographic metadata. A missing source prompts retrieval rather than a default negative code. For abstract-only/metadata-only, code YES or EXPLICIT_NO only if direct, field-specific affirmative/negative evidence exists; otherwise assign INSUFFICIENT_ACCESS, and record attempted retrieval.

## D. Unit of observation and multi-experiment aggregation

`Paper_ID` is immutable study identity; `Experiment_ID` names each materially different experiment where needed. An experiment changes when test dates, asset cohort, forecast horizon, label, split, or experimental pipeline materially differ. Extract all materially relevant configurations, and designate a **primary reported forecasting experiment** using prespecified order: article-identified headline test > principal results table > first complete evaluation. Do not choose experiment with best score. Retain supplemental experiments to flag `MIXED`. For paper-level positive practice prevalence, report `ANY_YES` and `PRIMARY_YES` separately in sensitivity analyses; neither can be silently substituted for the other. Leakage risk is determined at experiment level before study aggregation; any verified high-risk experiment contributing to headline claims is a `HIGH` candidate with experiment details.

## E. Negative-search audit

Before `NOT_REPORTED` in an accessible full-text paper, document at least: accessible manuscript and supplements; exact or representative search terms; inspected methodological sections, equations, tables and appendices; repository/source availability; the field-specific search decision. Text searching is a locator, not a substitute for reading. A genuine direct statement is required for EXPLICIT_NO. For inaccessible documents, classify INSUFFICIENT_ACCESS, even after search attempts; do not presume no method existed.

## F. Domain-specific interpretation pitfalls

1. **TV01/TV02/TV03:** a stated 80:20 split does not establish time order, untouched test, or independence. The frozen `Chronological_Split=Yes` and `Validation_Status=Temporally ordered` measure distinct things and must not be forced into agreement.
2. **TV04 vs PL04:** a rolling input lookback is not rolling-origin validation. End-to-end training boundary evidence cannot be inferred from a named transform.
3. **PL09 vs PL11:** a verified mechanism is necessary to say High, but absence of identified leakage is not evidence of Low. Risk must be supported, not constructed circularly from frozen Phase A labels.
4. **ST01/ST02/ST03:** existence of p-values does not imply serial-dependence-aware inference or corrected multiplicity.
5. **EC01/EC02/EC03:** empirical forecasting accuracy, simulated trading, and net-of-cost financial utility are different constructs.
6. **RB01/RB02:** mention of volatility, COVID-19 or crisis events does not by itself establish a separately evaluated robustness stratum.
7. **EX01/EX02:** an attention layer or post hoc visual is not proof of explanatory fidelity.
8. **RP01/RP02:** a bare GitHub link or generic data-provider citation is not a verified working reproducibility artifact.

## G. Phase B2 schema contract (DESIGN ONLY; not created or populated during B1)

A. `B2_study_index`: Paper_ID, immutable metadata, exact Phase A source SHA, full-text scope, accession/version.  
B. `B2_field_decisions`: Paper_ID, optional Experiment_ID, Field_ID, PhaseA_Exact_Column, PhaseA_Original_Value, PhaseB_Proposed_Value, workflow status, explanation, source assertion IDs, confidence, primary coder, coding date, codebook version.  
C. `B2_evidence_assertions`: Assertion_ID, Paper_ID, Experiment_ID, Field_ID, Source_ID, evidence role (support/refute/context), exact short quotation, page label, PDF page, section, table/figure or code lines, extract date, source SHA.  
D. `B2_source_registry`: Source_ID, Paper_ID, source type, version, publisher DOI/URL, local accession, checksum, date retrieved, evidence scope, source conflicts.  
E. `B2_negative_search_log`: Paper_ID, Field_ID, Source_ID, terms searched, methods/results/appendices checked, outcome, retrieval limitations, assessor/time.  
F. `B2_change_manifest`: Paper_ID, Experiment_ID, Field_ID, original Phase A value, proposed Phase B value, reason, evidence assertions, proposed status, adjudicator and decision/date (blank until performed).  
G. `B2_unresolved`: unresolved item, conflicting evidence, needed source, assigned owner, state, next action.  
H. `B2_protocol_amendments`: semver, before/after rule, reason, impacted IDs, author approval and date.

**Validation constraints:** no new Paper_ID, no duplicates in `(Paper_ID, Experiment_ID, Field_ID, coding_version)`; positive/explicit negative verdict requires at least one specific source assertion; NOT_REPORTED requires completed negative-search log; scope-constrained classifications must be valid; every departure from original Phase A codes must have an explicit change explanation; Phase C adjudicated values remain a separate future data layer. Any figures/tables arising from B6 must be deferred from the manuscript until Phase C reliability is complete.

## H. B3 stratified pilot plan (DESIGN ONLY)

**40 studies**: 30 Full_Text, 6 Abstract_Only and 4 Metadata_Only. Full-text quotas spanning all 11 method families where full text actually exists:

| Full-text method family | Pilot quota | Available Full_Text |
|---|---:|---:|
| Deep-learning models | 7 | 88 |
| Hybrid deep-learning models | 6 | 80 |
| Sentiment/NLP-driven models | 4 | 57 |
| Transformer/attention-based models | 4 | 57 |
| Metaheuristic-optimized models | 3 | 37 |
| Ensemble/tree-based machine learning | 1 | 28 |
| Graph-based models | 1 | 14 |
| Multimodal-fusion models | 1 | 10 |
| Other/unclear | 1 | 2 |
| ANN/neuro-fuzzy models | 1 | 1 |
| Statistical/econometric models | 1 | 1 |

Within these quotas, balance historical periods (aim for at least eight pre-2025 papers where feasible), original Phase A high/low/unclear leakage codes, and current validation types; oversample some disputed and high-leakage cases without changing denominator representation. The abstract-only and metadata-only calibration cases test missingness handling rather than evidence verification from non-existent full texts. Selection in B3 must use a documented deterministic random seed and ID-level audit; **no pilot IDs have been selected in B1**. Pilot success criteria: comprehensible rules and acceptable exception handling; every affirmative/negative extraction traceable to an identified source; all NOT_REPORTED decisions supported by search log; all conflicts queued; a complete author-reviewed decision on codebook changes. Independent duplicate-coder reliability is reserved for Phase C.

## I. Nonnegotiable completion gates

- B1: author approves codebook, eligibility/scope policy, exception rules, source hierarchy, schemas, and pilot quotas; a protocol version is frozen.
- B2: source checksum/485 IDs verified; mapping created without any source edits; coding cells blank and originals preserved.
- B3/B4: stratified IDs and evidence-retrieval trail recorded; pilot coded and exceptions reviewed.
- B5/B6: all 375 full-text records accounted for by field; abstract and metadata scopes explicitly partitioned; unresolved/insufficient sources tallied; changes supported by passages; re-reconciliation computed from Phase B files.
- Phase C: independent second coding plus chance-corrected agreement, then final adjudication, then and only then manuscript count updates.

## J. Reference guidance (supporting, not mechanically imported)

- PRISMA 2020 reporting statement: https://www.prisma-statement.org/prisma-2020
- Cochrane Handbook, Chapter 5, collecting data: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05
- TRIPOD+AI BMJ 2024 (clinical prediction reporting, conceptually informative, not a finance-specific risk-of-bias tool): https://www.bmj.com/content/385/bmj-2023-078378

This ARCO codebook is **bespoke to stock-market forecasting**. It is not claimed to be an officially validated PRISMA, Cochrane or TRIPOD risk-of-bias instrument, nor does it constitute independent coding reliability evidence.
