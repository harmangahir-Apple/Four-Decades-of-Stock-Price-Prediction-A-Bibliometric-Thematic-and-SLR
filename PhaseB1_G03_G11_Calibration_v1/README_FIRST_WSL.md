# ARCO B1 — G03/G11 beginner calibration kit

This kit **does not approve either gate** and **does not examine original studies**. It tests the v1.2 reporting-state logic with 12 explicitly **synthetic** scenarios. Your frozen 485-row, 51-column workbook is not opened or changed.

## 1. Copy ZIP into your WSL project and extract

```bash
cd ~/projects/Stock_Price_Prediction_SLR_ACME
conda activate Harman_GPU
unzip -o ARCO_B1_G03_G11_12Case_Calibration_Kit.zip -d PhaseB1_G03_G11_Calibration_v1
```

## 2. Run calibration

```bash
python PhaseB1_G03_G11_Calibration_v1/calibrate_g03_g11.py \
  --output-dir PhaseB1_G03_G11_Calibration_Results
```

This should print `PASS: 12/12 synthetic evidence-state cases`. Read the report:

```bash
code PhaseB1_G03_G11_Calibration_Results/B1_G03_G11_Calibration_Report.md
```

## 3. Review each case yourself (no automatic approval)

```bash
code PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv
```

For each row, put `ACCEPT` or `REVISE`, your actual author name, the date you made the decision in `YYYY-MM-DD`, and comments. If you choose REVISE, say what rule must change. Do not write invented quotes, PDF pages or Paper_IDs. A synthetic case shows how a proposed rule works, not whether any paper actually followed that practice.

## 4. Validate your 12 individual decisions (only after completing the sheet)

```bash
python PhaseB1_G03_G11_Calibration_v1/calibrate_g03_g11.py \
  --author-review PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv \
  --output-dir PhaseB1_G03_G11_Calibration_Results
```

When 12 accepted, the **calibration** will read `ALL_ACCEPTED_BY_REVIEWING_AUTHOR` but the B1 gates **remain NOT APPROVED** until a versioned protocol and actual gate ratification. If any case requires revision, update the scientific rules and rerun tests first. Do not insert APPROVE into G03/G11 automatically or edit your existing v1.1 sign-off manifest.

## Files

- `B1_12_Synthetic_Calibration_Cases.csv`: synthetic cases only, not study observations
- `B1_12_Case_Expected_Results.json`: expected code/report outcomes
- `B1_Author_Calibration_Review_FILL_THIS.csv`: unsigned review worksheet
- `calibrate_g03_g11.py`: logic test + safeguards, standard Python only
- `B1_v1_2_Scientific_Rule_Addendum_REFERENCE_NOT_APPROVED.md`: source proposed addendum
- `B1_Calibration_Reviewer_Decision_Guide.md`: plain-English state decisions
- `B1_Calibration_Review.xlsx`: readable worksheet copy of synthetic cases and blank author decisions

**Next stage:** author review of these 12 cases; if accepted, ratify the versioned v1.2 protocol and its hash manifest. Subsequent real-paper calibration must use authentic, traceable primary-study sources.
