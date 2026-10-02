#!/usr/bin/env bash
set -euo pipefail

seed_dir="${1:-.core1-s0/mccarthy-eval}"
witness="tests/fixtures/post-d4-evalquote-witness.lisp"
seed_sha="$(git -C "$seed_dir" rev-parse HEAD)"

test "$seed_sha" = "6031f92652066825a245c806c0773e9e524257bd"
printf 'S0 seed commit: %s\n' "$seed_sha"

gcc -no-pie -O0 -s -o "$seed_dir/mccarthy-kernel" "$seed_dir/mccarthy-kernel.s"

if sed '/^[[:space:]]*;/d' "$witness" | grep -Eq '\b(FEXPR|FSUBR)\b'; then
  echo "ordinary EVALQUOTE executable witness must not import FEXPR/FSUBR staging" >&2
  exit 1
fi

mkdir -p .core1-s0
cat lib/core1.lisp "$witness" > .core1-s0/post-d4-evalquote-full.lisp

expected='((A . B) A (A . B) (C1-ERROR ARITY 00000101))'
raw="$(
  cd "$seed_dir"
  ./mccarthy-kernel ../post-d4-evalquote-full.lisp
)"

actual="$(printf '%s\n' "$raw" | tail -n 1)"
prefix="$(printf '%s\n' "$raw" | sed '$d')"

printf 'EVALQUOTE expected=%s\n' "$expected"
printf 'EVALQUOTE actual=%s\n' "$actual"

if [ -n "$prefix" ] && printf '%s\n' "$prefix" | grep -Ev '^NIL$' | grep -q .; then
  echo "unexpected non-NIL bootstrap output before EVALQUOTE observation" >&2
  printf '%s\n' "$prefix" >&2
  exit 1
fi

test "$actual" = "$expected"

echo "EVALQUOTE-DERIVED-D4=PASS"
echo "FEXPR-FSUBR=EXCLUDED"
