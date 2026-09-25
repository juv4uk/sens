#!/bin/sh
# #1433: швидкий детермінований бенчмарк для CI.
#
# Кількість виконаних інструкцій (valgrind cachegrind "I refs") для кожного
# навантаження × форми (en / sens). На відміну від часу, інструкції не
# залежать від шуму спільної CI-машини — регрес у 1% видно чесно.
#
#   sh ci_bench.sh CI_BENCH_BINARY WORKLOAD_DIR OUT.tsv
#
# WORKLOAD_DIR — вихід `run.py --emit DIR --small`.
set -eu
BIN=$1
DIR=$2
OUT=$3

measure() {
  valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null \
    "$BIN" "$DIR" "$1" "$2" 2>&1 >/dev/null |
    sed -n 's/.*I *refs: *//p' | tr -d ','
}

printf 'workload\tform\tinstructions\n' > "$OUT"
printf 'empty\t-\t%s\n' "$(measure empty -)" >> "$OUT"
for expected in "$DIR"/*.expected; do
  name=$(basename "$expected" .expected)
  for form in en sens; do
    # Спершу правильність: неправильна відповідь — збій, не число.
    "$BIN" "$DIR" "$name" "$form"
    printf '%s\t%s\t%s\n' "$name" "$form" "$(measure "$name" "$form")" >> "$OUT"
  done
done
cat "$OUT"
