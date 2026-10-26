#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: exact D4 selector-width law executes in SENS.
# Native SENS owns both verdicts; no Python, JSON, digest, or receipt.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=d4-selector-width
law=tests/semantic/d4-selector-width-law.sens
mutant=tests/semantic/d4-selector-width-mutant.sens

if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION id=%s actual=executor-missing path=%s\n' "$id" "$cli" >&2
  exit 1
fi
if [[ ! -s "$law" || ! -s "$mutant" ]]; then
  printf 'REGRESSION id=%s layer=fixture expected=non-empty-law-and-mutant actual=missing-or-empty\n' "$id" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"

if ! "$cli" "$law" > "$tmp/actual" 2> "$tmp/law.err"; then
  printf 'REGRESSION id=%s layer=SENS-law expected=D1:1 actual=execution-error\n' "$id" >&2
  cat "$tmp/law.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=SENS-law expected=D1:1 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi

if "$cli" "$mutant" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
    printf 'REGRESSION id=%s-mutant layer=SENS expected=not-D1:1 actual=false-positive\n' "$id" >&2
    exit 1
  fi
fi

printf 'SENS_NATIVE_PASS id=%s law=D1:1 mutant=not-D1:1 semantic_authority=trit-sequence\n' "$id"
