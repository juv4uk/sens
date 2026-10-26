#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: D3 quotation law executes in SENS; cmp checks only D1 bytes.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=d3-як-є-щит
law=tests/semantic/d3-як-є-щит-law.lisp
mutant=tests/semantic/d3-як-є-щит-mutant.lisp
# Core4 defines D8 structural equality; without this source the physical T5M
# negative witness can fail with unknown Text7 before producing its D1 verdict.

if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION id=%s layer=executor actual=missing\n' "$id" >&2
  exit 1
fi
for source in "$law" "$mutant"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    printf 'REGRESSION id=%s layer=source actual=missing-or-symlink path=%s\n' "$id" "$source" >&2
    exit 1
  fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected-positive"
printf '0\n' > "$tmp/expected-negative"

if ! timeout 45s "$cli" --t5m-files lib/core4-parts/core4-language.lisp lib/твердження.lisp "$law" > "$tmp/positive.out" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=positive actual=execution-error\n' "$id" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-positive" "$tmp/positive.out"; then
  printf 'REGRESSION id=%s layer=positive expected=D1:так actual=divergent\n' "$id" >&2
  exit 1
fi

if ! timeout 45s "$cli" --t5m-files lib/core4-parts/core4-language.lisp lib/твердження.lisp "$mutant" > "$tmp/negative.out" 2> "$tmp/negative.err"; then
  printf 'REGRESSION id=%s-mutant layer=negative actual=execution-error\n' "$id" >&2
  cat "$tmp/negative.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-negative" "$tmp/negative.out"; then
  printf 'REGRESSION id=%s-mutant layer=negative expected=D1:ні actual=divergent\n' "$id" >&2
  exit 1
fi

printf 'D3_ЯК_Є_ЩИТ=OK authority=SENS_form positive=D1:так negative=D1:ні evidence=cmp carrier=Zig/T5M\n'
