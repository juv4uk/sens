#!/usr/bin/env bash
# Механічна межа Git. Закон зберігається в knowledge/file-authority-policy.lisp.
# Цей тимчасовий foreign-механізм не доводить семантику SENS.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
BASELINE_SHA="9c94727eb1c45378f3debccf633aad2366e13599"
POLICY="knowledge/file-authority-policy.lisp"
CENSUS="knowledge/foreign-tools-census.lisp"

blocked() {
  printf 'FILE-AUTHORITY: BLOCKED — %s\n' "$1" >&2
  return 1
}

foreign_recorded() {
  local path="$1" record
  record="((path . \"$path\") (independence_status . foreign) (migration_plan . \"міграція: "
  grep -F "$record" "$CENSUS" | grep -Eq 'міграція: [^"]{12,}"'
}

check_new_path() {
  local path="$1"
  case "$path" in
    lib/*|knowledge/*|witnesses/*)
      case "$path" in
        *.lisp|*.sens) ;;
        *) blocked "новий важливий файл не .lisp/.sens: $path"; return 1 ;;
      esac
      if [[ -L "$path" ]]; then
        blocked "новий важливий шлях не може бути символічним посиланням: $path"
        return 1
      fi
      ;;
  esac
  case "$path" in
    *.py)
      case "$path" in
        tools/*.py)
          if ! foreign_recorded "$path"; then
            blocked "новий Python не має пофайлового foreign + плану міграції: $path"
            return 1
          fi
          ;;
        *) blocked "новий Python поза tools/: $path"; return 1 ;;
      esac
      ;;
    tools/*.sh)
      if ! foreign_recorded "$path"; then
        blocked "новий host-скрипт не внесено до census: $path"
        return 1
      fi
      ;;
  esac
  return 0
}

[[ -f "$POLICY" && -f "$CENSUS" ]] || { blocked "відсутня політика або census"; exit 1; }
grep -Fq "(activation-git-commit . \"$BASELINE_SHA\")" "$POLICY" \
  || { blocked "пін Git не збігається з SENS-постановою"; exit 1; }

if [[ "${1:-}" == "--self-test" ]]; then
  for bad in knowledge/new.json lib/new.lisp.fasl witnesses/new.txt scripts/new.py tools/unlisted.py tools/unlisted.sh; do
    if (check_new_path "$bad") >/dev/null 2>&1; then
      blocked "негативний свідок помилково прийнято: $bad"
      exit 1
    fi
  done
  for good in knowledge/new.lisp lib/new.sens witnesses/new.lisp tools/file-authority-guard.sh; do
    check_new_path "$good" || exit 1
  done
  printf 'FILE-AUTHORITY: NEGATIVE CONTROLS PASS\n'
  exit 0
fi

git cat-file -e "$BASELINE_SHA^{commit}" 2>/dev/null \
  || { blocked "пінований Git baseline недоступний: $BASELINE_SHA"; exit 1; }
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
git ls-tree -r -z --name-only "$BASELINE_SHA" > "$scratch/baseline" \
  || { blocked "не вдалося прочитати Git baseline"; exit 1; }
git ls-tree -r -z --name-only HEAD > "$scratch/current" \
  || { blocked "не вдалося прочитати поточне Git дерево"; exit 1; }

declare -A old_paths=()
while IFS= read -r -d '' path; do
  old_paths["$path"]=1
done < "$scratch/baseline"

checked=0
failed=0
while IFS= read -r -d '' path; do
  if [[ -n "${old_paths[$path]+found}" ]]; then
    continue
  fi
  checked=$((checked + 1))
  if ! check_new_path "$path"; then
    failed=$((failed + 1))
  fi
done < "$scratch/current"

if (( failed != 0 )); then
  blocked "відхилено $failed з $checked нових шляхів; чинний baseline=$BASELINE_SHA"
  exit 1
fi
printf 'FILE-AUTHORITY: PASS — %s нових шляхів; baseline=%s; семантична атестація окрема\n' "$checked" "$BASELINE_SHA"
