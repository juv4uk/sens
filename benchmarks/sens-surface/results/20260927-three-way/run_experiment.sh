#!/bin/sh
set -eu
VG=${VG:-valgrind}
OLDP=${OLDP:?шлях до phase_bench старого коміту}
OLDC=${OLDC:?шлях до ci_bench старого коміту}
NEWP=${NEWP:?шлях до phase_bench поточного коміту}
NEWC=${NEWC:?шлях до ci_bench поточного коміту}
WL=${WL:?каталог run.py --emit --small --forms en,sens,legacy-en}
OUT=${OUT:-instructions.tsv}
m() { "$VG" --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null "$@" 2>&1 >/dev/null | sed -n 's/.*I *refs: *//p' | tr -d ','; }
printf 'rep\tside\tworkload\tform\tmode\tinstructions\n' > "$OUT"
for rep in 1 2 3; do
  printf '%s\told\tempty\t-\tci\t%s\n' $rep "$(m $OLDC $WL empty -)" >> "$OUT"
  printf '%s\tnew\tempty\t-\tci\t%s\n' $rep "$(m $NEWC $WL empty -)" >> "$OUT"
  for f in "$WL"/*.expected; do
    n=$(basename "$f" .expected)
    for mode in session parse full; do
      "$OLDP" "$WL" "$n" legacy-en $mode
      printf '%s\told\t%s\tlegacy-en\t%s\t%s\n' $rep "$n" $mode "$(m $OLDP $WL $n legacy-en $mode)" >> "$OUT"
    done
    printf '%s\told\t%s\tlegacy-en\tci\t%s\n' $rep "$n" "$(m $OLDC $WL $n legacy-en)" >> "$OUT"
    for form in en sens; do
      for mode in session parse lower full; do
        "$NEWP" "$WL" "$n" $form $mode
        printf '%s\tnew\t%s\t%s\t%s\t%s\n' $rep "$n" $form $mode "$(m $NEWP $WL $n $form $mode)" >> "$OUT"
      done
      printf '%s\tnew\t%s\t%s\tci\t%s\n' $rep "$n" $form "$(m $NEWC $WL $n $form)" >> "$OUT"
    done
  done
done
wc -l < "$OUT"
