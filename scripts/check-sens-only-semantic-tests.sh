#!/usr/bin/env bash
# Гейт коридор/архів. Shell лише координує Git/CI; жодної семантики SENS тут немає.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
ARCHIVE="docs/language-policy-archive.md"
ARCHIVE_URL="docs/language-policy-archive.md"
die() { echo "МОВНИЙ_ГЕЙТ=RED причина=$*" >&2; exit 1; }

[[ -f "$ARCHIVE" ]] || die "відсутній єдиний реєстр $ARCHIVE"
grep -Fq '| Артефакт | Локація | Причина виключення з гейту | Статус |' "$ARCHIVE" || die "неправильний заголовок реєстру"
grep -Fq 'ARCHIVE — стан артефакта' "$ARCHIVE" || die "архів має визначати ARCHIVE як стан, не борг"
archive_rows() {
  awk -F'|' '/^\|/ && $0 !~ /Артефакт/ {
    artifact=$2; location=$3; reason=$4; status=$5
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", artifact)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", location)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", reason)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
    if (artifact != "" && location != "" && reason != "" && status == "ARCHIVE") print artifact "|" location "|" reason "|" status
  }' "$ARCHIVE"
}
archive_count="$(archive_rows | awk 'END {print NR+0}')"
[[ "$archive_count" -gt 0 ]] || die "реєстр не має рядків ARCHIVE"

# Кожний рядок мусить мати точно прив'язаний до коміту SHA; без посилання
# на витік виключення не є архівною реєстрацією.
while IFS= read -r row; do
  [[ "$row" == \|*\|*\|*\|* ]] || continue
  [[ "$row" == *"| ARCHIVE |" ]] || continue
  [[ "$row" =~ https://github\.com/juv4uk/sens/commit/[0-9a-f]{40} ]] || die "рядок ARCHIVE без pinned commit SHA: $row"
done < "$ARCHIVE"

archive_has_location() {
  local path="$1"
  awk -F'|' -v wanted="$path" '/^\|/ && $0 ~ /ARCHIVE/ {
    location=$3; gsub(/^[[:space:]]+|[[:space:]]+$/, "", location)
    if (index(location, wanted) > 0) found=1
  } END {exit !found}' "$ARCHIVE"
}
archive_has_artifact() {
  local artifact="$1"
  awk -F'|' -v wanted="`$artifact`" '/^\|/ && $0 ~ /ARCHIVE/ {
    column=$2; if (index(column,wanted)>0) found=1
  } END {exit !found}' "$ARCHIVE"
}
first_field_is_sens_source() {
  local field="$1"
  [[ "$field" == SENS_SOURCE=* && "${field#SENS_SOURCE=}" != "" ]]
}
gate_new_artifact() {
  local artifact="$1" is_new="$2" first_field="$3"
  # Архів звільняє тільки наявну історичну річ. Не можна використати
  # сусідній рядок чи старий виняток для щойно доданого файлу.
  if [[ "$is_new" == false ]] && archive_has_artifact "$artifact"; then
    return 0
  fi
  if [[ "$is_new" == true ]] && first_field_is_sens_source "$first_field"; then
    return 0
  fi
  return 1
}

# Самоперевірка гейту: реальний архівний шлях має бути зарахований у N;
# новий чужий тест без поля/реєстрації має бути RED.
self_test() {
  local first_artifact first_location simulated_new
  first_artifact="$(awk -F'|' '/^\|/ && /ARCHIVE/ {a=$2; gsub(/^[[:space:]]+|[[:space:]]+$/, "", a); if(a ~ /\`[^\`]+\`/) {sub(/^.*\`/,"",a); sub(/\`.*$/,"",a); print a; exit}}' "$ARCHIVE")"
  [[ -n "$first_artifact" ]] || die "self-test не знайшов зареєстрований артефакт"
  archive_has_artifact "$first_artifact" || die "self-test позитив: архівний артефакт не зараховано"
  gate_new_artifact "$first_artifact" false "" || die "self-test позитив: зареєстрований архів відхилено"
  local counted
  counted="$(archive_rows | awk 'END {print NR+0}')"
  [[ "$counted" -eq "$archive_count" ]] || die "self-test позитив: ARCHIVE counter не врахував рядок"
  simulated_new="tests/__gate_self_test_foreign.py"
  if gate_new_artifact "$simulated_new" true ""; then
    die "self-test негатив: новий чужий тест без SENS_SOURCE прийнято"
  fi
  echo "GATE_SELF_TEST=OK archive_positive=ARCHIVE_COUNTED negative_new_foreign=RED_EXPECTED"
}
if [[ "${1:-}" == "--self-test" ]]; then self_test; exit 0; fi

# Нові test/benchmark-файли в PR: поле SENS_SOURCE має стояти першим у
# PR-body. Зміна вже існуючого архівного runner не запускає масову міграцію.
event_name="${GITHUB_EVENT_NAME:-}"
if [[ "$event_name" == "pull_request" && -n "${GITHUB_EVENT_PATH:-}" && -f "${GITHUB_EVENT_PATH}" ]]; then
  pr_body="$(jq -r '.pull_request.body // ""' "$GITHUB_EVENT_PATH")"
  first_field="${pr_body%%$'\n'*}"
  base_sha="$(jq -r '.pull_request.base.sha' "$GITHUB_EVENT_PATH")"
  head_sha="$(jq -r '.pull_request.head.sha' "$GITHUB_EVENT_PATH")"
  [[ "$base_sha" =~ ^[0-9a-f]{40}$ && "$head_sha" =~ ^[0-9a-f]{40}$ ]] || die "немає pinned PR base/head SHA"
  git cat-file -e "$base_sha^{commit}" 2>/dev/null || git fetch --no-tags origin "$base_sha" --depth=1
  while IFS=$'\t' read -r status path; do
    [[ "$status" == A* ]] || continue
    case "$path" in
      tests/*|crates/*/tests/*|benchmarks/*)
        if ! first_field_is_sens_source "$first_field"; then
          die "новий gated test/benchmark $path без SENS_SOURCE першим полем PR-body; виключення заборонено"
        fi
        ;;
    esac
  done < <(git diff --name-status "$base_sha...$head_sha")
fi

# Кожен workflow, який запускає історичний чужомовний runner, повинен
# мати архівний рядок. Виконання runner-а тут не вимикається і не стає PASS
# від самого факту реєстрації.
runner_pattern='python3?[[:space:]]+.*(test|bench|benchmark|trial|run\.py)|pytest([[:space:]]|$)|node[[:space:]]+--test|npm[[:space:]]+(test|run[[:space:]]+(test|bench|benchmark))|npx[[:space:]]+(jest|vitest|mocha)|bun[[:space:]]+test|deno[[:space:]]+test|go[[:space:]]+test([[:space:]]|$)|racket[[:space:]]+.*(test|bench)'
workflow_count=0
missing_runner_workflows=()
while IFS= read -r workflow; do
  [[ -f "$workflow" ]] || continue
  if grep -Eq "$runner_pattern" "$workflow"; then
    workflow_count=$((workflow_count + 1))
    if ! archive_has_location "$workflow"; then
      missing_runner_workflows+=("$workflow")
    fi
  fi
done < <(find .github/workflows -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) -print | sort)
if (("${#missing_runner_workflows[@]}" != 0)); then
  printf 'МОВНИЙ_ГЕЙТ=RED причина=успадковані workflow без рядків ARCHIVE count=%s\n' "${#missing_runner_workflows[@]}" >&2
  printf '  missing_archive: %s\n' "${missing_runner_workflows[@]}" >&2
  exit 1
fi

self_test
echo "ARCHIVE (поза мовним коридором): $archive_count артефактів — $ARCHIVE_URL"
echo "МОВНИЙ_ГЕЙТ=OK registry=ARCHIVE runner_workflows=$workflow_count evidence=NOT_VERIFIED"
