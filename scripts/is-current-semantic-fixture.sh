#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <repo-relative-path>" >&2
  exit 2
fi

path="$1"
case "$path" in
  tests/fixtures/*) ;;
  *) exit 1 ;;
esac

name="${path#tests/fixtures/}"
if [[ "$name" =~ ^(bare-sid-literal|canon-zero|control-dispatch|deep-structural-relation|exact-q-binary|knowledge-clause-kind|mathematical-result|reason-honesty|reason-module-honesty|reason-observe-honesty|structural-observation|structure-core|unification-outcome)-v[0-9]+\.lisp$ ]]; then
  exit 0
fi

exit 1
