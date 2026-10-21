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
python3 scripts/migrate-three-pass.py "$source_file" \
  --out "$dir" --report "$dir/receipt.json" --codec t5m \
  --source-surface укр "${binding_args[@]}"
python3 - "$dir/receipt.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as stream:
    report = json.load(stream)
summary = report['summary']
if not (summary['files_written'] == 1 and summary['files_blocked'] == 0
        and summary['files_not_program'] == 0 and len(report['files']) == 1
        and report['files'][0]['status'] == 'written'
        and report['physical_producer'] == 'PINNED_ZIG_T5M_CARRY'):
    raise SystemExit('ПОМИЛКА: Zig/T5M не підтвердив фізичну пару')
PY
name="$(basename "${source_file%.lisp}")"
pair="$dir/$name.sens"
view="$dir/$name"
if [[ ! -s "$pair" || ! -s "$view" || -L "$pair" || -L "$view" ]]; then
  echo 'ПОМИЛКА: немає обох звичайних файлів свіжої фізичної пари' >&2
  exit 2
fi
# Повноцінний запуск, а не Python-імітація SENS-eval.
if "$binary" "$pair" >"$dir/eval.stdout" 2>"$dir/eval.stderr"; then
  mode=standalone
elif "$binary" --t5m-pair "$source_file" "$pair" >"$dir/eval.stdout" 2>"$dir/eval.stderr"; then
  mode=paired
else
  cat "$dir/eval.stderr" >&2
  echo 'ПОМИЛКА: справжній SENS не виконав жоден перевірений маршрут; пару не змінено' >&2
  exit 2
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
cp "$pair" "$committed_pair"
cp "$view" "$committed_view"
cmp "$pair" "$committed_pair"
cmp "$view" "$committed_view"
printf 'T5M_REFRESHED source=%s mode=%s physical=ZIG_VERIFIED executed=SENS semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' "$source_file" "$mode"
