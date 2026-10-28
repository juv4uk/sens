#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: структурний бенчмарк виконує лише нативний SENS.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=бенчмарк-структура
law=tests/semantic/бенчмарк-структура-law.lisp
mutant=tests/semantic/бенчмарк-структура-mutant.lisp

if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=executor actual=missing path=%s\n' "$id" "$cli" >&2
  exit 1
fi
for source in "$law" "$mutant"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    printf 'REGRESSION test_id=%s layer=source actual=missing-or-symlink path=%s\n' "$id" "$source" >&2
    exit 1
  fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected-positive"
printf '0\n' > "$tmp/expected-negative"

if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$law" > "$tmp/positive.out" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=sens-positive actual=execution-error\n' "$id" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-positive" "$tmp/positive.out"; then
  printf 'REGRESSION id=%s layer=sens-positive expected=D1:так actual=divergent\n' "$id" >&2
  exit 1
fi

if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$mutant" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=sens-negative actual=execution-error\n' "$id" >&2
  cat "$tmp/mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-negative" "$tmp/mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=sens-negative expected=D1:ні actual=divergent\n' "$id" >&2
  exit 1
fi

printf 'sample\telapsed_us\tstdout_bytes\n' > "$tmp/samples.tsv"
for iteration in {1..11}; do
  start_us="${EPOCHREALTIME/./}"
  if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$law" > "$tmp/sample-$iteration.out" 2> "$tmp/sample-$iteration.err"; then
    printf 'REGRESSION id=%s layer=sens-repeat iteration=%s actual=execution-error\n' "$id" "$iteration" >&2
    cat "$tmp/sample-$iteration.err" >&2
    exit 1
  fi
  end_us="${EPOCHREALTIME/./}"
  if ! cmp -s "$tmp/expected-positive" "$tmp/sample-$iteration.out"; then
    printf 'REGRESSION id=%s layer=sens-repeat iteration=%s expected=D1:так actual=divergent\n' "$id" "$iteration" >&2
    exit 1
  fi
  sample_bytes="$(wc -c < "$tmp/sample-$iteration.out" | tr -d '[:space:]')"
  printf '%s\t%s\t%s\n' "$iteration" "$((end_us - start_us))" "$sample_bytes" >> "$tmp/samples.tsv"
done
mapfile -t sorted_wall < <(tail -n +2 "$tmp/samples.tsv" | cut -f2 | sort -n)
if (( ${#sorted_wall[@]} != 11 )); then
  printf 'REGRESSION id=%s layer=benchmark expected=11-samples actual=%s\n' "$id" "${#sorted_wall[@]}" >&2
  exit 1
fi
# Export unaggregated measurements only after both SENS-owned verdicts pass.
# This is evidence for time, NOT an independent host-language semantic law.
if [[ -n "${SENS_BENCH_SAMPLES_OUT:-}" ]]; then
  if [[ -L "$SENS_BENCH_SAMPLES_OUT" ]]; then
    echo 'REGRESSION id=бенчмарк-структура layer=evidence actual=symlink-destination' >&2
    exit 1
  fi
  cp -- "$tmp/samples.tsv" "$SENS_BENCH_SAMPLES_OUT"
fi
printf 'БЕНЧМАРК_СТРУКТУРА=PASS native=SENS positive=D1:так mutant=D1:ні samples=11 p50_us=%s p90_us=%s output=cmp\n' "${sorted_wall[5]}" "${sorted_wall[9]}"
