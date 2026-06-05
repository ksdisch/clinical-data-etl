#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit): auto-format and autofix Python files
# right after Claude edits them, so the CI `ruff format --check` + lint gates stay
# green by construction. Cloud-safe (pure ruff; no DB/network). Non-blocking on
# success; on UNFIXABLE lint it exits 2 so the remaining issues are surfaced to
# Claude (the edit has already been applied either way).
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | python3 -c \
  'import json,sys;print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' \
  2>/dev/null)

[ -z "$file" ] && exit 0
case "$file" in *.py) ;; *) exit 0 ;; esac
[ -f "$file" ] || exit 0

if   [ -x ".venv/bin/ruff" ]; then RUFF=".venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then RUFF="ruff"
else exit 0   # ruff not installed (e.g. minimal env) — skip silently
fi

"$RUFF" format "$file"        >/dev/null 2>&1 || true
"$RUFF" check  "$file" --fix  >/dev/null 2>&1 || true

# Anything left after --fix is not auto-fixable: report it back.
if ! remaining=$("$RUFF" check "$file" 2>&1); then
  echo "ruff: unresolved lint issues in $file (auto-fix applied what it could):" >&2
  echo "$remaining" >&2
  exit 2
fi
exit 0
