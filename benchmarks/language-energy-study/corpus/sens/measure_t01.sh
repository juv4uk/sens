#!/usr/bin/env bash
# ENERGY-02 / #6287. Physical T01 cold-process timing; no SENS semantic oracle.
# A measured n=24 run is never accepted on the basis of the n=12 VERIFY run.
set -euo pipefail

if (( $# > 2 )); then
  printf 'usage: %s [path/to/sens] [output-directory]\n' "$0" >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$root"
cli="${1:-target/release/sens}"
out="${2:-.ci-metrics/sens-t01-cold}"

if [[ ! -x "$cli" ]]; then
  printf 'BLOCKED missing_executable=%s\n' "$cli" >&2
  exit 1
fi
cli="$(cd "$(dirname "$cli")" && pwd)/$(basename "$cli")"
for executable in /usr/bin/time timeout awk git uname; do
  if ! command -v "$executable" > /dev/null 2>&1; then
    printf 'BLOCKED missing_tool=%s\n' "$executable" >&2
    exit 1
  fi
done

src="benchmarks/language-energy-study/corpus/sens"
verify="$src/t01_fib.lisp"
measure="$src/t01_fib_measure.lisp"
if [[ ! -f "$verify" || ! -f "$measure" ]]; then
  printf 'BLOCKED missing_T01_source\n' >&2
  exit 1
fi

# Linux GNU time reports one child process's maximum RSS in KiB, not its
# descendants or total system memory. Both observations include process start.
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

if ! timeout 90s "$cli" --t5m-mint "$verify" "$tmp/verify.sens" > "$tmp/mint-verify.out" 2> "$tmp/mint-verify.err"; then
  printf 'BLOCKED mint_verify_failed\n' >&2
  cat "$tmp/mint-verify.err" >&2
  exit 1
fi
if ! timeout 90s "$cli" --t5m-mint "$measure" "$tmp/measure.sens" > "$tmp/mint-measure.out" 2> "$tmp/mint-measure.err"; then
  printf 'BLOCKED mint_measure_failed\n' >&2
  cat "$tmp/mint-measure.err" >&2
  exit 1
fi
for artifact in "$tmp/verify.sens" "$tmp/measure.sens"; do
  if [[ ! -s "$artifact" ]]; then
    printf 'BLOCKED minted_file_empty=%s\n' "$artifact" >&2
    exit 1
  fi
done

# External byte-output parity is a precondition for PHYSICAL comparison; it
# does not assert language semantics (SENS positive/negative witnesses do).
check_output() {
  local expected="$1" actual="$2" label="$3"
  if ! printf '%s\n' "$expected" | cmp -s - "$actual"; then
    printf 'BLOCKED output_mismatch task=T01 case=%s expected=%s\n' "$label" "$expected" >&2
    cat "$actual" >&2
    exit 1
  fi
}

if ! timeout 90s "$cli" "$tmp/verify.sens" > "$tmp/verify.out" 2> "$tmp/verify.err"; then
  printf 'BLOCKED SENS_verify_execution_failed\n' >&2
  cat "$tmp/verify.err" >&2
  exit 1
fi
check_output 144 "$tmp/verify.out" verify_n12
if ! timeout 90s "$cli" "$tmp/measure.sens" > "$tmp/measure.out" 2> "$tmp/measure.err"; then
  printf 'BLOCKED SENS_measure_preflight_failed\n' >&2
  cat "$tmp/measure.err" >&2
  exit 1
fi
check_output 46368 "$tmp/measure.out" measure_n24

mkdir -p "$out"
out="$(cd "$out" && pwd)"
sha="$(git rev-parse HEAD)"
{
  printf 'repository_sha\t%s\n' "$sha"
  printf 'source_verify\t%s\n' "$verify"
  printf 'source_measure\t%s\n' "$measure"
  printf 'functional_unit\tT01 naive Fibonacci n=24\n'
  printf 'verification\tT01 n=12 -> 144; measure n=24 -> 46368; exact stdout\n'
  printf 'measurement_boundary\tseparate cold process incl. startup; prior verification warms CPU/cache\n'
  printf 'samples\t5 process launches in ONE session (not independent sessions)\n'
  printf 'energy\tENERGY_NOT_MEASURED (no sensor integration in this harness)\n'
  printf 'rss_scope\tGNU time %%M KiB, peak child-process resident set\n'
  printf 'os\t%s\n' "$(uname -srmo)"
  printf 'cpu\t%s\n' "$(awk -F: '/^model name/{gsub(/^[ \t]+/, "", $2);print $2;exit}' /proc/cpuinfo)"
  printf 'sens_version\t%s\n' "$("$cli" --version 2>/dev/null | head -n 1)"
} > "$out/environment.tsv"

printf 'sample\telapsed_seconds\tpeak_rss_kib\tuser_seconds\tsystem_seconds\n' > "$out/samples.tsv"
for trial in 1 2 3 4 5; do
  # The measured program is the child of /usr/bin/time; timeout is an outer
  # guard only. Output and every field are independently checked per trial.
  if ! timeout 90s /usr/bin/time -f '%e\t%M\t%U\t%S' -o "$tmp/metrics" \
    "$cli" "$tmp/measure.sens" > "$tmp/stdout" 2> "$tmp/stderr"; then
    printf 'BLOCKED sample_failed=%s\n' "$trial" >&2
    cat "$tmp/stderr" >&2
    exit 1
  fi
  check_output 46368 "$tmp/stdout" "measure_n24_sample_$trial"
  if ! awk -F '\t' 'NF != 4 {exit 1} $1 !~ /^[0-9]+(\.[0-9]+)?$/ {exit 1} $2 !~ /^[0-9]+$/ {exit 1} $3 !~ /^[0-9]+(\.[0-9]+)/$/ {exit 1} $4 !~ /^[0-9]+(\.[0-9]+)?$/ {exit 1} END {if (NR != 1) exit 1}' "$tmp/metrics"; then
    printf 'BLOCKED invalid_GNU_time_sample=%s\n' "$trial" >&2
    exit 1
  fi
  printf '%s\t%s\n' "$trial" "$(cat "$tmp/metrics")" >> "$out/samples.tsv"
done
printf 'T01_COLD_RSS_EXPLORATORY sha=%s samples=5 raw=%s energy=ENERGY_NOT_MEASURED\n' "$sha" "$out/samples.tsv"
