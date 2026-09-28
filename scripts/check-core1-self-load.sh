#!/usr/bin/env bash
set -euo pipefail
root_dir=$(git rev-parse --show-toplevel)
kernel=${MCCARTHY_KERNEL:?set MCCARTHY_KERNEL to the built mccarthy-eval kernel}
fixture=$(mktemp)
trap 'rm -f "$fixture"' EXIT
{
  cat "$root_dir/lib/core1.lisp"
  printf '%s\n' '(C1-EVAL-PROGRAM-THEN'
  printf '%s\n' '  (QUOTE ('
  sed '/^[[:space:]]*;/d' "$root_dir/lib/core1.lisp"
  printf '%s\n' '  ))'
  cat <<'LISP'
  (QUOTE
    (00100111
      (C1-PRIMITIVE-IDENTITY (00000001 CONS))
      (C1-FOUND-VALUE
        (C1-LOOKUP-IN
          (00000001 X)
          (00000001 ((X . Y)))))
      (C1-DEFINE-NAMEP 00001001))))
LISP
} > "$fixture"
actual=$("$kernel" "$fixture")
expected='(00000100 Y T)'
printf 'CORE1-SELF-LOAD expected=%s\n' "$expected"
printf 'CORE1-SELF-LOAD actual=%s\n' "$actual"
test "$actual" = "$expected"
