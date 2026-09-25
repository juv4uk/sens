#!/usr/bin/env bash
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
}
trap cleanup EXIT

run_case() {
  local fixture=$1
  local expected=$2
  local extension="${fixture##*.}"
  probe="tests/semantic-authority-guard-probe.${extension}"
  cp "$fixture" "$probe"
  local digest
  digest="$(sha256sum "$probe" | awk '{print $1}')"
  printf '(changed "%s" "%s")\n' "$probe" "$digest" > tests/semantic-authority-changes.lisp
  "$my_lisp" scripts/semantic-authority-guard.lisp > tests/semantic-authority-verdict.lisp
  cat tests/semantic-authority-verdict.lisp
  if [[ "$expected" == "violation" ]]; then
    if "$my_lisp" scripts/semantic-authority-guard-enforce.lisp; then
      echo "ERROR: expected semantic-authority guard failure for $fixture" >&2
      exit 1
    fi
    grep -q "host-to-language-authority-leak" tests/semantic-authority-verdict.lisp
  else
    "$my_lisp" scripts/semantic-authority-guard-enforce.lisp
    grep -q "semantic-authority-ok" tests/semantic-authority-verdict.lisp
  fi
  rm -f "$probe"
}

# Legacy #1049 RED fixtures are now deliberately GREEN: Rust/local executor
# semantics are no longer restricted by this guard.
run_case tests/fixtures/semantic-authority-guard/forbidden-sid-meaning.rs allowed
run_case tests/fixtures/semantic-authority-guard/forbidden-island-sid.rs allowed
run_case tests/fixtures/semantic-authority-guard/forbidden-isa-sid.rs allowed
run_case tests/fixtures/semantic-authority-guard/forbidden-fallback.rs allowed
run_case tests/fixtures/semantic-authority-guard/allowed-generated-projection.rs allowed

# The new RED is the reverse authority edge into Lisp-owned semantic source.
run_case tests/fixtures/semantic-authority-guard/forbidden-lisp-host-authority.lisp violation
# Supported SENS alias with a Cyrillic extension is protected the same way.
run_case tests/fixtures/semantic-authority-guard/forbidden-lisp-host-authority.сенс violation

# Rust may be cited as observation/evidence without becoming language authority.
run_case tests/fixtures/semantic-authority-guard/allowed-lisp-host-evidence.lisp allowed
