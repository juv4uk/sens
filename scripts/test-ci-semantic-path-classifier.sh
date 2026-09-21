#!/usr/bin/env bash
set -euo pipefail

classifier="scripts/is-current-semantic-fixture.sh"

if [[ ! -f "$classifier" ]]; then
  echo "#376 RED: missing semantic fixture classifier: $classifier" >&2
  exit 1
fi

positive_paths=(
  tests/fixtures/binary-numeric-v1.lisp
  tests/fixtures/bare-sid-literal-v1.lisp
  tests/fixtures/canon-zero-v2.lisp
  tests/fixtures/control-dispatch-v1.lisp
  tests/fixtures/deep-structural-relation-v1.lisp
  tests/fixtures/exact-q-binary-v1.lisp
  tests/fixtures/knowledge-clause-kind-v1.lisp
  tests/fixtures/mathematical-result-v1.lisp
  tests/fixtures/reason-honesty-v1.lisp
  tests/fixtures/reason-module-honesty-v1.lisp
  tests/fixtures/reason-observe-honesty-v1.lisp
  tests/fixtures/structural-observation-v1.lisp
  tests/fixtures/structure-core-v1.lisp
  tests/fixtures/unification-outcome-v1.lisp
)

for path in "${positive_paths[@]}"; do
  if ! bash "$classifier" "$path"; then
    echo "#376 classifier missed current semantic fixture: $path" >&2
    exit 1
  fi
done

negative_paths=(
  tests/fixtures/translation-corpus-v1.lisp
  tests/fixtures/oracle-results.lisp
  tests/fixtures/inventory.lisp
  docs/archive/example-v1.lisp
)

for path in "${negative_paths[@]}"; do
  if bash "$classifier" "$path"; then
    echo "#376 classifier overreached into non-current semantic fixture: $path" >&2
    exit 1
  fi
done

echo "semantic fixture path classifier self-test: PASS"
