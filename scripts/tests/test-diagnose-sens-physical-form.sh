#!/usr/bin/env bash
# Перевіряє позиції форм, не обчислює SENS.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/program.lisp" <<'EOF'
; (у-коментарі) — не Lisp-форма
(визначити перевірка (як-є "дужки ( і ) та ;"))
; інша хибна форма ()
(за-умовою
  ((порожній? (як-є ())) (атом? (як-є ()))))
(атом? (як-є ()))
EOF
echo 'kind=Type [physical_form_index=1 physical_word_start=3]' > "$tmp/native.err"
bash "$root/scripts/diagnose-sens-physical-form.sh" "$tmp/program.lisp" "$tmp/native.err" probe > "$tmp/out"
grep -Fq 'id=probe physical_form_index=1 source_line=4 lexical_form_count=3 scope=diagnostic-not-semantic' "$tmp/out"
grep -Fq 'SENS_FORM_SOURCE id=probe first_line=(за-умовою' "$tmp/out"
echo 'no form index reported' > "$tmp/native.err"
bash "$root/scripts/diagnose-sens-physical-form.sh" "$tmp/program.lisp" "$tmp/native.err" probe > "$tmp/out"
grep -Fq 'physical_form_index=NOT_REPORTED status=NOT_ASSERTED' "$tmp/out"
echo 'kind=Type [physical_form_index=999]' > "$tmp/native.err"
if bash "$root/scripts/diagnose-sens-physical-form.sh" "$tmp/program.lisp" "$tmp/native.err" probe > "$tmp/out"; then
 echo 'REGRESSION: nonexistent index was accepted' >&2; exit 1
fi
grep -Fq 'status=INDEX_OUT_OF_RANGE lexical_form_count=3' "$tmp/out"
printf 'SENS_FORM_LOCATION_TEST_PASS checks=4 mechanism=source-position-only\n'
