#!/usr/bin/env bash
# T01-symbolic-recursion driver for SENS (ENERGY-02 / #6287).
# Reads TASK_N, evaluates naive recursive Fibonacci via SENS REPL (surface укр),
# prints exactly one decimal line for parity_check.py --run.
#
# Does NOT measure energy. ENERGY_NOT_MEASURED remains the energy status
# until a real RAPL path is available on the host.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SENS_BIN="${SENS_BIN:-$ROOT/target/release/sens}"
N="${TASK_N:-}"

if [[ -z "${N}" ]]; then
  echo "TASK_N required" >&2
  exit 2
fi
if ! [[ "$N" =~ ^[0-9]+$ ]]; then
  echo "TASK_N must be non-negative integer" >&2
  exit 2
fi
if [[ ! -x "$SENS_BIN" ]]; then
  echo "SENS binary missing or not executable: $SENS_BIN" >&2
  exit 2
fi

# Naive recursive fib matching parity_check.ref_T01 / C/JS:
# fib(k) = k if k < 2 else fib(k-1)+fib(k-2)
# Ukrainian surface names from lib/domains/d4.lisp + d5.lisp + d3 cond.
forms=$(cat <<FORMS
(визначити фіб
  (функція (k)
    (за-умовою
      ((менше? k 2) k)
      (так (додати (фіб (відняти k 1)) (фіб (відняти k 2)))))))
(фіб ${N})
FORMS
)

tmp="$(mktemp)"
trap 'rm -f "$tmp" "$tmp.err"' EXIT
if ! printf '%s\n' "$forms" | timeout 120s "$SENS_BIN" --surface=укр >"$tmp" 2>"$tmp.err"; then
  echo "SENS execution failed" >&2
  cat "$tmp.err" >&2 || true
  exit 2
fi
if grep -Eq 'Помилка|unknown Text7|#t7:|REGRESSION' "$tmp" "$tmp.err" 2>/dev/null; then
  echo "SENS language error" >&2
  cat "$tmp" "$tmp.err" >&2 || true
  exit 2
fi

# Keep only the last pure decimal line (define may print intermediate values).
result="$(tr -d '\r' <"$tmp" | sed 's/^sens\[укр\]>[[:blank:]]*//' | grep -E '^[0-9]+$' | tail -1 || true)"
if [[ -z "$result" ]]; then
  echo "SENS produced no decimal result line" >&2
  echo "--- stdout ---" >&2
  cat "$tmp" >&2
  echo "--- stderr ---" >&2
  cat "$tmp.err" >&2 || true
  exit 2
fi
printf '%s\n' "$result"
