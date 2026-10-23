#!/usr/bin/env bash
# Self-test механічного охоронця; семантику визначає лише фізичний SENS.
set -euo pipefail
guard="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/guard-test-ownership-ratchet.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git -C "$tmp" init -q
git -C "$tmp" config user.email "ratchet@example.invalid"
git -C "$tmp" config user.name "SENS guard self-test"
printf 'baseline\n' >"$tmp/README"
git -C "$tmp" add README
git -C "$tmp" commit -qm baseline
base="$(git -C "$tmp" rev-parse HEAD)"

case_added() {
  local id="$1" path="$2" expected="$3" status=0 head
  git -C "$tmp" reset --hard -q "$base"
  git -C "$tmp" clean -fdq
  mkdir -p "$(dirname "$tmp/$path")"
  printf 'fixture\n' >"$tmp/$path"
  git -C "$tmp" add "$path"
  git -C "$tmp" commit -qm "$id"
  head="$(git -C "$tmp" rev-parse HEAD)"
  bash "$guard" "$base" "$head" "$tmp" >"$tmp/out" 2>"$tmp/err" || status=$?
  if [[ "$expected" == allow && "$status" -eq 0 ]] ||
     [[ "$expected" == reject && "$status" -eq 1 ]]; then
    if [[ "$expected" == reject ]]; then
      grep -Fq "fixture=$path" "$tmp/err"
      grep -Fq "REPRO:" "$tmp/err"
    fi
    printf 'PASS case=%s expected=%s observed=%s\n' "$id" "$expected" "$status"
  else
    cat "$tmp/out" "$tmp/err" >&2
    echo "FAIL case=$id expected=$expected observed=$status" >&2
    exit 1
  fi
}

case_added "SENS-law" "tests/semantic/guard-law.lisp" allow
case_added "Rust-mechanism" "crates/sens/tests/guard.rs" allow
case_added "Zig-codec" "research/zig-codecs/guard.zig" allow
case_added "Python-test" "tests/test_new_semantic.py" reject
case_added "Python-benchmark" "scripts/bench_new_semantic.py" reject
case_added "JSON-semantic" "tests/semantic/guard.json" reject
case_added "Rust-semantic" "tests/semantic/guard.rs" reject
case_added "Zig-semantic" "tests/semantic/guard.zig" reject
echo "TEST_OWNERSHIP_SELFTEST_PASS cases=8"
