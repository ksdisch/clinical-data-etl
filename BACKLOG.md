# Backlog

Lightweight fix-tracking for clinical-data-etl — open items so they don't get lost.
This is not a sprint board. For the documentation roadmap, see [`docs/artifacts-plan.md`](docs/artifacts-plan.md).

## Open

### Environment
- [ ] **Prefect local DB conflict.** Running `make pipeline` (or the flow tests) can fail at
  startup with `alembic ... Can't locate revision '4dfa692e02a7'` when `~/.prefect/prefect.db`
  was created by / is shared with another project's Prefect version. Workaround: use an isolated
  store, e.g. `export PREFECT_HOME=$(pwd)/.prefect` before running. Permanent options: scope
  `PREFECT_HOME` to the project (and gitignore it), or `prefect server database reset` — but a
  reset wipes other projects' Prefect state too. _Surfaced during the 2026-05-30 runtime verification._

### CI / dependencies
- [ ] **Pin dependencies or commit a lockfile.** Unpinned floors (e.g. `pandera>=0.18`) let pandera
  drift to 0.31, which silently broke CI `typecheck` for ~2 months until fixed in PR #2. Add tighter
  bounds or commit a lockfile (an untracked `uv.lock` already exists locally) so dependency drift
  can't redden `main` unnoticed.
- [ ] **Add a dbt job to CI.** CI runs lint/typecheck/pytest but not dbt, so dbt model/test changes
  are only validated locally. Add a `dbt compile` (or seed-backed `dbt build`) job — see
  `docs/artifacts-plan.md` Component 4 for a ready-to-paste workflow snippet.

## Deferred (until Phase 2 activates)
- [ ] **Tier 3 docs.** ADR directory, full column-level data dictionary, intermediate-model column
  descriptions (see `docs/artifacts-plan.md`).
- [ ] **Phase 2 dataset.** Integrate diabetes readmission (`brandao/diabetes`) as a second fact
  table; the raw-dir placeholder already exists.

---

_Done items are not tracked here. The dbt 1.7 → 1.10 floor bump (commit `aab50d4`) is complete._
