#!/usr/bin/env bash
# Конкурс фізичних вимірювань: Rust=механізм, Zig=коридор, SENS=закони.
# Жоден з вимірювачів не обчислює й не підмінює результат мови.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo"

usage() {
  cat <<'HELP'
Використання: bash benchmarks/mechanism/contest-triad.sh [--all|--rust|--zig|--sens] [--rapl]
  --all   усі три незалежні доріжки (типово)
  --rust  тільки вимір механізму копіювання фізичних байтів
  --zig   тільки вимір кодування/декодування T5M
  --sens  тільки нативна семантика, мутант і час через SENS→Zig/T5M→SENS
  --rapl  додатково виміряти енергію Rust-механізму; без RAPL — помилка
Змінна SENS_BIN: шлях до вже зібраного sens (типово target/debug/sens).
Команда НЕ порівнює швидкості різної роботи та НЕ додає нового мовного оракула.
HELP
}

die() {
  printf 'КОНКУРС_ПОМИЛКА %s\n' "$*" >&2
  exit 2
}

# Фізичні метрики мають бути додатними числами, не просто рядком у stdout.
# Це НЕ тест і НЕ визначення семантики SENS.
metric() {
  local line="$1" name="$2" token
  for token in $line; do
    if [[ "$token" == "$name="* ]]; then
      printf '%s' "${token#*=}"
      return 0
    fi
  done
  return 1
}

positive_integer() {
  [[ "$1" =~ ^[0-9]+$ && "$1" =~ [1-9] ]]
}

lane=all
rapl=0
while (( $# )); do
  case "$1" in
    --all|--rust|--zig|--sens)
      [[ "$lane" == all || "$lane" == "${1#--}" ]] || die 'оберіть лише одну доріжку'
      lane="${1#--}";;
    --rapl) rapl=1;;
    --help|-h) usage; exit 0;;
    *) die "невідомий параметр: $1";;
  esac
  shift
done
[[ "$lane" == all || "$lane" == rust || "$lane" == zig || "$lane" == sens ]] || die 'некоректна доріжка'
(( ! rapl )) || [[ "$lane" == all || "$lane" == rust ]] || die '--rapl допустимий лише з Rust'

command -v git >/dev/null || die 'git відсутній: неможливо вказати SHA досліду'
sha="$(git rev-parse --verify HEAD 2>/dev/null)" || die 'це не Git checkout'
# Незакомічені зміни не отримують доказової сили.
git diff --quiet -- || die 'незакомічені зміни робочого дерева: відмовлено у звіті'
git diff --cached --quiet -- || die 'незакомічені staged зміни: відмовлено у звіті'
[[ -z "$(git ls-files --others --exclude-standard)" ]] || die 'незакомічені нові файли: відмовлено у звіті'
printf 'КОНКУРС_ДЖЕРЕЛО sha=%s os=%s mode=%s rapl=%s\n' "$sha" "$(uname -s)" "$lane" "$rapl"

tmp="$(mktemp -d)" || die 'не вдалося створити tmp'
trap 'rm -rf -- "$tmp"' EXIT
rust=не-запускався
zig_lane=не-запускався
sens=не-запускався

if [[ "$lane" == all || "$lane" == rust ]]; then
  command -v rustc >/dev/null || die 'Rust-механізм: rustc не знайдено'
  printf 'КОНКУРС_RUST_ІНСТРУМЕНТ %s\n' "$(rustc --version)"
  rustc --edition=2021 -O benchmarks/mechanism/rust-byte-copy-bench.rs -o "$tmp/rust-mechanism" || die 'помилка збірки Rust'
  "$tmp/rust-mechanism" > "$tmp/rust.stdout" || die 'помилка бенчмарку Rust'
  grep -q '^RUST_BYTE_COPY_BENCH ' "$tmp/rust.stdout" || die 'Rust не видав фізичні виміри'
  rust_report="$(grep '^RUST_BYTE_COPY_BENCH ' "$tmp/rust.stdout")"
  [[ "$(grep -c '^RUST_BYTE_COPY_BENCH ' "$tmp/rust.stdout")" == 1 ]] || die 'Rust: очікується рівно один підсумок'
  [[ "$(metric "$rust_report" samples)" == 11 && "$(metric "$rust_report" batch)" == 512 ]] || die 'Rust: невірне число проб чи копій'
  positive_integer "$(metric "$rust_report" p50_ns)" || die 'Rust: немає додатної медіани'
  positive_integer "$(metric "$rust_report" p90_ns)" || die 'Rust: немає додатного p90'
  cat "$tmp/rust.stdout"
  rust=виміряно
  if (( rapl )); then
    "$tmp/rust-mechanism" --rapl > "$tmp/rapl.stdout" || die 'RAPL недоступний або бенчмарк відхилив показ; джоулі НЕ виміряно'
    grep -q '^RUST_MECHANISM_RAPL ' "$tmp/rapl.stdout" || die 'відсутні реальні покази RAPL'
    rapl_report="$(grep '^RUST_MECHANISM_RAPL ' "$tmp/rapl.stdout")"
    [[ "$(grep -c '^RUST_MECHANISM_RAPL ' "$tmp/rapl.stdout")" == 1 ]] || die 'RAPL: очікується рівно одна фізична проба'
    positive_integer "$(metric "$rapl_report" measured_uj)" || die 'RAPL: немає додатної енергії'
    positive_integer "$(metric "$rapl_report" copies)" || die 'RAPL: немає фактичних копій'
    cat "$tmp/rapl.stdout"
  fi
fi

if [[ "$lane" == all || "$lane" == zig ]]; then
  command -v zig >/dev/null || die 'Zig-коридор: zig не знайдено'
  printf 'КОНКУРС_ZIG_ІНСТРУМЕНТ %s\n' "$(zig version)"
  zig run -O ReleaseFast -lc bench_t5m.zig > "$tmp/zig.stdout" 2> "$tmp/zig.stderr" || {
    cat "$tmp/zig.stderr" >&2
    die 'Zig T5M codec / benchmark не виконано'
  }
  [[ "$(grep -c '^ZIG_T5M_SAMPLE ' "$tmp/zig.stderr" || true)" == 11 ]] || die 'Zig: немає 11 сирих проб'
  grep -q '^ZIG_T5M_BENCH ' "$tmp/zig.stderr" || die 'Zig: немає підсумку T5M'
  zig_report="$(grep '^ZIG_T5M_BENCH ' "$tmp/zig.stderr")"
  [[ "$(grep -c '^ZIG_T5M_BENCH ' "$tmp/zig.stderr")" == 1 ]] || die 'Zig: очікується рівно один фізичний підсумок'
  [[ "$(metric "$zig_report" samples)" == 11 ]] || die 'Zig: невірна кількість проб'
  positive_integer "$(metric "$zig_report" decode_p50_ns_per_op)" || die 'Zig: невірна медіана decode'
  positive_integer "$(metric "$zig_report" encode_p50_ns_per_op)" || die 'Zig: невірна медіана encode'
  cat "$tmp/zig.stdout"
  cat "$tmp/zig.stderr"
  zig_lane=виміряно
fi

if [[ "$lane" == all || "$lane" == sens ]]; then
  sens_bin="${SENS_BIN:-$repo/target/debug/sens}"
  if [[ "$sens_bin" != /* ]]; then sens_bin="$repo/$sens_bin"; fi
  [[ -x "$sens_bin" ]] || die "SENS: виконавчий файл відсутній: $sens_bin"
  # Git HEAD є SHA вихідного дерева, не доказом походження вже зібраного виконуваного файла.
  printf 'КОНКУРС_SENS_ВИКОНАВЕЦЬ path=%s build_sha=не-підтверджено\n' "$sens_bin"
  # Логіку позитивного й негативного свідків обчислює тільки SENS.
  bash scripts/prove-бенчмарк-структура.sh "$sens_bin" > "$tmp/sens.stdout" || die 'SENS: позитивний/негативний свідок або час не доведено'
  grep -q '^БЕНЧМАРК_СТРУКТУРА=PASS native=SENS positive=D1:так mutant=D1:ні samples=11 ' "$tmp/sens.stdout" || die 'SENS: немає повного нативного звіту'
  cat "$tmp/sens.stdout"
  sens=нативний-свідок
fi

[[ "$(git rev-parse --verify HEAD 2>/dev/null)" == "$sha" ]] || die 'HEAD змінився під час вимірювання'
git diff --quiet -- || die 'файли змінилися під час вимірювання'
git diff --cached --quiet -- || die 'індекс змінився під час вимірювання'
[[ -z "$(git ls-files --others --exclude-standard)" ]] || die 'виявлено нові незакомічені файли під час вимірювання'
printf 'КОНКУРС_ПІДСУМОК sha=%s rust=%s zig=%s sens=%s міжмовний-рейтинг=заборонено\n' "$sha" "$rust" "$zig_lane" "$sens"
