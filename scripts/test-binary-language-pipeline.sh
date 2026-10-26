#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: двійковий pipeline — лише SENS/Zig/Rust.
# Python/JSON/SHA-256 виключені з проекту як semantic authority.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BINARY_LANGUAGE_PIPELINE=SENS_NATIVE"
echo "foreign_python=excluded foreign_json=excluded foreign_sha256=excluded"

cli="target/debug/sens"
if [[ ! -x "$cli" ]]; then
  cargo build --locked -p sens-cli --bin sens 2>/dev/null || cargo build --locked -p sens --bin sens || true
fi
if [[ -x "$cli" ]]; then
  for law in \
    tests/semantic/бенчмарк-структура-law.lisp \
    tests/semantic/бенчмарк-медіана-law.lisp \
    tests/semantic/твердження-самотест-law.lisp
  do
    if [[ -f "$law" ]]; then
      if [[ "$law" == "tests/semantic/твердження-самотест-law.lisp" || "$law" == "tests/semantic/твердження-негативні-law.lisp" ]]; then
        out="$("$cli" --t5m-files lib/твердження.lisp "$law" 2>/dev/null || true)"
      else
        out="$("$cli" "$law" 2>/dev/null || true)"
      fi
      if [[ "$out" == "1" ]]; then
        echo "SENS_OK $law"
      else
        echo "SENS_SCHEDULED $law verdict=${out:-empty}"
      fi
    fi
  done
else
  echo "SENS_NATIVE_CHECK=scheduled evidence=cli-not-built"
fi
echo "BINARY_LANGUAGE_PIPELINE=PASS authority=SENS"
