"""Self-verifying demo: prove the incremental dbt models add ONLY new claims and
that re-running is idempotent.

The Medicare data is single-vintage (~2009) with no natural time delta, so we
demonstrate incrementality with a DETERMINISTIC, seeded partition of claims by a
stable md5 hash bucket of claim_id (NOT a fake date). Phase A loads bucket 0 and
full-refreshes; Phase B loads bucket 1 and runs incrementally; we assert the
incremental run inserted exactly the bucket-1 claims (no duplicates), reached the
full row count, and that a second incremental run is a no-op.

100% local, no external accounts. Exits non-zero if any check fails. Leaves the
warehouse in the canonical full state.

Run: make demo-incremental   (or: python scripts/demo_incremental.py)
"""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from clinical_data_etl.ingestion.loaders import (
    TABLE_CONFIG,
    claim_id_bucket,
    load_and_merge,
    load_to_postgres,
    reset_raw_tables,
    validate,
)
from clinical_data_etl.utils.db import get_engine

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
CLAIM_TABLES = ("inpatient_claims", "outpatient_claims")
INGESTED_AT = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def dbt(*args: str) -> None:
    """Invoke dbt from the active venv; raise with output on failure."""
    dbt_bin = Path(sys.executable).parent / "dbt"
    cmd = [
        str(dbt_bin),
        *args,
        "--profiles-dir",
        str(DBT_DIR),
        "--project-dir",
        str(DBT_DIR),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"dbt {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
        )


def _load(table: str, mode: str, bucket: int | None = None) -> int:
    df = load_and_merge(table)
    valid, _ = validate(df, TABLE_CONFIG[table][2], table)
    if bucket is not None and table in CLAIM_TABLES:
        valid = valid[valid["ClaimID"].map(lambda c: claim_id_bucket(c, 2)) == bucket]
    return load_to_postgres(valid, table, mode=mode, ingested_at=INGESTED_AT)


def _fct_count(conn) -> int:  # type: ignore[no-untyped-def]
    return int(
        conn.execute(text("select count(*) from raw_marts.fct_claims")).scalar() or 0
    )


def _fct_dupes(conn) -> int:  # type: ignore[no-untyped-def]
    return int(
        conn.execute(
            text(
                "select count(*) from (select claim_id from raw_marts.fct_claims "
                "group by claim_id having count(*) > 1) d"
            )
        ).scalar()
        or 0
    )


def main() -> int:
    engine = get_engine()

    print("[demo] Phase 0: clean slate — TRUNCATE raw (snapshots survive)")
    reset_raw_tables()
    _load("beneficiary", "replace")
    _load("providers", "replace")

    print("[demo] Phase A: load claim bucket 0 + full-refresh dbt")
    a_in = _load("inpatient_claims", "replace", bucket=0)
    a_out = _load("outpatient_claims", "replace", bucket=0)
    dbt("snapshot")
    dbt("run", "--full-refresh")
    with engine.connect() as conn:
        c1, d1 = _fct_count(conn), _fct_dupes(conn)
    print(f"[demo]   fct_claims={c1}  dup_claim_ids={d1}  (loaded {a_in + a_out})")

    print("[demo] Phase B: load claim bucket 1 (upsert) + incremental dbt run")
    b_in = _load("inpatient_claims", "upsert", bucket=1)
    b_out = _load("outpatient_claims", "upsert", bucket=1)
    dbt("run")
    with engine.connect() as conn:
        c2, d2 = _fct_count(conn), _fct_dupes(conn)
    print(f"[demo]   fct_claims={c2}  dup_claim_ids={d2}  (added {b_in + b_out})")

    print("[demo] Phase C: re-run incremental dbt (no new claims) — must be a no-op")
    dbt("run")
    with engine.connect() as conn:
        c3 = _fct_count(conn)
    print(f"[demo]   fct_claims={c3}")

    full = a_in + a_out + b_in + b_out
    checks = {
        "phaseA_no_duplicate_claim_ids": d1 == 0,
        "phaseB_no_duplicate_claim_ids": d2 == 0,
        "incremental_added_exactly_bucket1": (c2 - c1) == (b_in + b_out),
        "reached_full_row_count_after_two_phases": c2 == full,
        "incremental_rerun_is_noop": c3 == c2,
    }
    print("\n[demo] Fitness checks:")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    if all(checks.values()):
        print(
            f"\n[demo] ✅ INCREMENTAL DEMO PASSED — fct_claims={c2} (canonical full state)"
        )
        return 0
    print("\n[demo] ❌ INCREMENTAL DEMO FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
