#!/usr/bin/env bash
set -euo pipefail

root_dir="$(git rev-parse --show-toplevel)"
cd "$root_dir"
sens="${SENS_BIN:-$root_dir/target/debug/sens}"
[[ -x "$sens" ]] || {
  printf 'CORE1_NATIVE_MISSING sens=%s\n' "$sens" >&2
  exit 2
}

python3 - <<'PY'
import re
import sys
from pathlib import Path

def read_forms(path):
    source = strip_lisp_comments(Path(path).read_text())
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]', source)
    forms = []
    cursor = 0
    def read_one():
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError('unexpected end of source')
        if tokens[cursor] != '(':
            value = tokens[cursor]
            cursor += 1
            return value
        cursor += 1
        items = []
        while cursor < len(tokens) and tokens[cursor] != ')':
            items.append(read_one())
        if cursor == len(tokens):
            raise ValueError('unclosed list')
        cursor += 1
        return items
    while cursor < len(tokens):
        forms.append(read_one())
    return forms

def strip_lisp_comments(source):
    output = []
    in_string = False
    escaped = False
    in_comment = False
    for char in source:
        if in_comment:
            if char == '\n':
                output.append(char)
                in_comment = False
            continue
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            output.append(char)
            in_string = True
        elif char == ';':
            in_comment = True
        else:
            output.append(char)
    return ''.join(output)

try:
    core1_forms = read_forms('lib/core1.lisp')
except ValueError as error:
    print(f'CORE1_SOURCE_PARSE_ERROR {error}', file=sys.stderr)
    raise SystemExit(1)

core1_names = {
    form[1] for form in core1_forms
    if isinstance(form, list) and len(form) >= 3 and form[0] == 'визначити'
}
resident_names = {}
for path in Path('lib/domains').glob('d*.lisp'):
    try:
        tables = read_forms(path)
    except ValueError as error:
        print(f'CORE1_DOMAIN_TABLE_PARSE_ERROR file={path} error={error}', file=sys.stderr)
        raise SystemExit(1)
    for table in tables:
        if not isinstance(table, list) or not table or table[0] != 'domain-table-1':
            continue
        for row in table[1:]:
            if not isinstance(row, list) or not row or not isinstance(row[0], str):
                continue
            for surface in row[1:]:
                if (isinstance(surface, list) and len(surface) == 2
                        and surface[0] == 'укр' and isinstance(surface[1], str)):
                    resident_names.setdefault(surface[1], set()).add((path.stem, row[0]))

domain_definitions = {}
ambiguous_definitions = []
for name in sorted(core1_names & resident_names.keys()):
    identities = resident_names[name]
    if len(identities) != 1:
        ambiguous_definitions.append(name)
    else:
        domain_definitions[name] = next(iter(identities))
if ambiguous_definitions:
    print('CORE1_AMBIGUOUS_DOMAIN_DEFINITION ' + ' '.join(ambiguous_definitions), file=sys.stderr)
    raise SystemExit(1)
domain_definition_summary = ','.join(
    f'{name}@{domain}:{bits}'
    for name, (domain, bits) in sorted(domain_definitions.items())
)

special_forms = {'визначити', 'функція', 'мітка', 'за-умовою', 'як-є'}
unresolved = []
def check_expression(expr, bound, owner):
    if not isinstance(expr, list) or not expr:
        return
    head = expr[0]
    # Quoted forms are data and are not callable references.
    if head == 'як-є':
        return
    if head == 'функція':
        parameters = set(expr[1][1:]) if len(expr) > 1 and isinstance(expr[1], list) else set()
        for body in expr[2:]:
            check_expression(body, bound | parameters, owner)
        return
    if head == 'мітка':
        for body in expr[2:]:
            check_expression(body, bound | {expr[1]}, owner)
        return
    if head == 'за-умовою':
        for clause in expr[1:]:
            if isinstance(clause, list):
                for item in clause:
                    check_expression(item, bound, owner)
        return
    if (isinstance(head, str) and head not in special_forms
            and head not in core1_names and head not in resident_names
            and head not in bound and not head.startswith(':')
            and not re.fullmatch(r'-?\d+', head)):
        unresolved.append((owner, head))
    if isinstance(head, list):
        check_expression(head, bound, owner)
    for argument in expr[1:]:
        check_expression(argument, bound, owner)

for form in core1_forms:
    if isinstance(form, list) and len(form) >= 3 and form[0] == 'визначити':
        check_expression(form[2], set(), form[1])
if unresolved:
    details = ' '.join(f'{owner}:{name}' for owner, name in sorted(set(unresolved)))
    print('CORE1_UNRESOLVED_CALLS ' + details, file=sys.stderr)
    raise SystemExit(1)
print(f'CORE1_STATIC_AUDIT_OK definitions={len(core1_names)} domain_residents={len(resident_names)} core1_source_domain_definitions={len(domain_definitions)} exact_bindings={domain_definition_summary or "none"} unresolved_calls=0 ambiguous_domain_definitions=0')
PY

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT

cat lib/core1.lisp tests/integration/core1/core1-local-variable.lisp \
  > "$scratch/core1-standalone.lisp"
"$sens" --t5m-mint \
  "$scratch/core1-standalone.lisp" \
  "$scratch/core1-standalone.sens"
"$sens" "$scratch/core1-standalone.sens" > "$scratch/core1-standalone.out"
printf '%s\n' '((2 3) 1 7 1 ((0 0 0) 0 (0 9 0) 1 1) 9 (7 7 99 11 () 4 5))' > "$scratch/core1-standalone.expected"
cmp -s "$scratch/core1-standalone.expected" "$scratch/core1-standalone.out" || {
  echo 'CORE1_STANDALONE_LOCAL_VARIABLE_MISMATCH' >&2
  diff -u "$scratch/core1-standalone.expected" "$scratch/core1-standalone.out" >&2 || true
  exit 1
}

"$sens" --t5m-mint tests/integration/core1/core1-list-length.lisp \
  "$scratch/core1-list-length-fixture.sens"
cmp -s "$scratch/core1-list-length-fixture.sens" \
  tests/integration/core1/core1-list-length.sens || {
  echo 'CORE1_LIST_LENGTH_T5M_PAIR_MISMATCH' >&2
  exit 1
}
"$sens" --t5m-files lib/core1.lisp \
  tests/integration/core1/core1-list-length.lisp \
  > "$scratch/core1-list-length.out"
printf '%s\n' '(5 5 0)' > "$scratch/core1-list-length.expected"
cmp -s "$scratch/core1-list-length.expected" \
  "$scratch/core1-list-length.out" || {
  echo 'CORE1_LIST_LENGTH_MISMATCH' >&2
  diff -u "$scratch/core1-list-length.expected" \
    "$scratch/core1-list-length.out" >&2 || true
  exit 1
}

"$sens" --t5m-mint tests/integration/core1/core1-reverse.lisp \
  "$scratch/core1-reverse-fixture.sens"
cmp -s "$scratch/core1-reverse-fixture.sens" \
  tests/integration/core1/core1-reverse.sens || {
  echo 'CORE1_REVERSE_T5M_PAIR_MISMATCH' >&2
  exit 1
}
"$sens" --t5m-files lib/core1.lisp \
  tests/integration/core1/core1-reverse.lisp \
  > "$scratch/core1-reverse.out"
printf '%s\n' '(1 1 1)' > "$scratch/core1-reverse.expected"
cmp -s "$scratch/core1-reverse.expected" \
  "$scratch/core1-reverse.out" || {
  echo 'CORE1_REVERSE_MISMATCH' >&2
  diff -u "$scratch/core1-reverse.expected" \
    "$scratch/core1-reverse.out" >&2 || true
  exit 1
}

"$sens" --t5m-mint tests/integration/core1/core1-append.lisp \
  "$scratch/core1-append-fixture.sens"
cmp -s "$scratch/core1-append-fixture.sens" \
  tests/integration/core1/core1-append.sens || {
  echo 'CORE1_APPEND_T5M_PAIR_MISMATCH' >&2
  exit 1
}
"$sens" --t5m-files lib/core1.lisp \
  tests/integration/core1/core1-append.lisp \
  > "$scratch/core1-append.out"
printf '%s\n' '(1 1 1)' > "$scratch/core1-append.expected"
cmp -s "$scratch/core1-append.expected" \
  "$scratch/core1-append.out" || {
  echo 'CORE1_APPEND_MISMATCH' >&2
  diff -u "$scratch/core1-append.expected" \
    "$scratch/core1-append.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-array-boundaries.lisp \
  > "$scratch/core1-array-boundaries.lisp"
"$sens" --t5m-mint \
  tests/integration/core1/core1-array-boundaries.lisp \
  "$scratch/core1-array-boundaries-fixture.sens"
cmp -s "$scratch/core1-array-boundaries-fixture.sens" \
  tests/integration/core1/core1-array-boundaries.sens || {
  echo 'CORE1_ARRAY_BOUNDARY_T5M_PAIR_MISMATCH' >&2
  exit 1
}
"$sens" --t5m-mint \
  "$scratch/core1-array-boundaries.lisp" \
  "$scratch/core1-array-boundaries.sens"
"$sens" --t5m-pair \
  "$scratch/core1-array-boundaries.lisp" \
  "$scratch/core1-array-boundaries.sens" \
  > "$scratch/core1-array-boundaries.out"
printf '%s\n' '(1 1 1 0 () 10 (10 20 99) 1 1 1)' \
  > "$scratch/core1-array-boundaries.expected"
cmp -s "$scratch/core1-array-boundaries.expected" \
  "$scratch/core1-array-boundaries.out" || {
  echo 'CORE1_ARRAY_BOUNDARY_MISMATCH' >&2
  diff -u "$scratch/core1-array-boundaries.expected" \
    "$scratch/core1-array-boundaries.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-properties.lisp \
  > "$scratch/core1-properties.lisp"
"$sens" --t5m-mint "$scratch/core1-properties.lisp" "$scratch/core1-properties.sens"
"$sens" "$scratch/core1-properties.sens" > "$scratch/core1-properties.out"
printf '%s\n' '(43 44 43 0 ())' > "$scratch/core1-properties.expected"
cmp -s "$scratch/core1-properties.expected" "$scratch/core1-properties.out" || {
  echo 'CORE1_PROPERTY_LIST_MISMATCH' >&2
  diff -u "$scratch/core1-properties.expected" "$scratch/core1-properties.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-reader-markers.lisp \
  > "$scratch/core1-reader-markers.lisp"
"$sens" --t5m-mint "$scratch/core1-reader-markers.lisp" "$scratch/core1-reader-markers.sens"
"$sens" "$scratch/core1-reader-markers.sens" > "$scratch/core1-reader-markers.out"
printf '%s\n' '(1 1)' > "$scratch/core1-reader-markers.expected"
cmp -s "$scratch/core1-reader-markers.expected" "$scratch/core1-reader-markers.out" || {
  echo 'CORE1_READER_MARKER_MISMATCH' >&2
  diff -u "$scratch/core1-reader-markers.expected" "$scratch/core1-reader-markers.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-condition-domains.lisp \
  > "$scratch/core1-condition-domains.lisp"
"$sens" --t5m-mint "$scratch/core1-condition-domains.lisp" "$scratch/core1-condition-domains.sens"
"$sens" "$scratch/core1-condition-domains.sens" > "$scratch/core1-condition-domains.out"
printf '%s\n' '(22 11 1)' > "$scratch/core1-condition-domains.expected"
cmp -s "$scratch/core1-condition-domains.expected" "$scratch/core1-condition-domains.out" || {
  echo 'CORE1_CONDITION_DOMAIN_MISMATCH' >&2
  diff -u "$scratch/core1-condition-domains.expected" "$scratch/core1-condition-domains.out" >&2 || true
  exit 1
}

check_core1_condition_rejection() {
  local source="$1"
  if "$sens" --t5m-files lib/core1.lisp "$source" \
      > "$scratch/core1-condition-negative.out" 2> "$scratch/core1-condition-negative.err"; then
    printf 'CORE1_INVALID_CONDITION_ACCEPTED source=%s\n' "$source" >&2
    exit 1
  fi
  grep -Fq 'D4:0100 NOT requires an exact D1 PredicateBit' "$scratch/core1-condition-negative.err" || {
    printf 'CORE1_WRONG_CONDITION_REJECTION source=%s\n' "$source" >&2
    cat "$scratch/core1-condition-negative.err" >&2
    exit 1
  }
}

check_core1_condition_rejection tests/integration/core1/reject-core1-cond-empty.lisp
check_core1_condition_rejection tests/integration/core1/reject-core1-cond-number-zero.lisp

cat lib/core1.lisp tests/integration/core1/core1-call-arity.lisp \
  > "$scratch/core1-call-arity.lisp"
"$sens" --t5m-mint "$scratch/core1-call-arity.lisp" "$scratch/core1-call-arity.sens"
"$sens" "$scratch/core1-call-arity.sens" > "$scratch/core1-call-arity.out"
printf '%s\n' '(8 1 1)' > "$scratch/core1-call-arity.expected"
cmp -s "$scratch/core1-call-arity.expected" "$scratch/core1-call-arity.out" || {
  echo 'CORE1_CALL_ARITY_MISMATCH' >&2
  diff -u "$scratch/core1-call-arity.expected" "$scratch/core1-call-arity.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-d7-callability.lisp \
  > "$scratch/core1-d7-callability.lisp"
"$sens" --t5m-mint \
  "$scratch/core1-d7-callability.lisp" \
  "$scratch/core1-d7-callability.sens"
"$sens" "$scratch/core1-d7-callability.sens" > "$scratch/core1-d7-callability.out"
printf '%s\n' '(22 33 44)' > "$scratch/core1-d7-callability.expected"
cmp -s "$scratch/core1-d7-callability.expected" "$scratch/core1-d7-callability.out" || {
  echo 'CORE1_D7_DOMAIN_FUNCTION_MISMATCH' >&2
  diff -u "$scratch/core1-d7-callability.expected" "$scratch/core1-d7-callability.out" >&2 || true
  exit 1
}

if "$sens" --t5m-files \
    lib/core1.lisp \
    tests/integration/core1/reject-core1-d7-as-function.lisp \
    > "$scratch/core1-d7-negative.out" 2> "$scratch/core1-d7-negative.err"; then
  echo 'CORE1_ACCEPTED_D7_TEXT_AS_FUNCTION' >&2
  exit 1
fi
grep -Fq 'D7 1100110 не має допущеного механізму виклику' \
  "$scratch/core1-d7-negative.err" || {
  echo 'CORE1_D7_REJECTION_DIAGNOSTIC_MISMATCH' >&2
  cat "$scratch/core1-d7-negative.err" >&2
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-prog-coverage.lisp \
  > "$scratch/core1-prog-coverage.lisp"
"$sens" --t5m-mint \
  "$scratch/core1-prog-coverage.lisp" \
  "$scratch/core1-prog-coverage.sens"
"$sens" "$scratch/core1-prog-coverage.sens" > "$scratch/core1-prog-coverage.out"
printf '%s\n' '(7 42 1 1 ())' > "$scratch/core1-prog-coverage.expected"
cmp -s "$scratch/core1-prog-coverage.expected" "$scratch/core1-prog-coverage.out" || {
  echo 'CORE1_PROG_COVERAGE_MISMATCH' >&2
  diff -u "$scratch/core1-prog-coverage.expected" "$scratch/core1-prog-coverage.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/integration/core1/core1-prog-rev.lisp \
  > "$scratch/core1-prog-rev.lisp"
"$sens" --t5m-mint "$scratch/core1-prog-rev.lisp" "$scratch/core1-prog-rev.sens"
"$sens" "$scratch/core1-prog-rev.sens" > "$scratch/core1-prog-rev.out"
printf '%s\n' '1' > "$scratch/core1-prog-rev.expected"
cmp -s "$scratch/core1-prog-rev.expected" "$scratch/core1-prog-rev.out" || {
  echo 'CORE1_PROG_RECURSIVE_REV_MISMATCH' >&2
  diff -u "$scratch/core1-prog-rev.expected" "$scratch/core1-prog-rev.out" >&2 || true
  exit 1
}

cat lib/core1.lisp tests/semantic/core1-gc-reachability-laws.lisp \
  > "$scratch/core1-gc.lisp"
"$sens" --t5m-mint "$scratch/core1-gc.lisp" "$scratch/core1-gc.sens"
"$sens" "$scratch/core1-gc.sens" > "$scratch/core1-gc.out"
printf '%s\n' '1' > "$scratch/core1-gc.expected"
cmp -s "$scratch/core1-gc.expected" "$scratch/core1-gc.out" || {
  echo 'CORE1_GC_REACHABILITY_MISMATCH' >&2
  diff -u "$scratch/core1-gc.expected" "$scratch/core1-gc.out" >&2 || true
  exit 1
}

echo 'CORE1_NATIVE_OK self_loaded=YES arrays=YES array_boundaries=YES properties=YES reader_markers=YES exact_conditions=YES call_arity=YES domain_functions=YES d7_data_not_callable=YES gc_model=YES exact_domains=YES negatives=3'
