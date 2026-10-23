#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
tool="$repo/scripts/report-sens-law-hotspots.sh"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/ev"
printf 'id\tstatus\twall_ms\nalpha\tPASS\t20\nbeta\tRED\t30\n' > "$tmp/ev/law-timings.tsv"
printf 'id\tstage\texit\telapsed_us\nalpha\tdirect\t0\t100\nbeta\tdirect\t2\t300\nalpha\tzig-open\t0\t15\nbeta\tzig-open\t0\t25\n' > "$tmp/ev/law-stage-timings.tsv"
bash "$tool" "$tmp/ev" "$tmp/report.md" > "$tmp/log"
grep -Fq '| direct | 2 | 1 | 100 | 300 | 300 |' "$tmp/report.md"
grep -Fq '| zig-open | 2 | 0 | 15 | 25 | 25 |' "$tmp/report.md"
grep -Fq '| beta | direct | 2 | RED | 300 |' "$tmp/report.md"
grep -Fq 'SENS_PHASE_BENCHMARK_SUMMARY checked=2 passed=1 red=1' "$tmp/log"
printf 'bad\trow\n' >> "$tmp/ev/law-stage-timings.tsv"
if bash "$tool" "$tmp/ev" "$tmp/invalid.md" > "$tmp/invalid.out" 2>&1; then
 echo 'REPORTER_TEST_FAILED: malformed evidence was accepted' >&2; exit 1
fi
echo 'REPORTER_TEST_PASS checks=5 evidence=synthetic reporting_only=true'
