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
  answer=$(valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null \
            --log-file="$OUT/$base.vg" "$SENS" "$f" | grep -v '^$' | tail -1)
  ir=$(sed -n 's/.*I *refs: *//p' "$OUT/$base.vg" | tr -d ',')
  ok=no
  [ "$answer" = "$(cat "$OUT/programs/$name.expected")" ] && ok=yes
  printf '%s\t%s\t%s\t%s\n' "$name" "$form" "$ir" "$ok" >> "$OUT/icount.tsv"
  echo "$name $form $ir $ok"
done
