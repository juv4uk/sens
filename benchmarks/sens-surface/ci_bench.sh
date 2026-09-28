#!/bin/sh
# #1433: швидкий відтворюваний бенчмарк для CI.
#
# Кількість виконаних інструкцій (valgrind cachegrind "I refs") для кожного
# навантаження × форми × режиму, REPS повторів. На відміну від часу,
# інструкції майже не залежать від шуму спільної машини (розкид ≤ ~0.7%).
#
#   sh ci_bench.sh CI_BENCH_BINARY WORKLOAD_DIR OUT.tsv [FORMS] [REPS]
#
# WORKLOAD_DIR — вихід `run.py --emit DIR --small`. FORMS — через пробіл
# (за замовчуванням "en sens").
# Форма `sens` спершу кодується в двійковий вигляд (fasl, функція = 1 байт)
# самим бінарником — цей крок не міряється.
# Режими: load — лише завантажити програму; full — завантажити й виконати.
#
# #1587: у кожному рядку — розмір навантаження (колонка params із params.tsv,
# який пише run.py --emit). Рядок без розміру не виводиться.
# #1586: середовище замірів (load-контекст) фіксується окремим файлом
# оточення; сам цей TSV — лише інструкції.
set -eu
BIN=$1
DIR=$2
OUT=$3
FORMS=${4:-en sens}
REPS=${5:-3}

# Розмір навантаження з params.tsv; відсутній файл/рядок — "-", не збій.
paramsof() {
  if [ -f "$DIR/params.tsv" ]; then
    awk -F'\t' -v n="$1" '$1 == n { print $2; found = 1; exit }
      END { if (!found) print "-" }' "$DIR/params.tsv"
  else
    echo -
  fi
}

measure() {
  valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null \
    "$BIN" "$DIR" "$@" 2>&1 >/dev/null |
    sed -n 's/.*I *refs: *//p' | tr -d ','
}

printf 'workload\tparams\tform\tmode\trep\tinstructions\n' > "$OUT"
rep=1
while [ "$rep" -le "$REPS" ]; do
  printf 'empty\t-\t-\tfull\t%s\t%s\n' "$rep" "$(measure empty -)" >> "$OUT"
  rep=$((rep + 1))
done
for expected in "$DIR"/*.expected; do
  name=$(basename "$expected" .expected)
  for form in $FORMS; do
    if [ "$form" = sens ]; then
      "$BIN" "$DIR" "$name" sens encode
    fi
    # Спершу правильність: неправильна відповідь — збій, не число.
    "$BIN" "$DIR" "$name" "$form" full
    for mode in load full; do
      rep=1
      while [ "$rep" -le "$REPS" ]; do
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$(paramsof "$name")" "$form" "$mode" "$rep" \
          "$(measure "$name" "$form" "$mode")" >> "$OUT"
        rep=$((rep + 1))
      done
    done
  done
done
cat "$OUT"
