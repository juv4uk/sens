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
# Бінарний T5M-аудитор лежить поряд із чинним SENS CLI, а не в Python.
reader="$(dirname "$binary")/sens-trit"
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
if [[ ! -f "$source_file" || -L "$source_file" || ! -x "$binary" || ! -x "$reader" ]]; then
  echo 'ПОМИЛКА: джерело або чинний виконуваний SENS недоступні' >&2
  exit 2
fi
source_hash="$(sha256sum "$source_file" | cut -d' ' -f1)"
dir="$(mktemp -d)"
trap 'rm -rf "$dir"' EXIT
name="$(basename "${source_file%.lisp}")"
pair="$dir/$name.sens"
view="$dir/$name"

# Одна SENS-сесія виконує визначення --binding-source і саму програму.
# Zig пакує готові слова; Python/JSON у цьому маршруті відсутні.
if ! timeout 60s "$binary" --t5m-mint-pair "$source_file" "$pair" "${binding_args[@]}" \
  >"$dir/mint.stdout" 2>"$dir/mint.stderr"; then
  cat "$dir/mint.stderr" >&2
  echo 'ПОМИЛКА: T5M_NATIVE_MINT_PAIR_FAILED' >&2
  exit 2
fi
producer=SENS_ZIG_NATIVE
if [[ ! -s "$pair" || -L "$pair" ]]; then
  echo 'ПОМИЛКА: SENS/Zig не створив звичайний непорожній фізичний T5M-файл' >&2
  exit 2
fi
# --t5m-mint-pair створює лише фізичні байти .sens, не бітовий перегляд.
# Перегляд відкриває той самий нативний Zig/T5M reader; Python не бере участі.
if ! timeout 45s "$reader" open "$pair" >"$view" 2>"$dir/view.stderr"; then
  cat "$dir/view.stderr" >&2
  echo 'ПОМИЛКА: T5M_NATIVE_VIEW_OPEN_FAILED; пару не змінено' >&2
  exit 2
fi
if [[ ! -s "$view" || -L "$view" ]]; then
  echo 'ПОМИЛКА: Zig/T5M не створив звичайний непорожній бітовий перегляд' >&2
  exit 2
fi
# Без справжнього Zig decode/encode і точного same-stem бітового перегляду
# фізичний носій не може бути опублікований навіть при успішному eval.
if ! timeout 45s "$reader" verify-view "$pair" >"$dir/inverse.stdout" 2>"$dir/inverse.stderr"; then
  cat "$dir/inverse.stderr" >&2
  echo "ПОМИЛКА: T5M_REFRESH_VIEW_ROUNDTRIP_FAILED source=$source_file; пару не змінено" >&2
  exit 2
fi
# Парний вхід обов'язковий: Zig звіряє саме джерело з фізичним T5M,
# а SENS його виконує. Standalone може бути непідтриманим для D7/D24+,
# але сам по собі не доводить оберненості джерела.
if ! timeout 45s "$binary" --t5m-pair "$source_file" "$pair" "${binding_args[@]}" >"$dir/paired.stdout" 2>"$dir/paired.stderr"; then
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
else
  status=$?
  # Парний SENS уже підтвердив виконання. Але невідома помилка
  # автономного reader не повинна тихо дозволяти публікацію пари.
  # Paired-only допустимий лише для двох відомих меж D24+/D7.
  if (( status != 124 && status != 137 )) &&
     { grep -Fq 'T5M requires exact source projection to D24+ before transport' "$dir/standalone.stderr" ||
       grep -Fq 'unknown Text7 binding:' "$dir/standalone.stderr" ||
       { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$dir/standalone.stderr" &&
         grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$dir/standalone.stderr"; }; }; then
    sed 's/^/SENS paired-only відома межа: /' "$dir/standalone.stderr" >&2
  else
    sed 's/^/SENS standalone невідома помилка: /' "$dir/standalone.stderr" >&2
    printf 'ПОМИЛКА: T5M_STANDALONE_UNEXPECTED_FAIL source=%s status=%s; пару не змінено\n' "$source_file" "$status" >&2
    exit 2
  fi
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
# Публікація лише після SENS + Zig: жодних Python/JSON у цьому шляху.
# Резервні копії та стадія розміщені на тому самому томі, що й цілі.
# Не замінюємо чужий новостворений файл і не стираємо паралельну зміну.
publish_dir="$(mktemp -d "$(dirname "$committed_pair")/.sens-executed.XXXXXXXX")"
installed_pair=0
installed_view=0
had_pair=0
had_view=0
pair_stamp=""
view_stamp=""
rollback_one() {
  local target="$1" original="$2" expected="$3" stamp="$4" had="$5"
  # Не торкатися чужого запису, якщо носій змінився після нашого rename.
  if [[ -L "$target" || ! -f "$target" ]] ||
     [[ "$(stat -c '%d:%i' "$target")" != "$stamp" ]] ||
     ! cmp -s "$target" "$expected"; then
    echo "T5M_REFRESH_ROLLBACK_CONFLICT path=$target action=manual-review" >&2
    return 1
  fi
  if (( had )); then
    mv -fT -- "$original" "$target"
  else
    rm -- "$target"
  fi
}
cleanup_publish() {
  local status=$?
  trap - EXIT
  if (( status != 0 )); then
    local rollback_failed=0
    if (( installed_view )); then
      rollback_one "$committed_view" "$publish_dir/old.view" "$publish_dir/expected.view" "$view_stamp" "$had_view" || rollback_failed=1
    fi
    if (( installed_pair )); then
      rollback_one "$committed_pair" "$publish_dir/old.sens" "$publish_dir/expected.sens" "$pair_stamp" "$had_pair" || rollback_failed=1
    fi
    if (( rollback_failed )); then
      echo "T5M_REFRESH_BACKUPS path=$publish_dir; паралельну зміну не перезаписано" >&2
      rm -rf -- "$dir"
      exit 2
    fi
    echo "T5M_REFRESH_INSTALL_FAILED source=$source_file status=$status; відновлено попередню пару" >&2
  fi
  rm -rf -- "$publish_dir" "$dir"
  exit "$status"
}
trap cleanup_publish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cp -- "$pair" "$publish_dir/new.sens"
cp -- "$pair" "$publish_dir/expected.sens"
cp -- "$view" "$publish_dir/new.view"
cp -- "$view" "$publish_dir/expected.view"
if [[ -f "$committed_pair" ]]; then
  had_pair=1
  cp -p -- "$committed_pair" "$publish_dir/old.sens"
  chmod --reference="$committed_pair" "$publish_dir/new.sens"
fi
if [[ -f "$committed_view" ]]; then
  had_view=1
  cp -p -- "$committed_view" "$publish_dir/old.view"
  chmod --reference="$committed_view" "$publish_dir/new.view"
fi
# Перевірка після стадіювання: не випереджати іншого writer.
for target in "$committed_pair" "$committed_view"; do
  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    echo "T5M_REFRESH_TARGET_CHANGED path=$target" >&2
    exit 2
  fi
done
if (( had_pair )); then
  [[ -f "$committed_pair" ]] && cmp -s "$committed_pair" "$publish_dir/old.sens" || {
    echo "T5M_REFRESH_CONCURRENT_CHANGE path=$committed_pair" >&2; exit 2;
  }
elif [[ -e "$committed_pair" || -L "$committed_pair" ]]; then
  echo "T5M_REFRESH_CONCURRENT_CHANGE path=$committed_pair" >&2; exit 2
fi
if (( had_view )); then
  [[ -f "$committed_view" ]] && cmp -s "$committed_view" "$publish_dir/old.view" || {
    echo "T5M_REFRESH_CONCURRENT_CHANGE path=$committed_view" >&2; exit 2;
  }
elif [[ -e "$committed_view" || -L "$committed_view" ]]; then
  echo "T5M_REFRESH_CONCURRENT_CHANGE path=$committed_view" >&2; exit 2
fi
if [[ "$(sha256sum "$source_file" | cut -d' ' -f1)" != "$source_hash" ]]; then
  echo 'ПОМИЛКА: вихідний Lisp змінився перед записом; пару не змінено' >&2
  exit 2
fi
# Для нової цілі hardlink із stage: створення атомарне й без clobber.
# Існуючу ціль замінює rename; точні наші байти/інод відомі для rollback.
if (( had_pair )); then
  mv -fT -- "$publish_dir/new.sens" "$committed_pair"
else
  ln -- "$publish_dir/new.sens" "$committed_pair"
fi
# Позначити новий inode нашим ДО очищення stage; помилка rm теж відкотиться.
installed_pair=1
pair_stamp="$(stat -c '%d:%i' "$committed_pair")"
if (( ! had_pair )); then rm -- "$publish_dir/new.sens"; fi
cmp "$publish_dir/expected.sens" "$committed_pair"
if (( had_view )); then
  mv -fT -- "$publish_dir/new.view" "$committed_view"
else
  ln -- "$publish_dir/new.view" "$committed_view"
fi
installed_view=1
view_stamp="$(stat -c '%d:%i' "$committed_view")"
if (( ! had_view )); then rm -- "$publish_dir/new.view"; fi
cmp "$publish_dir/expected.view" "$committed_view"
trap - EXIT INT TERM
rm -rf -- "$publish_dir" "$dir"
printf 'T5M_REFRESHED source=%s mode=%s physical=%s executed=SENS semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' "$source_file" "$mode" "$producer"
