#!/usr/bin/env bash
set -euo pipefail
if (($# != 1)); then
  echo "usage: $0 MY_LISP_BIN" >&2
  exit 2
fi
my_lisp=$1
probe=tests/semantic-authority-guard-probe.rs
cleanup() {
  rm -f "$probe"
}
trap cleanup EXIT

run_case() {
  local fixture=$1
  local expected=$2
  cp "$fixture" "$probe"
  printf '(changed "%s")\n' "$probe" > tests/semantic-authority-changes.lisp
  "$my_lisp" scripts/semantic-authority-guard.lisp > tests/semantic-authority-verdict.lisp
  cat tests/semantic-authority-verdict.lisp
  if [[ "$expected" == "violation" ]]; then
    if "$my_lisp" scripts/semantic-authority-guard-enforce.lisp; then
      echo "ERROR: expected semantic-authority guard failure for $fixture" >&2
      "$my_lisp" scripts/semantic-authority-guard-debug.lisp || true
      exit 1
    fi
    grep -q "semantic-authority-violation" tests/semantic-authority-verdict.lisp
  else
    "$my_lisp" scripts/semantic-authority-guard-enforce.lisp
    grep -q "semantic-authority-ok" tests/semantic-authority-verdict.lisp
  fi
}

run_case tests/fixtures/semantic-authority-guard/forbidden-sid-meaning.rs violation
run_case tests/fixtures/semantic-authority-guard/forbidden-island-sid.rs violation
run_case tests/fixtures/semantic-authority-guard/forbidden-isa-sid.rs violation
run_case tests/fixtures/semantic-authority-guard/forbidden-fallback.rs violation
run_case tests/fixtures/semantic-authority-guard/allowed-generated-projection.rs allowed
