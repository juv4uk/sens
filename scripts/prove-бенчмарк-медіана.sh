#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: час і звірка D1 для закону, виконаного native SENS.
# Немає Python, JSON, хешів чи постійних звітів; тимчасові зразки видаляються.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=бенчмарк-медіана
library=lib/бенчмарк.lisp
law=tests/semantic/бенчмарк-медіана-law.lisp
mutant=tests/semantic/бенчмарк-медіана-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION id=%s layer=executor actual=missing path=%s\n' "$id" "$cli" >&2
  exit 1
fi
for source in "$library" "$law" "$mutant"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    printf 'REGRESSION id=%s layer=source actual=missing-or-symlink path=%s\n' "$id" "$source" >&2
    exit 1
  fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected-positive"
printf '0\n' > "$tmp/expected-negative"

if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$library" "$law" > "$tmp/positive.out" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=sens-positive actual=execution-error\n' "$id" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-positive" "$tmp/positive.out"; then
  printf 'REGRESSION id=%s layer=sens-positive expected=D1:так actual=divergent\n' "$id" >&2
  exit 1
fi

if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$library" "$mutant" > "$tmp/negative.out" 2> "$tmp/negative.err"; then
  printf 'REGRESSION id=%s layer=sens-negative actual=execution-error\n' "$id" >&2
  cat "$tmp/negative.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-negative" "$tmp/negative.out"; then
  printf 'REGRESSION id=%s layer=sens-negative expected=D1:ні actual=divergent\n' "$id" >&2
  exit 1
fi

for iteration in {1..11}; do
  start_us="${EPOCHREALTIME/./}"
  if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$library" "$law" > "$tmp/sample.out" 2> "$tmp/sample.err"; then
    printf 'REGRESSION id=%s layer=benchmark iteration=%s actual=execution-error\n' "$id" "$iteration" >&2
    cat "$tmp/sample.err" >&2
    exit 1
  fi
  end_us="${EPOCHREALTIME/./}"
  if ! cmp -s "$tmp/expected-positive" "$tmp/sample.out"; then
    printf 'REGRESSION id=%s layer=benchmark iteration=%s expected=D1:так actual=divergent\n' "$id" "$iteration" >&2
    exit 1
  fi
  printf '%s\n' "$((end_us - start_us))" >> "$tmp/elapsed"
done
mapfile -t sorted_wall < <(sort -n "$tmp/elapsed")
if (( ${#sorted_wall[@]} != 11 )); then
  printf 'REGRESSION id=%s layer=benchmark expected=11-samples actual=%s\n' "$id" "${#sorted_wall[@]}" >&2
  exit 1
fi
printf 'БЕНЧМАРК_МЕДІАНА=PASS native=SENS libraries=lib/твердження.lisp+lib/бенчмарк.lisp positive=D1:так mutant=D1:ні samples=11 p50_us=%s p90_us=%s\n' "${sorted_wall[5]}" "${sorted_wall[9]}"
