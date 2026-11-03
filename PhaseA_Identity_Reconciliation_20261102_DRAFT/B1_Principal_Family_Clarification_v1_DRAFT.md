# Proposed B1 Clarification: Principal Method Family

Status: DRAFT — NOT APPROVED
Date: 2026-11-03

## Scope

Prospective clarification for Phase B method-family
adjudication only. The original B1 source hierarchy,
45 coding fields, 11 gates and frozen Phase A cohort
remain unchanged.

## Proposed interpretive rule

1. Verify original publication identity before classification.
2. Identify the model or integrated framework actually
   implemented to predict the study's stock-market target.
3. Distinguish the proposed method from feature extraction,
   screening methods, benchmark models and related work.
4. Classify explicitly integrated architectures according
   to their documented forecasting contribution and the
   existing B1 family definitions.
5. For sentiment/NLP pipelines, examine whether text-based
   signal modelling is the principal contribution or an
   input to a separately identifiable prediction model.
6. For studies comparing several independent models,
   do not select a family solely from the best score or
   mention of an architecture. If no principal model is
   identifiable, consider the existing Other/unclear code,
   subject to the approved B1 codebook.
7. Record ambiguous family decisions, alternatives,
   supporting source passages and author adjudication.
8. Assess temporal leakage and validation independently
   of the principal-family decision.

## Cases requiring explicit adjudication

P02642: Sentiment/NLP-driven versus ensemble/tree-based
or other documented principal predictive architecture.

P00584: Comparative statistical/ML/DL study; determine
whether a principal forecasting architecture is specified.

P00853: Verify whether seven algorithms constitute an
integrated ensemble or independent comparison.

P01112: Verify integrated CNN/LSTM/attention precedence.
P03446: Verify ARIMA forecasting versus decision-tree screening.
P00211: Verify compact 1D-CNN versus benchmark models.

## Governance

This is a proposed clarification, not an amendment in force.
Author approval and a versioned implementation log are
required before any family reclassification or pilot
re-stratification. No changes to the frozen 485-study data.

Author decision: PENDING
Approval date:
Implementation status: NOT APPLIED
