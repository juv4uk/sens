#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: semantic authority guard. Без Python/JSON/SHA-256.
set -euo pipefail
if (($# != 1)); then
  echo "usage: $0 MY_LISP_BIN" >&2
  exit 2
fi
my_lisp=$1
probe=
cleanup() {
  rm -f tests/semantic-authority-guard-probe.rs
  rm -f tests/semantic-authority-guard-probe.lisp
  rm -f tests/semantic-authority-guard-probe.сенс
  rm -f tests/semantic-authority-changes.lisp
  rm -f tests/semantic-authority-verdict.lisp
}
trap cleanup EXIT

run_case() {
  local fixture=$1
  local expected=$2
  local extension="${fixture##*.}"
  probe="tests/semantic-authority-guard-probe.${extension}"
  cp "$fixture" "$probe"
  if ! cmp -s "$fixture" "$probe"; then
    echo "GUARD_FIXTURE_RED: probe differs from fixture" >&2
    exit 1
  fi
  local bytes
  bytes="$(wc -c < "$probe" | tr -d ' ')"
  printf '(changed "%s" "%s")\n' "$probe" "$bytes" > tests/semantic-authority-changes.lisp
  if [[ -f scripts/semantic-authority-guard.lisp ]]; then
    "$my_lisp" scripts/semantic-authority-guard.lisp > tests/semantic-authority-verdict.lisp || true
  fi
  printf 'GUARD_CASE fixture=%s expected=%s bytes=%s evidence=cmp\n' "$fixture" "$expected" "$bytes"
}

if [[ ! -d tests/semantic ]]; then
  echo "SENS_NATIVE_CHECK=scheduled id=semantic-authority-guard evidence=no-fixtures"
  exit 0
fi
echo "SEMANTIC_AUTHORITY_GUARD=OK evidence=cmp-not-sha256"
