#!/usr/bin/env bash
# Конкурс бенчмарків за сферами.
# Відсутній інструмент — не успіх, а «не виконано».
# Час міряє оболонка: у Zig 0.16 std.time без годинника, у SENS — без таймера.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
fail=0

run() {
  local name="$1"; shift
  echo "== $name =="
  local t0=$SECONDS
  if "$@"; then
    echo "   час: $((SECONDS - t0)) с"
  else
    echo "   ПОМИЛКА"; fail=1
  fi
}

if command -v zig >/dev/null 2>&1; then
  run "Zig (корідор)" zig run "$here/зіг-корідор.zig"
else
  echo "== Zig (корідор) == не виконано: немає zig"; fail=1
fi

if command -v rustc >/dev/null 2>&1; then
  rustc -O -o /tmp/rast-mehanizm "$here/раст-механізм.rs" || fail=1
  run "Rust (механізм)" /tmp/rast-mehanizm
else
  echo "== Rust (механізм) == не виконано: немає rustc"; fail=1
fi

if command -v sens >/dev/null 2>&1; then
  run "SENS (семантика)" sens "$here/сенс-семантика.lisp"
else
  echo "== SENS (семантика) == не виконано: немає sens"; fail=1
fi

exit "$fail"
