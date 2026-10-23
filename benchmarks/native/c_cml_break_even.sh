#!/usr/bin/env bash
# C_cml — третє число тези про найменшу плату: ціна РАЗОВОЇ спеціалізації.
#
# Два числа вже виміряні: C_запуск ≈ 2.2 мс, C_виконання ≈ 0.1 мс.
# Третє (це) показує, за якого N разова плата окупається:
#     N* = C_cml / C_виконання
# Тобто: для програм, коротших за N* виконань, разова плата — збиток;
# довших — виграш. Це і є «мінімум» у вимірюваному вигляді.
#
# Запуск (потрібен зібраний sens-cli з біном cml-export):
#     bash benchmarks/native/c_cml_break_even.sh <source.lisp> [repeats] [c_exec_us]
#
# Якщо sens/cml-export не зібрано — скрипт чесно каже, що вимір не відбувся
# (не вигадує число).
set -euo pipefail

src="${1:?вкажи source.lisp}"
repeats="${2:-11}"
c_exec_us="${3:-100}"   # C_виконання, мкс (типово 0.1 мс із наявних бенчмарків)

repo_root="$(git rev-parse --show-toplevel)"
bin="$repo_root/target/release/cml-export"
if [ ! -x "$bin" ]; then
  echo "НЕ ВИМІРЯНО: немає $bin — збери cargo build --release -p sens-cli --bin cml-export" >&2
  exit 2
fi
[ -f "$src" ] || { echo "немає джерела: $src" >&2; exit 2; }

out="$(mktemp -d)/out.fasl"
t0=$(date +%s%N)
for _ in $(seq 1 "$repeats"); do "$bin" --program-fasl "$src" "$out"; done
t1=$(date +%s%N)
c_cml_us=$(( (t1 - t0) / repeats / 1000 ))

echo "C_cml (разова спеціалізація): ${c_cml_us} мкс  (з ${repeats} прогонів)"
echo "C_виконання (питома):         ${c_exec_us} мкс"
if [ "$c_exec_us" -le 0 ]; then
  echo "N*: невизначено (C_виконання ≤ 0)"
else
  echo "N* (точка окупності):          $(( c_cml_us / c_exec_us )) виконань"
  echo "  коротші за N* — разова плата збиткова; довші — вигідна."
fi
