#!/usr/bin/env bash
# CI wrapper ONLY: binary SENS programs are the semantic authority.
set -euo pipefail
cd "$(dirname "$0")/.."
bin="${SENS_TRIT_BIN:-target/debug/sens-trit}"
root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/sens-e1-native-corpus"
if [[ ! -x "$bin" ]]; then
  echo "::error::E1_NATIVE_CORPUS_MISSING_EXECUTOR binary=$bin"
  exit 1
fi
mkdir -p "$root"
sha256sum "$bin"
positive=0
negative=0
preadmission=0

# Each existing SENS binary self-verdict must return exact D1:1.
for case_id in atom-empty atom-pair eq-reflexive eq-distinct car-cons cdr-cons cond-short-circuit nested-cons-atom; do
  source="tests/semantic/native-t5/$case_id.sens"
  target="$root/$case_id.sens"
  cp "$source" "$target"
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

# Existing language-negative SENS witnesses. If SENS rejects at the D2
# pre-admission stage, classify it honestly: NOT an E1 evaluator negative.
for case_id in reject-cond-three-fields reject-cond-non-d1 reject-eq-pair; do
  source="tests/semantic/native-t5/$case_id.sens"
  target="$root/$case_id.sens"
  cp "$source" "$target"
  if "$bin" eval "$target" > "$root/$case_id.t5.out" 2> "$root/$case_id.t5.err"; then
    echo "::error::E1_NATIVE_CORPUS_FAIL_OPEN id=$case_id stage=native-t5"
    exit 1
  fi
  if "$bin" encode-e1 "$target" > "$root/$case_id.encode.log" 2> "$root/$case_id.encode.err"; then
    carrier="$root/$case_id.e1"
    test -s "$carrier" || { echo "::error::E1_NATIVE_CORPUS_MISSING_E1 id=$case_id"; exit 1; }
    if "$bin" eval-e1 "$carrier" > "$root/$case_id.e1.out" 2> "$root/$case_id.e1.err"; then
      echo "::error::E1_NATIVE_CORPUS_FAIL_OPEN id=$case_id stage=e1-eval"
      exit 1
    fi
    if ! grep -Eq 'Language|current SENS' "$root/$case_id.e1.err" ||
       grep -q 'Transport(' "$root/$case_id.e1.err"; then
      echo "::error::E1_NATIVE_CORPUS_UNINFORMATIVE_REJECTION id=$case_id expected=SENS-language"
      cat "$root/$case_id.e1.err" >&2
      exit 1
    fi
    sha256sum "$source" "$carrier" "$root/$case_id.e1.err"
    echo "E1_NATIVE_CORPUS_NEGATIVE_PASS id=$case_id layer=eval authority=SENS"
    negative=$((negative+1))
  else
    sha256sum "$source" "$root/$case_id.encode.err"
    echo "E1_NATIVE_CORPUS_PREADMISSION_REJECTED id=$case_id layer=D2 no_e1_execution=true"
    preadmission=$((preadmission+1))
  fi
done
test "$positive" -eq 8
test "$((negative+preadmission))" -eq 3
echo "E1_NATIVE_CORPUS_PASS positive=$positive native_negative=$negative preadmission_negative=$preadmission authority=SENS"
