#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: native SENS owns all lexical-dependency claims.
# This script only pins transport, source provenance and observed execution.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo "usage: bash scripts/prove-meta-eval-lexical-shadow-d1.sh [native-sens-path]" >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-lexical-shadow-d1-law.lisp
mutant=tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp
id=meta-eval-lexical-shadow-d1
reproduce="bash scripts/prove-meta-eval-lexical-shadow-d1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval expected=native-executor actual=missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
python3 - "$law" "$mutant" <<'PY'
from pathlib import Path
import sys

law = Path(sys.argv[1]).read_text(encoding="utf-8")
mutant = Path(sys.argv[2]).read_text(encoding="utf-8")
before = "(my-form-references-name? (001 (001 target)) (001 target)) #d1:0"
after = "(my-form-references-name? (001 (001 target)) (001 target)) #d1:1"
if law.count(before) != 1 or mutant != law.replace(before, after):
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: mutant must change exactly quoted datum D1:0 -> D1:1")
if law.count("(101 (my-form-references-name? ") != 5:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: expected five live single-form checks")
if law.count("(101 (my-lambda-def-references-name? ") != 3:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: expected three live definition checks")
for kind, source in (("positive", law), ("mutant", mutant)):
    depth = 0
    for raw_line in source.splitlines():
        line = raw_line.split(";", 1)[0]
        for ch in line:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth < 0:
                raise SystemExit("META_LEXICAL_TRANSPORT_RED: unmatched close in " + kind)
    if depth != 0:
        raise SystemExit("META_LEXICAL_TRANSPORT_RED: unmatched open in " + kind)
print("META_LEXICAL_TRANSPORT_PASS source_forms=8 mutant_changed_D1_bits=1 semantic_pass=NOT_INFERRED")
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
  printf 'REGRESSION id=%s-mutant layer=eval fixture=%s expected=D1-noncallable actual=accepted first_diff=quoted-D1 reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
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
printf 'NATIVE_SENS_PASS id=%s SENS_self_verdicts=8 mutant=D1-noncallable authority=SENS\n' "$id"
