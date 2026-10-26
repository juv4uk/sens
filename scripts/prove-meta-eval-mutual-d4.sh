#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: перевірка наявних фізичних SENS D4-свідків.
# Семантика — в SENS; оболонка перевіряє лише вердикт і точну негативну діагностику.
# Без Python, JSON, SHA-256 і нових артефактів.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=meta-eval-mutual-d4
law_bits=tests/semantic/meta-eval-mutual-d4-law.bits
mutant_bits=tests/semantic/meta-eval-mutual-d4-mutant.bits
law=tests/semantic/meta-eval-mutual-d4-law.sens
mutant=tests/semantic/meta-eval-mutual-d4-mutant.sens
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=physical actual=executor-missing\n' "$id" >&2
  exit 1
fi
for witness in "$law_bits" "$mutant_bits" "$law" "$mutant"; do
  if [[ ! -s "$witness" || -L "$witness" ]]; then
    printf 'REGRESSION test_id=%s layer=physical witness=%s actual=missing-or-link\n' "$id" "$witness" >&2
    exit 1
  fi
done
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version 2>/dev/null || echo unknown)"
if ! "$cli" "$law" > "$tmp/actual" 2> "$tmp/positive.err"; then
  printf 'REGRESSION test_id=%s layer=physical-positive actual=execution-error\n' "$id" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION test_id=%s layer=physical-positive actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if "$cli" "$mutant" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-negative actual=unexpected-success\n' "$id" >&2
  cat "$tmp/mutant.out" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-negative expected=D1-non-callable actual=unrelated-error\n' "$id" >&2
  cat "$tmp/mutant.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_PASS id=%s positive=D1:1 negative=D1-non-callable authority=SENS carrier=physical-T5M\n' "$id"
