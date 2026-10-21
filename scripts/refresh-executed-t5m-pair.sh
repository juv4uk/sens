#!/usr/bin/env bash
# Одна фізична T5M-пара оновлюється лише після справжнього SENS-виконання.
# Не змінює .lisp і не видає виконання за семантичну сертифікацію релізу.
set -euo pipefail
if (( $# < 2 )); then
  echo 'виклик: bash scripts/refresh-executed-t5m-pair.sh lib/файл.lisp target/debug/sens [--binding-source lib/залежність.lisp ...]' >&2
  exit 2
fi
source_file="$1"
binary="$2"
shift 2
binding_args=("$@")
if [[ "$source_file" != *.lisp || "$source_file" == /* || "$source_file" == ../* || "$source_file" == */../* ]]; then
  echo 'ПОМИЛКА: потрібен відносний шлях до конкретного .lisp у репозиторії' >&2
  exit 2
fi
while (( $# )); do
  if [[ "$1" != --binding-source || $# -lt 2 ]]; then
    echo 'ПОМИЛКА: додатково дозволені лише пари --binding-source ШЛЯХ' >&2
    exit 2
  fi
  shift 2
done
root="$(git rev-parse --show-toplevel)"
cd "$root"
if [[ ! -f "$source_file" || -L "$source_file" || ! -x "$binary" ]]; then
  echo 'ПОМИЛКА: джерело або чинний виконуваний SENS недоступні' >&2
  exit 2
fi
source_hash="$(sha256sum "$source_file" | cut -d' ' -f1)"
dir="$(mktemp -d)"
trap 'rm -rf "$dir"' EXIT
name="$(basename "${source_file%.lisp}")"
pair="$dir/$name.sens"
view="$dir/$name"

if (( ${#binding_args[@]} == 0 )); then
  # Чинний маршрут: SENS-reader → Zig T5M → обидва фізичні файли.
  # У цьому шляху немає Python чи JSON, і немає окремого кодера.
  if ! timeout 60s "$binary" --t5m-mint-pair "$source_file" "$pair" \
    >"$dir/mint.stdout" 2>"$dir/mint.stderr"; then
    cat "$dir/mint.stderr" >&2
    echo 'ПОМИЛКА: T5M_NATIVE_MINT_PAIR_FAILED' >&2
    exit 2
  fi
  producer=SENS_ZIG_NATIVE
else
  # Тимчасова сумісність з явними додатковими DEFINE: не зупиняємо
  # чинні міграції, доки native reader не одержить preload source API.
  # Це лише допоміжний resolver; парна семантика завжди належить SENS.
  python3 scripts/migrate-three-pass.py "$source_file" \
    --out "$dir" --report "$dir/receipt.json" --codec t5m \
    --source-surface укр --refresh-existing "${binding_args[@]}"
  python3 - "$dir/receipt.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as stream:
    report = json.load(stream)
summary = report['summary']
if not (summary['files_written'] == 1 and summary['files_blocked'] == 0
        and summary['files_not_program'] == 0 and len(report['files']) == 1
        and report['files'][0]['status'] == 'refreshed'
        and report['physical_producer'] == 'PINNED_ZIG_T5M_CARRY'):
    raise SystemExit('ПОМИЛКА: Zig/T5M не підтвердив фізичну пару')
PY
  producer=ZIG_WITH_EXPLICIT_BINDINGS
fi
if [[ ! -s "$pair" || ! -s "$view" || -L "$pair" || -L "$view" ]]; then
  echo 'ПОМИЛКА: немає обох звичайних файлів свіжої фізичної пари' >&2
  exit 2
fi
# Парний вхід обов'язковий: Zig звіряє саме джерело з фізичним T5M,
# а SENS його виконує. Standalone може бути непідтриманим для D7/D24+,
# але сам по собі не доводить оберненості джерела.
if ! timeout 45s "$binary" --t5m-pair "$source_file" "$pair" >"$dir/paired.stdout" 2>"$dir/paired.stderr"; then
  cat "$dir/paired.stderr" >&2
  echo 'ПОМИЛКА: T5M_PAIRED_SOURCE_EXECUTION_FAIL; пару не змінено' >&2
  exit 2
fi
mode=paired
# Коли standalone також виконується, зіставляємо дійсні результати
# обох SENS-входів побайтно, не host-оракулом і не лише exit=0.
if timeout 45s "$binary" "$pair" >"$dir/standalone.stdout" 2>"$dir/standalone.stderr"; then
  if ! cmp -s "$dir/standalone.stdout" "$dir/paired.stdout"; then
    echo "ПОМИЛКА: T5M_PAIRED_RESULT_MISMATCH standalone_sha256=$(sha256sum "$dir/standalone.stdout" | cut -d' ' -f1) paired_sha256=$(sha256sum "$dir/paired.stdout" | cut -d' ' -f1); пару не змінено" >&2
    exit 2
  fi
  mode=paired-and-standalone
fi
if [[ "$(sha256sum "$source_file" | cut -d' ' -f1)" != "$source_hash" ]]; then
  echo 'ПОМИЛКА: вихідний Lisp змінився під час перевірки; пару не змінено' >&2
  exit 2
fi
committed_pair="${source_file%.lisp}.sens"
committed_view="${source_file%.lisp}"
for target in "$committed_pair" "$committed_view"; do
  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    echo "ПОМИЛКА: ціль не є звичайним файлом: $target" >&2
    exit 2
  fi
done
# Публікація — лише файлові операції Bash, без Python/JSON.
# Стадіюємо файли поруч із цілями; якщо друга заміна не відбулася,
# повертаємо точні попередні байти обох файлів.
stage_pair="$(mktemp "${committed_pair}.sens-stage.XXXXXX")"
stage_view="$(mktemp "${committed_view}.view-stage.XXXXXX")"
trap 'rm -rf "$dir"; rm -f "$stage_pair" "$stage_view"' EXIT
cp "$pair" "$stage_pair"
cp "$view" "$stage_view"
if [[ -f "$committed_pair" ]]; then
  cp -p "$committed_pair" "$dir/previous.sens"
  had_pair=1
else
  had_pair=0
fi
if [[ -f "$committed_view" ]]; then
  cp -p "$committed_view" "$dir/previous.view"
  had_view=1
else
  had_view=0
fi
if ! mv -f "$stage_pair" "$committed_pair"; then
  echo 'ПОМИЛКА: T5M_PAIR_INSTALL_FAILED; наявну пару не змінено' >&2
  exit 2
fi
if ! mv -f "$stage_view" "$committed_view"; then
  if (( had_pair )); then cp -p "$dir/previous.sens" "$committed_pair"; else rm -f "$committed_pair"; fi
  if (( had_view )); then cp -p "$dir/previous.view" "$committed_view"; else rm -f "$committed_view"; fi
  echo 'ПОМИЛКА: T5M_VIEW_INSTALL_FAILED; відновлено попередню пару' >&2
  exit 2
fi
cmp "$pair" "$committed_pair"
cmp "$view" "$committed_view"
printf 'T5M_REFRESHED source=%s mode=%s physical=%s executed=SENS semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' "$source_file" "$mode" "$producer"
