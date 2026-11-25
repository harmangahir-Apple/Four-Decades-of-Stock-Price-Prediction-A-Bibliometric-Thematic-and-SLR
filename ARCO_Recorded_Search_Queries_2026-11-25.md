# Recorded database search strategies — ARCO Revision-I

**Provenance:** Transcribed from Supplementary Information, Section S2 (Scopus listing, Web of Science listing and IEEE Xplore Table S2); not a new or independently executed retrieval. The search/export workflow was finalized on 19 June 2026. This document contains query text and metadata only, not licensed bibliographic exports or source PDFs.

**Scope:** Different database interfaces and year restrictions were used. Results are historical export counts and should not be interpreted as currently reproducible live hit counts.

## Scopus

- Recorded coverage: 1985–2026; 4,832 source rows contributed to the merge.
- Query field: `TITLE-ABS-KEY`.

```text
TITLE-ABS-KEY(
(
    "stock price prediction" OR
    "stock price forecasting" OR
    "stock market prediction" OR
    "stock market forecasting" OR
    "share price prediction" OR
    "share price forecasting" OR
    "equity price prediction" OR
    "equity price forecasting"
)
AND
(
    "computational intelligence" OR
    "artificial intelligence" OR
    "machine learning" OR
    "deep learning" OR
    "neural network" OR
    "neural networks" OR
    "artificial neural network" OR
    "support vector machine" OR
    "support vector regression" OR
    "random forest" OR
    "decision tree" OR
    "gradient boosting" OR
    "XGBoost" OR
    "LightGBM"
)
)
```

## Web of Science

- Recorded coverage: 1985–2025; search executed 19 June 2026; 100 exported records.
- Recorded restrictions: English; articles, proceedings papers, books and book chapters.
- Query field: `TS` (Topic).

```text
TS=(
  "stock price prediction" OR
  "stock price forecasting" OR
  "stock market prediction" OR
  "stock market forecasting" OR
  "financial time series forecasting" OR
  "equity price prediction" OR
  "share price prediction"
)
AND
TS=(
  "machine learning" OR
  "deep learning" OR
  "computational intelligence" OR
  "artificial intelligence" OR
  "neural network" OR
  "LSTM" OR
  "GRU" OR
  "CNN" OR
  "transformer" OR
  "attention mechanism" OR
  "graph neural network" OR
  "sentiment analysis" OR
  "multimodal" OR
  "metaheuristic" OR
  "evolutionary optimization" OR
  "feature selection" OR
  "hyperparameter optimization"
)
```

## IEEE Xplore

- Five method-specific query runs; conferences and journals; potentially overlapping results.
- The **3,572 total is query-run rows**, not verified unique IEEE publications.

### Q1 — 1991–2026; 1,547 raw query-run rows

```text
("stock price prediction" OR "stock market prediction" OR "stock price forecasting") AND ("machine learning" OR "deep learning")
```

### Q2 — 2005–2026; 1,161 raw query-run rows

```text
("stock price prediction" OR "stock market prediction") AND (LSTM OR GRU OR CNN OR "convolutional neural network")
```

### Q3 — 2004–2026; 189 raw query-run rows

```text
("stock price prediction" OR "stock market forecasting") AND (transformer OR "attention mechanism" OR "self-attention")
```

### Q4 — 2008–2026; 602 raw query-run rows

```text
("stock price prediction" OR "stock market prediction") AND ("sentiment analysis" OR "financial news" OR NLP OR "natural language processing")
```

### Q5 — 2004–2026; 73 raw query-run rows

```text
("stock price prediction" OR "stock market forecasting") AND (metaheuristic OR "genetic algorithm" OR "particle swarm optimization" OR "grey wolf optimizer")
```

## Recorded total and interpretation

Scopus: 4,832 rows; Web of Science: 100 rows; IEEE Xplore: 3,572 query-run rows. Together these contributed 8,504 rows to the CSV-based merge **before within-source and cross-source deduplication**. The deduplicated bibliometric corpus contains 5,022 publications.

## Reproducibility caveats

- Database indexing and live search interfaces may have changed since the historical export.
- The exact search strings and recorded date windows are preserved here; retrieval results are not revalidated by this transcription.
- This file complements Supplementary Section S2 and is separate from the previously published eight-file selected-code Zenodo archive.
- No original publisher PDFs, licensed search exports, controlled study-level records, or unpublished adjudication documents are included.
