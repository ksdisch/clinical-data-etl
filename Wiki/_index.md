# Wiki index

| Page | Covers | Last reviewed |
|------|--------|---------------|
| [Pipeline-Architecture](Pipeline-Architecture.md) | The compiled map of the three-star pipeline: sources → pandera → Postgres raw → dbt layers → Prefect, plus the load-bearing quirks per source | 2026-07-26 |
| [History](History.md) | Chronological eras-and-milestones narrative of how the project got here, mined from merged PRs, git history, wrap logs, and ADRs (append-only) | 2026-07-26 |
| [Data-Contracts](Data-Contracts.md) | What each pipeline layer guarantees: pandera enforcement per source, dbt test types per mart, known quality gaps (orphan claims, NULL fraud labels, high-null columns), and SCD2 temporal invariants | 2026-07-26 |
| [Operational-Runbook](Operational-Runbook.md) | Authoritative step order (Prefect flow), Makefile targets and what they actually do, failure modes and first-checks, upsert-vs-replace semantics, and verified row-count fitness functions | 2026-07-26 |
