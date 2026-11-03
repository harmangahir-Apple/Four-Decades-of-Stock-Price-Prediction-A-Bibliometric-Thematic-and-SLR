# ARCO Phase B1: scientific review of G01–G11, 29 October 2026

## Verification performed

Technical gate via existing B1 `phaseB1_signoff_gate.py`: **PASS** against the supplied frozen workbook (485 studies; 51 fields; 375 full text, 85 abstract only, 25 metadata only). No author decisions supplied.

## Reviewer-informed recommended treatment

| Gate | Recommended author-review disposition | Reviewer-facing significance |
|---|---|---|
| G01 | Technically verified; author can consider approval | Current 485-study source supersedes historical 493/494 handovers. |
| G02 | Review and refine if needed | R1 requested baseline type, XAI, uncertainty quantification; 45-field codebook includes them, but study-level counts are not yet produced. |
| G03 | **Hold pending explicit methodological reporting crosswalk** | R1 sees original Yes/No/Unclear design as non-discriminating. Distinguish “no documentation after exhaustive full-text search” from explicit non-use and inaccessible evidence. |
| G04 | Protocol may be approved; extraction is pending | Reviewer 2 demands reproducible searches; S2 documents query expressions, but B2/B4 evidence quotes and original-PDF access require actual source verification. |
| G05 | Review experiment-level leakage aggregation | Low leakage risk must require affirmative safeguards, and high risk should not be derived from design proxies alone. |
| G06 | Review experiment-selection hierarchy | Distinguish primary evaluation from supporting experiments, avoid post-hoc selecting the best outcomes. |
| G07 | Approve only as a **pilot design**, not completed audit | 40-case pilot (30 full text, 6 abstract, 4 metadata) does not substitute for reviewer-requested ~100 previously-unverified independent checks. |
| G08 | Schema approval possible; B2 implementation pending | 51-column source mapping and no-overwrite contract; add source-level evidence log and change ledger. |
| G09 | Approve phase boundary, **not reliability achieved** | Historical 37/40 correction audit is not Cohen's κ; second reviewer and independent coding planned for Phase C. |
| G10 | Protocol approval possible | Do not update manuscript figures/counts until Phase B verification + C reliability. Historic 4,974 application-area number is obsolete; current frozen is 4,975. |
| G11 | **Hold with G03** | Never convert not reported to actual not performed; permit defensible reporting negatives from fully audited texts, with precise manuscript table labeling. |

## High-priority reviewer conflict

Reviewer 1 explicitly requests a four-column Table 10: **Yes, No (full text read, practice not present), Not recoverable (abstract or metadata only), Unclear (ambiguous full text)**. The draft B1 state model instead uses YES, EXPLICIT_NO, NOT_REPORTED, INSUFFICIENT_ACCESS, AMBIGUOUS and NOT_APPLICABLE. These should not be naively conflated.

Recommended solution: retain the granular extraction states, then explicitly document an independently defined reporting table:

1. Affirmatively documented;
2. Not documented after complete full-text + available supplement check (record separate explicit non-use counts);
3. Not recoverable due to evidence-scope limitations;
4. Genuinely ambiguous or conflicting;
5. Not applicable reported separately or excluded per specified field denominator.

This can satisfy the purpose of the reviewer's request while avoiding false methodological-negative claims. **The reporting crosswalk requires author approval and should be incorporated in a versioned B1 revision before G03/G11 sign-off**. It does not yet change published counts.

## Present manuscript/supplement status

- Latest manuscript, PDF p. 41: Table 10 still has Yes, No, Unclear columns.
- Latest supplement, PDF p. 38: Table S18 already reports family-level methodological profiles derived from Phase A. Main manuscript Section 7 references S18, but the reviewer requested family-by-dimension numbers directly in main text. That is a manuscript integration decision for after B/C, not evidence Phase B codes exist.
- Latest supplement, PDF p. 27: S15 describes historical 40-study verification; it does not establish inter-reviewer chance-corrected agreement.
- Latest supplement, PDF p. 42: explicitly recognizes absence of formal inter-reviewer κ.
- Reviewer 2: database queries are now printed in Supplement S2 (pp. 8–12), but public repository accessibility remains a separate current verification task.

## No automated author approval

Even if every link and keyword check passes, the script never writes `APPROVE` or `REJECT`. The human author must review the scientific judgments and the primary evidence before signing.
