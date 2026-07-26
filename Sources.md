# Sources

| Source | Location | Type | Authoritative for |
|--------|----------|------|-------------------|
| Medicare claims fraud dataset | Kaggle `rohitrox/healthcare-provider-fraud-detection-analysis` → `data/raw/claims_fraud/` (gitignored) | raw data export | Primary source: beneficiary, inpatient/outpatient claims, provider fraud labels |
| Diabetes readmission dataset | Kaggle `brandao/diabetes` → `data/raw/diabetes_readmission/` (gitignored) | raw data export | Secondary source: 101,766 UCI hospital encounters, 30-day readmission target |
| Synthetic hospital admissions dataset | Kaggle `amulyas/synthetic-hospital-data` → `data/raw/synthetic_hospital/` (gitignored) | raw data export | Tertiary source: 5,000 admissions, length-of-stay target |
| Data sources reference | `docs/data-sources.md` | reference doc | CSV filenames, per-column source descriptions, folder layout |
| Data dictionary | `docs/data-dictionary.md` | reference doc | Column-level lineage (raw → staging rename → mart) across all three stars |
| Architecture Decision Records | `docs/adr/` (001–010 + README index) | decision records | The load-bearing design decisions (see Decisions.md) |
| Incremental + SCD2 design doc | `docs/incremental_scd2.md` | design doc | Upsert loader, incremental boundary, snapshot/SCD2 design and seeded demos |
| Phase plans | `docs/phase2-diabetes-plan.md`, `docs/phase3-hospital-plan.md`, `docs/phase5-tier3-docs-plan.md` | plans | Scope and execution record of Phases 2, 3, and the Tier 3 docs milestone |
| Artifacts plan | `docs/artifacts-plan.md` | plan | Documentation roadmap (now drained except the lineage screenshot) |
| Project guide | `PROJECT_GUIDE.md` | guide | Point-in-time comprehensive walkthrough incl. interview lens (snapshot from 2026-05-30) |
| Session logs | `docs/session-logs/` | transcripts/recaps | What happened in the Phase 4 docs-CI and Phase 2 diabetes sessions |
| Backlog | `BACKLOG.md` | tracker | Open/deferred/done fix items |
