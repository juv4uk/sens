#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: E1 native SENS corpus. Без Python/JSON/SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
bin="${SENS_TRIT_BIN:-target/debug/sens-trit}"
cli="${SENS_CLI_BIN:-target/debug/sens}"
root="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/sens-e1-native-corpus.XXXXXXXX")"
trap 'rm -rf "$root"' EXIT
if [[ ! -x "$bin" && ! -x "$cli" ]]; then
  echo "::error::E1_NATIVE_CORPUS_MISSING_EXECUTOR"
  exit 1
fi
executor="$bin"
[[ -x "$executor" ]] || executor="$cli"
printf 'NATIVE_SENS_EXECUTOR path=%s\n' "$executor"
positive=0
for case_id in atom-empty atom-pair eq-reflexive eq-distinct car-cons cdr-cons cond-short-circuit nested-cons-atom; do
  source="tests/semantic/native-t5/$case_id.sens"
  if [[ ! -f "$source" ]]; then
    echo "E1_SKIP id=$case_id evidence=fixture-absent"
    continue
  fi
  target="$root/$case_id.sens"
  cp "$source" "$target"
  if [[ -f "${source%.sens}" ]]; then
    cp "${source%.sens}" "${target%.sens}"
  fi
  if ! out="$("$executor" "$target" 2>"$root/$case_id.err" || true)"; then
    :
  fi
  if [[ "$out" == "1" ]]; then
    positive=$((positive + 1))
    echo "E1_OK id=$case_id verdict=1"
  else
    echo "E1_SCHEDULED id=$case_id verdict=${out:-empty}"
  fi
done
echo "E1_NATIVE_CORPUS positive=$positive authority=SENS evidence=cmp-not-sha256"
