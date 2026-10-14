#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: only native SENS judges eight lexical laws.
# One source form per case: report the first precise failing case.
set -euo pipefail
cd "$(dirname "$0")/.."
fixture_only=false
if [[ "${1:-}" == "--check-fixtures" ]]; then
  fixture_only=true
elif [[ $# -gt 1 ]]; then
  echo "usage: bash scripts/prove-meta-eval-lexical-shadow-d1.sh [native-sens-path|--check-fixtures]" >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-lexical-shadow-d1-law.lisp
mutant=tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp
mutants=tests/semantic/meta-eval-lexical-shadow-d1-mutants.lisp
id=meta-eval-lexical-shadow-d1
reproduce="bash scripts/prove-meta-eval-lexical-shadow-d1.sh $cli"


# Transport-only: exact source equality outside ONE D1 bit and D2 balance.
# This code does not evaluate quote, binder lookup, or D1 semantic truth.
python3 - "$law" "$mutant" "$mutants" "$lib" <<'PY'
from pathlib import Path
import re
import sys
import hashlib
def forms(path):
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith(";")]
positive, first_mutant, negatives = map(forms, sys.argv[1:])
if len(positive) != 8 or len(first_mutant) != 8 or len(negatives) != 8:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: require eight forms in every source")
pattern = re.compile(r" #d1:([01])\) #d1:1\) \(#d1:1 \(#d1:0\)\)\)$")
def flip_expected(form):
    matches = list(pattern.finditer(form))
    if len(matches) != 1:
        raise SystemExit("META_LEXICAL_TRANSPORT_RED: ambiguous D1 EQ expectation")
    match = matches[0]
    new = "0" if match.group(1) == "1" else "1"
    return form[:match.start(1)] + new + form[match.end(1):]
if negatives != [flip_expected(form) for form in positive]:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: each negative must change exactly its own D1 bit")
if first_mutant != [negatives[0], *positive[1:]]:
    raise SystemExit("META_LEXICAL_TRANSPORT_RED: prior one-bit mutant provenance mismatch")
# Fixture integrity only: never infer the meaning of a D1/D3 value from Python.
# Pin each source call to its actual, still named library definition.
library = Path(sys.argv[4]).read_bytes()
expected_heads = (["my-form-references-name?"] * 5
                  + ["my-lambda-def-references-name?"] * 3)
for i, (head, form) in enumerate(zip(expected_heads, positive), 1):
    if not form.startswith("(110 ((101 (" + head + " "):
        raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: wrong live call-head case={i}")
    if ("(0011 " + head + "\n").encode("ascii") not in library:
        raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: current library missing definition case={i}")
for case, form in enumerate((*positive, *negatives), 1):
    depth = 0
    for ch in form:
        if ch == "(": depth += 1
        elif ch == ")": depth -= 1
        if depth < 0: raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: early D2 close case={case}")
    if depth: raise SystemExit(f"META_LEXICAL_TRANSPORT_RED: open D2 frame case={case}")
for i, (good, wrong) in enumerate(zip(positive, negatives), 1):
    for role, expression in (("law", good), ("mutant", wrong)):
        payload = library + b"\n" + expression.encode("utf-8") + b"\n"
        sha = hashlib.sha256(payload).hexdigest()
        print(f"META_LEXICAL_SOURCE_SHA case={i} role={role} sha256={sha}")
print("META_LEXICAL_TRANSPORT_PASS positive_forms=8 one-bit-mutants=8 semantic_pass=NOT_INFERRED")
PY

if [[ "$fixture_only" == true ]]; then
  printf 'META_LEXICAL_FIXTURES_VERIFIED_ONLY positive_forms=8 negative_forms=8 semantic_pass=NOT_RUN\n'
  exit 0
fi
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval expected=native-executor actual=missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
mapfile -t forms < <(grep -v '^[[:space:]]*;' "$law" | sed '/^[[:space:]]*$/d')
mapfile -t mutant_forms < <(grep -v '^[[:space:]]*;' "$mutants" | sed '/^[[:space:]]*$/d')
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$law" "$mutant" "$mutants"
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
  { cat "$lib"; printf '\n%s\n' "${mutant_forms[$i]}"; } > "$tmp/mutant-$case_no.lisp"
  printf 'NATIVE_SENS_MUTANT id=%s-mutant-%s fixture=%s reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce"
  sha256sum "$tmp/mutant-$case_no.lisp"
  if "$cli" "$tmp/mutant-$case_no.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
    printf 'REGRESSION test_id=%s-mutant-%s layer=eval fixture=%s expected=D1-noncallable actual=accepted first_diff=D1-EQ-expected-bit reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce" >&2
    sha256sum "$tmp/mutant.out" >&2
    exit 1
  fi
  if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
    printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant-%s layer=eval fixture=%s expected=D1-noncallable actual=unrelated-failure first_diff=unknown reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce" >&2
    cat "$tmp/mutant.err" >&2
    sha256sum "$tmp/mutant.err" "$tmp/mutant.out" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant-%s expected=D1-noncallable stderr_sha256=' "$id" "$case_no"
  sha256sum "$tmp/mutant.err"
done
printf 'NATIVE_SENS_PASS test_id=%s positive_forms=8 negative_forms=8 mutant=D1-noncallable authority=SENS\n' "$id"
