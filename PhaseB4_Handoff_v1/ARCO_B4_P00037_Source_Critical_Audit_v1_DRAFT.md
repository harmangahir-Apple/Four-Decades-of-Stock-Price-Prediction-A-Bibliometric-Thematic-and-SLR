# ARCO B4 — P00037 Critical Full-Text Coding Audit (DRAFT)

**Status:** AI-assisted draft; 45/45 B1 fields assessed; **0 author-approved field decisions**. This is not a frozen or locked coding record.
**Study:** P00037 — *Building a Robust Stock Price Prediction Using LSTM and VECM*; DOI `10.3837/tiis.2026.04.003`.
**PDF:** 34 pages; SHA-256 `1022188a7721135a00042b112629f1d5039920e33d377c37c7a552fed173c3fa`.
**B1 source:** `PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv`; SHA-256 `a1d5778ee8bfcbf8ac314e6f1e70934039434bc9e7e164f0ff915141b7f5a814`.
**Interpretation:** A field-level `YES` means its **reported published evidence** meets the operative threshold; it does **not** independently establish statistical validity, executable correctness, or absence of leakage. `AMBIGUOUS` flags an unresolved boundary or unsubstantiated implementation. PL11 is an ordinal field with status `INDETERMINATE`.

## Coding counts

| Draft code | Count |
|---|---:|
| YES | 11 |
| AMBIGUOUS | 20 |
| NOT_REPORTED | 11 |
| NOT_APPLICABLE | 2 |
| INDETERMINATE | 1 |

**Total:** 45 / 45.

## Priority evidence-quality exceptions

| Severity | Issue | PDF location | B1 impact | Adjudication note |
|---|---|---|---|---|
| CRITICAL | COVID shock stress-test heldout claim conflicts with 2015–2021 training | PDF pp. 9, 29–30 | TV03, PL09, PL11, RB02 | Do not treat 2020 as verified independent crisis holdout without distinct training lineage. |
| CRITICAL | Paper calls Tables 1 and 2 experimental outcome tables, but the tables contain unrelated descriptive data | PDF pp. 18, 22, 27 | BL01, BL03, ST01, RB01, RP02 | Table 1 is Microsoft April-2015 prices; Table 2 is 1960–1963 US car sales; no per-model numeric forecast results table found. |
| HIGH | Inference described without test statistics, p-values, decision thresholds or numerical intervals | PDF pp. 28–29 | ST01, ST02, ST03, ST04 | Diebold–Mariano and paired tests claimed; no numeric test outputs verified. |
| HIGH | Economic backtest and costs claimed without reproducible trading protocol or cost assumptions | PDF pp. 23–24, 27 | EC01–EC05 | Sharpe 1.87 is reported, but no trade mapping, executed positions, quantified costs or net-of-cost numbers. |
| HIGH | Code URL accessible but end-to-end study code absent from current repository | PDF p. 31; https://github.com/DewanHabib10/Stock_market_paper | RP01, RP02 | At 2026-11-03: README names three scripts; only vecm_model.py observed. Demonstration produces synthetic data. |
| MODERATE | No explicit forecast horizon, while daily data and price/directional outputs are discussed | PDF pp. 8–9, 21 | TV05, TV06 | Forecast origin to target lead needs source evidence. |
| MODERATE | Main paper claims equity-index panel but provides unrelated Microsoft and car-sales tables | PDF pp. 8, 18, 22 | RP02 | Data provenance and result-to-cohort trace need verification. |
| MODERATE | Executive numerical claims are inconsistent in wording | PDF pp. 1, 27, 30 | BL01 | Abstract/result: 27% and 43% RMSE changes; conclusion: by a factor of 27 and factor of 43. |
| MODERATE | Source paper describes a hybrid econometric+LSTM architecture | PDF pp. 6–7, 25 | Principal_Method_Family | Proposed hybrid deep-learning classification is separate from B1 45-field coding and subject to B1-family amendment approval. |

## All 45 field-level draft decisions

| Field | Draft status | Source pages | Confidence | Reasoning summary |
|---|---|---|---|---|
| TV01 — Validation design classified | YES | 9,21,24 | HIGH | Design subtype: chronological holdout with described expanding-origin/rolling CV. TV02 and TV03 assessed separately. |
| TV02 — Chronological split | YES | 9 | HIGH | Explicit time-ordered calendar periods satisfy TV02; the claimed COVID-2020 unseen stress test is assessed separately. |
| TV03 — Untouched final test | AMBIGUOUS | 9,29 | MODERATE | The paper does not reconcile whether the 2020 event analysis uses a separately trained model; untouched-test declaration cannot validate all reported test claims. |
| TV04 — Sequential reevaluation | YES | 9,24 | MODERATE | Multiple sequential origins with train-update and out-of-sample scoring are described, although fold dates and outputs are not given. |
| TV05 — Horizon / label timing | NOT_REPORTED | 7,9,21,25,26 | HIGH | No unambiguous t to t+h target construction or horizon found in the full text; sampling frequency is not a horizon. |
| TV06 — Overlap control | NOT_REPORTED | 9,21 | HIGH | No explicit purge, embargo, nonoverlapping target-outcome proof, or horizon-specific overlap control; TV05 is unclear. |
| TV07 — Panel membership separation | YES | 8,9 | MODERATE | Evidence establishes time-period grouping across the listed markets, not out-of-asset generalization; multi-asset evaluation goal is temporal transfer. |
| PL01 — Scaling / normalization boundary | YES | 6,9 | HIGH | Explicit train-only scaler boundary meets the B1 threshold as a reported protocol; independent implementation not verified. |
| PL02 — Feature-selection boundary | AMBIGUOUS | 9,19 | MODERATE | The supervised feature-selection fit and nested CV boundaries are not specifically demonstrated for all folds. |
| PL03 — Imputation boundary | AMBIGUOUS | 8,9 | HIGH | Source does not specify whether interpolation/model imputation is fitted only to available past data at each forecast origin. |
| PL04 — Decomposition / transform boundary | AMBIGUOUS | 9,10,19 | MODERATE | Fitting windows for every wavelet/decomposition and feature transform are not demonstrated on a complete live pipeline. |
| PL05 — Point-in-time features | AMBIGUOUS | 8,18,19 | MODERATE | No detailed economic-release calendars, data revision vintage, or explicit point-in-time as-of joins for each external feature. |
| PL06 — Text / news timestamp alignment | NOT_APPLICABLE | 8,31 | MODERATE | The audited method does not establish a text/NLP signal source requiring publication timestamp alignment. |
| PL07 — Graph / cross-asset construction | AMBIGUOUS | 8,9,10 | MODERATE | As-of control for every estimated cross-asset relation is asserted generically but not demonstrated; this field is treated as applicable to estimated cross-asset structure. |
| PL08 — Hyperparameter selection isolation | YES | 9,20,21 | MODERATE | Bayesian search uses validation rather than the final test according to authors; independent code confirmation absent. |
| PL09 — Leakage mechanism verified | AMBIGUOUS | 9,29 | HIGH | Potential overlap in crisis stress evaluation; no verified experiment-specific contamination trace or explicit proof the crisis model used the same training regime. No global EXPLICIT_NO. |
| PL10 — Training-only overall boundary | AMBIGUOUS | 8,9,19 | HIGH | All materially fitted transforms must be proved train-constrained; that requirement is unmet for several operations. |
| PL11 — Overall leakage-risk adjudication | INDETERMINATE | 8,9,19,21,29 | HIGH | Special ordinal B1 judgment. No verified material leakage mechanism for HIGH; no affirmative protection across all boundaries for LOW. |
| BL01 — Baseline comparator reported | YES | 23,24,27 | MODERATE | At least named comparator/task-level quantitative claims are supplied, but no baseline-by-baseline performance table appears. |
| BL02 — Naive/task baseline | NOT_REPORTED | 23,24,27,30 | HIGH | No actual naive stock-price or direction baseline evaluation documented. |
| BL03 — Strong model-family comparator | AMBIGUOUS | 24,27,30 | MODERATE | Strong modern comparators are named, but corresponding implemented quantitative results, configurations and test metrics are not shown. |
| BL04 — Fair evaluation / tuning budget | AMBIGUOUS | 9,24,30 | MODERATE | Comparable tuning budgets across architectures not documented consistently; common metrics are insufficient. |
| BL05 — Component ablation | YES | 20 | MODERATE | Component-wise VECM feature ablation under common splits and hyperparameters is described. Numeric ablation table absent; treat results as author-reported. |
| ST01 — Formal comparative inference | AMBIGUOUS | 23,28,29 | HIGH | Actual test statistics, p-values, explicit alpha/decision thresholds or method-specific test table are absent; cannot verify the B1 YES threshold. |
| ST02 — Temporal-dependence-aware inference | AMBIGUOUS | 28,29 | MODERATE | Specific dependence adjustment, horizon correction, test statistic and loss sequence not supplied. |
| ST03 — Multiplicity control | NOT_REPORTED | 20,23,28,29 | HIGH | No prespecified multiple-testing adjustment, hierarchical control or explicit unadjusted final-testing statement found. |
| ST04 — Uncertainty of estimated performance | NOT_REPORTED | 26,28,31 | HIGH | No numerical interval bounds, endpoint-specific interval table or bootstrap interval estimate is reported. |
| EC01 — Implemented economic evaluation | AMBIGUOUS | 23,24,27 | MODERATE | No documented forecast-to-trade mapping or realized trading series to verify the claimed backtest as an implemented strategy. |
| EC02 — Transaction cost inclusion | AMBIGUOUS | 23 | MODERATE | No numerical commission, fee, spread or other quantified trading-cost assumption found; threshold for YES unmet. |
| EC03 — Net-of-cost results | NOT_REPORTED | 23,24,27 | HIGH | No return, Sharpe, PnL or other economic outcome expressly identified as net of quantified trading costs. |
| EC04 — Actionable signal mapping | NOT_REPORTED | 23,24,26,27 | HIGH | No explicit position sign/size, forecast-to-order mapping, entry time, execution horizon, holding period and rebalance rule. |
| EC05 — Execution frictions and feasibility | AMBIGUOUS | 23,25,27 | MODERATE | No quantitative turnover, spread, liquidity or slippage scenario with operational timing parameters. |
| RB01 — Regime-specific performance | NOT_REPORTED | 20,23,29 | HIGH | No numeric performance figures separated by pre-defined market regimes were supplied. |
| RB02 — External shock-period stress test | AMBIGUOUS | 9,29,30 | HIGH | Named event window exists, but no separate stress metrics and purported unseen 2020 data overlaps the stated 2015–2021 train period. |
| RB03 — Market/asset transfer | NOT_REPORTED | 8,9,26 | HIGH | No separate held-out asset or market-transfer evaluation that isolates previously unseen market membership. |
| RB04 — Sensitivity / stability | AMBIGUOUS | 19,20,26,29 | MODERATE | Run counts, per-seed scores, interval widths and sensitivity outcome tables are not provided. |
| EX01 — Explanation produced | YES | 19,27 | MODERATE | Qualitative model explanation is reported as performed; no actual per-feature numerical attributions or detailed explanation figure supplied. |
| EX02 — Explanation quality assessed | NOT_REPORTED | 19,27,31 | HIGH | No fidelity, perturbation, stability, counterfactual-validity or expert plausibility check for explanations. |
| EX03 — Forecast uncertainty quantified | NOT_REPORTED | 21,26,28 | HIGH | No forecast-level quantile, prediction interval, predictive distribution or calibrated predictive-uncertainty output. |
| EX04 — Calibration / coverage checked | NOT_APPLICABLE | 21,22,27,28 | MODERATE | Softmax described as a possible classification output and intervals refer to endpoint performance, not predictive probabilities or intervals. |
| RP01 — Executable code access | AMBIGUOUS | 31 | HIGH | LINK_REPORTED=YES; ARTIFACT_VERIFIED=PARTIAL; complete study-specific runnable forecasting pipeline not verified. See live URL and check date. |
| RP02 — Underlying data access | AMBIGUOUS | 8,18,26,31 | MODERATE | DATA_LINK_ACTIVE=PARTIAL_DEMONSTRATION; DATA_EXACT_RECONSTRUCTIBLE=NO_NOT_VERIFIED; actual data/raw price cohorts cannot be recovered exactly from supplied artifacts. |
| RP03 — Hyperparameter/config disclosure | AMBIGUOUS | 20,21,24,26 | MODERATE | Principal model configuration substantially described; baseline-specific configurations, input/lookback and full executable pipeline not recoverable. |
| RP04 — Seeds and stochastic protocol | YES | 16,21,26 | MODERATE | A stochastic-control policy and repeat-run design are reported under B1 threshold. Numeric seeds/run counts not supplied for empirical model (repository synthetic demo sets 42). |
| RP05 — Data partition identifiers | YES | 8,9 | MODERATE | Date-range endpoints and studied indices are identified; actual session manifest/fold identifiers not archived, so exact row-level reconstruction still limited. |

## Source-and-code evidence notes

- **PDF citations:** Pages in the CSV and this report refer to physical PDF pages 1–34, not printed KSII folios (1630–1663).
- **GitHub URL:** https://github.com/DewanHabib10/Stock_market_paper (checked 2026-11-03). Public root visibly contains `README.md`, `raw_data.csv`, `vecm_model.py`, `vecm_residuals.csv`.
- **Code coverage:** Repository README mentions `feature_engineering.py` and `lstm_model.py` but those scripts were not present at the time of review; no exact Git commit was captured and no reproduction was run.
- **Synthetic data:** Available `vecm_model.py` seeds an example `np.random.seed(42)` and synthesizes 1,000 business-day records. This example seed cannot be attributed to the paper’s empirical evaluation.
- **Evidence hierarchy:** PDF methodology declarations are reported claims. External repository inspection is linked evidence only for RP01/RP02. Do not use external generic literature to fill in missing fields.
- **Taxonomy:** VECM residuals enter the LSTM forecaster (pp. 6–7, 25). A `Hybrid deep-learning models` principal-family classification is plausible but must await approval of the B1 proposed precedence clarification.

## Governance and integration

1. Keep source Phase A 485-study workbook, the B1 codebook, and B3 40-study pilot unchanged.
2. Retain the generated CSV/Markdown as **B4 draft evidence**; the author should review every `AMBIGUOUS`, `INDETERMINATE`, and central `YES` entry, particularly the two critical exceptions.
3. Codebook ordinal PL11 must **never** be collapsed into binary YES/NO; report denominator/status mapping only after author review.
4. Copy the draft artifacts into a new versioned `PhaseB4` area in WSL only after manually verifying local source/codebook SHA-256 values, and store receipt hashes.
5. Do not mark `P00037` author-finalized or propagate its coding to all 485 studies before author sign-off.
