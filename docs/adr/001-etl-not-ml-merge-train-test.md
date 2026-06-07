# ADR-001: Merge Train/Test splits at ingest (ETL, not ML)

**Status:** Accepted

## Context

The primary Medicare claims-fraud dataset ships each of its four tables as two CSVs — a `Train_*`
and a `Test_*` split — a partition that exists for the dataset's original Kaggle ML competition.
This project is an **ETL / analytics-engineering** pipeline, not a model-training pipeline: there is
no downstream model that must never see the test rows. Preserving the split would mean carrying a
`split` column (or two parallel raw tables) through staging, intermediate, and marts for no analytical
benefit, and it would understate the `dim_provider` / `dim_beneficiary` aggregates by roughly half.

## Decision

Concatenate the Train and Test CSVs into a single raw table per source table during ingestion. Both
files validate against the **same** pandera schema before they are merged (`load_and_merge` in
`src/clinical_data_etl/ingestion/loaders.py`). The split is not preserved anywhere downstream.

One consequence is handled explicitly: the Test provider file has **no `PotentialFraud` column**.
`ProviderSchema` makes the fraud flag nullable and the loader adds `PotentialFraud = NaN` when the
column is absent, so the merged table is rectangular. See ADR-002 for where that label lands.

## Consequences

- **Easier:** the whole pipeline reasons about one row-per-entity grain; the mart aggregates cover the
  full provider/beneficiary population.
- **Harder / accepted:** the original competition's train/test boundary is gone — fine here because no
  model is trained, but it means this warehouse cannot be used to reproduce that competition's scoring
  without re-deriving the split.
- Creates the missing-column edge case that ADR-002 and the nullable `ProviderSchema` absorb.
