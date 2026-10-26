#!/usr/bin/env bash
# Select exact changed SENS sources for the existing native Lisp → Zig/T5M → SENS runner.
# This selector is mechanism only; semantic verdicts remain in SENS.
set -euo pipefail
cd "$(dirname "$0")/.."

raw="$RUNNER_TEMP/changed-lisp-raw.txt"
manifest="$RUNNER_TEMP/changed-t5m-lisp.txt"
base="$BEFORE_SHA"

if [[ "$GITHUB_EVENT_NAME" == pull_request ]]; then
  if ! git cat-file -e "$GITHUB_SHA^1" 2>/dev/null; then
    timeout 60s git fetch --no-tags --deepen=2 origin "$GITHUB_REF"
  fi
  base="$(git rev-parse "$GITHUB_SHA^1")"
fi
if [[ -z "$base" || "$base" =~ ^0+$ ]]; then
  if git cat-file -e "$GITHUB_SHA^1" 2>/dev/null; then
    base="$(git rev-parse "$GITHUB_SHA^1")"
  else
    echo "::error::T5M_CHANGED_BASE_UNAVAILABLE event=$GITHUB_EVENT_NAME" >&2
    exit 2
  fi
fi
if ! git cat-file -e "$base^{commit}" 2>/dev/null; then
  timeout 60s git fetch --no-tags --depth=1 origin "$base"
fi

git -c core.quotePath=false diff --name-only -z --diff-filter=ACMRT "$base" "$GITHUB_SHA" -- \
  '*.lisp' '*.sens' '*.rs' '*.zig' \
  '.github/workflows/ci.yml' '.github/workflows/ci-heavy.yml' \
  'scripts/prove-lisp-semantic-t5m.sh' 'scripts/prove-lisp-language-laws.sh' \
  'scripts/execute_changed_lisp_t5m.sh' 'scripts/ci-*' 'scripts/ci_*' \
  'scripts/check-*' 'scripts/check_*' 'scripts/guard-*' 'scripts/mint-*' > "$raw"

mapfile -d '' -t changed_paths < "$raw"
selected=()
has_lisp=false
has_rust=false
has_zig=false
workflow_changed=false

add_selected() {
  local candidate="$1"
  local present
  for present in "${selected[@]}"; do
    [[ "$present" == "$candidate" ]] && return 0
  done
  selected+=("$candidate")
}

has_source_form() {
  local line trimmed
  while IFS= read -r line || [[ -n "$line" ]]; do
    trimmed="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$trimmed" || "$trimmed" == \;* ]] && continue
    return 0
  done < "$1"
  return 1
}

has_definition() {
  local line trimmed
  while IFS= read -r line || [[ -n "$line" ]]; do
    trimmed="${line#"${line%%[![:space:]]*}"}"
    case "$trimmed" in
      "(визначити "*|"(визначити)"*|"(define "*|"(define)"*) return 0 ;;
    esac
  done < "$1"
  return 1
}

for original in "${changed_paths[@]}"; do
  [[ -z "$original" ]] && continue
  case "$original" in
    *$'\n'*|*$'\r'*|*$'\t'*|[[:space:]]*|*[[:space:]])
      printf 'T5M_CHANGED_PATH_INVALID path=%q\n' "$original" >&2
      exit 2
      ;;
  esac

  case "$original" in
    .github/workflows/ci.yml|.github/workflows/ci-heavy.yml|scripts/prove-lisp-semantic-t5m.sh|scripts/prove-lisp-language-laws.sh|scripts/execute_changed_lisp_t5m.sh|scripts/ci-*|scripts/ci_*|scripts/check-*|scripts/check_*|scripts/guard-*|scripts/mint-*)
      workflow_changed=true
      continue
      ;;
  esac

  case "$original" in
    *.lisp) has_lisp=true ;;
    *.rs) has_rust=true; continue ;;
    *.zig) has_zig=true; continue ;;
  esac

  name="$original"
  [[ "$name" == *.sens ]] && name="${name%.sens}.lisp"
  [[ "$name" == *.lisp ]] || continue
  case "$name" in
  lib/domains/*|lib/generated/*|knowledge/*|docs/*|research/*|contracts/*|lib/machine/xed/generated/*|language-contract.lisp) continue ;;
esac

  if [[ ! -f "$name" || -L "$name" ]]; then
    printf 'T5M_CHANGED_SOURCE_INVALID path=%s\n' "$name" >&2
    exit 1
  fi

  case "$name" in
    lib/core4-parts/*)
      if [[ ! -f lib/core4.lisp || -L lib/core4.lisp ]]; then
        printf 'T5M_CORE4_AGGREGATE_MISSING fragment=%s\n' "$name" >&2
        exit 1
      fi
      add_selected lib/core4.lisp
      printf 'T5M_CORE4_FRAGMENT_IN_AGGREGATE fragment=%s source=lib/core4.lisp\n' "$name"
      continue
      ;;
    lib/surface/*)
      if ! has_definition "$name"; then
        printf 'T5M_NONPROGRAM_SURFACE path=%s\n' "$name"
        continue
      fi
      ;;
  esac

  if ! has_source_form "$name"; then
    continue
  fi

  case "$name" in
  "tests/semantic/utf8-direct-d1-law.lisp"|\
  "tests/semantic/utf8-direct-d1-mutant.lisp"|\
  "tests/semantic/meta-eval-graph-d1-law.lisp"|\
  "tests/semantic/meta-eval-graph-d1-mutant.lisp"|\
  "tests/semantic/meta-eval-predicates-d1-law.lisp"|\
  "tests/semantic/meta-eval-predicates-d1-mutant.lisp"|\
  "tests/semantic/meta-eval-lexical-shadow-d1-physical-law.lisp"|\
  "tests/semantic/meta-eval-lexical-shadow-d1-physical-mutant.lisp"|\
  "tests/semantic/meta-fc-predicates-d1-mutant.lisp"|\
  "tests/semantic/unification-occurs-check-law.lisp"|\
  "tests/semantic/unification-occurs-check-mutant.lisp"|\
  "tests/semantic/d9-map-hidden-tail-positive.lisp"|\
  "tests/semantic/d9-map-hidden-tail-get-negative.lisp"|\
  "tests/semantic/d9-map-hidden-tail-insert-negative.lisp"|\
  "tests/semantic/d11-scan-fold-d3-tail-law.lisp"|\
  "tests/semantic/d11-scan-fold-d3-tail-mutant.lisp"|\
  "tests/semantic/d11-scan-fold-d3-tail-scan-improper-negative.lisp"|\
  "tests/semantic/d11-scan-fold-d3-tail-left-improper-negative.lisp"|\
  "tests/semantic/d11-scan-fold-d3-tail-right-improper-negative.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-law.lisp"|\
  "tests/semantic/d11-assoc-delete-proper-law.lisp"|\
  "tests/semantic/d11-assoc-delete-order-mutant.lisp"|\
  "tests/semantic/d11-assoc-delete-improper-tail-negative.lisp"|\
  "tests/semantic/d11-assoc-delete-invalid-record-negative.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-structure-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-pairs-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-pairs-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-adjacent-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-mutant.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-pairs-mutant.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-directed-adjacent-mutant.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-nullary-law.lisp"|\
  "tests/semantic/d11-srfi1-list-equality-mutant.lisp"|\
  "tests/semantic/d11-reason-proof-trace-law.lisp"|\
  "tests/semantic/d11-reason-proof-results-law.lisp"|\
  "tests/semantic/d11-reason-proof-results-mutant.lisp"|\
  "tests/semantic/d11-reason-proof-results-improper-accum-negative.lisp"|\
  "tests/semantic/d11-reason-proof-results-improper-scan-negative.lisp"|\
  "tests/semantic/d11-reason-proof-results-improper-map-negative.lisp"|\
  "tests/semantic/d11-reason-proof-results-improper-attach-negative.lisp"|\
  "tests/semantic/d11-reason-index-law.lisp"|\
  "tests/semantic/d11-reason-index-mutant.lisp"|\
  "tests/semantic/d11-reason-index-improper-reverse-negative.lisp"|\
  "tests/semantic/d11-reason-index-improper-buckets-negative.lisp"|\
  "tests/semantic/d11-reason-index-improper-rules-negative.lisp"|\
  "tests/semantic/d11-reason-proof-trace-mutant.lisp"|\
  "tests/semantic/d11-reason-proof-trace-improper-provenance-negative.lisp"|\
  "tests/semantic/d11-reason-proof-trace-improper-count-negative.lisp"|\
  "tests/semantic/d11-srfi1-find-tail-laws.lisp"|\
  "tests/semantic/d11-clojure-juxt-laws.lisp"|\
  "tests/semantic/d11-clojure-juxt-mutant.lisp"|\
  "tests/semantic/d11-clojure-juxt-improper-d1-tail-negative.lisp"|\
  "tests/semantic/d11-clojure-frequencies-unary-law.lisp"|\
  "tests/semantic/d11-clojure-frequencies-unary-mutant.lisp"|\
  "tests/semantic/d11-clojure-frequencies-improper-count-negative.lisp"|\
  "tests/semantic/d11-clojure-frequencies-improper-groups-negative.lisp"|\
  "tests/semantic/unification-variable-shape-law.lisp"|\
  "tests/semantic/unification-variable-shape-positive.lisp"|\
  "tests/semantic/unification-variable-shape-negative.lisp"|\
  "tests/semantic/unification-variable-shape-mutant.lisp"|\
  "tests/semantic/unification-constructor-law.lisp"|\
  "tests/semantic/unification-constructor-mutant.lisp"|\
  "tests/semantic/unification-occurs-predicate-law.lisp"|\
  "tests/semantic/unification-occurs-predicate-mutant.lisp"|\
  "tests/semantic/core-d3-car-cdr-cons-mutant.lisp"|\
  "tests/semantic/utf8-boundary-laws.lisp"|\
  "tests/semantic/utf8-boundary-mutant.lisp"|\
  "tests/semantic/utf8-quotient-laws.lisp"|\
  "tests/semantic/utf8-quotient-mutant.lisp"|\
  "tests/semantic/result-status-laws.lisp"|\
  "tests/semantic/d11-srfi1-span-break-laws.lisp"|\
  "tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp"|\
  "tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp"|\
  "tests/semantic/d7-epistemic-structural-tag-law.lisp"|\
  "tests/semantic/d7-epistemic-structural-tag-mutant.lisp"|\
  "tests/semantic/language-law-epistemic-records.lisp"|\
  "tests/semantic/language-mutant-epistemic-records.lisp"|\
  "tests/semantic/усі-за-предикатом-law.lisp"|\
  "tests/semantic/усі-за-предикатом-mutant.lisp"|\
  "tests/semantic/існує-за-предикатом-law.lisp"|\
  "tests/semantic/існує-за-предикатом-mutant.lisp"|\
  "tests/semantic/d6-zip-proper-law.lisp"|\
  "tests/semantic/d6-zip-proper-mutant.lisp"|\
  "tests/semantic/d6-zip-improper-tail-negative.lisp"|\
  "tests/semantic/d6-zip-improper-root-negative.lisp"|\
  "tests/semantic/d6-filter-improper-tail-negative.lisp"|\
  "tests/semantic/ukr-lists-d24-language-law.lisp"|\
  "tests/semantic/d24-polynomial-language-law.lisp"|\
  "tests/semantic/d24-polynomial-language-mutant.lisp"|\
  "tests/semantic/d24-ackermann-language-law.lisp"|\
  "tests/semantic/d24-ackermann-language-mutant.lisp"|\
  "tests/semantic/d24-fibonacci-language-law.lisp"|\
  "tests/semantic/d24-fibonacci-language-mutant.lisp"|\
  "tests/semantic/d24-reader-fraction-language-law.lisp"|\
  "tests/semantic/d24-reader-fraction-language-mutant.lisp"|\
  "tests/semantic/d24-reader-zero-denominator-negative.lisp"|\
  "tests/semantic/d4-recursion-benchmark-law.lisp"|\
  "tests/semantic/d4-recursion-benchmark-mutant.lisp"|\
  "tests/semantic/d3-proper-tail-hot-law.lisp"|\
  "tests/semantic/d3-proper-tail-hot-mutant.lisp"|\
  "tests/semantic/d4-recursion-atom-result-law.lisp"|\
  "tests/semantic/d4-recursion-atom-result-mutant.lisp"|\
  "tests/fixtures/conformance-transition-witness.lisp"|\
  "tests/fixtures/witness-runner.lisp"|\
  "tests/fixtures/epistemic-authority-witness.lisp"|\
  "tests/fixtures/d11-list-equality-improper-left-must-error.lisp"|\
  "tests/fixtures/d11-list-equality-improper-right-must-error.lisp"|\
  "tests/fixtures/d11-list-equality-invalid-singleton-must-error.lisp"|\
  "tests/fixtures/d11-list-equality-invalid-third-must-error.lisp"|\
  "tests/fixtures/d11-dwim-exact-context-positive.lisp"|\
  "tests/fixtures/d11-dwim-extra-field-negative.lisp"|\
  "tests/fixtures/d11-dwim-unrelated-extra-field-negative.lisp"|\
  "tests/fixtures/d11-dwim-dotted-record-negative.lisp"|\
  "tests/fixtures/d11-unfold-terminal-left-atom-must-error.lisp"|\
  "tests/fixtures/d11-unfold-terminal-left-dotted-must-error.lisp"|\
  "tests/fixtures/d11-unfold-terminal-right-atom-must-error.lisp"|\
  "tests/fixtures/d11-unfold-terminal-right-dotted-must-error.lisp"|\
  "tests/semantic/d5-exact-numbers-filter-law.lisp"|\
  "tests/semantic/d5-exact-numbers-filter-mutant.lisp"|\
  "tests/semantic/d5-exact-numbers-filter-improper-tail-negative.lisp"|\
  "tests/semantic/d6-any-improper-tail-negative.lisp"|\
  "tests/semantic/d6-all-improper-tail-negative.lisp"|\
  "tests/semantic/d4-zip-equal-length-law.lisp"|\
  "tests/semantic/d4-zip-equal-length-mutant.lisp"|\
  "tests/semantic/d4-zip-extra-left-negative.lisp"|\
  "tests/semantic/d4-zip-extra-right-negative.lisp"|\
  "tests/semantic/d4-zip-improper-right-negative.lisp"|\
  "tests/semantic/d9-f6-package-key-canonicalization-law.lisp"|\
  "tests/semantic/d9-f6-package-key-canonicalization-mutant.lisp"|\
  "tests/semantic/d9-f6-bindings-shape-law.lisp"|\
  "tests/semantic/d9-f6-bindings-shape-mutant.lisp"|\
  "tests/semantic/d9-f6-object-addresses-law.lisp"|\
  "tests/semantic/d9-f6-object-addresses-mutant.lisp"|\
  "tests/semantic/d9-f6-object-addresses-d1-root-negative.lisp"|\
  "tests/semantic/d9-f6-object-addresses-d1-tail-negative.lisp"|\
  "tests/semantic/d9-f6-object-addresses-empty-address-negative.lisp"|\
  "tests/semantic/d5-pairlis-total-list-law.lisp"|\
  "tests/semantic/d5-pairlis-total-list-mutant.lisp"|\
  "tests/semantic/d5-pairlis-improper-key-tail-negative.lisp"|\
  "tests/semantic/d5-pairlis-improper-value-tail-negative.lisp"|\
  "tests/semantic/d5-pairlis-extra-value-negative.lisp"|\
  "tests/fixtures/wsm-fs-record-producer.lisp")
    printf 'T5M_DEPENDENT_FIXTURE path=%s route=native-law-bundle\n' "$name"
    continue
    ;;
esac

  add_selected "$name"
done

if [[ "$has_lisp" == true || "$workflow_changed" == true ]]; then
  for witness in (
    "tests/semantic/ukr-d3-structural-selftest.lisp"
    "tests/semantic/language-law-d1-d4-ukr.lisp"
    "tests/semantic/language-law-d4-closure-shadow-ukr.lisp"
    "tests/semantic/language-mutant-d4-closure-shadow-ukr.lisp"
    "tests/semantic/language-law-d3-cond-demand.lisp"
    "tests/semantic/language-mutant-d3-cond-demand.lisp"
    "tests/semantic/language-law-d4-parameter-shadowing.lisp"
    "tests/semantic/language-mutant-d4-parameter-shadowing.lisp"
    "tests/semantic/language-law-quote-inertness.lisp"
    "tests/semantic/language-mutant-quote-inertness.lisp"
    "tests/semantic/lisp-d4-lexical-closure-laws.lisp"
    "tests/semantic/lisp-d4-recursive-list-laws.lisp"
    "tests/semantic/lisp-d4-recursive-list-mutant.lisp"
    "tests/semantic/lisp-d3-atom-cond-laws.lisp"
    "tests/semantic/lisp-d3-cons-selectors-laws.lisp"
    "tests/semantic/lisp-d3-eq-branches-laws.lisp"
    "tests/semantic/language-law-d3-eq-symmetry-ukr.lisp"
    "tests/semantic/language-mutant-d3-eq-symmetry-ukr.lisp"
    "tests/semantic/lisp-d3-d4-list-self-verdict.lisp"
    "tests/semantic/d3-structural-native-t5m-law.lisp"
    "tests/semantic/d3-structural-native-t5m-mutant.lisp"
  ); do
    add_selected "$witness"
    printf 'SENS_LISP_SEMANTIC_LAW source=%s authority=SENS\n' "$witness"
  done
fi

: > "$manifest"
if (("${#selected[@]}" > 0)); then
  printf '%s\n' "${selected[@]}" > "$manifest"
fi
{
  printf 'has_lisp=%s\n' "$([[ "$has_lisp" == true || "$workflow_changed" == true ]] && printf true || printf false)"
  printf 'has_files=%s\n' "$([[ "${#selected[@]}" -gt 0 ]] && printf true || printf false)"
  printf 'has_rust=%s\n' "$([[ "$has_rust" == true ]] && printf true || printf false)"
  printf 'has_zig=%s\n' "$([[ "$has_zig" == true ]] && printf true || printf false)"
  printf 'lisp_files<<SENS_LISP_FILES\n'
  cat "$manifest"
  printf 'SENS_LISP_FILES\n'
} >> "$GITHUB_OUTPUT"

printf 'T5M_CHANGED_EXECUTABLE_LISP count=%s\n' "${#selected[@]}"
for name in "${selected[@]}"; do
  printf 'T5M_CHANGED_FILE %s\n' "$name"
done
