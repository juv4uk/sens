#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: laws and mutants execute in SENS; Zig/T5M only transports.
set -euo pipefail
cd "$(dirname "$0")/.."

cli="${1:-target/debug/sens}"
trit="${2:-target/debug/sens-trit}"
id=lisp-semantic-t5m
law=tests/semantic/d9-string-append-physical.lisp
mutant=tests/semantic/d9-string-append-physical-mutant.lisp

for executable in "$cli" "$trit"; do
  if [[ ! -x "$executable" ]]; then
    printf 'REGRESSION test_id=%s layer=executor actual=missing path=%s\n' "$id" "$executable" >&2
    exit 1
  fi
done
for source in "$law" "$mutant"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    printf 'REGRESSION test_id=%s layer=source actual=missing-or-symlink path=%s\n' "$id" "$source" >&2
    exit 1
  fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

prove_one() {
  local name="$1" source="$2" expected="$3"
  local base="$tmp/$name" physical="$tmp/$name.sens"
  printf '%s\n' "$expected" > "$base.expected"

  if ! timeout 45s "$cli" "$source" > "$base.direct" 2> "$base.direct.err"; then
    printf 'REGRESSION id=%s layer=sens-direct actual=execution-error source=%s\n' "$name" "$source" >&2
    cat "$base.direct.err" >&2
    return 1
  fi
  if ! cmp -s "$base.expected" "$base.direct"; then
    printf 'REGRESSION id=%s layer=sens-direct expected=%s actual=divergent\n' "$name" "$expected" >&2
    return 1
  fi

  if ! timeout 45s "$cli" --t5m-pair "$source" "$physical" > "$base.paired" 2> "$base.paired.err"; then
    printf 'REGRESSION id=%s layer=zig-t5m-pair actual=execution-error source=%s\n' "$name" "$source" >&2
    cat "$base.paired.err" >&2
    return 1
  fi
  if [[ ! -s "$physical" ]]; then
    printf 'REGRESSION id=%s layer=physical-pair actual=missing-output\n' "$name" >&2
    return 1
  fi
  if ! cmp -s "$base.expected" "$base.paired"; then
    printf 'REGRESSION id=%s layer=zig-t5m-pair expected=%s actual=divergent\n' "$name" "$expected" >&2
    return 1
  fi
  if ! cmp -s "$base.direct" "$base.paired"; then
    printf 'REGRESSION id=%s layer=carrier-parity actual=divergent\n' "$name" >&2
    return 1
  fi

  if ! timeout 45s "$trit" eval "$physical" > "$base.standalone" 2> "$base.standalone.err"; then
    printf 'REGRESSION id=%s layer=sens-trit-standalone actual=execution-error\n' "$name" >&2
    cat "$base.standalone.err" >&2
    return 1
  fi
  if ! cmp -s "$base.expected" "$base.standalone"; then
    printf 'REGRESSION id=%s layer=sens-trit-standalone expected=%s actual=divergent\n' "$name" "$expected" >&2
    return 1
  fi
  printf 'NATIVE_SENS_PASS id=%s result=%s direct=PASS paired=PASS standalone=PASS comparison=cmp\n' "$name" "$expected"
}

prove_one lisp-semantic-t5m-positive "$law" 1
prove_one lisp-semantic-t5m-mutant "$mutant" 0
printf 'NATIVE_SENS_PHYSICAL_PAIR_PASS id=%s checks=positive-mutant paths=direct-paired-standalone\n' "$id"
