#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: one native physical T5 self-verdict and its one-bit mutant.
# Zig alone creates physical T5; native binary SENS owns the verdict.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="target/debug/sens"
if [[ "$#" -ge 1 ]]; then cli="$1"; fi
id=retired-quote-inert-d3
law=tests/semantic/retired-quote-inert-d3-law.bits
mutant=tests/semantic/retired-quote-inert-d3-mutant.bits
if [[ ! -x "$cli" ]]; then
  echo "REGRESSION test_id=$id layer=eval kind=UNINFORMATIVE-EXECUTOR cli=$cli reproduce='cargo build --locked -p sens-cli --bin sens && bash scripts/prove-retired-quote-inert.sh'" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# Only Zig builds the physical T5 .sens bytes; no Python encoder.
python3 scripts/prepare_h2_zig_t5.py quote "$tmp"

printf 'test_id=%s layer=eval executor=%s version=%s\n' "$id" "$cli" "$("$cli" --version)"
sha256sum "$cli" "$law" "$mutant" "$tmp/law.sens" "$tmp/mutant.sens"
reproduce="bash scripts/prove-retired-quote-inert.sh $cli"
printf 'reproduce=%q\n' "$reproduce"
expected="$tmp/expected"
actual="$tmp/actual"
printf '1\n' > "$expected"
if ! "$cli" "$tmp/law.sens" > "$actual" 2> "$tmp/law.stderr"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:YES actual=execution-error first_diff=unknown reproduce=%q\n' \
    "$id" "$law" "$reproduce" >&2
  cat "$tmp/law.stderr" >&2
  sha256sum "$expected" "$actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS test_id=%s expected_sha256=' "$id"
sha256sum "$expected"
printf 'NATIVE_SENS_DIGESTS test_id=%s actual_sha256=' "$id"
sha256sum "$actual"
if ! cmp -s "$expected" "$actual"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:YES actual=wrong-verdict first_diff=0 reproduce=%q\n' \
    "$id" "$law" "$reproduce" >&2
  exit 1
fi
if "$cli" "$tmp/mutant.sens" > "$tmp/mutant.actual" 2> "$tmp/mutant.stderr"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=noncallable-rejection actual=accepted first_diff=quoted-D1 reproduce=%q\n' \
    "$id-mutant" "$mutant" "$reproduce" >&2
  sha256sum "$tmp/mutant.actual" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.stderr"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s layer=eval fixture=%s expected=D1-noncallable actual=unclassified-failure reproduce=%q\n' \
    "$id-mutant" "$mutant" "$reproduce" >&2
  cat "$tmp/mutant.stderr" >&2
  sha256sum "$tmp/mutant.stderr" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE test_id=%s kind=D1-noncallable sha256_stderr=' "$id-mutant"
sha256sum "$tmp/mutant.stderr"
printf 'NATIVE_SENS_PASS test_id=%s physical_positive=1 mutant=D1-noncallable authority=binary-SENS\n' "$id"
