#!/usr/bin/env bash
# Діагностика продуктивності реального Lisp → Zig/T5M → SENS.
# Сценарій тільки підсумовує часові виміри: мовні вердикти належать SENS.
set -euo pipefail

if (( $# != 1 )); then
  echo 'Використання: report-sens-law-stage-benchmarks.sh law-stage-timings.tsv' >&2
  exit 2
fi
input="$1"
if [[ ! -f "$input" || -L "$input" ]]; then
  echo "SENS_STAGE_BENCHMARK_INVALID_INPUT path=$input" >&2
  exit 2
fi

clean="$(mktemp)"
trap 'rm -f "$clean"' EXIT
# Неправильний формат не може породжувати вигадану продуктивність або PASS.
LC_ALL=C awk -F '\t' '
  NR == 1 {
    if ($0 != "id\tstage\texit\telapsed_us") {
      print "SENS_STAGE_BENCHMARK_INVALID_HEADER" > "/dev/stderr"
      bad = 1
    }
    next
  }
  {
    if (NF != 4 || $1 !~ /^[a-zA-Z0-9_-]+$/ ||
        $2 !~ /^[a-z][a-z0-9-]*$/ || $3 !~ /^[0-9]+$/ ||
        $4 !~ /^[0-9]+$/ || length($4) > 12) {
      print "SENS_STAGE_BENCHMARK_INVALID_RECORD line=" NR > "/dev/stderr"
      bad = 1
      next
    }
    rows++
    print $1 "\t" $2 "\t" $3 "\t" $4
  }
  END {
    if (rows == 0) {
      print "SENS_STAGE_BENCHMARK_EMPTY" > "/dev/stderr"
      bad = 1
    }
    if (bad) exit 2
  }
' "$input" > "$clean"

printf '### Діагностика фаз Lisp → Zig/T5M → SENS\n\n'
printf 'Реальні виміри окремих команд (разом зі стартом CLI). p50/p90 — **між різними свідками**, не повтори одного тесту; це не оцінка прискорення. Після відмови наступні фази не вимірюються.\n\n'
printf '| Фаза | Вимірів | Невдалих команд | p50, мс | p90, мс | Макс., мс | Найповільніший свідок |\n'
printf '|---|---:|---:|---:|---:|---:|---|\n'
LC_ALL=C sort -t $'\t' -k2,2 -k4,4n "$clean" | LC_ALL=C awk -F '\t' '
  function flush(   i50,i90) {
    if (n == 0) return
    i50 = int((n + 1) / 2)
    i90 = int((9 * n + 9) / 10)
    printf "| `%s` | %d | %d | %.1f | %.1f | %.1f | `%s` |\n", \
      stage, n, errors, values[i50] / 1000, values[i90] / 1000, values[n] / 1000, slowest
    delete values
    n = 0
    errors = 0
  }
  $2 != stage { flush(); stage = $2 }
  {
    values[++n] = $4 + 0
    if ($3 != "0") errors++
    slowest = $1
  }
  END { flush() }
'
printf '\nНайповільніші окремі фази (для адресної оптимізації):\n\n'
printf '| Свідок | Фаза | Код виходу | Час, мс |\n'
printf '|---|---|---:|---:|\n'
LC_ALL=C sort -t $'\t' -k4,4nr "$clean" | LC_ALL=C awk -F '\t' 'NR <= 5 {printf "| `%s` | `%s` | %s | %.1f |\n", $1, $2, $3, $4 / 1000}'
printf '\nПомилки фази залишаються **RED**; таблиця не замінює Lisp/SENS-вердикти.\n'