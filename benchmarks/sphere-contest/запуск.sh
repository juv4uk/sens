#!/usr/bin/env bash
# Конкурс бенчмарків за сферами. Відсутній інструмент — не успіх, а «не виконано».
set -uo pipefail
тут="$(cd "$(dirname "$0")" && pwd)"
стан=0

if command -v sens-cli >/dev/null 2>&1; then
  echo "== SENS (семантика) =="
  /usr/bin/time -f "  %e с" sens-cli "$тут/сенс-семантика.lisp" || стан=1
else
  echo "== SENS (семантика) == не виконано: немає sens-cli"; стан=1
fi

if command -v zig >/dev/null 2>&1; then
  echo "== Zig (корідор) =="
  zig run "$тут/зіг-корідор.zig" || стан=1
else
  echo "== Zig (корідор) == не виконано: немає zig"; стан=1
fi

if command -v rustc >/dev/null 2>&1; then
  echo "== Rust (механізм) =="
  rustc -O -o /tmp/раст-механізм "$тут/раст-механізм.rs" && /tmp/раст-механізм || стан=1
else
  echo "== Rust (механізм) == не виконано: немає rustc"; стан=1
fi

exit "$стан"
