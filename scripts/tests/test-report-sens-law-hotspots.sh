#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
tool="$repo/scripts/report-sens-law-hotspots.sh"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/ev"
printf 'id\tstatus\twall_ms\nalpha\tPASS\t20\nbeta\tRED\t30\nexpected-type-negative\tPASS\t10\n' > "$tmp/ev/law-timings.tsv"
printf 'id\tstage\texit\telapsed_us\nalpha\tdirect\t0\t100\nbeta\tdirect\t2\t300\nbeta\tsens-paired-core4-diagnostic\t0\t250\nexpected-type-negative\tdirect\t1\t200\nalpha\tzig-open\t0\t15\nbeta\tzig-open\t0\t25\nexpected-type-negative\tsens-paired\t1\t210\nexpected-type-negative\tsens-standalone-sens\t1\t220\nalpha\tsens-standalone-trit-core4\t0\t310\nbeta\tsens-standalone\t1\t190\n' > "$tmp/ev/law-stage-timings.tsv"
bash "$tool" "$tmp/ev" "$tmp/report.md" > "$tmp/log"
grep -Fq '| direct | 3 | 2 | 200 | 300 | 300 |' "$tmp/report.md"
grep -Fq '| zig-open | 2 | 0 | 15 | 25 | 25 |' "$tmp/report.md"
grep -Fq '| beta | direct | 2 | RED | 300 |' "$tmp/report.md"
grep -Fq '| sens-paired | 1 | 1 | 210 | 210 | 210 |' "$tmp/report.md"
grep -Fq '| sens-paired-core4-diagnostic | 1 | 0 | 250 | 250 | 250 |' "$tmp/report.md"
grep -Fq 'Type-negative' "$tmp/report.md"
grep -Fq 'SENS_PHASE_BENCHMARK stage=direct count=3 nonzero_exit=2' "$tmp/log"
grep -Fq 'SENS_PHASE_BENCHMARK_SUMMARY checked=3 passed=2 red=1' "$tmp/log"
# Негативні Type-відхилення за 200/300 мкс не знижують p50 успішного direct=100.
grep -Fq '| direct | exit=0 | 1 | 100 | 100 | 100 |' "$tmp/report.md"
grep -Fq '| direct | exit!=0 | 2 | 200 | 300 | 300 |' "$tmp/report.md"
grep -Fq '| zig-open | exit=0 | 2 | 15 | 25 | 25 |' "$tmp/report.md"
grep -Fq '| sens-standalone-sens | exit!=0 | 1 | 220 | 220 | 220 |' "$tmp/report.md"
grep -Fq '| sens-standalone-trit-core4 | exit=0 | 1 | 310 | 310 | 310 |' "$tmp/report.md"
grep -Fq '| sens-standalone | exit!=0 | 1 | 190 | 190 | 190 |' "$tmp/report.md"
grep -Fq 'SENS_PHASE_EXIT_CLASS stage=sens-standalone-trit-core4 exit_class=zero count=1 p50_us=310' "$tmp/log"
grep -Fq 'SENS_PHASE_EXIT_CLASS stage=direct exit_class=zero count=1 p50_us=100' "$tmp/log"
grep -Fq 'SENS_PHASE_EXIT_CLASS stage=direct exit_class=nonzero count=2 p50_us=200' "$tmp/log"
printf 'bad\trow\n' >> "$tmp/ev/law-stage-timings.tsv"
if bash "$tool" "$tmp/ev" "$tmp/invalid.md" > "$tmp/invalid.out" 2>&1; then
 echo 'REPORTER_TEST_FAILED: malformed evidence was accepted' >&2; exit 1
fi
echo 'REPORTER_TEST_PASS checks=18 evidence=synthetic reporting_only=true'
