#!/usr/bin/env bash
# CI transport only. The sole semantic executor is the real ELF target/debug/sens.
set -euo pipefail
umask 077

if [[ -z "$RUNNER_TEMP" ]]; then
  echo "::error::UNINFORMATIVE-EXECUTOR RUNNER_TEMP is required" >&2
  exit 1
fi
binary="target/debug/sens"
store="$RUNNER_TEMP/sens-native-evidence"
trace="$store/executor.log"
mkdir -p "$store"
emit() { printf '%s\n' "$*" | tee -a "$trace"; }
sha() { sha256sum "$1" | cut -d ' ' -f 1; }
bad() { echo "::error::UNINFORMATIVE-EXECUTOR $*" >&2; exit 1; }

action="$1"
shift
if [[ "$action" == run ]]; then
  [[ "$#" -eq 4 ]] || bad "usage: run ID FIXTURE positive|reject-non-callable EXPECTATION"
  id="$1"; fixture="$2"; mode="$3"; expectation="$4"
  [[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || bad "invalid witness id"
  [[ "$fixture" == tests/semantic/* ]] || bad "semantic witness must be a physical tests/semantic path: $fixture"
  [[ -f "$fixture" ]] || bad "fixture missing: $fixture"
  [[ -x "$binary" ]] || bad "native SENS binary missing or not executable: $binary"
  [[ "$(head -c 4 "$binary" | od -An -tx1 | tr -d ' \n')" == 7f454c46 ]] || bad "executor is not an ELF binary"
  [[ "$mode" == positive || "$mode" == reject-non-callable ]] || bad "unsupported mode"
  [[ ! -e "$store/$id.proof" ]] || bad "duplicate witness id $id"
  if [[ "$mode" == positive ]]; then
    [[ -f "$expectation" ]] || bad "expected output missing"
    expected_sha="$(sha "$expectation")"
  else
    [[ "$expectation" == "not callable" ]] || bad "negative witness must check the SENS non-callable error"
    expected_sha="$(printf '%s' "$expectation" | sha256sum | cut -d ' ' -f 1)"
  fi
  version="$("$binary" --version)" || bad "native SENS --version failed"
  [[ "$version" == sens\ * ]] || bad "unexpected SENS version: $version"
  binary_sha="$(sha "$binary")"
  fixture_sha="$(sha "$fixture")"
  stdout="$store/$id.stdout"
  stderr="$store/$id.stderr"
  emit "SENS_EXECUTOR_BEGIN id=$id kind=$mode semantic_authority=native-ELF-SENS"
  emit "SENS_EXECUTOR_BINARY path=$binary version=$version sha256=$binary_sha"
  emit "SENS_EXECUTOR_INPUT path=$fixture sha256=$fixture_sha"
  emit "SENS_EXECUTOR_PROCESS command=./$binary $fixture"
  set +e
  "./$binary" "$fixture" > "$stdout" 2> "$stderr"
  status="$?"
  set -e
  actual_sha="$(sha "$stdout")"
  stderr_sha="$(sha "$stderr")"
  verdict=FAIL
  if [[ "$mode" == positive ]]; then
    if [[ "$status" -eq 0 ]] && cmp -s "$expectation" "$stdout"; then verdict=PASS; fi
  else
    if [[ "$status" -ne 0 ]] && grep -Fqi "$expectation" "$stderr"; then verdict=PASS; fi
  fi
  emit "SENS_EXECUTOR_DIGESTS id=$id expected_sha256=$expected_sha actual_stdout_sha256=$actual_sha actual_stderr_sha256=$stderr_sha exit_code=$status"
  emit "SENS_EXECUTOR_REPRODUCE id=$id command=./$binary $fixture"
  emit "SENS_EXECUTOR_END id=$id verdict=$verdict"
  printf '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n' \
    "$id" "$fixture" "$mode" "$expectation" "$binary_sha" "$fixture_sha" "$expected_sha" "$actual_sha" "$stderr_sha" "$status" "$verdict" > "$store/$id.proof"
  if [[ "$verdict" != PASS ]]; then
    echo "SENS_EXECUTOR_STDERR id=$id" >&2
    tail -n 25 "$stderr" >&2
    bad "native semantic witness failed id=$id status=$status"
  fi
  exit 0
fi

if [[ "$action" == scan ]]; then
  [[ "$#" -ge 1 ]] || bad "scan must name mandatory native witnesses"
  [[ -f "$trace" ]] || bad "native executor transcript absent"
  [[ -x "$binary" ]] || bad "native binary absent during ratchet"
  current_binary_sha="$(sha "$binary")"
  for id in "$@"; do
    [[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || bad "bad scan id"
    proof="$store/$id.proof"
    [[ -f "$proof" ]] || bad "missing native executor evidence id=$id"
    IFS='|' read -r record_id fixture mode expectation binary_sha fixture_sha expected_sha actual_sha stderr_sha status verdict < "$proof"
    [[ "$record_id" == "$id" && "$verdict" == PASS ]] || bad "no native PASS id=$id"
    [[ "$binary_sha" == "$current_binary_sha" && "$fixture_sha" == "$(sha "$fixture")" ]] || bad "binary/input digest drift id=$id"
    [[ "$actual_sha" == "$(sha "$store/$id.stdout")" && "$stderr_sha" == "$(sha "$store/$id.stderr")" ]] || bad "output digest drift id=$id"
    if [[ "$mode" == positive ]]; then
      [[ "$status" -eq 0 && "$expected_sha" == "$(sha "$expectation")" ]] || bad "expected output/exit drift id=$id"
      cmp -s "$expectation" "$store/$id.stdout" || bad "native stdout no longer matches expected id=$id"
    elif [[ "$mode" == reject-non-callable ]]; then
      [[ "$status" -ne 0 && "$expectation" == "not callable" ]] || bad "false negative-test claim id=$id"
      grep -Fqi "$expectation" "$store/$id.stderr" || bad "wrong negative error id=$id"
      [[ "$expected_sha" == "$(printf '%s' "$expectation" | sha256sum | cut -d ' ' -f 1)" ]] || bad "negative criterion digest drift id=$id"
    else
      bad "unrecognized native witness mode id=$id"
    fi
    [[ "$(grep -Fc "SENS_EXECUTOR_BEGIN id=$id " "$trace")" -eq 1 ]] || bad "begin not unique in log id=$id"
    [[ "$(grep -Fxc "SENS_EXECUTOR_END id=$id verdict=PASS" "$trace")" -eq 1 ]] || bad "completed native process absent in log id=$id"
    [[ "$(grep -Fc "SENS_EXECUTOR_PROCESS command=./$binary $fixture" "$trace")" -ge 1 ]] || bad "executable command absent in log id=$id"
    emit "SENS_EXECUTOR_RATCHET_PASS id=$id binary_sha256=$binary_sha input_sha256=$fixture_sha actual_sha256=$actual_sha"
  done
  emit "SENS_NATIVE_EXECUTOR_GATE_PASS count=$#"
  exit 0
fi
bad "unknown action: $action"
