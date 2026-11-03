# ARCO Phase B1 — Reviewer-informed scientific sign-off review

**Output type:** evidence-assisted recommendations, NOT author ratification.

**Audit UTC:** 2026-10-29T08:40:39.598395+00:00

**Frozen technical gate:** PASS.

**Evidence discipline:** current manuscript and supplementary take precedence for present claims; reviewer documents are reviewer demands; historical handovers are provenance only and may contain stale counts.

**Automatic gate approval:** prohibited. No source or approval form was edited.

## Executive findings

1. Reviewer 1 requests a more informative full-text documentary absence classification. G03/G11 must define a response-compatible crosswalk without asserting actual non-use.
2. The current main Table 10 remains a Yes/No/Unclear table; the new Phase B reporting design is not yet applied.
3. Supplement S18 already provides historical method-family audit marginal counts; B1 fields are not verified recoding results.
4. Reviewer 1 calls for independent checks including a sample of approximately 100 previously unverified records. The 40-study B3 pilot serves a different purpose. Phase C is pending.
5. Older handover files describe superseded corpus sizes; do not let them change the frozen Phase A workbook.

## Gate-by-gate review

### G01: Corpus integrity and immutable Phase A freeze
**Proposed disposition:** `TECHNICAL_PASS_CONDITIONAL_AUTHOR_REVIEW` (not an author decision).
**Critical check:** Ensure historical handovers (493/494/4,974) do not overwrite the current 485/4,975 freeze. Require exact workbook checksum and unique-ID audit.
**Reviewer matches:** R1=2, R2=1; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 5 — “…statement, and no code section, that is evidence of no public code. Coding 485 studies (98.6%) as unclear on code availability treats a checkable fact as unknowable. The same applies to transaction costs, statistical testing, and economic evalua…”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 7 — “… and Unclear on genuinely ambiguous full-text cases. For the 379 full-text records this is a recoding of evidence already extracted, not new work. I expect it to move a large share of the Unclear mass into hard negatives and strengthen the paper…”
- reviewer2: `Reviewer-2 Comments(2).docx`, DOCX paragraph 3 — “…n addition, the authors must explain more precisely how the 1,059 eligible records were reduced to 494 supporting studies—whether each record was screened individually and on what basis irrelevant ones were excluded—and although Section 2.5 desc…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…e-year thematic evolution. Separately, a purposively prioritized subset of 485 studies published during 2016– 2026 was retained for detailed technical synthesis and methodological audit after seven author-approved exclusions from the canonical 4…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 4 — “…rds retained at least one usable source keyword. A high-priority subset of 485 studies was retained for detailed technical synthesis. The novelty of the study lies in connecting four complementary analytical levels: 1. bibliometric performance a…”

### G02: 45-field codebook, evidence thresholds and all reviewer audit domains
**Proposed disposition:** `REVIEW_THRESHOLDS_BEFORE_APPROVAL` (not an author decision).
**Critical check:** Check field definitions for baselines, XAI, prediction uncertainty and experimental controls. A field existing in the codebook is not evidence that papers were recoded.
**Reviewer matches:** R1=2, R2=1; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 3 — “…model, regime-specific evaluation, shock context, shock-period evaluation, economic evaluation, transaction costs, formal statistical testing, and code availability. Only chronological split (5) and data availability (2) record any negatives at ”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 4 — “…cit negative evidence was recoverable." No author writes that they omitted statistical tests. The No category is therefore unreachable by construction, the scheme collapses to Yes and Unclear, and Unclear absorbs two states that need separating:…”
- reviewer2: `Reviewer-2 Comments(2).docx`, DOCX paragraph 3 — “…ction in the accompanying files linked on GitHub, which further limits the reproducibility of the screening and analysis process.”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…time information, temporal validation, training-only preprocessing, strong baselines, uncertainty quantification, regime and shock testing, net-of-cost evaluation, and reproducible experimentation. 1 Introduction 1.1 Background and motivation St…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 3 — “…e to noise, and apparent improve- ments may result from data leakage, weak baselines, inappropriate validation, or the persistence of price levels rather than genuine forecasting ability. These characteristics make stock-market prediction an imp…”

### G03: Evidence outcomes and missingness
**Proposed disposition:** `AMEND_OR_DOCUMENT_REVIEWER_CROSSWALK` (not an author decision).
**Critical check:** CRITICAL: Reviewer 1 requests a visible full-text-assessed-not-documented category. Distinguish observable documentary non-reporting from explicit non-use of a method. Agree reporting aggregation before G03 approval.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 2 — “Major 1. The audit coding scheme cannot produce a negative finding”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 3 — “In Table 10, the No column reads 0 for nine of eleven dimensions: non-stationarity acknowledged, regime-aware model, regime-specific evaluation, shock context, shock-period evaluation, economic evaluat…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 37 — “…tion, or repository statement provided sufficient supporting evi- dence. A negative classification was assigned only when explicit negative evidence 37”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 41 — “Table 10 Evidence-supported methodological practices in the frozen n = 485 technical synthesis. Methodological dimension Yes, n (%) No, n (%) Unclear, n (%) Non-stationarity acknowledged 75 (15.5%) 0 (0.0%) 410 (84.5%…”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 6 — “… Technical-synthesis studies supported by acces- sible full-text evidence. Abstract-only evi- 85 Technical-synthesis studies for which coding dence was limited to the abstract and available bibli- ographic information. Metadata-only evi- 25 Tech…”

### G04: Source precedence, provenance, negative search log
**Proposed disposition:** `APPROVE_ONLY_IF_PROVENANCE_REQUIREMENTS_ACCEPTED` (not an author decision).
**Critical check:** The review PDFs are secondary evidence for B1 design; actual full texts, archived pages, PDF page indices, URL checks and negative-search logs are still required for B4/B5.
**Reviewer matches:** R1=2, R2=1; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 4 — “…n 5.5: "A negative classification was assigned only when explicit negative evidence was recoverable." No author writes that they omitted statistical tests. The No category is therefore unreachable by construction, the scheme collapses to Yes and…”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 5 — “… to establish. For several dimensions, absence is directly observable in a full text. If you read a complete paper and find no repository link, no data statement, and no code section, that is evidence of no public code. Coding 485 studies (98.6%…”
- reviewer2: `Reviewer-2 Comments(2).docx`, DOCX paragraph 3 — “…t from credible and up-to-date references; and the numbers reported in the supplementary tables as well as the supplementary sections must be explicitly inserted and precisely cited in the main text, since without accurate cross-referencing a ri…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…s, graph models, multimodal systems, and explainable forecasting. However, evidence remains difficult to compare because studies differ in targets, horizons, markets, input modalities, validation proce- dures, and evaluation criteria. This revie…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 3 — “…improve- ments may result from data leakage, weak baselines, inappropriate validation, or the persistence of price levels rather than genuine forecasting ability. These characteristics make stock-market prediction an important testbed for comput…”

### G05: Leakage-risk rules and experiment-specific aggregation
**Proposed disposition:** `REVIEW_AGGREGATION_AND_LOW_RISK_CRITERIA` (not an author decision).
**Critical check:** LOW must require affirmative protection of applicable pathways; mixed primary/supporting experiments need a predeclared policy. Verify historical leakage signals only from authentic study-level evidence.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 5 — “…in both directions. It makes the numbers hard to read, since 92.1% unclear leakage risk is consistent with anything from no leakage to widespread leakage. It also understates the problem the paper is trying to establish. For several dimensions, …”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 13 — “…milies at once, and so does a GA-tuned LSTM. No priority rule resolves the overlap. The collision is large: sentiment/NLP (80) and transformer/attention (68) together cover 148 studies, and the paper's own co-citation network surfaces BERT and F…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…n was not recoverable in 65.4% of studies, validation design in 82.1%, and preprocessing boundary in 92.2%. Economic eval- uation was established in 7.6%, formal statistical testing in 9.9%, and public code availability in 1.4%. These percentage…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 3 — “…signal relative to noise, and apparent improve- ments may result from data leakage, weak baselines, inappropriate validation, or the persistence of price levels rather than genuine forecasting ability. These characteristics make stock-market pre…”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 2 — “…h representative recent reviews . . . . . 22 S8.2 Technical extraction and methodological audit . . . . . 25 S8.3 Coding verification and adjudication . . . . . . . . . . . 27 S9 Extended bibliometric rankings and diagnostics 28 S10 Extended met…”

### G06: Multi-experiment to study-level summary
**Proposed disposition:** `APPROVE_ONLY_AFTER_PREDEFINING_EXPERIMENT_POLICY` (not an author decision).
**Critical check:** Require an experiment selection plan before viewing performance; report primary-vs-any-positive sensitivity and preserve conflicts. A paper-level YES cannot automatically represent all experiments.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 4 — “That pattern follows from the stated rule in Section 5.5: "A negative classification was assigned only when explicit negative evidence was recoverable." No author writes that they omitted statistical tests. The No category is therefore unreachab…”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 8 — “Major 2. Four classification steps run on rules that are unstated or contradicted”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…liometric performance analysis, science mapping, thematic evolution, and a study-level methodologi- cal audit. Records from Scopus, Web of Science, and IEEE Xplore were merged and deduplicated, yielding 5,022 publications spanning 1987–2026. The…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 3 — “…e computational challenge therefore extends beyond model fitting. Reliable experimentation requires temporally valid splitting, training-only preprocessing, appropriate benchmark models, leakage-free feature construction, uncertainty estima- tio…”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 1 — “…thods, Search Strategies, Extended Results, Verification, Limitations, and Method-Family Synthesis for Four Decades of Stock Price Prediction: A Bibliometric, Thematic, and Systematic Review of Computational Intelligence Approaches Harmanjeet Si…”

### G07: Stratified B3 pilot and independent sampling
**Proposed disposition:** `PILOT_PROVISIONAL__PHASE_C_SAMPLE_SEPARATE` (not an author decision).
**Critical check:** Proposed 40-study B3 pilot is NOT the ~100 previously-unverified second-reviewer sample requested by Reviewer 1. Pilot IDs, eligible strata, seed and deviation logs remain to be generated.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 11 — “…ipt does not say who or what performed the assignment, gives no validation sample, no accuracy estimate, and no tie-breaking rule. Mutual exclusivity forces thousands of tie-breaks in a literature where sentiment-based price forecasting is commo…”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 14 — “…e audit percentages. State the application-area procedure with a validated sample and the tie-breaking rule. Either recode the 25 metadata-only records under the stated modality rule, or amend the rule to name the narrower conditions under which…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 9 — “…not selected by probability sampling and does not constitute an exhaustive sample of the 5,022-record bibliometric corpus. Of the 485 studies in the technical-synthesis subset, 375 (77.3%) were published during 2025–2026. Consequently, the study…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 10 — “…x/Biblioshiny, while Zotero supported refer- ence management and duplicate verification. Elicit and SciSpace supported evidence recovery, and generative-AI tools supported language refinement, code checking, and consistency review. All assisted …”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 2 — “…upplementary Technical-Synthesis Tables 19 S8 Extended review protocol and coding verification 21 S8.1 Comparison with representative recent reviews . . . . . 22 S8.2 Technical extraction and methodological audit . . . . . 25 S8.3 Coding verific…”

### G08: B2 schema, source-to-ID mappings, audit and change tracking
**Proposed disposition:** `TECHNICAL_SCHEMA_REVIEW_REQUIRED` (not an author decision).
**Critical check:** Confirm complete 51-column map; 45 fields with experiment-level records; new blank B2 outcomes; Paper_ID and source hashes; raw text and adjudication logs. Do not equate Table S14 description with a populated B2 register.
**Reviewer matches:** R1=2, R2=1; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 3 — “…atistical testing, and code availability. Only chronological split (5) and data availability (2) record any negatives at all.”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 5 — “… a full text. If you read a complete paper and find no repository link, no data statement, and no code section, that is evidence of no public code. Coding 485 studies (98.6%) as unclear on code availability treats a checkable fact as unknowable.…”
- reviewer2: `Reviewer-2 Comments(2).docx`, DOCX paragraph 3 — “…t from credible and up-to-date references; and the numbers reported in the supplementary tables as well as the supplementary sections must be explicitly inserted and precisely cited in the main text, since without accurate cross-referencing a ri…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…liometric performance analysis, science mapping, thematic evolution, and a study-level methodologi- cal audit. Records from Scopus, Web of Science, and IEEE Xplore were merged and deduplicated, yielding 5,022 publications spanning 1987–2026. The…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 4 — “… perspectives, thematic evolution, systematic technical syn- thesis, and a study-level audit of validation design, preprocessing boundaries, leakage, economic evaluation, statistical inference, and reproducibility. Among the representative recen…”

### G09: Phase C independent coding and reliability boundaries
**Proposed disposition:** `APPROVE_PHASE_C_BOUNDARY_NOT_COMPLETION` (not an author decision).
**Critical check:** The original 37/40 check is NOT Cohen kappa. Phase C needs an actual independent coding set, sampling design and dimension-wise chance-corrected agreement; do not mark reviewer request completed at B1.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 21 — “Major 4. Coding reliability is unquantified, and the manuscript supplies the numbers to bound it”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 24 — “…headline percentages by a third or more. Section 9.3 states that no second independent coding was produced and Cohen's kappa was not calculated, so the audit's precision is currently unknown. For a paper whose thesis is that the field leaves its…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 6 — “…u- ation metrics are commonly used? RQ7. What are the major methodological limitations, reproducibility issues, research gaps, and future directions in stock price prediction research? 2.2 Search strategy and database coverage Searches were cond…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 9 — “…s scientifically inferior. The complete extraction fields, audit criteria, verification procedure, and adjudication outcomes are reported in Supplementary Table S14 and Supplementary Table S15. Table 2 shows that the full-text-only sensitivity a…”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 2 — “…upplementary Technical-Synthesis Tables 19 S8 Extended review protocol and coding verification 21 S8.1 Comparison with representative recent reviews . . . . . 22 S8.2 Technical extraction and methodological audit . . . . . 25 S8.3 Coding verific…”

### G10: Publication freeze, revision control and denominator governance
**Proposed disposition:** `APPROVE_ONLY_WITH_EXPLICIT_VERSION_CONTROL` (not an author decision).
**Critical check:** Maintain current Phase A counts until B and C close. Historical 493/4,974 snapshots must be flagged as archival, not reconciled by silently changing current numbers.
**Reviewer matches:** R1=2, R2=1; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 1 — “Recommendation: major revision”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 7 — “…ly the same split to Table 2, Table 9, Figure 12 Panel B, and the abstract percentages.”
- reviewer2: `Reviewer-2 Comments(2).docx`, DOCX paragraph 3 — “This manuscript addresses a relevant topic; however, several major revisions are required before it can be considered for publication. The abstract needs to be rewritten to clearly present the objective, method, findings, and conclusions; the Ba…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…us, Web of Science, and IEEE Xplore were merged and deduplicated, yielding 5,022 publications spanning 1987–2026. The four- decade corpus was used for bibliometric and intellectual-structure analyses, while incomplete 2026 coverage was excluded …”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 4 — “…ssing boundaries, leakage, economic evaluation, statistical inference, and reproducibility. Among the representative recent reviews examined in Supplementary Table S13, none combined cross-database bibliometric performance analysis, multiple sci…”

### G11: Scientific scope and negative evidence safeguards
**Proposed disposition:** `AMEND_OR_DOCUMENT_REVIEWER_CROSSWALK` (not an author decision).
**Critical check:** Mandatory reviewer-response crosswalk must specify: full-text assessed-not-documented is a reporting negative, NOT verified non-performance. Limited-access cases stay not recoverable absent direct evidence.
**Reviewer matches:** R1=2, R2=0; current main=2, supplement=2.

- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 2 — “Major 1. The audit coding scheme cannot produce a negative finding”
- reviewer1: `Reviewer-1 Comments(2).docx`, DOCX paragraph 3 — “…ability. Only chronological split (5) and data availability (2) record any negatives at all.”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 2 — “…om complete-year thematic evolution. Separately, a purposively prioritized subset of 485 studies published during 2016– 2026 was retained for detailed technical synthesis and methodological audit after seven author-approved exclusions from the c…”
- manuscript: `Manuscript(20261029-083519).pdf`, PDF page 4 — “… of this review is not limited to enumerating forecasting architectures or reporting bibliometric growth. Its central computational engineer- ing contribution is the reconstruction of the complete forecasting pipeline as an information-constrain…”
- supplementary: `Supplementary(20261029-083517).pdf`, PDF page 1 — “…y Information: Methods, Search Strategies, Extended Results, Verification, Limitations, and Method-Family Synthesis for Four Decades of Stock Price Prediction: A Bibliometric, Thematic, and Systematic Review of Computational Intelligence Approac…”

## Interpretation safeguards

- Keyword/text matches are **leads**, not proof of methodological compliance or reviewer satisfaction.
- DOCX locators refer to paragraph or table row, never presumed printed page numbers.
- Reviewer comments refer to the original manuscript; they can contain superseded 493/379 values.
- This audit cannot verify original papers or recorded quotations because a complete 375-paper full-text library is not supplied.
- The working B1 author approval form remains untouched. After genuine review, fill its gates and run the original sign-off gate.
- No manuscript counts, codebook fields, or frozen 485-study classifications have been changed.
