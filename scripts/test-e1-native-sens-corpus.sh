#!/usr/bin/env bash
# CI wrapper ONLY: binary SENS programs are the semantic authority.
set -euo pipefail
cd "$(dirname "$0")/.."
bin="${SENS_TRIT_BIN:-target/debug/sens-trit}"
root="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/sens-e1-native-corpus.XXXXXXXX")"
if [[ ! -x "$bin" ]]; then
  echo "::error::E1_NATIVE_CORPUS_MISSING_EXECUTOR binary=$bin"
  exit 1
fi
mkdir -p "$root"
sha256sum "$bin"
positive=0
negative=0

# Each existing SENS binary self-verdict must return exact D1:1.
for case_id in atom-empty atom-pair eq-reflexive eq-distinct car-cons cdr-cons cond-short-circuit nested-cons-atom; do
  source="tests/semantic/native-t5/$case_id.sens"
  target="$root/$case_id.sens"
  cp "$source" "$target"
  cp "${source%.sens}" "${target%.sens}"
  # Справжній Zig/T5M засвідчує фізичний код до мовного eval.
  if ! "$bin" verify-view "$target" > "$root/$case_id.view.out" 2> "$root/$case_id.view.err"; then
    echo "::error::E1_NATIVE_CORPUS_INVALID_T5M id=$case_id layer=transport expected=byte-exact-view actual=invalid-or-drifted"
    cat "$root/$case_id.view.err" >&2
    exit 1
  fi
  if ! "$bin" eval "$target" > "$root/$case_id.t5.out" 2> "$root/$case_id.t5.err"; then
    echo "::error::E1_NATIVE_CORPUS_RED id=$case_id layer=eval stage=t5 reproduce='$bin eval $target'"
    cat "$root/$case_id.t5.err" >&2
    exit 1
  fi
  if ! cmp -s "$root/$case_id.t5.out" <(printf '1\n'); then
    echo "::error::E1_NATIVE_CORPUS_BAD_SELF_VERDICT id=$case_id expected=D1:1"
    cat "$root/$case_id.t5.out" >&2
    exit 1
  fi
  if ! "$bin" encode-e1 "$target" > "$root/$case_id.encode.log" 2> "$root/$case_id.encode.err"; then
    echo "::error::E1_NATIVE_CORPUS_RED id=$case_id stage=e1-encode"
    cat "$root/$case_id.encode.err" >&2
    exit 1
  fi
  carrier="$root/$case_id.e1"
  test -s "$carrier" || { echo "::error::E1_NATIVE_CORPUS_MISSING_E1 id=$case_id"; exit 1; }
  if ! "$bin" eval-e1 "$carrier" > "$root/$case_id.e1.out" 2> "$root/$case_id.e1.err"; then
    echo "::error::E1_NATIVE_CORPUS_RED id=$case_id stage=e1-eval reproduce='$bin eval-e1 $carrier'"
    cat "$root/$case_id.e1.err" >&2
    exit 1
  fi
  cmp "$root/$case_id.t5.out" "$root/$case_id.e1.out" || {
    echo "::error::E1_NATIVE_CORPUS_VERDICT_MISMATCH id=$case_id"
    sha256sum "$root/$case_id.t5.out" "$root/$case_id.e1.out"
    exit 1
  }
  sha256sum "$source" "$carrier" "$root/$case_id.e1.out"
  echo "E1_NATIVE_CORPUS_POSITIVE_PASS id=$case_id authority=SENS"
  positive=$((positive+1))
done

# Три точні негативні закони: D2-носій валідний, але сам SENS
# мусить відхилити семантично неправильну форму, незалежно від E1.
# Кодування E1 не має права бути "підтвердженням" відмови.
for case_id in reject-cond-three-fields reject-cond-non-d1 reject-eq-pair; do
  case "$case_id" in
    reject-cond-three-fields)
      expected_diagnostic='D3:110 COND requires exactly (test expression); three-part compatibility is forbidden' ;;
    reject-cond-non-d1)
      expected_diagnostic='D3:110 COND expects exact D1:1 / D1:0' ;;
    reject-eq-pair)
      expected_diagnostic='eq expects two atoms' ;;
  esac
  source="tests/semantic/native-t5/$case_id.sens"
  target="$root/$case_id.sens"
  cp "$source" "$target"
  cp "${source%.sens}" "${target%.sens}"
  if ! "$bin" verify-view "$target" > "$root/$case_id.view.out" 2> "$root/$case_id.view.err"; then
    echo "::error::E1_NATIVE_CORPUS_INVALID_T5M id=$case_id layer=transport expected=byte-exact-view actual=invalid-or-drifted"
    cat "$root/$case_id.view.err" >&2
    exit 1
  fi
  if "$bin" eval "$target" > "$root/$case_id.t5.out" 2> "$root/$case_id.t5.err"; then
    echo "::error::E1_NATIVE_CORPUS_FAIL_OPEN id=$case_id layer=sens-t5 expected=Type-or-InvalidForm actual=accepted"
    exit 1
  fi
  if ! grep -Fq "$expected_diagnostic" "$root/$case_id.t5.err"; then
    echo "::error::E1_NATIVE_CORPUS_WRONG_REJECTION id=$case_id layer=sens-t5 expected=$expected_diagnostic actual=other"
    cat "$root/$case_id.t5.err" >&2
    exit 1
  fi
  # Лише успішний Zig E1 encode веде до справжнього негативного
  # виконання SENS. Transport/D2 error не може підмінити семантику.
  if ! "$bin" encode-e1 "$target" > "$root/$case_id.encode.log" 2> "$root/$case_id.encode.err"; then
    echo "::error::E1_NATIVE_CORPUS_ENCODE_FAILED id=$case_id layer=zig-e1 expected=encoded actual=rejected"
    cat "$root/$case_id.encode.err" >&2
    exit 1
  fi
  carrier="$root/$case_id.e1"
  test -s "$carrier" || { echo "::error::E1_NATIVE_CORPUS_MISSING_E1 id=$case_id"; exit 1; }
  if "$bin" eval-e1 "$carrier" > "$root/$case_id.e1.out" 2> "$root/$case_id.e1.err"; then
    echo "::error::E1_NATIVE_CORPUS_FAIL_OPEN id=$case_id layer=sens-e1 expected=Type-or-InvalidForm actual=accepted"
    exit 1
  fi
  if ! grep -Fq 'E1 -> current SENS evaluator rejected:' "$root/$case_id.e1.err" ||
     ! grep -Fq "$expected_diagnostic" "$root/$case_id.e1.err"; then
    echo "::error::E1_NATIVE_CORPUS_WRONG_REJECTION id=$case_id layer=sens-e1 expected=$expected_diagnostic actual=other"
    cat "$root/$case_id.e1.err" >&2
    exit 1
  fi
  sha256sum "$source" "$carrier" "$root/$case_id.e1.err"
  echo "E1_NATIVE_CORPUS_NEGATIVE_PASS id=$case_id layer=eval authority=SENS"
  negative=$((negative+1))
done
test "$positive" -eq 8
test "$negative" -eq 3
echo "E1_NATIVE_CORPUS_PASS positive=$positive native_negative=$negative authority=SENS"
