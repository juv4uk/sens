#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS mutual D4; use the ratified binary source and physical pair.
set -euo pipefail
cd "$(dirname "$0")/.."
trit="${SENS_TRIT:-target/debug/sens-trit}"
source=tests/semantic/meta-eval-mutual-d4-law.bits
physical=tests/semantic/meta-eval-mutual-d4-law.sens
id=meta-eval-mutual-d4

for path in "$trit" "$source" "$physical"; do
  if [[ ! -s "$path" || -L "$path" ]]; then
    printf 'REGRESSION test_id=%s layer=fixture missing-or-invalid=%s\n' "$id" "$path" >&2
    exit 1
  fi
done
if [[ ! -x "$trit" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-not-executable path=%s\n' "$id" "$trit" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -- "$source" "$tmp/source.bits"
if ! "$trit" encode "$tmp/source.bits" >"$tmp/encode.out" 2>"$tmp/encode.err"; then
  printf 'REGRESSION test_id=%s layer=Zig-T5M-encode actual=execution-error\n' "$id" >&2
  cat "$tmp/encode.err" >&2
  exit 1
fi
if ! cmp -s "$physical" "$tmp/source.sens"; then
  printf 'REGRESSION test_id=%s layer=physical-pair expected=canonical-T5M actual=byte-drift\n' "$id" >&2
  exit 1
fi

if ! "$trit" eval "$physical" >"$tmp/actual" 2>"$tmp/eval.err"; then
  printf 'REGRESSION test_id=%s layer=physical-SENS expected=D1:1 actual=execution-error\n' "$id" >&2
  cat "$tmp/eval.err" >&2
  exit 1
fi
printf '1\n' >"$tmp/expected"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION test_id=%s layer=physical-SENS expected=D1:1 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
printf 'NATIVE_SENS_PASS id=%s source=binary-SENS carrier=Zig/T5M evidence=cmp\n' "$id"
