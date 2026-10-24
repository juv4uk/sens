#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: лише запуск SENS та порівняння вироків D1.
# Усі закони, входи, логічні умови й мутанти написані в .lisp.
set -euo pipefail
cd "$(dirname "$0")/.."
if (( $# > 1 )); then
  echo 'usage: bash scripts/prove-lisp-language-laws.sh [native-sens-path]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=lisp-language-laws layer=executor expected=native-sens actual=missing path=%s\n' "$cli" >&2
  exit 1
fi
# Той самий Zig-кодек відкриває і перевіряє фізичні слова.
reader="$(dirname "$cli")/sens-trit"
if [[ ! -x "$reader" ]]; then
  printf 'REGRESSION test_id=lisp-language-laws layer=Zig-T5M expected=sens-trit actual=missing path=%s\n' "$reader" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR test_id=lisp-language-laws path=%s version=%s\n' "$cli" "$("$cli" --version)"
for id in d1-not d2-cond-laziness d3-structure d4-lexical-scope d4-second-selector d4-closure-pair d4-nested-pair-selectors d3-dotted-pair d3-cons-pair-roundtrip d3-nested-cons-reconstruction d3-cond-demand d4-parameter-shadowing quote-inertness d5-recursive-list d6-compose-flip; do
  case "$id" in
    d3-cond-demand|d4-parameter-shadowing|quote-inertness)
      law="tests/semantic/language-law-$id.lisp"
      mutant="tests/semantic/language-mutant-$id.lisp"
      ;;
    *)
      law="tests/semantic/$id-law.lisp"
      mutant="tests/semantic/$id-mutant.lisp"
      ;;
  esac
  if [[ ! -f "$law" || ! -f "$mutant" ]] || cmp -s "$law" "$mutant"; then
    printf 'REGRESSION test_id=%s layer=fixture expected=distinct-pair actual=missing-or-identical\n' "$id" >&2
    exit 1
  fi
  # D6 COMPOSE/FLIP живе у чинному Core4; нативний paired використовує
  # той самий профіль, що й prove-lisp-semantic-t5m.sh, без host-оракула.
  paired_profile=()
  [[ "$id" != d6-compose-flip ]] || paired_profile=(--core4-runtime)
  for kind in law mutant; do
    file="$law"
    [[ "$kind" == mutant ]] && file="$mutant"
    expected=1
    [[ "$kind" == mutant ]] && expected=0
    printf '%s\n' "$expected" > "$tmp/expected"
    printf 'NATIVE_SENS_CASE test_id=%s kind=%s fixture=%s expected=D1:%s\n' "$id" "$kind" "$file" "$expected"
    sha256sum "$file"
    # Автором закону є .lisp; SENS створює точні слова, Zig — T5M-байти.
    physical="$tmp/$id-$kind.sens"
    view="$tmp/$id-$kind"
    if ! timeout 45s "$cli" --t5m-mint "$file" "$physical" > "$tmp/mint.out" 2> "$tmp/stderr"; then
      printf 'REGRESSION test_id=%s layer=codec input=%s expected=Zig-T5M actual=mint-failure\n' "$id" "$file" >&2
      cat "$tmp/stderr" >&2
      exit 1
    fi
    if [[ ! -s "$physical" ]] ||
       ! timeout 45s "$reader" open "$physical" > "$view" 2> "$tmp/stderr" ||
       ! timeout 45s "$reader" verify-view "$physical" > "$tmp/verify.out" 2> "$tmp/stderr"; then
      printf 'REGRESSION test_id=%s layer=Zig-T5M input=%s expected=canonical-roundtrip actual=invalid-carrier\n' "$id" "$file" >&2
      cat "$tmp/stderr" >&2
      exit 1
    fi
    # Парне виконання SENS порівнює фізичні слова з вихідною програмою.
    # Shell не обчислює семантику й не оголошує standalone фізичного входу.
    if ! timeout 45s "$cli" --t5m-pair "$file" "$physical" "${paired_profile[@]}" > "$tmp/actual" 2> "$tmp/stderr"; then
      printf 'REGRESSION test_id=%s layer=physical-eval input=%s expected=D1:%s actual=execution-error\n' "$id" "$file" "$expected" >&2
      cat "$tmp/stderr" >&2
      exit 1
    fi
    if ! cmp -s "$tmp/expected" "$tmp/actual"; then
      printf 'REGRESSION test_id=%s layer=eval input=%s expected=D1:%s actual=%q\n' "$id" "$file" "$expected" "$(cat "$tmp/actual")" >&2
      exit 1
    fi
    printf 'NATIVE_SENS_PASS test_id=%s kind=%s expected=D1:%s executor=SENS carrier=Zig/T5M standalone=NOT_CLAIMED\n' "$id" "$kind" "$expected"
  done
done
printf 'NATIVE_SENS_SUITE_PASS suite=lisp-language-laws laws=15 mutants=15 authority=SENS\n'
