# ARCO Revision-I — Phase B2 Initialization Tool (v1.0)

**Phase B1 authorization verified from your terminal output:**
`B1_v1_2_AUTHOR_RATIFICATION_RECORDED__B2_INITIALIZATION_AUTHORIZED`.

**This downloaded kit itself is not a B2 author receipt.** The Python initializer validates your actual, locally generated B1 receipt before creating B2 study–field tables. It will stop rather than bypass any missing or mismatched approval.

## Step 1 — Unzip in VS Code WSL

Place `ARCO_PhaseB2_Initialization_Kit_20261029.zip` in your project root:

```bash
cd ~/projects/Stock_Price_Prediction_SLR_ACME
conda activate Harman_GPU
unzip -o ARCO_PhaseB2_Initialization_Kit_20261029.zip -d PhaseB2_Init_Toolkit
```

## Step 2 — Run read-only authorization preflight

```bash
python PhaseB2_Init_Toolkit/initialize_arco_phase_b2.py \
  --frozen ./Supplementary_Data_S1_485_FROZEN.xlsx \
  --b1-package PhaseB1_v1_2_Signoff_Candidate \
  --receipt PhaseB1_v1_2_Signoff_Audit/B1_v1_2_AUTHOR_RATIFICATION_RECEIPT.json \
  --calibration-review PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv \
  --output-dir PhaseB2_Initialized_v1 \
  --preflight
```

Expected:

```text
AUTHORIZATION CHECK: PASS
485-study frozen checksum, 45-field signed codebook, 11 author gates, 12-case calibration: PASS
STATUS: PREFLIGHT_ONLY__NO_FILES_WRITTEN
```

## Step 3 — Initialize blank B2 evidence tables

Rerun with identical parameters **but omit `--preflight`**:

```bash
python PhaseB2_Init_Toolkit/initialize_arco_phase_b2.py \
  --frozen ./Supplementary_Data_S1_485_FROZEN.xlsx \
  --b1-package PhaseB1_v1_2_Signoff_Candidate \
  --receipt PhaseB1_v1_2_Signoff_Audit/B1_v1_2_AUTHOR_RATIFICATION_RECEIPT.json \
  --calibration-review PhaseB1_G03_G11_Calibration_v1/B1_Author_Calibration_Review_FILL_THIS.csv \
  --output-dir PhaseB2_Initialized_v1
```

Expected:

```text
B2 INITIALIZATION: PASS
Frozen: 485 x 51 SHA-256 95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5
B1 AUTHOR RATIFICATION: verified locally
Fields: 45; new decision slots: 21825; NEW CODES: 0
STATUS: B2_INITIALIZED_NOT_CODED
```

The tool **refuses to overwrite a nonempty output directory**, preventing accidental destruction of future evidence records. If initialization fails, inspect the error; do not edit the frozen workbook or signed B1 inputs to make it pass.

## Step 4 — Inspect the outputs

```bash
code PhaseB2_Initialized_v1/README_B2_INIT.md
code PhaseB2_Initialized_v1/B2_field_decisions_INITIAL_UNCODED_21825.csv
code PhaseB2_Initialized_v1/B2_INITIALIZATION_RECEIPT.json
```

All 21,825 decision slots are **unassessed** with **blank new values**. The original Phase A values are included **only as historical comparison**, not as Phase B findings. No scientific claims are verified at initialization.

## Methodological protections

1. The original 485-study XLSX is only read and must not be edited.
2. Do not replace the original `YES/Unclear` values by the proposed B1 categories without source-level verification.
3. New positive, negative, LOW/HIGH leakage findings need traceable original-study passages, sections/pages or versioned verified code.
4. `NOT_REPORTED` requires a documented search of sufficiently accessible full text; unavailable essential appendices may require `INSUFFICIENT_ACCESS`.
5. B3's 40-case pilot will be selected separately with a frozen seed and stratum rules.
6. Phase C must involve genuine independent evidence coding; never claim kappa or agreement from this initialization or historical 37/40 pilot.
7. Do not revise manuscript/supplement counts before B and C close.

## Included schema preview

`ARCO_PhaseB2_Initialization_Blueprint.xlsx` includes an easy-to-read diagram of the initialization state, 485-paper index, 45-field codebook, 51-column mapping and expected output-file descriptions. It is **for reference only**, not a verified B2 initialized dataset.
