"""Self-verifying demo: prove the SCD Type 2 fraud-label history works.

The source data is static, so we demonstrate change history with a DETERMINISTIC,
seeded "second vintage": flip is_potential_fraud from No -> Yes on a fixed set of
providers (chosen by sorted provider_id), re-run the snapshot, and assert that a
second version row materialises with correct temporal validity (old row closed,
new row current) and that the temporal-validity invariants still hold.

This is explicitly a SEEDED demo — the source CSVs don't change on their own. The
script restores the baseline (1 version per provider) at the end, so it is fully
re-runnable and leaves a clean state.

100% local, no external accounts. Exits non-zero if any check fails.

Run: make demo-scd2   (or: python scripts/demo_scd2.py)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from clinical_data_etl.utils.db import get_engine

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
K = 5  # number of providers to flip


def dbt(*args: str) -> None:
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


def main() -> int:
    engine = get_engine()

    print("[scd2] Establishing baseline snapshot (one version per provider)")
    dbt("snapshot")
    with engine.connect() as conn:
        base = int(
            conn.execute(
                text("select count(*) from snapshots.snap_provider_fraud")
            ).scalar()
            or 0
        )
        flipped = [
            row[0]
            for row in conn.execute(
                text(
                    'select "Provider" from raw.providers '
                    'where "PotentialFraud" = \'No\' order by "Provider" limit :k'
                ),
                {"k": K},
            )
        ]
    print(
        f"[scd2]   baseline snapshot rows={base}; flipping {len(flipped)} providers -> 'Yes'"
    )
    if len(flipped) < K:
        print("[scd2] ❌ not enough 'No' providers to flip; run the pipeline first")
        return 1

    print("[scd2] Second vintage: flip fraud label, re-snapshot, rebuild history")
    with engine.begin() as conn:
        conn.execute(
            text(
                'update raw.providers set "PotentialFraud" = \'Yes\' where "Provider" = any(:p)'
            ),
            {"p": flipped},
        )
    dbt("snapshot")
    dbt("run", "--select", "dim_provider_history")
    dbt(
        "test",
        "--select",
        "assert_provider_history_no_overlap",
        "assert_provider_history_one_current",
    )

    with engine.connect() as conn:
        total = int(
            conn.execute(
                text("select count(*) from snapshots.snap_provider_fraud")
            ).scalar()
            or 0
        )
        two_versions = int(
            conn.execute(
                text(
                    "select count(*) from (select provider_id from raw_marts.dim_provider_history "
                    "where provider_id = any(:p) group by provider_id having count(*) = 2) d"
                ),
                {"p": flipped},
            ).scalar()
            or 0
        )
        current_is_fraud = int(
            conn.execute(
                text(
                    "select count(*) from raw_marts.dim_provider_history "
                    "where provider_id = any(:p) and is_current and is_potential_fraud"
                ),
                {"p": flipped},
            ).scalar()
            or 0
        )
        old_closed = int(
            conn.execute(
                text(
                    "select count(*) from raw_marts.dim_provider_history "
                    "where provider_id = any(:p) and not is_current and valid_to is not null"
                ),
                {"p": flipped},
            ).scalar()
            or 0
        )

    checks = {
        "snapshot_grew_by_K": total == base + K,
        "K_flipped_providers_have_two_versions": two_versions == K,
        "current_version_is_fraud_true": current_is_fraud == K,
        "old_version_closed_with_valid_to": old_closed == K,
    }
    print("\n[scd2] Fitness checks:")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    print("\n[scd2] Restoring baseline (revert flip + fresh snapshot)")
    with engine.begin() as conn:
        conn.execute(
            text(
                'update raw.providers set "PotentialFraud" = \'No\' where "Provider" = any(:p)'
            ),
            {"p": flipped},
        )
        conn.execute(text("drop table if exists snapshots.snap_provider_fraud"))
    dbt("snapshot")
    dbt("run", "--select", "dim_provider_history", "dim_provider")

    if all(checks.values()):
        print("\n[scd2] ✅ SCD2 DEMO PASSED — baseline restored")
        return 0
    print("\n[scd2] ❌ SCD2 DEMO FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
