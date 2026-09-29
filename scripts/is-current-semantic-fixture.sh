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

# #1709: the Lisp-owned semantic witness corpus. A version suffix is part of
# the name on purpose — a changed law is a new version, never a quiet edit.
# `semantic/runner.lisp` is deliberately NOT here: it is the witness protocol
# the Rust observer drives, not a fixture holding laws.
if [[ "$name" =~ ^semantic/(atom-1bit|cond-2part|core-universal|eq-1bit|predicate-1bit)-v[0-9]+\.lisp$ ]]; then
  exit 0
fi

if [[ "$name" =~ ^(bare-sid-literal|canon-zero|control-dispatch|exact-q-binary|knowledge-clause-kind|mathematical-result|reason-honesty|reason-module-honesty|reason-observe-honesty|structural-observation|structure-core|unification-outcome)-v[0-9]+\.lisp$ ]]; then
  exit 0
fi

exit 1
