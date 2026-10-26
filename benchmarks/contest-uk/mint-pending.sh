#!/usr/bin/env bash
# Допуск неопарених українських Lisp до конкурсу тільки живим SENS/Zig/T5M.
set -euo pipefail
cd "$(dirname "$0")/../.."
dir=benchmarks/contest-uk
sens="${SENS_BIN:-$PWD/target/debug/sens}"
trit="${SENS_TRIT_BIN:-$PWD/target/debug/sens-trit}"
[[ -x "$sens" && -x "$trit" ]] || { echo "CONTEST_NATIVE_MISSING" >&2; exit 2; }
tmp="$(mktemp -d "$dir/.mint-pending.XXXXXXXX")"
unverified=""
cleanup() {
  [[ -z "$unverified" ]] || rm -f -- "$unverified.sens" "$unverified"
  rm -rf -- "$tmp"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
admitted=0
failed=0
for source in "$dir"/*.lisp; do
  [[ -f "$source" && ! -L "$source" ]] || continue
  stem="${source%.lisp}"
  if [[ -e "$stem" || -L "$stem" || -e "$stem.sens" || -L "$stem.sens" ]]; then
    [[ -s "$stem.sens" && -f "$stem" && ! -L "$stem" && ! -L "$stem.sens" ]] && continue
    echo "CONTEST_INCOMPLETE_PAIR source=$source" >&2
    failed=$((failed+1))
    continue
  fi
  # Побайтовий знімок джерела перевіряється на кожній межі виконання.
  name="${stem##*/}"
  source_snapshot="$tmp/$name.source.snapshot"
  cp -- "$source" "$source_snapshot"
  source_stable() { cmp -s "$source_snapshot" "$source"; }
  stage="$tmp/$name.sens"
  rm -f -- "$stage" "$tmp/$name"
  if ! source_stable ||
     ! "$sens" --t5m-mint "$source" "$stage" >"$tmp/mint.out" 2>"$tmp/error" ||
     ! source_stable ||
     [[ ! -s "$stage" ]] ||
     ! "$trit" open "$stage" >"$tmp/$name" 2>>"$tmp/error" ||
     ! source_stable ||
     ! "$trit" verify-view "$stage" >/dev/null 2>>"$tmp/error" ||
     ! source_stable ||
     ! "$sens" --t5m-pair "$source" "$stage" >"$tmp/paired" 2>>"$tmp/error" ||
     ! source_stable ||
     ! "$sens" "$stage" >"$tmp/standalone" 2>>"$tmp/error" ||
     ! source_stable ||
     ! cmp -s "$tmp/paired" "$tmp/standalone"; then
    echo "CONTEST_NATIVE_RED source=$source stage=preflight" >&2
    cat "$tmp/error" >&2
    failed=$((failed+1))
    continue
  fi
  if ! ln -- "$stage" "$stem.sens"; then
    echo "CONTEST_COLLISION source=$source" >&2
    failed=$((failed+1))
    continue
  fi
  unverified="$stem"
  if ! ln -- "$tmp/$name" "$stem"; then
    rm -f -- "$stem.sens"
    unverified=""
    echo "CONTEST_COLLISION source=$source" >&2
    failed=$((failed+1))
    continue
  fi
  if ! SENS_CONTEST_PROOF_ONLY=true SENS_BIN="$sens" SENS_TRIT_BIN="$trit" \
       bash "$dir/judge.sh" "$stem.sens" >"$tmp/judge.out" 2>"$tmp/judge.err"; then
    rm -f -- "$stem.sens" "$stem"
    unverified=""
    echo "CONTEST_NATIVE_RED source=$source stage=judge" >&2
    cat "$tmp/judge.err" >&2
    failed=$((failed+1))
    continue
  fi
  if ! source_stable; then
    rm -f -- "$stem.sens" "$stem"
    unverified=""
    echo "CONTEST_SOURCE_CHANGED source=$source action=reject_stale_proof" >&2
    failed=$((failed+1))
    continue
  fi
  unverified=""
  admitted=$((admitted+1))
  printf 'CONTEST_NATIVE_ADMITTED source=%s bytes=%s\n' "$source" "$(wc -c < "$stem.sens")"
done
printf 'CONTEST_NATIVE_MINT_RESULT admitted=%s failed=%s\n' "$admitted" "$failed"
(( failed == 0 ))
