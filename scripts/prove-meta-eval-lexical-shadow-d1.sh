#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: only native SENS judges eight lexical laws.
# One source form per case: report the first precise failing case.
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

# Transport-only: exact source equality outside ONE D1 bit and D2 balance.
# This code does not evaluate quote, binder lookup, or D1 semantic truth.
python3 - "$law" "$mutant" <<'PY'
from pathlib import Path
import sys
positive = Path(sys.argv[1]).read_text(encoding="utf-8")
negative = Path(sys.argv[2]).read_text(encoding="utf-8")
def forms(source: str) -> list[str]:
    return [line.strip() for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith(";")]
p, n = forms(positive), forms(negative)
if len(p) != 8 or len(n) != 8:
    raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: require eight forms, actual={len(p)}/{len(n)}")
first_expected = "(my-form-references-name? (001 (001 target)) (001 target)) #d1:0"
first_mutated = "(my-form-references-name? (001 (001 target)) (001 target)) #d1:1"
if p[0].count(first_expected) != 1 or n != [p[0].replace(first_expected, first_mutated), *p[1:]]:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: mutant must change one D1 bit, in case=1 only")
for i, text in enumerate((*p, *n), 1):
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth < 0:
            raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: premature D2 close form={i}")
    if depth:
        raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: unmatched D2 open form={i}")
print("META_LEXICAL_TRANSPORT_PASS positive_forms=8 mutant_changed_D1_bits=1 semantic_pass=NOT_INFERRED")
PY

mapfile -t forms < <(grep -v '^[[:space:]]*;' "$law" | sed '/^[[:space:]]*$/d')
mapfile -t mutant_forms < <(grep -v '^[[:space:]]*;' "$mutant" | sed '/^[[:space:]]*$/d')
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$law" "$mutant"
printf '1\n' > "$tmp/expected"
for i in "${!forms[@]}"; do
  case_no=$((i+1))
  case_id="$id-$case_no"
  { cat "$lib"; printf '\n%s\n' "${forms[$i]}"; } > "$tmp/$case_no.lisp"
  printf 'NATIVE_SENS_CASE id=%s layer=eval test_case=%s fixture=%s reproduce=%q\n' "$case_id" "$case_no" "$law" "$reproduce"
  sha256sum "$tmp/$case_no.lisp"
  if ! "$cli" "$tmp/$case_no.lisp" > "$tmp/actual" 2> "$tmp/stderr"; then
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=execution-error first_diff=unknown reproduce=%q\n' "$case_id" "$law" "$reproduce" >&2
    cat "$tmp/stderr" >&2
    sha256sum "$tmp/expected" "$tmp/actual" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_DIGESTS test_id=%s expected_sha256=' "$case_id"
  sha256sum "$tmp/expected"
  printf 'NATIVE_SENS_DIGESTS test_id=%s actual_sha256=' "$case_id"
  sha256sum "$tmp/actual"
  if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    first_diff="$(cmp "$tmp/expected" "$tmp/actual" 2>/dev/null | head -n1 || true)"
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=wrong-verdict first_diff=%q reproduce=%q\n' "$case_id" "$law" "$first_diff" "$reproduce" >&2
    exit 1
  fi
done

{ cat "$lib"; printf '\n%s\n' "${mutant_forms[0]}"; } > "$tmp/mutant-1.lisp"
sha256sum "$tmp/mutant-1.lisp"
if "$cli" "$tmp/mutant-1.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant-1 layer=eval fixture=%s expected=D1-noncallable actual=accepted first_diff=quoted-D1 reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  sha256sum "$tmp/mutant.out" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant-1 layer=eval fixture=%s expected=D1-noncallable actual=unrelated-failure first_diff=unknown reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  cat "$tmp/mutant.err" >&2
  sha256sum "$tmp/mutant.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant-1 stderr_sha256=' "$id"
sha256sum "$tmp/mutant.err"
printf 'NATIVE_SENS_PASS test_id=%s positive_forms=8 mutant=D1-noncallable authority=binary-SENS\n' "$id"
