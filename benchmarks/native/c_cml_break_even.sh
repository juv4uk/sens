#!/usr/bin/env bash
# Вартість одного Lisp → FASL експорту в окремому процесі.
# --program-fasl лише читає джерело, викликає parse та fasl_encode і записує файл.
# Це НЕ компіляція/спеціалізація CML і не свідчення прискорення виконання.
# Реальна точка окупності потребує C_спеціалізація та різниці часу виконання
# до й після спеціалізації: N* = C_спеціалізація / (C_до - C_після).
#
# Запуск (потрібен зібраний sens-cli з біном cml-export):
#     bash benchmarks/native/c_cml_break_even.sh <source.lisp> [repeats]
#
# Третій аргумент старого інтерфейсу приймаємо, але не використовуємо.
# Якщо cml-export не зібрано, число не вигадується.
set -euo pipefail

src="${1:?вкажи source.lisp}"
repeats="${2:-11}"
if ! [[ "$repeats" =~ ^[1-9][0-9]*$ ]]; then
  echo "НЕВІРНИЙ ПАРАМЕТР: repeats має бути додатним цілим числом" >&2
  exit 2
fi
legacy_exec_us="${3:-}"
if [ -n "$legacy_exec_us" ]; then
  echo "УВАГА: старий аргумент c_exec_us ігнорується: FASL-експорт не вимірює спеціалізацію" >&2
fi

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
c_fasl_export_us=$(( (t1 - t0) / repeats / 1000 ))

echo "C_fasl_export_process_mean: ${c_fasl_export_us} мкс (один процес на експорт, середнє з ${repeats} прогонів)"
echo "C_cml_specialization: НЕ ВИМІРЯНО (експорт FASL не є спеціалізацією)"
echo "N* (окупність спеціалізації): НЕ ВИМІРЯНО (немає C_спеціалізація та C_до - C_після)"
