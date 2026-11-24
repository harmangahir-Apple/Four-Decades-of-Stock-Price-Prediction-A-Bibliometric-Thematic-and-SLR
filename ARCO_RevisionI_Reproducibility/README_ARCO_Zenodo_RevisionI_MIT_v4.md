# ARCO Revision-I — selected methodological-audit scripts and Table 10 aggregate verifier

**Archive type:** Selected-code software archive supporting partial reproducibility.  
**Zenodo DOI:** `10.5281/zenodo.24497076`  
**Manuscript:** *Stock Price Prediction: A Bibliometric, Thematic, and Systematic Review of Computational Intelligence Approaches* (ARCO Revision-I, *Archives of Computational Methods in Engineering*).

## Scope and limitations

This deposit is a **partial, selected-code archive**. It contains three previously collected methodological-audit scripts plus a Table 10 aggregate verification script and a non-identifying aggregate CSV. It does **not** contain the study-level controlled data or all code necessary to reproduce every figure, table, screening decision, or source adjudication in the article. The study-level inputs required by two scripts are not supplied here, pending rights, evidence provenance, and release approval. Code being available does not independently authenticate its underlying study-level classifications.

The analytical populations have **different meanings and must never be pooled**:

- **Historical frozen 485-study technical register:** used for older validation-design and leakage-signal distributions and as the principal-family lookup.
- **Author-approved complete-profile subset, 353 studies:** 10 methodological dimensions per study; a nonrandom subset of 475 provisionally eligible studies, with 122 profiles incomplete.
- **Historical 484-study staging cohort:** used only by an older coverage audit; not the 353-profile Table 10 or current manuscript prevalence estimate.

## Contents

| File | Role | Requirements / limitations |
|---|---|---|
| `ARCO_Table10_N353_Aggregate_Verifier_v1.py` | Validates and formats the author-approved ten-dimension N=353 four-state aggregate counts | Runs standalone with the companion pinned aggregate CSV; **does not** independently recode study-level decisions |
| `ARCO_Table10_N353_AuthorApproved_Aggregate_v1.csv` | Ten-dimension aggregate four-state counts; no Paper IDs or source excerpts | SHA256 `009bfa599ba4fb7de672603c06d279a54216473b17f93daed90627c3ccd13fe8` |
| `ARCO_Figure12_OriginalStyle_N353_v2.py` | Recreates the manuscript's three-panel Figure 12 from counts **embedded in the script**; Panel A and C N=485, Panel B N=353 | Standalone figure-generation demonstration, **not** a source-data recalculation |
| `ARCO_R1_Major3_N353_FamilyPractice_ReadOnly_v1.py` | Prints the family × seven-practice cross-tabulation for the 353 complete profiles | Needs the **exact** author-approved 3,532-row controlled master and frozen 485-row CSV, with embedded SHA256 pins; neither included here |
| `ARCO_Major1_FourState_Coverage_Gate_v1.py` | Historical stage-17 coverage/queue audit (484 studies and 14 dimensions) | Needs **three** exact SHA256-pinned, private source CSVs; creates a new output directory; **does not** regenerate the current N=353 Table 10 |

## Minimal environment

Python 3.10+ is recommended. The Figure 12 script requires NumPy and Matplotlib. The other three Python scripts use Python's standard library.

```bash
python -m pip install -r requirements_ARCO_Zenodo.txt
```

For controlled local use, keep source CSVs outside a public archive and do not commit any paths containing identities or licensed database exports.

## Execution

### Table 10 (standalone aggregate verifier; no controlled source register required)

```bash
python ARCO_Table10_N353_Aggregate_Verifier_v1.py --self-test
python ARCO_Table10_N353_Aggregate_Verifier_v1.py \
  --output-dir ./table10_verified_new
```

The script validates its companion CSV against a pinned checksum and ten exact
four-state count tuples, then produces a formatted CSV, a LaTeX **tabular fragment**
and a JSON verification report in a **new** output folder. It refuses to overwrite an
existing folder. The input counts were approved through the private study-level
adjudication workflow; this public script does **not** independently reproduce
source-level approval, record identities, literature screening, author decisions,
or the N=352 historical-document-recovery sensitivity. The zeros in the
`Not_recoverable` column reflect selection of complete profiles, not a claim about
all provisionally eligible studies.

### Figure 12 (standalone, with hard-coded approved aggregate counts)

```bash
python ARCO_Figure12_OriginalStyle_N353_v2.py --output-dir ./figure12_output
```

Creates `Fig12_OriginalStyle_A485_B353_C485_NoCaption.pdf` and `Fig12_OriginalStyle_A485_B353_C485_NoCaption_preview.png`. The figure script was syntax-checked and executed in an isolated review environment on 2026-11-24. This confirms rendering functionality, **not** source-level provenance or a new statistical result.

### Family × practices (restricted input required)

```bash
python ARCO_R1_Major3_N353_FamilyPractice_ReadOnly_v1.py \
  --master /PATH/TO/author_approved_3532_master.csv \
  --frozen /PATH/TO/frozen_485_register.csv
```

The script rejects CSVs whose SHA256 checksums differ from those pinned in the script. It prints the seven selected methodological indicators and family denominators but writes no CSV. It is **not independently executable from this Zenodo deposit alone**.

### Historical 484-study coverage audit (restricted input required)

```bash
python ARCO_Major1_FourState_Coverage_Gate_v1.py \
  --cohort /PATH/TO/historical_484_scenario.csv \
  --ledger /PATH/TO/stage17_author_ledger.csv \
  --overlay /PATH/TO/stage17_source_overlay.csv \
  --outdir ./historical_coverage_OUTPUT_NEW
```

The script refuses an output directory that already exists and checks the three input SHA256 hashes. It writes coverage summaries and an unassessed-case queue **only into the new local directory**. Outputs can include study identifiers and must be reviewed before public dissemination. This is **historical staged analysis**, not a current N=353 reproduction.

## Data and reproducibility boundaries

The historical 485-study register, complete-profile N=353 approved master, 484-study staging cohort, stage-17 ledger, and source overlay are **not** redistributed through this selected-code archive. Those inputs include provenance/permissions questions that require separate review. No publisher full-text PDFs or proprietary bibliographic exports are included in this selected-code deposit.

The independently executable components of the archive are **Table 10 aggregate arithmetic/formatting from the supplied approved aggregate CSV**, and **Figure 12 rendering from embedded aggregates**. Neither provides independent study-level source adjudication. To substantiate stronger reproducibility claims, the release must add an approved, non-restricted input-data substitute or an independently regenerable data pathway; exact Table 10 source/data generation and study-level provenance remain separate release gates.

## Related repository

Historical research-code repository:  
https://github.com/harmangahir-Apple/Four-Decades-of-Stock-Price-Prediction-A-Bibliometric-Thematic-and-SLR

The GitHub repository contains historical and provisional artifacts; its entire contents should **not** be regarded as a finalized, rights-cleared public research deposit. The contents of the historical GitHub repository are not certified by this archive.

## Citation and license

The **eight-file selected-code Zenodo deposit** (four Python scripts, one aggregate CSV,
one requirements file, this README, and `LICENSE`) is made available under the
**MIT License (SPDX identifier: `MIT`)**, with authorization from the relevant
software contributors and rights holders. See `LICENSE` for the full terms.
The MIT License permits reuse and adaptation subject to preserving its copyright
and permission notices; it does not apply to restricted or third-party datasets,
publisher PDFs, or any materials outside this specific Zenodo deposit.

Use the version-specific Zenodo DOI `10.5281/zenodo.24497076` to cite this
archived release **after the Zenodo record is published**. A DOI reserved for a
draft is not evidence that the archived software is publicly released.
