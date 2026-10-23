#!/usr/bin/env bash
# Механічний ratchet: нові тести семантики — Lisp/SENS, не Python/JSON.
# Історичні файли НЕ сертифікуються та не блокуються лише за існування.
set -euo pipefail

if (( $# < 2 || $# > 3 )); then
  echo "usage: bash scripts/guard-test-ownership-ratchet.sh BASE_SHA HEAD_SHA [TEST_REPO]" >&2
  exit 2
fi
base="$1"
head="$2"
repo="${3:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)}"
for ref in "$base" "$head"; do
  if ! git -C "$repo" cat-file -e "$ref^{commit}" 2>/dev/null; then
    echo "::error::TEST_OWNERSHIP_BASE_UNAVAILABLE layer=git ref=$ref expected=commit actual=missing" >&2
    exit 2
  fi
done

changed="$(mktemp)"
trap 'rm -f "$changed"' EXIT
if ! git -C "$repo" diff --no-ext-diff --no-renames --name-only --diff-filter=A -z \
    "$base" "$head" -- tests/ scripts/ benchmarks/ >"$changed"; then
  echo "::error::TEST_OWNERSHIP_DIFF_FAILED layer=git base=$base head=$head" >&2
  exit 2
fi

checked=0
rejected=0
while IFS= read -r -d '' path; do
  ((checked+=1))
  reason=
  case "$path" in
    tests/semantic/*.py|tests/semantic/*.json|tests/semantic/*.rs|tests/semantic/*.zig)
      reason="semantic-tests-require-Lisp-to-Zig-T5M-to-SENS"
      ;;
    tests/test_*.py|scripts/test-*.py|scripts/bench*.py|benchmarks/*.py)
      reason="new-tests-and-benchmarks-require-native-owner"
      ;;
  esac
  if [[ -n "$reason" ]]; then
    ((rejected+=1))
    printf '::error file=%s,title=TEST_OWNERSHIP_REGRESSION::layer=test-authority fixture=%s expected=Lisp/SENS-semantics-or-Rust/Zig-mechanism actual=Python/JSON/host-semantic-file reason=%s base=%s head=%s\n' \
      "$path" "$path" "$reason" "$base" "$head" >&2
  fi
done <"$changed"
printf 'TEST_OWNERSHIP_RATCHET checked=%s rejected=%s historic=NOT_CERTIFIED semantics=NOT_ASSERTED base=%s head=%s\n' \
  "$checked" "$rejected" "$base" "$head"
if ((rejected > 0)); then
  echo "REPRO: bash scripts/guard-test-ownership-ratchet.sh $base $head" >&2
  exit 1
fi
