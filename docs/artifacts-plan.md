# Engineering Artifact Audit & Generation Plan
> Generated: 2026-05-30 | Repo: clinical-data-etl | Status: Plan only — no artifacts generated yet

## Project Profile
PROJECT PROFILE
- Shape: data pipeline
- Primary language(s): Python 3.11+, SQL (dbt)
- Stack: pandas 2.x, pandera 0.18+, SQLAlchemy 2.x, psycopg2-binary, Prefect 2.x, python-dotenv, dbt-core 1.7+, dbt-postgres 1.7+, pytest 8.x, ruff 0.3+, mypy 1.9+ (strict), Docker (PostgreSQL 16), GitHub Actions CI
- Datastores: PostgreSQL 16 (Docker), 4 schemas: raw / staging / intermediate / marts; no cloud datastore
- Deployment / orchestration: Local only — Docker Compose for Postgres, Prefect 2.x flow (`clinical-data-etl-pipeline`) in `src/clinical_data_etl/orchestration/flows.py` + `tasks.py`; `make pipeline` as the primary entry point; no cloud deployment configured
- Audience: portfolio
- Maturity: maintenance (MVP complete since 2026-04-04; no commits since)
- Team size: solo (ksdisch, all commits co-authored with Claude Code)
- Active areas (from recent git): Nothing actively changing. Last two commits (2026-04-04) were CI green-up fixes — skipping CSV-dependent tests, adding pip cache, ruff format compliance. The repo has been dormant for ~56 days.
- Existing docs/diagrams:
  - `/README.md` — quickstart, ASCII architecture diagram, ASCII star-schema ERD, Makefile target table; quality 4/5; current but thin
  - `/PROJECT_GUIDE.md` — deep portfolio narrative, Mermaid architecture diagram, annotated key flows, full commit chronology, user guide with troubleshooting; quality 5/5; current but **UNTRACKED (never committed to git)**
  - `/CLAUDE.md` — AI working context document; quality 4/5; mostly current with two known stale items (`int_claims_joined` should be `int_claims_unified`; `tasks.py` missing from folder listing)
  - `.github/workflows/ci.yml` — three-job CI (lint/typecheck/test); quality 5/5; current
  - `.github/workflows/claude.yml` — @claude PR comment handler; quality 4/5; current
  - `.github/workflows/claude-code-review.yml` — auto PR code review via Claude Code plugin; quality 3/5; current but undocumented plugin dependency
  - `dbt/models/staging/src_raw.yml` — dbt source declarations; quality 3/5; no descriptions or freshness checks
  - `dbt/models/staging/schema.yml` — staging model tests and descriptions; quality 4/5; sparse column coverage
  - `dbt/models/intermediate/schema.yml` — intermediate model tests; quality 4/5; minor
  - `dbt/models/marts/schema.yml` — mart model tests with severity:warn on orphan beneficiary relationship; quality 4/5; aggregate columns undescribed
- Notable gaps observed:
  - `PROJECT_GUIDE.md` exists only on disk — never committed; any git clone or CI run would not have it
  - `CLAUDE.md` names `int_claims_joined` in the architecture diagram but the actual model is `int_claims_unified`
  - No CI badge in README
  - Kaggle slug discrepancy between README (`amulyas/synthetic-hospital-data`) and CLAUDE.md (`amulyas/synth-hospital-data`) — one is wrong
  - `make setup` uses `python3.12` explicitly but README says `python -m venv .venv` (implies any Python)
  - CI pipeline skips CSV-dependent tests entirely because raw Kaggle data is not checked in — the pipeline is not end-to-end testable in GitHub Actions
  - No dbt CI job (dbt models/tests not run in CI)
  - No `data/rejected/` quarantine directory mentioned in README
  - `conftest.py` is empty — no shared pytest fixtures
  - `dim_provider` and `dim_beneficiary` aggregate/chronic-condition columns lack dbt column descriptions
  - No dbt source freshness checks defined
- 3 sharpest open questions before recommending confidently:
  1. **Is PROJECT_GUIDE.md intentionally untracked, or was it accidentally omitted from commits?** If it should be committed, doing so is the single highest-leverage action — it transforms a disk artifact into a durable portfolio asset.
  2. **What is the intended audience interaction with this repo?** If a hiring manager will clone and run it, the README's Python version ambiguity (`python` vs `python3.12`) and the missing Kaggle data download instructions are blockers. If it is review-only (GitHub browse), those gaps matter less.
  3. **Should the CLAUDE.md stale references (`int_claims_joined`, missing `tasks.py`) be corrected now, or is CLAUDE.md treated as a living document that gets updated per-session?** The answer determines whether a one-time fix commit is warranted or whether this is expected drift.

---

DISCOVERY SUMMARY

The clinical-data-etl project is a solo portfolio pipeline that reached MVP in a single day (2026-04-02) and has been dormant since a CI fix on 2026-04-04. The most consequential architectural decision is the ETL-not-ML framing of the Medicare fraud dataset: train and test CSV splits are merged at ingestion time, with the missing `PotentialFraud` column on the test provider split patched inline before pandera validation, rejected rows quarantined to `data/rejected/`, and the clean subset loaded into PostgreSQL via DROP CASCADE (intentionally tearing down dependent dbt views). The dbt layer follows a strict star schema with fraud label deliberately kept in `dim_provider` rather than denormalized onto `fct_claims`, and the 30 beneficiary rows rejected by pandera result in 88 orphan claims that are handled as a `severity: warn` in the marts schema test rather than a pipeline failure. The most critical gap is that `PROJECT_GUIDE.md` — the highest-quality documentation artifact in the repo — has never been committed to git, making it invisible to anyone who clones the repository. Documentation quality is otherwise strong, with the primary maintenance burden being the stale `int_claims_joined` reference in CLAUDE.md and the absence of a CI badge or dbt CI job wiring that would make the pipeline's health visible at a glance.

---

## Phase 3 — Artifact Audit

No repo-root LICENSE file. Now I have everything needed to produce the full audit table.

| Category | Artifact | Status | Location | Justification / Evidence |
|---|---|---|---|---|
| **REPO HYGIENE** | README.md | ✅ PRESENT | `/README.md` | 197 lines; covers quickstart, ASCII architecture diagram, ASCII star-schema ERD, prerequisites, Makefile targets table, tech stack. Quality 4/5. Minor gaps: no CI badge, Kaggle slug discrepancy (`amulyas/synthetic-hospital-data` vs CLAUDE.md `amulyas/synth-hospital-data`), Python version ambiguity (`python` vs `python3.12` in Makefile). |
| **REPO HYGIENE** | CONTRIBUTING.md | ⛔ NOT APPLICABLE | — | Solo portfolio repo (one contributor, ksdisch, all 8 commits). No external contributors anticipated. |
| **REPO HYGIENE** | CODE_OF_CONDUCT.md | ⛔ NOT APPLICABLE | — | Solo portfolio project, not an open-source community project. No issue/PR participation from third parties. |
| **REPO HYGIENE** | LICENSE | 🟢 RECOMMENDED | — | No LICENSE file at repo root (only `.venv` dependency licenses exist). Portfolio repos are public on GitHub; without a license, code is technically all-rights-reserved, which can confuse hiring reviewers who want to run or fork it. A permissive MIT or Apache-2.0 license takes 30 seconds and sends the right signal for a portfolio asset. |
| **REPO HYGIENE** | CHANGELOG.md | 🟡 OPTIONAL | — | The git log is small (8 commits, all 2026-04-02 to 04-04), the project is dormant, and PROJECT_GUIDE.md already contains a full commit chronology with milestone summaries. A separate CHANGELOG would duplicate that. Low leverage. |
| **REPO HYGIENE** | .env.example | ✅ PRESENT | `/.env.example` | 6 variables (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DATABASE_URL`). Defaults match `docker-compose.yml` and `dbt/profiles.yml` exactly. Quality 5/5. |
| **REPO HYGIENE** | PR/issue templates | 🟡 OPTIONAL | — | Solo portfolio repo with no open PRs or issues. The existing `claude.yml` / `claude-code-review.yml` GitHub Actions cover automated review on any future PRs. Templates add friction without benefit for a one-person project. |
| **REPO HYGIENE** | Makefile / Taskfile / justfile | ✅ PRESENT | `/Makefile` | Covers `setup`, `download-data`, `db-up`, `db-down`, `test`, `lint`, `pipeline`, `pipeline-ingest`, `pipeline-dbt`. Matches the Makefile target table in README exactly. One minor gap: `test` calls bare `pytest` instead of `.venv/bin/pytest`, relying on an activated venv. |
| **DECISION & DESIGN** | ADRs (Architecture Decision Records) | ⚠️ STALE/THIN | `CLAUDE.md` § "Architectural Decisions", `PROJECT_GUIDE.md` § "Decisions & Tradeoffs" | The decisions are documented in narrative prose (ETL-not-ML framing, fraud label in `dim_provider` not `fct_claims`, DROP CASCADE rationale, Train/Test merge, 30-row pandera rejects as warn not error) but are spread across two files and not structured as discrete numbered records. PROJECT_GUIDE.md is also untracked. For a portfolio context, the prose form is adequate if PROJECT_GUIDE.md is committed — no formal ADR directory needed. Upgrading to ⚠️ because the best decision doc (PROJECT_GUIDE.md) is not in git. |
| **DECISION & DESIGN** | Design Doc / Tech Spec | ✅ PRESENT | `/PROJECT_GUIDE.md` (untracked) | 433-line document covering architecture, key flow walkthroughs, annotated code references, environment config table, and full decisions & tradeoffs section. Quality 5/5. **Critical gap: file is untracked (`??` in git status) — invisible to anyone who clones the repo.** Committing it is the single highest-leverage action in this audit. |
| **DECISION & DESIGN** | PRD (Product Requirements Doc) | ⛔ NOT APPLICABLE | — | Portfolio project, not a product with stakeholders or user stories. The project purpose is clearly defined in CLAUDE.md ("showcase: multi-source ETL design, data quality validation, dimensional modeling, workflow orchestration"). |
| **DECISION & DESIGN** | Postmortem / RCA template | ⛔ NOT APPLICABLE | — | No production incidents, no on-call, solo project. |
| **PLANNING** | Roadmap (now/next/later) | ⚠️ STALE/THIN | `README.md` § "Phase 2", `CLAUDE.md` § "Current Priority" | Phase 2 (diabetes readmission dataset) is mentioned in both files but there is no structured now/next/later breakdown, no acceptance criteria for Phase 2 items, and no indication of when/whether they will be built. Given the repo has been dormant 56 days, a one-paragraph roadmap section in README noting "MVP complete; Phase 2 deferred" would be more honest than leaving dangling Phase 2 bullets. |
| **PLANNING** | BACKLOG.md or external tracker | 🟡 OPTIONAL | — | Portfolio project with a complete MVP. No active sprint, no team, no tracker needed. The Phase 2 dataset directories (`data/raw/diabetes_readmission/`, `data/raw/synthetic_hospital/`) exist on disk and imply future work, but there's no urgency to formalize a backlog. |
| **PLANNING** | Sprint plan / WBS | ⛔ NOT APPLICABLE | — | Solo developer, no team coordination needed. MVP built in a single day. |
| **DIAGRAMS** | C4 Context diagram | 🟡 OPTIONAL | — | Overkill for a local-only pipeline with no external users, no API consumers, and no cloud services. The ASCII architecture diagram in README and the Mermaid flowchart in PROJECT_GUIDE.md together cover the context adequately. |
| **DIAGRAMS** | C4 Container diagram | 🟡 OPTIONAL | — | Same rationale as C4 Context. The system has only two runtime containers (Python process + PostgreSQL via Docker Compose); both are fully described in README and PROJECT_GUIDE.md already. |
| **DIAGRAMS** | C4 Component diagram | ⛔ NOT APPLICABLE | — | The codebase is small (4 Python modules + dbt models). The folder structure in CLAUDE.md and the key flow walkthroughs in PROJECT_GUIDE.md cover component responsibilities more usefully than a UML component diagram would. |
| **DIAGRAMS** | Sequence diagram (pipeline flow) | ✅ PRESENT | `/PROJECT_GUIDE.md` § "Key Flows" (untracked) | PROJECT_GUIDE.md contains four annotated prose + Mermaid flow walkthroughs: end-to-end pipeline, provider ingestion with missing-column patch, raw→marts dbt layer, failure handling. Serves the same purpose as a sequence diagram with more context. Gap: file is untracked. |
| **DIAGRAMS** | Flowchart (data flow) | ✅ PRESENT | `/README.md` (ASCII), `/PROJECT_GUIDE.md` (Mermaid, untracked) | README has an ASCII architecture diagram matching the actual pipeline stages (CSV → Ingestion → PostgreSQL raw → dbt staging/intermediate/marts → Prefect). PROJECT_GUIDE.md has a richer Mermaid flowchart. |
| **DIAGRAMS** | State machine | ⛔ NOT APPLICABLE | — | No stateful entity with meaningful state transitions. Prefect flow states (pending/running/completed/failed) are Prefect's built-in concern and do not need a custom state diagram. |
| **DIAGRAMS** | ERD (entity-relationship) | ✅ PRESENT | `/README.md` § "Star Schema ERD" | ASCII ERD showing `fct_claims` at center with FK relationships to `dim_beneficiary` (BeneID), `dim_provider` (Provider), plus the 88-orphan warn note. Accurate against the actual mart models. Could be enriched with column listings but is adequate for portfolio purposes. |
| **DIAGRAMS** | Data lineage diagram | 🟢 RECOMMENDED | — | `dbt docs generate` produces an interactive lineage DAG at zero cost — run `dbt docs generate && dbt docs serve` and the graph is available. README mentions dbt but never mentions `dbt docs`. Adding a `make dbt-docs` target and a screenshot or link would directly address a common DE/AE interview question ("how do you document your lineage?"). Evidence: 9 dbt models across 3 layers with cross-layer `ref()` dependencies that are already compiled in `dbt/target/` — the lineage graph already exists, just unexposed. |
| **DIAGRAMS** | Dimensional model / star schema diagram | ✅ PRESENT | `/README.md` § "Star Schema ERD" | Present as ASCII art. Covers grain, FK relationships, and the fraud label placement decision. Quality 3/5 — no column listings, no data types. Adequate for portfolio browsing. |
| **DIAGRAMS** | Pipeline/DAG diagram | ✅ PRESENT | `/README.md` (ASCII), `/PROJECT_GUIDE.md` (Mermaid, untracked) | Pipeline stages are diagrammed in both files. The Prefect flow DAG (4 tasks: ingest → dbt run → dbt test → validate marts) is described in PROJECT_GUIDE.md § "End-to-End Pipeline Flow". |
| **DIAGRAMS** | Network/topology diagram | ⛔ NOT APPLICABLE | — | Single-host local deployment. Docker Compose runs one container (`clinical_etl_db`) on localhost:5432. No network topology worth diagramming. |
| **DIAGRAMS** | Wireframes/mockups | ⛔ NOT APPLICABLE | — | No UI. CLI and Makefile entry points only (`python -m clinical_data_etl`, `make pipeline`). |
| **OPS & RELIABILITY** | Runbook (setup/teardown/deploy) | ✅ PRESENT | `/README.md` § Quick Start, `/PROJECT_GUIDE.md` § User Guide (untracked) | README covers: prerequisites, venv setup, `pip install -e ".[dev]"`, `.env` copy, `make db-up`, `make pipeline`. PROJECT_GUIDE.md adds env-var table, all Makefile targets with descriptions, usage examples (`--ingest-only`, `--dbt-only`, `--full`), and a troubleshooting section. Minor gap: README's `python -m venv .venv` conflicts with Makefile's hardcoded `python3.12`. |
| **OPS & RELIABILITY** | Playbook (incident scenarios) | ⛔ NOT APPLICABLE | — | Local-only portfolio project. No production environment, no incident management needed. |
| **OPS & RELIABILITY** | Postmortem template | ⛔ NOT APPLICABLE | — | No production incidents possible; solo, local-only project. |
| **OPS & RELIABILITY** | SLI/SLO/SLA doc | ⛔ NOT APPLICABLE | — | No service, no uptime commitment, no production users. |
| **OPS & RELIABILITY** | On-call / escalation doc | ⛔ NOT APPLICABLE | — | Solo portfolio project. |
| **KNOWLEDGE** | Onboarding doc | ⚠️ STALE/THIN | `/README.md` § Prerequisites + Setup | README covers happy-path setup but has two gaps that would block a reviewer trying to clone and run: (1) no Kaggle data download instructions beyond `make download-data` (the Kaggle CLI must be configured with an API token, which is not mentioned); (2) the Python version ambiguity (`python` in README, `python3.12` in Makefile) would cause a silent failure on machines where `python3.12` is not on `$PATH`. PROJECT_GUIDE.md fixes both but is untracked. |
| **KNOWLEDGE** | API docs | ⛔ NOT APPLICABLE | — | No HTTP API. The project exposes only a Python CLI (`python -m clinical_data_etl`) and Makefile targets, both fully documented in README and PROJECT_GUIDE.md. |
| **KNOWLEDGE** | Data dictionary | 🟢 RECOMMENDED | — | The Medicare claims fraud dataset has non-obvious column names (`BeneID`, `ClmAdmitDiagnosisCode`, `ClmProcedureCode_1`–`_6`, `ChronicCond_Alzheimer`–`ChronicCond_HeartFailure`, `IPAnnualReimbursementAmt`) that are not described in any dbt schema YAML beyond a handful of key columns. `dbt/models/marts/schema.yml` has no descriptions for `dim_provider` aggregate columns (`total_claims`, `total_reimbursement`) and `dim_beneficiary` chronic condition flag columns (11 of them). A data dictionary — even a `dbt/models/marts/schema.yml` column description pass — would directly answer "what does this data mean?" for any hiring reviewer who opens the repo. Evidence: marts/schema.yml confirmed to have undescribed aggregate and chronic-condition columns. |
| **KNOWLEDGE** | Glossary | 🟡 OPTIONAL | — | The domain terms (BeneID, inpatient vs outpatient, PotentialFraud, reimbursement) are standard Medicare/CMS terminology. A glossary would be helpful but is low-leverage compared to the data dictionary gap above. PROJECT_GUIDE.md provides enough inline context for the key decisions. |

---

## Phase 4 — Generation & Maintenance Plan

Now I have everything needed. Here is the complete Phase 4 plan.

---

# Phase 4: Documentation Generation & Maintenance Plan
## clinical-data-etl

---

## Component 1: Priority Order

### Tier 1 — This Week (High leverage, low effort, highest credibility impact)

**1. Commit `PROJECT_GUIDE.md`** — It is the single best documentation artifact in the repo and is completely invisible to anyone who clones it. A hiring manager who finds it on disk by accident is a hiring manager who almost missed it. One `git add PROJECT_GUIDE.md && git commit` turns a disk artifact into a durable portfolio signal. Zero writing required.

**2. Fix stale references in `CLAUDE.md`** — `int_claims_joined` appears in the architecture diagram but the actual model is `int_claims_unified` (confirmed in `dbt/models/intermediate/schema.yml`). `tasks.py` is listed in the orchestration module description but is present on disk — needs verification and either addition or removal. These stale references undermine trust in the document that Claude Code uses as working context. Low effort, high trust cost if left broken.

**3. Add CI badge to `README.md`** — One line of Markdown. Hiring reviewers look at the badge first. The CI workflow is already green (three-job pipeline: lint/typecheck/test). The badge URL is deterministic from the repo slug. Effort: 5 minutes.

**4. Fix `README.md` / `Makefile` Python version ambiguity** — `README.md` says `python -m venv .venv` but `Makefile` hardcodes `python3.12`. On a machine where only `python3.11` is installed, `make setup` silently fails with "python3.12: command not found". The fix is to change the Makefile to `python3` (or add a note in README). Effort: 10 minutes.

**5. Add `LICENSE` (MIT)** — No license file exists. Public GitHub repos without a license are technically all-rights-reserved. A hiring reviewer who wants to run or fork it may hesitate. MIT takes 30 seconds and removes the ambiguity. One file, no decisions beyond the license choice.

---

### Tier 2 — This Month (Medium leverage, worth scheduling)

**6. Add column descriptions to `dbt/models/marts/schema.yml`** — `dim_provider`'s aggregate columns (`total_claims`, `total_reimbursement`, `unique_beneficiaries`, `avg_reimbursement_per_claim`) and `dim_beneficiary`'s 11 chronic condition flag columns have no descriptions. An analytics engineer who opens the dbt docs and sees undescribed columns in the marts layer signals incomplete work. The pandera `schemas.py` already names all 11 `ChronicCond_*` columns — the descriptions can be derived directly from those names. Effort: M.

**7. Enrich `dbt/models/staging/src_raw.yml`** with source descriptions and freshness checks — The file has 4 table entries with no descriptions, no column documentation, no `loaded_at_field`, and no `freshness` block. For a portfolio repo that claims to demonstrate "data quality validation," the source layer being entirely undescribed is a visible gap. Effort: S.

**8. Add `make dbt-docs` target + screenshot** — `dbt docs generate && dbt docs serve` produces an interactive lineage DAG that directly answers the AE interview question "how do you document your lineage?" The graph already exists in `dbt/target/` — it just needs to be exposed. A single screenshot committed to `docs/images/dbt-lineage.png` and referenced in `README.md` makes this concrete to a viewer who won't run the pipeline locally. Effort: S for the Makefile target; M for screenshot capture and README section.

**9. Update `README.md` Phase 2 section to be honest about status** — Currently implies Phase 2 is coming. The repo has been dormant 56 days. Replace "Phase 2 Extensions" with a "Roadmap" section that says "MVP complete as of 2026-04-04; Phase 2 deferred." This is accurate and less misleading than presenting aspirational items as planned work. Effort: S.

**10. Clarify Kaggle CLI credential setup in `README.md`** — The setup instructions say `make download-data` but do not mention that the Kaggle CLI requires a `~/.kaggle/kaggle.json` API token file. A reviewer cloning cold will hit an authentication error. One sentence and a link to the Kaggle API docs page fixes this. Effort: S.

---

### Tier 3 — Nice to Have (Low urgency, do if Phase 2 activates)

**11. Structured ADR directory (`docs/adr/`)** — The key decisions (ETL-not-ML framing, DROP CASCADE rationale, fraud label in `dim_provider`, 30-row beneficiary rejects as warn) are documented in `PROJECT_GUIDE.md` but not as discrete records. This matters more if Phase 2 introduces new decisions that conflict with Phase 1 choices. Convert the existing decision prose to 3–4 numbered ADR files when Phase 2 begins.

**12. Data dictionary (`docs/data-dictionary.md`)** — A column-level reference for the Medicare claims columns that have non-obvious names (`ClmAdmitDiagnosisCode`, `IPAnnualReimbursementAmt`, `RenalDiseaseIndicator`, etc.). The pandera `schemas.py` and dbt YAML already contain most of this in machine-readable form — a data dictionary would synthesize it into a human-readable reference. Worth doing when the repo is used in interviews where a viewer will ask "what does this column mean?"

**13. `dbt/models/intermediate/schema.yml` column coverage expansion** — `int_claims_enriched` has column descriptions for `claim_id` and `age_at_claim` but not the 11 chronic condition flag columns carried through from `stg_beneficiary`. Low urgency since intermediate models are not the primary analytics interface.

---

## Component 2: Per-Artifact Details

### 1. Commit `PROJECT_GUIDE.md`

- **Target path**: `/PROJECT_GUIDE.md` (already on disk, just untracked)
- **Format**: Markdown (already written, no new content needed)
- **Effort**: S (git add + commit only)
- **Dependencies**: None — file exists and is complete
- **Key content already present**:
  - Mermaid architecture flowchart and annotated key flows (4 walkthroughs)
  - Full decisions & tradeoffs section covering ETL-not-ML framing, DROP CASCADE, fraud label placement, 30-row pandera reject handling
  - Complete Makefile target reference with usage examples and `--ingest-only` / `--dbt-only` / `--full` flags
  - Troubleshooting section covering common Docker and dbt connection errors

### 2. Fix stale references in `CLAUDE.md`

- **Target path**: `/CLAUDE.md`
- **Format**: Markdown (edit only)
- **Effort**: S
- **Dependencies**: Verify `tasks.py` presence on disk at `src/clinical_data_etl/orchestration/` — if absent from the folder listing, add it; if present, remove the gap note
- **Key content to correct**:
  - Replace `int_claims_joined` with `int_claims_unified` in the architecture diagram and Data Flow section (confirmed name from `dbt/models/intermediate/schema.yml` line 4)
  - Add `tasks.py` to the orchestration module listing if it exists on disk
  - Confirm the `data/rejected/` directory is mentioned (it exists: `data/rejected/beneficiary_rejected.csv`, `inpatient_claims_rejected.csv`, `test_providers_rejected.csv`)

### 3. CI badge in `README.md`

- **Target path**: `/README.md` (line 3, after the intro paragraph)
- **Format**: Markdown badge (one line)
- **Effort**: S
- **Dependencies**: CI workflow must be passing (it is, per recent commits)
- **Key content**:
  - Badge URL: `[![CI](https://github.com/ksdisch/clinical-data-etl/actions/workflows/ci.yml/badge.svg)](https://github.com/ksdisch/clinical-data-etl/actions/workflows/ci.yml)`
  - Place immediately after the project description sentence, before the Architecture section

### 4. `README.md` Python version fix + Kaggle credential note

- **Target path**: `/README.md` (Setup section); `/Makefile` (line 4)
- **Format**: Markdown + Makefile
- **Effort**: S
- **Dependencies**: None
- **Key content**:
  - Change `Makefile` line 4 from `python3.12 -m venv .venv` to `python3 -m venv .venv` (or `python3.11`)
  - Change `README.md` manual venv instruction to match: `python3 -m venv .venv`
  - Add one-liner before `make download-data`: "Requires Kaggle CLI credentials: copy your `kaggle.json` API token to `~/.kaggle/kaggle.json` (see [Kaggle API docs](https://github.com/Kaggle/kaggle-api#api-credentials))"
  - Resolve slug discrepancy: `README.md` uses `amulyas/synthetic-hospital-data`; `CLAUDE.md` uses `amulyas/synth-hospital-data`; the `Makefile` uses `amulyas/synthetic-hospital-data` — verify which is the correct Kaggle dataset slug and use it consistently in all three files

### 5. `LICENSE` (MIT)

- **Target path**: `/LICENSE`
- **Format**: Plain text (MIT license boilerplate)
- **Effort**: S
- **Dependencies**: Confirm the license choice (MIT is appropriate for a portfolio project)
- **Key content**:
  - Standard MIT text with `Copyright (c) 2026 ksdisch`
  - No modifications needed

### 6. Column descriptions in `dbt/models/marts/schema.yml`

- **Target path**: `/dbt/models/marts/schema.yml`
- **Format**: YAML
- **Effort**: M (writing descriptions for ~20 columns across 3 models)
- **Dependencies**: `schemas.py` for canonical column names and semantics; `dbt/models/marts/` SQL files for the actual SELECT columns
- **Key content**:
  - `dim_provider`: Add descriptions for `total_claims` ("Count of distinct claims linked to this provider"), `total_reimbursement` ("Sum of reimbursement_amount across all linked claims"), `unique_beneficiaries` ("Count of distinct beneficiaries who had a claim with this provider"), `avg_reimbursement_per_claim` ("total_reimbursement / total_claims")
  - `dim_beneficiary`: Add descriptions for all 11 `has_*` chronic condition flag columns (derived from `ChronicCond_*` in `schemas.py`: `has_alzheimers`, `has_heart_failure`, `has_kidney_disease`, `has_cancer`, `has_obstr_pulmonary`, `has_depression`, `has_diabetes`, `has_ischemic_heart`, `has_osteoporasis`, `has_rheumatoid_arthritis`, `has_stroke`) — note that value 1 = condition present, 2 = condition absent (from `pa.Check.isin([1, 2])` in `schemas.py`)
  - `fct_claims`: Add descriptions for `claim_type` ("'inpatient' or 'outpatient' — source table indicator"), `age_at_claim` ("Beneficiary age in whole years at claim_start_date, computed in int_claims_enriched"), `admission_date` and `discharge_date` ("NULL for outpatient claims")

### 7. Enrich `dbt/models/staging/src_raw.yml`

- **Target path**: `/dbt/models/staging/src_raw.yml`
- **Format**: YAML
- **Effort**: S
- **Dependencies**: None (content derivable from CLAUDE.md data sources table)
- **Key content**:
  - Add `description` to the `raw` source: "Medicare claims fraud detection data ingested from Kaggle (rohitrox/healthcare-provider-fraud-detection-analysis). Train and test CSV splits merged at ingestion time."
  - Add `description` to each table: `beneficiary` ("Medicare beneficiary demographics including chronic condition flags and reimbursement totals. 138K rows from merged train/test splits."), `inpatient_claims` ("Inpatient claim records with admission/discharge dates, diagnosis and procedure codes. ~558K rows."), `outpatient_claims` ("Outpatient claim records. Same structure as inpatient minus admission dates. ~150K rows."), `providers` ("Provider list with fraud label. Test split providers have NULL fraud label.")
  - Do NOT add `freshness` checks — the data is batch-loaded via `make pipeline`, not streamed; freshness checks would always fail in CI since the raw data is not checked in

### 8. `make dbt-docs` target + `docs/images/` screenshot

- **Target path**: `/Makefile` (new target); `/docs/images/dbt-lineage.png` (new file); `/README.md` (new section)
- **Format**: Makefile target + PNG + Markdown
- **Effort**: M
- **Dependencies**: PostgreSQL must be running; data must have been ingested at least once (so dbt compile has a manifest)
- **Key content**:
  - Makefile target: `dbt-docs: \n\tcd dbt && dbt docs generate && dbt docs serve`
  - Also add `make dbt-compile` target: `cd dbt && dbt compile` — useful for validating SQL without running the pipeline
  - README section "Data Lineage" after the Star Schema ERD: one sentence + embedded screenshot at `docs/images/dbt-lineage.png` showing the 9-model DAG (4 staging → 2 intermediate → 3 mart models)
  - Screenshot must show the full 3-layer fan-in from `stg_*` through `int_claims_unified` → `int_claims_enriched` → `fct_claims`, and the direct staging→mart paths for `dim_beneficiary` and `dim_provider`

### 9. `README.md` Phase 2 / Roadmap section update

- **Target path**: `/README.md` (replace "Phase 2 Extensions" section)
- **Format**: Markdown
- **Effort**: S
- **Dependencies**: None
- **Key content**:
  - Section title: "## Roadmap"
  - "MVP complete as of April 2026. The pipeline ingests 848K rows end-to-end in ~36 seconds, passes 34 pytest tests and 28 dbt tests."
  - "Phase 2 (deferred): integrate the diabetes readmission dataset (`brandao/diabetes`, 70K encounters, 55 features) as a second fact table. The raw directory placeholder (`data/raw/diabetes_readmission/`) is already in place."
  - Remove the synthetic hospital bullet or move it to a "development utilities" note — it is a test fixture, not a real data source

---

## Component 3: Maintenance Cadence

### Per-PR triggers
Any PR that touches files in the categories below should update the corresponding artifacts before merge.

| Change type | Artifacts to update |
|---|---|
| New or renamed dbt model | `dbt/models/*/schema.yml` (add model entry + columns), `CLAUDE.md` architecture diagram, `README.md` architecture ASCII if a layer changes |
| New pandera schema column | Corresponding `dbt/models/staging/schema.yml` column entry; `docs/data-dictionary.md` if it exists |
| New Makefile target | `README.md` Makefile Targets table |
| New Python module or renamed file | `CLAUDE.md` Folder Structure section |
| New dbt test (schema or custom) | No artifact update required — tests are self-documenting via `dbt test` output |
| New ingestion table (Phase 2) | `dbt/models/staging/src_raw.yml` (new source table), `CLAUDE.md` Data Sources table, `README.md` Architecture diagram |

### Per-release triggers
This repo has no formal releases (no `git tag`, no versioned deployments). If a GitHub release is ever created (e.g., to mark Phase 2 completion), at that point:
- `PROJECT_GUIDE.md` commit chronology section gets a new entry
- `README.md` Phase 2 status note gets updated
- `CLAUDE.md` "Current Priority" section gets refreshed

### Per-significant-decision triggers
Any decision that changes the schema, the rejection behavior, or the mart grain must update:
- `CLAUDE.md` "Architectural Decisions" section (the `severity: warn` 30-row reject policy, the DROP CASCADE approach, the fraud label placement — if any of these change, the doc must change)
- `PROJECT_GUIDE.md` "Decisions & Tradeoffs" section
- If an ADR directory exists by then, a new numbered ADR file

### Per-incident triggers
Not applicable for a local-only portfolio project. No production incidents possible. If the pipeline is ever deployed to a cloud environment (Prefect Cloud, Airflow on GCP, etc.), incident triggers would apply.

### Quarterly review
The repo is dormant. The sole maintenance check that matters on a quarterly cadence is:
- Verify that the GitHub Actions CI badge is still green (dependency versions in `pyproject.toml` do not drift past compatibility)
- Check whether any Kaggle dataset slugs have changed (datasets occasionally get retired or re-uploaded under new slugs — the `rohitrox/healthcare-provider-fraud-detection-analysis` slug has been stable since 2019 but is worth verifying once before the next active session)
- Confirm `dbt-core` and `dbt-postgres` minor version pins are consistent with each other (they must match major.minor)

### Schema-change triggers (dbt + PostgreSQL specific)
This repo uses DROP CASCADE on the `raw` schema during ingestion. Any change to the raw table columns propagates automatically to all downstream dbt views via recompilation. However, these artifacts require manual updates when raw schema changes:

| Schema change | Artifacts requiring update |
|---|---|
| New column added to raw table | `dbt/models/staging/src_raw.yml` (add column entry), staging model SQL (SELECT or `*`), `dbt/models/staging/schema.yml` (add column description + tests if applicable) |
| Column renamed in raw table | pandera schema in `schemas.py`, staging model SQL alias, all downstream `ref()` usages if column propagates to intermediate/marts |
| New raw table added (Phase 2) | `src_raw.yml` new table entry, new `stg_*` model + schema.yml entry, `CLAUDE.md` data flow section, `README.md` architecture diagram |
| Mart column added | `dbt/models/marts/schema.yml` column description, `README.md` Star Schema ERD if it changes the visible grain |

---

## Component 4: Suggested Automation

### GitHub Actions — add to existing CI

**New job: `dbt-compile` (add to `ci.yml`)**

Add a fourth job that validates dbt model SQL without requiring data. This uses `dbt compile` against the PostgreSQL service that is already wired in the `test` job.

```yaml
dbt-compile:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16
      env:
        POSTGRES_DB: clinical_etl
        POSTGRES_USER: etl_user
        POSTGRES_PASSWORD: etl_pass
      ports:
        - 5432:5432
      options: >-
        --health-cmd "pg_isready -U etl_user -d clinical_etl"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: "pip"
    - run: pip install dbt-postgres>=1.7,<2.0
    - name: dbt compile
      working-directory: dbt
      env:
        DBT_PROFILES_DIR: .
        POSTGRES_HOST: localhost
        POSTGRES_PORT: 5432
        POSTGRES_DB: clinical_etl
        POSTGRES_USER: etl_user
        POSTGRES_PASSWORD: etl_pass
      run: dbt compile --profiles-dir .
```

This catches SQL syntax errors and broken `ref()` chains on every push without needing raw CSV data. It is the highest-leverage CI addition given that dbt models are not currently validated in CI at all.

**Note on dbt schema tests in CI**: Running `dbt test` in CI requires the raw tables to exist with data, which requires the Kaggle CSVs, which cannot be checked in. The `dbt compile` job above is the right boundary: it validates SQL structure without needing data. Full `dbt test` belongs in `make pipeline` locally only.

### Pre-commit hooks

Add a `.pre-commit-config.yaml` at repo root. The repo already uses `ruff` and `mypy` — making them run automatically on commit prevents the "oops, forgot to lint" CI failure cycle.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
        files: ^(src|tests)/
      - id: ruff-format
        files: ^(src|tests)/
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.0.0
    hooks:
      - id: sqlfluff-lint
        args: [--dialect, postgres]
        files: ^dbt/models/.*\.sql$
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        files: ^dbt/.*\.yml$
```

Install with: `pip install pre-commit && pre-commit install`

The `sqlfluff` hook on dbt SQL is particularly valuable here — it enforces consistent style across the 9 dbt model files and catches CTE ordering issues before they hit CI.

### Makefile additions

Add to the existing `Makefile` (currently has 9 targets):

```makefile
# Documentation
dbt-docs:
	cd dbt && dbt docs generate && dbt docs serve

dbt-compile:
	cd dbt && dbt compile

# Code quality
format:
	ruff format src/ tests/

typecheck:
	mypy src/

# Pre-commit
pre-commit-install:
	pip install pre-commit && pre-commit install

pre-commit-run:
	pre-commit run --all-files
```

The `dbt-docs` target is the most portfolio-relevant addition — it is the answer to "show me your data lineage" in an interview.

### pandera / ingestion automation

No additional CI automation for pandera is needed — the existing `pytest` job already runs the pandera schema unit tests in `tests/test_ingestion/test_schemas.py` against fixture DataFrames (not the raw CSVs). The key automation improvement for pandera is ensuring the `conftest.py` in `tests/` defines shared DataFrame fixtures so individual test files do not duplicate fixture construction. Currently `tests/conftest.py` is empty — this is a code quality gap, not a CI gap.

### Prefect automation note

Prefect 2.x flow runs are local-only. No cloud workspace is configured. No CI automation for Prefect is warranted until the flow is deployed to Prefect Cloud or a self-hosted server.

---

## Component 5: Naming Conventions & Structure

### Complete directory structure for all artifacts to be created

```
clinical-data-etl/
├── LICENSE                          # MIT license (new)
├── README.md                        # Add CI badge, fix Python version, Kaggle note, Roadmap section (edit)
├── PROJECT_GUIDE.md                 # Commit to git (already on disk, no edit)
├── CLAUDE.md                        # Fix int_claims_joined → int_claims_unified, add tasks.py (edit)
├── Makefile                         # Fix python3.12 → python3, add dbt-docs/dbt-compile/format/typecheck targets (edit)
├── .pre-commit-config.yaml          # New (if pre-commit automation is adopted)
│
├── docs/
│   ├── adr/                         # Architecture Decision Records (Phase 2 only — defer until new decisions arise)
│   │   └── 001-etl-not-ml-framing.md        # Convert existing prose decisions when Phase 2 begins
│   │   └── 002-fraud-label-in-dim-provider.md
│   │   └── 003-drop-cascade-raw-schema.md
│   │   └── 004-pandera-rejects-as-warn.md
│   └── images/
│       └── dbt-lineage.png          # Screenshot of dbt docs lineage DAG (new, M effort)
│
└── dbt/
    └── models/
        ├── staging/
        │   ├── src_raw.yml          # Add source + table descriptions (edit)
        │   └── schema.yml           # No change needed for Tier 1/2
        ├── intermediate/
        │   └── schema.yml           # Tier 3: add chronic condition flag descriptions
        └── marts/
            └── schema.yml           # Add column descriptions for dim_provider aggregates, dim_beneficiary chronic flags, fct_claims nullability notes (edit)
```

### ADR naming convention (when adopted)

- File pattern: `docs/adr/NNN-short-slug.md` where NNN is zero-padded to 3 digits
- Title format: "ADR-NNN: [Decision Title in Title Case]"
- Required sections: Context, Decision, Consequences, Status (Accepted / Superseded / Deprecated)
- Cross-reference to `PROJECT_GUIDE.md` "Decisions & Tradeoffs" section

### Diagram file conventions

- All images: `docs/images/<descriptor>.<ext>` — lowercase, hyphen-separated
- PNG for screenshots (dbt-lineage.png)
- Mermaid diagrams stay inline in Markdown files (PROJECT_GUIDE.md) — do not extract to separate `.mmd` files unless a diagram tool requires it
- No `.drawio` or `.excalidraw` files — the Mermaid + ASCII combination already present is sufficient and renders on GitHub without plugins

### Runbook location

- The primary runbook is `README.md` §§ "Setup" + "Makefile Targets" — this is the correct location for a portfolio project (one-file entry point)
- The extended troubleshooting runbook lives in `PROJECT_GUIDE.md` § "User Guide" — this is appropriate as the deep reference
- No separate `docs/runbook.md` is warranted — it would duplicate README and PROJECT_GUIDE.md

---

## Generation Session Kickoff

### Five highest-leverage artifacts to generate first, in order

1. **Commit `PROJECT_GUIDE.md`** — zero writing, one git command, highest single leverage action
2. **Fix `CLAUDE.md` stale references** (`int_claims_joined` → `int_claims_unified`, add `tasks.py` if present) — 10-minute edit that keeps AI working context accurate for every future session
3. **Add CI badge + fix Python version ambiguity in `README.md` / `Makefile`** — credibility-visible, 15 minutes total, groups well as one commit
4. **Add `LICENSE` (MIT)** — 30 seconds, removes the all-rights-reserved ambiguity for reviewers
5. **Add column descriptions to `dbt/models/marts/schema.yml`** — the most visible data quality gap to an AE reviewer who opens the repo and runs `dbt docs generate`

### Decisions the repo owner must make before generation starts

1. **Is `tasks.py` present in `src/clinical_data_etl/orchestration/`?** Run `ls src/clinical_data_etl/orchestration/` — if `tasks.py` exists, add it to the `CLAUDE.md` folder listing; if not, the CLAUDE.md reference is a ghost and should be removed.
2. **Which Kaggle slug is correct for the synthetic hospital dataset?** `amulyas/synthetic-hospital-data` (used in `README.md` and `Makefile`) or `amulyas/synth-hospital-data` (used in `CLAUDE.md`)? One attempt to `kaggle datasets download -d amulyas/synthetic-hospital-data` will resolve this in 10 seconds.
3. **MIT or Apache-2.0 license?** Both are appropriate. MIT is simpler (one paragraph). Apache-2.0 adds a patent grant clause that is irrelevant for a portfolio project. Recommend MIT unless there is a preference.

### Suggested prompt to start the next generation session

> "Start a new feature branch `docs/phase4-polish`, then work through this Phase 4 plan in order: (1) commit PROJECT_GUIDE.md as-is, (2) fix the int_claims_joined stale reference and tasks.py entry in CLAUDE.md, (3) add the CI badge and fix the Python version ambiguity in README.md and Makefile, (4) add an MIT LICENSE file, (5) add column descriptions to dbt/models/marts/schema.yml for the dim_provider aggregates and dim_beneficiary chronic condition flags — confirm each change with me before committing."

---

*This document is the source of truth for the follow-up generation session. Update it as artifacts are created.*
