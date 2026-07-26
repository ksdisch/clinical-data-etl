# History — clinical-data-etl

> How this project got here: a chronological narrative of eras and milestones,
> reconstructed from merged PRs, git history, wrap logs, and ADRs.
> PR numbers, merge dates, tags, and SHAs are **Fact** by construction; rationale
> lines carry explicit labels (**Fact** when quoted from a PR body/ADR, **Inference**
> when reconstructed). Decisions are anchored by ID to the project's decision
> ledger — never restated here. **Append-only:** new milestones are added at the
> bottom (above the Mining coverage footer); existing entries are never rewritten.

## Origin — 2026-04

Started as a portfolio project demonstrating Data Engineering / Analytics Engineering skills via a multi-source clinical ETL pipeline (pandas + pandera → PostgreSQL → dbt → Prefect) [Fact — CLAUDE.md project overview]. First commit `ce88df4` on 2026-04-02 ("feat: initial project scaffold"). The same day, the planned synthetic NDNQI data source was swapped for real Kaggle healthcare datasets (`9ef8aa4`) [Inference — commit message; rationale not otherwise recorded]. No kickoff brief exists in the repo.

## Era: MVP claims pipeline (2026-04)

Two build days of direct-to-main commits stood up the full Medicare-claims pipeline end to end; only GitHub automation went through a PR.

### End-to-end MVP pipeline — 2026-04-02
- **Landed:** ingestion layer with per-table pandera validation (`01965ad`), dbt star-schema marts (`affaf83`), Prefect orchestration flow (`a04b5a0`) — all direct commits, no PRs
- **Why:** ship a working claims star (fct_claims + dim_beneficiary + dim_provider) before layering polish [Inference — commit sequence]
- **Decisions from this phase:** train/test merge at ingest, fraud label placement, reject-and-continue validation — see D1, D2, D3 in `Decisions.md` (recorded retroactively as ADRs in PR #8)

### CI and GitHub automation — 2026-04-04
- **Landed:** CI workflow + intermediate dbt tests + star-schema ERD (`4301fd1`), CI-green fixes (`9c0c673`); Claude Code GitHub workflow (PR #1, merged 2026-04-02)
- **Why:** guard the pipeline with automated checks before pausing work [Inference — commit timing at the end of the build burst]

## Era: Documentation polish & CI rescue (2026-05)

After an ~8-week dormant gap, one intensive session brought the repo back to a defensible state.

### Phase 4 polish — repo hygiene, dbt docs, CI green — 2026-05-30
- **Landed:** artifact audit + generation plan, CI badge, LICENSE, PROJECT_GUIDE.md committed, dbt source/column docs, Mermaid lineage DAG, dbt 1.10 `arguments:` test migration — runtime-verified (`dbt test` 40 pass/1 warn) (PR #2); BACKLOG.md fix-tracker (PR #3)
- **Why:** "CI had been red on `main` since April" — pandera 0.31 drift + an unguarded CSV-dependent test; fixed, green for the first time in ~2 months [Fact — wrap log `docs/session-logs/2026-05-30-cde-phase4-docs-ci-green.md`]
- **Tradeoff:** dbt floor bumped 1.7 → 1.10 to keep the dependency contract honest, dropping 1.7–1.9 support [Fact — PR #2 body]

## Era: Production-shaping & three-star expansion (2026-06)

One week (June 5–7) transformed the single-star demo into a three-source dimensional warehouse with production mechanics, then documented it.

### Incremental models, idempotent upserts & SCD2 history — 2026-06-05
- **Landed:** `ON CONFLICT` upsert loader, incremental `int_claims_enriched`/`fct_claims`, `snap_provider_fraud` snapshot → `dim_provider_history`, orchestration reordered ingest → snapshot → run → test → validate (PR #4)
- **Why:** replace naive DROP+reload with "the two analytics-engineering mechanics interviews probe most — incremental materializations and SCD Type 2 snapshots" [Fact — PR #4 body] — see D5, D7 in `Decisions.md`
- **Tradeoff:** single-vintage source data, so incrementality/SCD2 are demonstrated with deterministic seeded inputs, framed explicitly as demos rather than faked CDC [Fact — PR #4 body]

### Diabetes readmission as a second star — 2026-06-05
- **Landed:** UCI diabetes dataset (101,766 encounters) wired through pandera → upsert → `fct_encounters` + `dim_patient` + seed-backed `dim_admission_type`; first use of `dbt/seeds/` (PR #5, stacked on PR #4)
- **Why:** make the "multi-source" claim real; two independent stars with no forced join is "the honest representation of multi-source" [Fact — PR #5 body] — see D4, D10 in `Decisions.md`

### Repo-specific Claude Code tooling — 2026-06-05
- **Landed:** vendored commands/skills, `new-dbt-model` + `add-source` skills, dbt/SQL reviewer subagents, ruff + `dbt parse` hooks, postgres/dbt MCP servers (PR #6)
- **Why:** make the repo's conventions enforceable and cloud-session-usable [Inference — PR #6 body describes the setup, not the motive]

### Synthetic hospital admissions as a third star — 2026-06-06
- **Landed:** third source (5,000 admissions) as `fct_hospital_admissions` + `dim_hospital_patient` + seed-backed `dim_severity`; incremental boundary switched `NOT IN` → `NOT EXISTS` across all four incremental models after a >14-min hang became a ~59s no-op (PR #7)
- **Why:** prove the ingest → validate → stage → model pattern generalizes [Fact — PR #7 body]; the source had no usable primary key, forcing a minted surrogate — see D8, D6 in `Decisions.md`

### Tier 3 docs — ADR directory & data dictionary — 2026-06-07
- **Landed:** 10 numbered ADRs under `docs/adr/` + index/template, column-level `docs/data-dictionary.md` across all three stars, full intermediate-model column coverage; drained the last open BACKLOG item (PR #8)
- **Why:** structure the prose in PROJECT_GUIDE.md into "discrete, skimmable records" [Fact — PR #8 body] — these ADRs are the source records behind D1–D10 in `Decisions.md`

## Era: Maintenance — tooling & knowledge layer (2026-06 – 2026-07)

Build work complete; subsequent changes keep the repo's agent tooling and knowledge layer current.

### Tooling upkeep — 2026-06-18 / 2026-07-18
- **Landed:** operating constraints vendored for cloud sessions (PR #9); fleet-wide `/claudify-repo` sweep vendoring all missing global commands/skills (PR #10)
- **Why:** part of a fleet-wide standardization of Claude Code tooling across projects [Fact — PR #10 body]

### Project wiki initialized — 2026-07-26
- **Landed:** PROJECT.md, HANDOFF.md, Sources.md, Decisions.md (D1–D11), `Wiki/_index.md` + `Wiki/Pipeline-Architecture.md`, CLAUDE.md wiki section (PR #11)
- **Why:** compiled knowledge layer with the ADR directory remaining the source of truth [Fact — PR #11 body] — see D11 in `Decisions.md`

---

## Mining coverage
_Backfilled 2026-07-26 by project-wiki BACKFILL. Entries after this date are
appended live by MAINTAIN._
- PR title sweep: all 11 merged PRs — no cap
- Deep reads: 9 of 11 PRs (#1, #2, #4, #5, #6, #7, #8, #10, #11 — size/label/title signal; cap 20)
- Also swept: git log (merges/no-merges), tags (none exist), wrap logs (`docs/session-logs/` ×2), ADRs (`docs/adr/` 001–010 via the `Decisions.md` ledger)
- Not mined: closed-unmerged PRs, issues
