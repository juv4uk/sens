#!/usr/bin/env bash
# Енергопрофіль бенчмарку: джоулі поруч із часом.
#
# Навіщо: час і енергія збігаються лише для CPU-bound коду. Наш evaluator
# memory-bound (72-байтовий Value, дві алокації на cons), тож потрібен
# прямий вимір, а не здогад «швидше = дешевше».
#
# Джерело цифр — RAPL (Running Average Power Limit), апаратні лічильники
# всередині чипа. Це МОДЕЛЬ, а не ватметр: чіп оцінює споживання за
# лічильниками активності. Похибка ~5-10% на Intel; на AMD домен DRAM
# часто не виставлений узагалі.
#
# ВАЖЛИВО: RAPL вимагає доступу до MSR (/dev/cpu/*/msr) і root.
# У контейнерах CI цього немає — скрипт свідомо падає з поясненням,
# а не вигадує число. Запускати на bare-metal (напр. self-hosted раннер).
#
# Використання:
#   scripts/energy-profile.sh <команда...>
#   scripts/energy-profile.sh --repeat 5 -- cargo run --release --bin sens -- bench.lisp
#   scripts/energy-profile.sh --list-events      показати доступні power-події

set -uo pipefail

REPEAT=1
EVENTS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repeat) REPEAT="$2"; shift 2 ;;
    --events) EVENTS="$2"; shift 2 ;;
    --list-events)
      if ! command -v perf >/dev/null 2>&1; then
        echo "perf не встановлено (пакет linux-perf)." >&2
        exit 2
      fi
      perf list 2>/dev/null | grep -iE 'power/energy' || {
        echo "RAPL-подій не знайдено: ядро не виставляє power/energy-*. Спробуйте root." >&2
        exit 2
      }
      exit 0 ;;
    --help|-h)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --) shift; break ;;
    *) break ;;
  esac
done

if [ $# -eq 0 ]; then
  echo "потрібна команда: scripts/energy-profile.sh -- <команда...>" >&2
  exit 2
fi

if ! command -v perf >/dev/null 2>&1; then
  echo "НЕ ВИМІРЯНО: perf не встановлено (Debian/Ubuntu: apt install linux-perf)." >&2
  exit 2
fi

# Перевірити, що RAPL справді доступний — інакше не вигадувати цифру.
if ! perf list 2>/dev/null | grep -qE 'power/energy-pkg'; then
  echo "НЕ ВИМІРЯНО: ядро не виставляє power/energy-pkg." >&2
  echo "  Причини: контейнер без MSR, немає root, або CPU без RAPL (не Intel)." >&2
  echo "  Це НЕ «нуль енергії» — це відсутність вимірювального приладу." >&2
  exit 2
fi

# Домен DRAM є не завжди; збираємо те, що є.
DEFAULT_EVENTS="power/energy-pkg/"
if perf list 2>/dev/null | grep -qE 'power/energy-ram'; then
  DEFAULT_EVENTS="power/energy-pkg/,power/energy-ram/"
fi
EVENTS="${EVENTS:-$DEFAULT_EVENTS}"

echo "Енергопрофіль · $REPEAT повтор(ів)"
echo "події: $EVENTS"
echo "команда: $*"
echo

run_once() {
  perf stat -x, -e "$EVENTS" -- "$@" 2>&1
}

# Перший прогін — прогрів (сторінки, кеш, JIT); у статистику не йде.
run_once "$@" >/dev/null 2>&1 || true

i=1
printf '%-4s %-14s %-14s %-14s\n' "#" "час_с" "джоулі_pkg" "джоулі_ram"
while [ "$i" -le "$REPEAT" ]; do
  out="$(run_once "$@")"
  secs="$(printf '%s\n' "$out" | awk -F, '/seconds time elapsed/ {print $1; exit}')"
  pkg="$(printf '%s\n' "$out"  | awk -F, '/power\/energy-pkg/ {print $1; exit}')"
  ram="$(printf '%s\n' "$out"  | awk -F, '/power\/energy-ram/ {print $1; exit}')"
  printf '%-4s %-14s %-14s %-14s\n' "$i" "${secs:-?}" "${pkg:-—}" "${ram:-—}"
  i=$((i + 1))
done

echo
echo "Як читати:"
echo "  • джоулі_pkg — усе, що чип спожив (ядра + кеш), за оцінкою RAPL."
echo "  • джоулі_ram — лише DRAM; якщо '—', домен не виставлений (часто на AMD)."
echo "  • Похибка ~5-10%: різниця C vs Rust у 3% — у межах шуму, а Python у 40× — ні."
echo "  • Порівнюйте МЕДІАНУ повторів, не один прогін."
