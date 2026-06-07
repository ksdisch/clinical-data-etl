# ADR-009: Invoke dbt via subprocess, not the Python API

**Status:** Accepted

## Context

The Prefect orchestration layer needs to run `dbt seed`, `dbt snapshot`, `dbt run`, and `dbt test` as
steps in the pipeline flow. dbt exposes a programmatic Python entry point (`dbtRunner`), which would let
the flow call dbt in-process and inspect rich result objects. But the programmatic API is version-
sensitive and couples the orchestration code to dbt's internals — the exact thing that has churned
across dbt minor versions and that this project deliberately pins narrowly (`dbt-core >=1.10,<1.11`)
because of.

## Decision

Invoke dbt through a thin `subprocess` helper (`_run_dbt_command`) rather than the Python API. The
Prefect task shells out to the `dbt` CLI, checks the exit code, and surfaces output. The task knows
nothing about dbt's internal objects.

## Consequences

- **Easier:** the orchestration layer is decoupled from dbt's internals — a dbt minor-version bump that
  changes the Python API surface does not touch the flow; if dbt were ever swapped for SQLMesh or plain
  SQL files, only `_run_dbt_command` changes.
- **Harder / accepted:** the flow gets a process exit code and stdout/stderr instead of structured result
  objects, so failure handling is coarser-grained (per-command, not per-model). For this pipeline that is
  the right trade — the granularity that matters (which *command* failed) is preserved, and the decoupling
  is worth far more than per-model result introspection.
