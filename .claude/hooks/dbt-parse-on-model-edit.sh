#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit): parse the dbt project after a model,
# snapshot, or macro SQL edit. Catches Jinja/ref/version-API drift — the same class
# of breakage the CI `dbt compile` step guards against — but `dbt parse` needs NO
# warehouse connection (profiles.yml has env_var defaults), so this is cloud-safe.
# Non-blocking on success; exits 2 with the error tail on a parse failure so Claude
# fixes it before pushing (the CI dbt job previously reddened main on exactly this).
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | python3 -c \
  'import json,sys;print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' \
  2>/dev/null)

[ -z "$file" ] && exit 0
case "$file" in
  *dbt/models/*.sql|*dbt/snapshots/*.sql|*dbt/macros/*.sql) ;;
  *) exit 0 ;;
esac

if   [ -x ".venv/bin/dbt" ]; then DBT=".venv/bin/dbt"
elif command -v dbt >/dev/null 2>&1; then DBT="dbt"
else exit 0   # dbt not installed — skip silently
fi

if ! out=$("$DBT" parse --profiles-dir dbt --project-dir dbt 2>&1); then
  echo "dbt parse failed after editing $file:" >&2
  printf '%s\n' "$out" | tail -n 30 >&2
  exit 2
fi
exit 0
