# ARCO Revision-I — Phase B1 reviewer-response rule addendum, v1.2 (DRAFT)

**Status:** proposed scientific protocol addendum, **NOT AUTHOR-APPROVED**. Prepared 2026-10-29. Supersedes no data, original `Paper_ID`, Phase A codes, or existing signed/unsigned B1 record. Proposed for author review of G03/G11 and supporting G05–G09.

## A. Audit estimand and outcome definition (G03, G11)

- **Target:** verifiable documentation of a study's methodological procedures, plus separately verified implementation evidence. A documented omission is **not** proof that a procedure was never implemented.
- **YES:** direct source evidence supports the field-specific criterion. May be established from narrower evidence scopes only if source gives direct, unambiguous support. Store evidence scope and source.
- **EXPLICIT_NO:** direct negation or authenticated code/results that affirmatively establish non-use of a specifically defined procedure. The negative assertion is limited to the source and study component established by the evidence.
- **NOT_REPORTED:** a *full-text-supported* assessment in which the article and all available directly linked supplementary methods/code material were searched by a documented protocol, and the criterion could not be established. Record searched locations, retrieval date, query terms or sections, evidence scope, and any unavailable supplements. **This is documentary non-reporting, not confirmed procedural non-use.** If a critical referenced supplement is unavailable, consider INSUFFICIENT_ACCESS rather than NOT_REPORTED.
- **INSUFFICIENT_ACCESS:** abstract-only, metadata-only, unlocatable required source, or otherwise inaccessible key material precludes an adequate assessment. A limited-access study may nonetheless receive YES/EXPLICIT_NO when a direct source-specific statement satisfies the threshold.
- **AMBIGUOUS:** pertinent accessible evidence is underspecified, internally conflicting, or source/version-discordant. Record conflicting passages and adjudication need.
- **NOT_APPLICABLE:** positive task-level evidence establishes that the defined item does not apply; lack of documentation never suffices. Field-specific criteria remain authoritative.
- **NOT_ASSESSED:** temporary workflow state, **not** a reportable evidence outcome.
- For overall leakage PL11 use distinct `HIGH`, `LOW`, `INDETERMINATE`, `CONFLICTED`, `NOT_APPLICABLE` statuses (not the general YES/NO table).

## B. Reviewer-facing reporting crosswalk (G03, G11)

Apply only to a field with a meaningful Yes/No/not-documented interpretation. Do not apply blindly to ordinal leakage-risk PL11 or nominal validation-design TV01.

| Internal evidence state | Four-column reporting destination | Mandatory nuance |
|---|---|---|
| YES | Yes (documented/verified) | Count only after evidence-backed Phase B decision; report scope breakdown |
| EXPLICIT_NO | No (not established/explicit non-use) | Subclass `no_subtype=EXPLICIT_NO`, preserve source and scope; do not conflate with non-reporting in the audit file |
| NOT_REPORTED | No (not documented after assessed full-text search) | Subclass `no_subtype=NOT_REPORTED`; **not proof of actual non-use** |
| INSUFFICIENT_ACCESS | Not recoverable | Some full-text cases may qualify if decisive linked material unavailable; do not assume all abstract cases lack positive evidence |
| AMBIGUOUS | Unclear | Conflicting or underspecified evidence, not missing source |
| NOT_APPLICABLE | Separate n(N/A), not silently assigned to No | Explain field-specific eligibility denominator; do not present 485 denominator if n(N/A) excluded |
| NOT_ASSESSED | No publication table permitted | B-phase incomplete |

Suggested four display columns for Table 10 and cognate summaries: **Yes**, **No / not documented after assessment**, **Not recoverable**, **Unclear**. Add `n(Not applicable)` explicitly as a fifth count in a note or separate column and state `n_applicable = 485 − n_NA`, while additionally reporting overall cohort n=485 and evidence-scope denominators 375/85/25. Do not falsely present this as four exhaustive categories over all 485 if any NA cases exist.

Do **not** reassign frozen Phase A Unknown/Unclear values en masse. Apply this crosswalk to **independently evidenced and adjudicated Phase B outcomes** after Phase C reliability assessment, and label the table appropriately. The proposed crosswalk addresses Reviewer 1's documentary-negative concern while preserving the difference between absent reporting and absent practice.

For code/data availability, note retrieval/check date and distinguish "no public link/source found in assessed material" from "verified code was never made public"; these claims are not interchangeable. Preserve a separate archived-link reachability flag. For transaction costs, statistical testing and economic evaluation, report what the assessed paper did or documented, not what authors intended.

## C. Multi-experiment and leakage rules (G05, G06)

1. Extract at `Paper_ID × Experiment_ID × Field_ID × Source_ID × Evidence_ID` level; study-level claims are **derived** and separately stored.
2. Determine primary evaluation from the author's declared principal experiment or predetermined main methods/results table **before viewing performance values**. Record the selection rule and fallback; if it remains unknowable, `PRIMARY_UNDETERMINED`, not the best reported outcome.
3. `HIGH` leakage risk for the study's primary reported claims requires a **verified material contamination pathway** in a primary or headline-supporting experiment, not merely a suspicious omission. Record leakage mechanism and its directional causal path to evaluation.
4. `LOW` requires documented safety of every materially applicable information path for the primary experiment: chronology, training-only transforms, target construction, text timestamps, and tuning/test isolation as applicable. Lack of evidence of leakage = `INDETERMINATE`, **not LOW**.
5. Retain `mixed_experiment_flag` if outcomes disagree across experiments. `CONFLICTED` is for incompatible evidence about the same claim, not for an ordinary combination of high- and low-risk experiments. Keep primary-risk and any-experiment-HIGH estimates distinct.
6. Preserve secondary experiments and negative / ambiguous findings. Do not aggregate by 'any positive' unless explicitly labelled as sensitivity analysis.

## D. Pilot versus independent reliability (G07, G09)

- **B3 calibration pilot:** 40 study IDs, 30 full text / 6 abstract / 4 metadata, with fixed random seed, prospective eligibility/stratum rules and explicit exception log. Pilot is for training/refinement of rules; do **not** use these same codings as independent confirmatory reliability evidence without documenting independence and contamination safeguards.
- All 11 method families are represented among full texts, but ANN/neuro-fuzzy and statistical/econometric each contain one full-text case; pilot draws in these singleton strata are deterministic census selections.
- **Phase C reliability:** independent blinded coding by a second eligible author from a separately reconstructed **current 485-study** previously unverified eligibility frame. Reviewer 1 proposes ~100 from the earlier unverified stratum (historically 330); re-identify exact eligible Paper_IDs after seven Phase A exclusions and account for B3 overlap before selecting. Report per-field denominators and appropriate chance-corrected agreement (e.g. Cohen κ for binary nominal codes, weighted κ for ordered scales when applicable, transparent agreement and prevalence diagnostics). No κ or error-adjusted intervals until real independent decisions exist.
- Any Phase C risk-adjusted confidence intervals must reflect the actual sampling frame and designs, rather than importing the historic 7.5% disagreement estimate as a universal misclassification rate.

## E. Evidence provenance and publication gates (G04, G08, G10)

- Each YES, EXPLICIT_NO, HIGH, LOW, or proposed substantive change must have a source location (PDF index, printed page if different, section, stable URL/DOI, source hash or code commit) and a literal verified passage / source line or documented code. An absent passage is not to be invented.
- NOT_REPORTED requires a time-stamped search-log record for the full-text and linked accessible materials; record source access failures separately. Chat handovers provide historical leads only.
- B2 must copy immutable Phase A Paper_ID and original 51-column map with frozen values unchanged; coding assignments and adjudications go to separately versioned working files.
- Main manuscript, tables, figures and abstract **stay at Phase A numbers** until Phase B evidence verification plus Phase C reliability are complete. Historical 493/494 and 4,974 snapshots are provenance, not current analysis denominators.
- Addendum ratification must receive genuine author consent, recorded date and source hashes. Do **not** edit the existing `B1_File_Hash_Manifest.json` or the original v1.1 sign-off folder in place; make a new versioned package before technical finalization.

## F. Acceptance test for v1.2

Before approving G03 and G11, perform a **documented 12-case code-state calibration** including: full-text YES; full-text explicit NO; full-text NOT_REPORTED with search log; full-text AMBIGUOUS; full-text with missing cited appendix; abstract-only positive; abstract-only missing detail; metadata-only missing detail; an inapplicable case with explicit task reason; mixed-experiment leakage; code-repository link inaccessible at check date; and a nominal/ordinal aggregation case. Real cited examples should be used when available; synthetic examples test logic only, never count as study verification. Check that all 485 records could be accounted for by an eventual reporting table without hidden NA or UNASSESSED values.

**Gate decision:** G03 and G11 remain HOLD until this addendum is reviewed, versioned and approved by an actual author. All gates remain pending actual author ratification.




## G03/G11 — Proposed Scientific Resolution

**Decision proposed:** Accept the Phase B1 v1.2 evidence-state crosswalk with the following clarification.

1. The six substantive evidence states (`YES`, `EXPLICIT_NO`, `NOT_REPORTED`, `INSUFFICIENT_ACCESS`, `AMBIGUOUS`, and `NOT_APPLICABLE`) shall remain independently identifiable in the Phase B evidence register.

2. For reviewer-facing reporting, `EXPLICIT_NO` and `NOT_REPORTED` may be aggregated under a clearly defined **No / not documented after assessment** category, provided their separate counts remain recoverable and are disclosed in the supplementary analysis.

3. The `NOT_REPORTED` classification shall be assigned only after documented examination of the accessible full text and relevant supporting materials. It shall not imply proven non-performance of the methodological procedure.

4. `INSUFFICIENT_ACCESS` shall remain distinct from full-text non-reporting. `AMBIGUOUS` shall be reserved for genuinely unclear or conflicting evidence.

5. `NOT_APPLICABLE` cases shall be separately reported with the appropriate denominator. `NOT_ASSESSED` records shall prevent publication of the corresponding incomplete Phase B table.

6. Phase A values and the frozen 485-study register shall remain unchanged. Updated manuscript counts shall be introduced only following Phase B evidence verification and Phase C independent reliability assessment.

**Scientific rationale:** This approach addresses Reviewer 1's concern about the inability of the original audit to distinguish assessed non-reporting from unrecoverable evidence while avoiding unsupported conclusions about actual methodological non-use.

**Approval status:** Proposed for author review; subject to the required 12-case coding-state calibration and formal protocol ratification.