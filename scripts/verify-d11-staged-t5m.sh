#!/usr/bin/env bash
# Д11: нативний SENS/Zig свідок оберненості чотирьох бібліотечних законів.
# Тимчасові байти НЕ є опублікованою фізичною парою в репозиторії.
set -euo pipefail

sens="${SENS_CLI:-target/debug/sens}"
trit="${SENS_TRIT_CLI:-target/debug/sens-trit}"
for executable in "$sens" "$trit"; do
  if [[ ! -x "$executable" ]]; then
    echo "D11_T5M_BINARY_MISSING layer=executor executable=$executable" >&2
    exit 2
  fi
done

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT

for source in \
  lib/d11-clojure-frequencies-unary.lisp \
  lib/d11-srfi1-find-tail.lisp \
  lib/d11-srfi1-list-equality.lisp \
  lib/d11-srfi1-unary-count.lisp \
  lib/d11-srfi1-set-relations.lisp \
  lib/list-foundation-compositions.lisp; do
  stem="${source##*/}"
  physical="$scratch/${stem%.lisp}.sens"
  bitview="${physical%.sens}"
  mint_flag=--t5m-mint
  bindings=()
  if [[ "$source" == "lib/d11-clojure-frequencies-unary.lisp" ]]; then
    mint_flag=--t5m-mint-pair
    bindings=(--binding-source lib/d11-clojure-group-by.lisp)
  fi

  if ! timeout 90s "$sens" "$mint_flag" "$source" "$physical" "${bindings[@]}"; then
    echo "D11_T5M_MINT_RED layer=lowering input=$source expected=SENS_ZIG_T5M actual=failure" >&2
    exit 1
  fi
  if [[ ! -s "$physical" ]]; then
    echo "D11_T5M_EMPTY layer=physical input=$source expected=nonempty actual=empty" >&2
    exit 1
  fi
  if ! timeout 90s "$trit" view "$physical" > "$bitview"; then
    echo "D11_T5M_VIEW_RED layer=projection input=$source expected=exact_bits actual=failure" >&2
    exit 1
  fi
  if [[ ! -s "$bitview" ]] || ! timeout 90s "$trit" verify-view "$physical"; then
    echo "D11_T5M_ROUNDTRIP_RED layer=ZigT5M input=$source expected=byte_exact actual=failure" >&2
    exit 1
  fi
  if ! timeout 90s "$sens" --t5m-pair "$source" "$physical" "${bindings[@]}" > "$scratch/paired.out"; then
    echo "D11_T5M_EVAL_RED layer=SENS input=$source expected=paired_execution actual=failure" >&2
    exit 1
  fi
  printf 'D11_T5M_STAGED_PASS source=%s bytes=%s physical=ZigT5M runtime=paired-SENS repository_pair=not_published\n' \
    "$source" "$(wc -c < "$physical")"
done
