# Phase 5 plan — Tier 3 docs: ADR directory, data dictionary, intermediate column coverage

> Status: ✅ complete | Branch: `claude/autonomous-milestone-skill-tg7FH`
> Milestone selected via `/autonomous-milestone` backlog triage (the only standing open item).
>
> **Outcome:** the documentation story is closed. A numbered ADR directory (`docs/adr/`) captures
> the load-bearing decisions as discrete records; a column-level `docs/data-dictionary.md` covers
> all three stars end-to-end (raw → staging rename → mart); and `dbt/models/intermediate/schema.yml`
> now documents every column the four intermediate models carry, not just the keys. Pure docs —
> no source/SQL behaviour changed, so no regression surface.

Close out the last item in `BACKLOG.md` ("Tier 3 docs") and the deferred Tier 3 entries in
`docs/artifacts-plan.md` (items 11–13). This is a documentation-only milestone: it adds reference
material a hiring reviewer (or future-me) can read without running the pipeline, and it does not
touch ingestion, dbt SQL, or orchestration behaviour.

## Why this milestone

Everything else on the roadmap is shipped: three independent stars, idempotent upsert ingest,
incremental models, SCD2 history, CI (incl. a `dbt compile` job), `PROJECT_GUIDE.md`, `LICENSE`,
CI badge, `make dbt-docs`, and full marts column descriptions. The single remaining gap is the
*decision* and *column* reference layer. For an Analytics-Engineering portfolio the two highest-value
artifacts here are (1) ADRs — they answer the "why did you do it this way?" interview question in a
form a reviewer can skim — and (2) a data dictionary — it answers "what does this column mean?" for
non-obvious Medicare / UCI / synthetic-hospital field names. Both are fully authorable from material
already in the repo (`schemas.py`, the staging/intermediate SQL, the marts `schema.yml`, and the
Decisions & Tradeoffs section of `PROJECT_GUIDE.md`), so the milestone is self-contained and
needs no database, dbt, or Kaggle access.

## Deliverables

### 1. `docs/adr/` — Architecture Decision Records
Convention (from `docs/artifacts-plan.md` §5): `docs/adr/NNN-short-slug.md`, 3-digit zero-padded;
title `ADR-NNN: Title Case`; sections **Context / Decision / Consequences / Status**; cross-reference
`PROJECT_GUIDE.md` § "Decisions & Tradeoffs".

- `README.md` — index table (number, title, status) + the convention note.
- `000-template.md` — the record template.
- `001-etl-not-ml-merge-train-test.md` — merge Train/Test splits at ingest (ETL, not ML).
- `002-fraud-label-in-dim-provider.md` — fraud label stays on `dim_provider`, never denormalised onto `fct_claims`.
- `003-reject-and-continue-validation.md` — quarantine rejects to `data/rejected/`; orphan-claims relationship test is `severity: warn`.
- `004-three-independent-stars.md` — no conformed key joins the three sources; deliberately independent stars.
- `005-idempotent-upsert-loader.md` — `ON CONFLICT` upsert + first-seen `ingested_at` (supersedes the original DROP CASCADE reload).
- `006-incremental-boundary-not-exists.md` — set-membership boundary via `NOT EXISTS` hash anti-join; `int_claims_unified` stays a full view.
- `007-scd2-fraud-history-snapshot.md` — SCD2 history on the fraud label via a dbt snapshot (check strategy) → `dim_provider_history`.
- `008-minted-surrogate-admission-id.md` — md5 surrogate `admission_id` for the keyless hospital source.
- `009-subprocess-dbt-invocation.md` — invoke dbt via subprocess, not the Python API, to keep the Prefect task decoupled.
- `010-seed-backed-conformed-lookups.md` — seed-backed lookup dims (`dim_admission_type`, `dim_severity`).

### 2. `docs/data-dictionary.md` — column-level reference
One section per star. For each: the raw source columns (type, nullability, recodes/sentinels) and the
mart-facing columns, with the staging rename noted. Pulls canonical names/types from `schemas.py`,
renames from the `stg_*` models, and semantics from the marts `schema.yml`.

### 3. Intermediate column coverage
Expand `dbt/models/intermediate/schema.yml` so all four intermediate models document every column they
carry (not just keys/derived fields). **Descriptions only** — no new tests — so dbt test behaviour and
the CI `dbt compile` job are unaffected.

### 4. Wire-up / honesty pass
- `BACKLOG.md` — move "Tier 3 docs" from Deferred → Recently done.
- `docs/artifacts-plan.md` — mark Tier 3 items 11–13 as done.
- `CLAUDE.md` — refresh "Current Priority" (Tier 3 docs complete) and add the new docs to the listing.
- `docs/data-sources.md` / `README.md` — cross-link the data dictionary and ADR directory.

## Validation (sandbox has no dbt/DB/venv)
- YAML: load the edited `schema.yml` with PyYAML to confirm it parses.
- Cross-check every documented column name against the actual `stg_*`/`int_*` SQL so the dictionary
  and the intermediate descriptions match real columns.
- Markdown link sanity.
- (CI will run `dbt compile` on push to confirm the YAML is valid dbt.)

## Out of scope
- The `make dbt-docs` lineage *screenshot* (Tier 2 #8) — needs a running DB to render; deferred.
- Any source/SQL change. This milestone is documentation only.
