#!/bin/sh
# #1413: кількість виконаних інструкцій (valgrind cachegrind, "I refs") —
# детермінована міра, незалежна від навантаження машини. Малі розміри
# навантажень (run.py --small), бо valgrind сповільнює в десятки разів.
#
#   guix time-machine -C channels.scm -- shell -m manifest.scm \
#       -m benchmarks/sens-surface/manifest.scm -- \
#       sh benchmarks/sens-surface/icount.sh target-guix/release/sens OUT_DIR
set -eu
SENS=$1
OUT=$2
HERE=$(dirname "$0")
mkdir -p "$OUT/programs"
python3 "$HERE/run.py" --sens "$SENS" --check-only --small >/dev/null
python3 - "$HERE" "$OUT/programs" <<'EOF'
import sys
sys.path.insert(0, sys.argv[1])
import run
from pathlib import Path
out = Path(sys.argv[2])
for name, wl in run.WORKLOADS.items():
    p = wl["small"]
    for form in ("en", "sens"):
        (out / f"{name}-{form}.lisp").write_text(
            run.render(run.program_text(wl, p), form, p), encoding="utf-8")
    (out / f"{name}.expected").write_text(wl["expected"](p) + "\n")
(out / "empty-en.lisp").write_text(run.EMPTY_SRC)
(out / "empty.expected").write_text("0\n")
EOF
printf 'program\tform\tinstructions\tanswer_ok\n' > "$OUT/icount.tsv"
for f in "$OUT"/programs/*.lisp; do
  base=$(basename "$f" .lisp)
  name=${base%-*}
  form=${base##*-}
  # Падіння SENS або Cachegrind не може ставати успішним результатом через tail.
  if output=$(valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null \
              --log-file="$OUT/$base.vg" "$SENS" "$f"); then
    :
  else
    rc=$?
    printf 'ICOUNT_ERROR id=%s layer=cachegrind input=%s expected=exit:0 actual=exit:%s\n' \
      "$base" "$f" "$rc" >&2
    exit "$rc"
  fi
  answer=$(printf '%s\n' "$output" | sed '/^$/d' | tail -1)
  ir=$(sed -n 's/.*I *refs: *//p' "$OUT/$base.vg" | tr -d ',')
  case "$ir" in
    ''|*[!0123456789]*)
      printf 'ICOUNT_ERROR id=%s layer=cachegrind input=%s expected=integer-I-refs actual=%s\n' \
        "$base" "$f" "$ir" >&2
      exit 3
      ;;
  esac
  expected=$(cat "$OUT/programs/$name.expected")
  ok=no
  [ "$answer" = "$expected" ] && ok=yes
  printf '%s\t%s\t%s\t%s\n' "$name" "$form" "$ir" "$ok" >> "$OUT/icount.tsv"
  echo "$name $form $ir $ok"
  if [ "$ok" = no ]; then
    printf 'ICOUNT_ERROR id=%s layer=sens input=%s expected=%s actual=%s\n' \
      "$base" "$f" "$expected" "$answer" >&2
    exit 3
  fi
done
