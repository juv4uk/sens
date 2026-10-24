#!/usr/bin/env bash
# Механічний регресійний тест: звіт не має показувати вимірювання без проб.
# Семантичних значень SENS цей тест не обчислює.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/evidence"
printf 'id\tstage\texit\telapsed_us\n' > "$tmp/evidence/law-stage-timings.tsv"
printf 'id\tstatus\twall_ms\n' > "$tmp/evidence/law-timings.tsv"

expect_rejected() {
  local case_id="$1"
  if bash scripts/report-sens-law-hotspots.sh "$tmp/evidence" "$tmp/report.md" > "$tmp/$case_id.log" 2>&1; then
    printf 'REGRESSION id=law-hotspots-empty layer=report case=%s expected=rejected actual=accepted\n' "$case_id" >&2
    exit 1
  fi
}

expect_rejected both-header-only
printf 'law-a\tdirect\t0\t1250\n' >> "$tmp/evidence/law-stage-timings.tsv"
expect_rejected law-header-only
printf 'law-a\tPASS\t1\n' >> "$tmp/evidence/law-timings.tsv"
# Позитивний контроль: валідні фазовий вимір і SENS-вердикт приймаються.
bash scripts/report-sens-law-hotspots.sh "$tmp/evidence" "$tmp/report.md" > "$tmp/valid.log"
if ! grep -Fq 'Свідків: 1, PASS: 1, RED: 0.' "$tmp/report.md"; then
  printf 'REGRESSION id=law-hotspots-valid layer=report expected=one-valid-sample actual=bad-summary\n' >&2
  exit 1
fi
printf 'SENS_LAW_HOTSPOTS_TEST_PASS rejected=2 valid=1\n'
