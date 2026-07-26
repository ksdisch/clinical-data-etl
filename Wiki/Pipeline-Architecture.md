# Pipeline-Architecture

## Purpose
The compiled, resume-a-cold-session map of how the pipeline fits together and the per-source quirks that are easy to forget. Details live in the linked sources — this page is the index of understanding, not a duplicate.

## Key understanding
- **Shape (Fact):** 3 Kaggle sources → pandas ingestion with per-table pandera schemas → PostgreSQL `raw` schema (idempotent `ON CONFLICT` upsert, first-seen `ingested_at`) → dbt (staging → intermediate → marts, 20 models, 2 seeds, 1 snapshot) → 3 deliberately independent star schemas → Prefect orchestration (`make pipeline`).
- **Per-source quirks (Fact):**
  - Claims fraud (primary, 4 tables): Train/Test CSVs merged at ingest; Test provider file has no `PotentialFraud` column → nullable flag, loader fills `NaN`.
  - Diabetes (secondary, 1 CSV, 101,766 rows): `?` missing sentinel recoded to NULL *before* pandera validation; target = 30-day readmission (~11%).
  - Hospital (tertiary, 1 CSV, 5,000 rows): no usable natural PK (`case_id` recycled) → surrogate `admission_id = md5(case_id-patientid)` minted at ingest; Excel `20-Nov`→`11-20` bracket artifact recoded in `Age`/`Stay`; target = length of stay (`is_long_stay`, ~48%).
- **Incremental design (Fact):** only `int_claims_enriched`, `fct_claims`, `fct_encounters`, `fct_hospital_admissions` are incremental (`delete+insert`, `NOT EXISTS` hash anti-join boundary — a `NOT IN` boundary previously caused a >14-min re-run hang vs ~59s now). `int_claims_unified` stays a full view because `dim_provider` aggregates over it.
- **History (Fact):** SCD2 on the provider fraud label via `dbt/snapshots/snap_provider_fraud.sql` (check strategy) → `dim_provider_history`, with no-overlap / one-current invariant tests.
- **Honest framing (Fact):** all sources are single-vintage, so incrementality and SCD2 are proven with deterministic seeded demos (`make demo-incremental`, `make demo-scd2`) — demos, not real CDC.
- **Test surface (Fact):** 56 pytest tests; 98 dbt tests (97 pass, 1 expected warn on the orphan-claims relationship, per ADR-003).

## Sources
- `CLAUDE.md` — the most current operational summary (priorities, per-source notes, incremental/SCD2 design notes)
- `README.md` — architecture diagrams, three ERDs, mermaid lineage, setup + Makefile targets
- `docs/adr/` — the ten load-bearing decision records (indexed in `Decisions.md`)
- `docs/data-dictionary.md` — column-level lineage across all three stars
- `docs/incremental_scd2.md` — incremental + SCD2 design and demo mechanics
- `PROJECT_GUIDE.md` — comprehensive walkthrough (Inference: partially stale — dated 2026-05-30, before the Phase 3 hospital star)

## Uncertainties & contradictions
- **Unresolved:** whether a Phase 4 exists or the project is portfolio-complete (no decision recorded).
- **Inference (minor staleness):** `PROJECT_GUIDE.md` predates Phase 3; prefer `CLAUDE.md`/`README.md` for current-state claims.

## Related pages
- (none yet — first topic page)

## Relevance to current work
Any new source must follow the documented path (pandera schema → upsert loader → raw table → staging → independent star — see the vendored `add-source` skill in `.claude/skills/`), and any new mart must respect the incremental-boundary and grain decisions above.

_Last reviewed: 2026-07-26_
