# ARCO Revision-I — Phase B3: next gate (2 November 2026)

This kit is a working **adjudication aid**, not a completed author review or source-verification receipt. It was prepared from the **71-page Manuscript(20261102-080357).pdf**, the **99-page Supplementary(20261102-080357).pdf**, the original ACME Reviewer 1 and Reviewer 2 comments, frozen 485-study register SHA-256 `95dfe27744de4cf7dd10ca7a7a937c871a39eec77661e69938f938168ab85da5`, the 40-study pilot selection, signed B1 protocol and external bibliographic discovery as of 2026-11-02.

## 1. Install without overwriting original files

Download `ARCO_B3_Next_Gate_20261102.zip` into `~/projects/Stock_Price_Prediction_SLR_ACME`, then:

```bash
cd ~/projects/Stock_Price_Prediction_SLR_ACME
unzip -o ARCO_B3_Next_Gate_20261102.zip -d B3_Next_Gate_Kit
python B3_Next_Gate_Kit/check_b3_author_review_readonly.py --project .
```

The script **only reads** existing files. The latest user-reported result was `BLANK: 40` on the author-review CSV. If it is still blank, the script will correctly report pending status. This is *not* approval.

## 2. Open the targeted adjudication worksheet

Open `B3_Next_Gate_Kit/B3_Next_Gate_Adjudication_Tracker.xlsx` in Excel. Sheet `Flagged Cases` includes four study-specific findings and links. Yellow columns H/I are **optional local reviewer notes**, not automatically accepted as final decisions. Column H allows `APPROVE`, `REJECT`, `PENDING` for local planning only; `PENDING` is not a valid approval decision in the canonical author-selection CSV.

The actual, canonical file is:

`PhaseB3_Pilot_Selected_v1/B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv`

For flagged papers, leave the canonical decision cell blank until you have checked source identity/eligibility/stratum. The 36 other cases are **approval candidates** only after actual author review; no script should sign for the author.

## 3. Resolve each flagged case BEFORE trying to lock the 40-case pilot

- `P01112`: obtain actual IEEE full text, verify hybrid CNN/LSTCN + attention mechanism and principal-family tie-break, assess effect on singleton ANN stratum.
- `P03446`: recover the CERGE-EI working paper, confirm whether non-journal working papers are permitted in *this review*; do **not** exclude for equity volatility alone (explicitly eligible in manuscript §2.3). Check publisher type and family.
- `P00584`: verify original article for DOI `10.55248/gengpi.07.0626.15b06`; document 2025 vs June 2026 / abbreviated-title conflict in a *separate amendment note*. Do not change frozen records.
- `P00853`: inspect Springer chapter to decide if it actually ensembles models or compares independent models; apply a consistent principal-family rule.

Record URLs, source versions, actual access dates, file hashes (if downloaded), original method passages and author findings. Search snippets are leads only, not primary-source methods coding.

## 4. Other reviewer requirements remain open

See `Reviewer Gap Tracker` sheet. The signed B1 codebook has 45 fields; the 485×45 B2 decision slots currently contain **zero new scientific codes**. Phase C requires separately coded independent records and genuine per-field agreement statistics. Keep all Phase A reported numbers untouched until evidence-level B and independent C reconciliations complete.

## 5. Source locations

- P01112 indexed abstract: https://eurekamag.com/research/104/038/104038454.php
- P03446 source record: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3996169
- P03446 institutional working paper: https://www.cerge-ei.cz/pdf/wp/Wp713.pdf
- P00584 bibliographic evidence: https://www.researchgate.net/publication/407208887_From_SMA_to_LSTM_A_Comparative_Analysis_of_Statistical_and_Machine_Learning_Models_for_Stock_Price_Prediction
- P00853 university publisher metadata: https://pure.southwales.ac.uk/en/publications/quantifying-market-signals-an-ensemble-iot-driven-approach-to-sto/
- P00853 Springer chapter index: https://link.springer.com/book/10.1007/978-981-96-3247-3?page=2

**Important:** Cross-source author lists may disagree (SSRN displays fewer authors for P03446 than the CERGE-EI working-paper PDF). Preserve and resolve discrepancies rather than silently selecting one.
