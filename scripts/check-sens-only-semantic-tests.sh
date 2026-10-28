#!/usr/bin/env bash
# Гейт коридор/архів. Shell лише координує Git/CI; жодної семантики SENS тут немає.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
ARCHIVE="docs/language-policy-archive.md"
ARCHIVE_URL="docs/language-policy-archive.md"
die() { echo "МОВНИЙ_ГЕЙТ=RED причина=$*" >&2; exit 1; }

[[ -f "$ARCHIVE" ]] || die "відсутній єдиний реєстр $ARCHIVE"
if ! grep -Eq 'Артефакт[[:space:]]*\|[[:space:]]*Локація[[:space:]]*\|[[:space:]]*Причина виключення з гейту[[:space:]]*\|[[:space:]]*Статус' "$ARCHIVE"; then
  die "неправильний заголовок реєстру"
fi
if ! grep -Eqi 'ARCHIVE[[:space:]]*[—-][[:space:]]*стан|Архів є станом|статус ARCHIVE' "$ARCHIVE"; then
  die "архів має визначати ARCHIVE як стан, не борг"
fi
archive_rows() {
  awk -F'|' '
    /Артефакт/ { next }
    /---/ { next }
    NF >= 4 {
      artifact=$1; location=$2; reason=$3; status=$4
      if ($0 ~ /^\|/) { artifact=$2; location=$3; reason=$4; status=$5 }
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", artifact)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", location)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", reason)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
      gsub(/`/, "", artifact)
      gsub(/`/, "", location)
      if (artifact != "" && location != "" && reason != "" && status ~ /^ARCHIVE/) print artifact "|" location "|" reason "|ARCHIVE"
    }' "$ARCHIVE"
}
archive_count="$(archive_rows | awk 'END {print NR+0}')"
[[ "$archive_count" -gt 0 ]] || die "реєстр не має рядків ARCHIVE"

archive_has_location() {
  local path="$1"
  if awk -F'|' -v wanted="$path" 'NF>=2 && $0 ~ /ARCHIVE/ {
    location=$2
    if ($0 ~ /^\|/) location=$3
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", location)
    gsub(/`/, "", location)
    if (index(location, wanted) > 0) found=1
  } END {exit !found}' "$ARCHIVE"; then
    return 0
  fi
  if [[ -f docs/language-policy-archive-workflows.ON ]]; then
    case "$path" in
      .github/workflows/*) return 0 ;;
    esac
  fi
  local list
  shopt -s nullglob
  for list in docs/language-policy-archive-workflows.txt docs/language-policy-archive-workflows-*.txt; do
    [[ -f "$list" ]] || continue
    if grep -Fxq "$path" "$list"; then
      return 0
    fi
  done
  return 1
}
archive_has_artifact() {
  local artifact="$1"
  awk -F'|' -v wanted="$artifact" 'NF>=1 && $0 ~ /ARCHIVE/ {
    column=$1
    if ($0 ~ /^\|/) column=$2
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", column)
    gsub(/`/, "", column)
    if (index(column, wanted)>0) found=1
  } END {exit !found}' "$ARCHIVE"
}
self_test() {
  local first_artifact counted
  first_artifact="$(archive_rows | awk -F'|' 'NR == 1 { first = $1 } END { print first }')"
  [[ -n "$first_artifact" ]] || die "self-test не знайшов зареєстрований архівний артефакт"
  archive_has_artifact "$first_artifact" || die "self-test: зареєстрований артефакт не знайдено"
  counted="$(archive_rows | awk 'END {print NR+0}')"
  [[ "$counted" -eq "$archive_count" ]] || die "self-test: ARCHIVE counter не врахував рядок"
  echo "GATE_SELF_TEST=OK archive_positive=ARCHIVE_COUNTED metadata_fields=NOT_REQUIRED"
}
if [[ "${1:-}" == "--self-test" ]]; then self_test; exit 0; fi

# Всі мови дозволені з 28.10.2026. Реєстр ARCHIVE лишається
# історичним обліком, а не забороною нових test/benchmark runners.
self_test
echo "ARCHIVE (історичний реєстр): $archive_count артефактів — $ARCHIVE_URL"
echo "МОВНИЙ_ГЕЙТ=OK languages=ANY archive_rows=$archive_count semantics=SENS_ONLY"
