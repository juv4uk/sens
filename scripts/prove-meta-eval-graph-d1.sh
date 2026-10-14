#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: run real library + SENS-authored D1/COND proof.
# Nothing here assigns meaning to a domain code, a predicate or an error.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-meta-eval-graph-d1.sh [native-sens-cli]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
id=meta-eval-graph-d1
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-graph-d1-law.lisp
mutant=tests/semantic/meta-eval-graph-d1-mutant.lisp
reproduce="bash scripts/prove-meta-eval-graph-d1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
python3 - "$law" "$mutant" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]).read_text(encoding="utf-8")
m = Path(sys.argv[2]).read_text(encoding="utf-8")
needle = "(my-cond-has-migration-clause? (001 ())) #d1:0"
if p.count(needle) != 1 or m != p.replace(needle, needle[:-1] + "1"):
    raise SystemExit("META_GRAPH_TRANSPORT_RED: expected one D1:0 -> D1:1 word mutation")
for fn in ("my-cond-has-migration-clause?", "my-params-bind-name?",
           "my-forms-reference-name?", "my-graph-dependencies-reach?"):
    if "(" + fn + " " not in p:
        raise SystemExit("META_GRAPH_TRANSPORT_RED: missing live helper call " + fn)
print("META_GRAPH_TRANSPORT_OK mutation=one-D1-bit semantic_pass=NOT_INFERRED")
PY
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat "$lib" "$law" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$law" "$mutant" "$tmp/positive.lisp" "$tmp/mutant.lisp"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:YES actual=execution-error first_diff=unknown reproduce=%q\n' "$id" "$law" "$reproduce" >&2
  cat "$tmp/positive.err" >&2
  sha256sum "$tmp/expected" "$tmp/actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS id=%s expected_sha256=' "$id"
sha256sum "$tmp/expected"
printf 'NATIVE_SENS_DIGESTS id=%s actual_sha256=' "$id"
sha256sum "$tmp/actual"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:YES actual=wrong-verdict first_diff=0 reproduce=%q\n' "$id" "$law" "$reproduce" >&2
  exit 1
fi
if "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=eval fixture=%s expected=D1-noncallable actual=accepted first_diff=D1:0-to-1 reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  sha256sum "$tmp/mutant.out" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
  printf 'UNINFORMATIVE-NEGATIVE id=%s-mutant layer=eval fixture=%s expected=D1-noncallable actual=unrelated-failure first_diff=unknown reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  cat "$tmp/mutant.err" >&2
  sha256sum "$tmp/mutant.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE id=%s-mutant stderr_sha256=' "$id"
sha256sum "$tmp/mutant.err"
printf 'NATIVE_SENS_PASS id=%s checks=7 semantic_authority=SENS\n' "$id"
