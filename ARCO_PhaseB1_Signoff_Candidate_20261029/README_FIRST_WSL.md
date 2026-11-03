# Phase B1 author sign-off — WSL quick instructions

Copy the archive into your existing WSL project root and extract without overwriting the original B1 files.

```bash
conda activate Harman_GPU
unzip -o ARCO_PhaseB1_Signoff_Candidate_20261029.zip -d PhaseB1_Signoff_Candidate
python PhaseB1_Signoff_Candidate/phaseB1_signoff_gate.py \
  --frozen "Supplementary_Data_S1_485_FROZEN(9).xlsx" \
  --package-dir PhaseB1_Signoff_Candidate \
  --output-dir PhaseB1_Signoff_Audit
```

If the frozen workbook is elsewhere in your project tree, pass its real path to `--frozen`; do not move or edit it. The script stops if the SHA-256 differs from the vetted copy. It also stops if the workbook has the wrong 485 IDs/51 fields/scope distributions.

Next read `B1_SCIENTIFIC_SIGNOFF_DOSSIER_v1_1.md` and the proposed rule amendments, then fill the CSV columns `Author_Decision`, `Approving_Author`, `Approval_Date_YYYY_MM_DD`, and `Author_Comments` for each row. Each gate requires an explicit `APPROVE` or `REJECT` (no automatic approvals). After genuine author ratification:

```bash
python PhaseB1_Signoff_Candidate/phaseB1_signoff_gate.py \
  --frozen "Supplementary_Data_S1_485_FROZEN(9).xlsx" \
  --package-dir PhaseB1_Signoff_Candidate \
  --output-dir PhaseB1_Signoff_Audit \
  --finalize
```

Expected before manual completion: `TECHNICAL_VALIDATION_PASS__AWAITING_AUTHOR_SIGNATURE`. After all gates are completed and validated: `B1_AUTHOR_RATIFICATION_RECORDED__B2_AUTHORIZED`. The latter certifies documented author-attestation only, not verified human identity or completed B2/B3/B4/B5/Phase C work.

The source workbook, original Phase A register and original codebook are never modified.
