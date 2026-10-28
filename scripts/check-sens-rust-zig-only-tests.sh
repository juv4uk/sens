#!/usr/bin/env bash
# Compatibility entrypoint kept for existing CI callers.
# Owner decision 2026-10-28: all programming languages are permitted.
# This check verifies that the SENS-owned semantic path still EXISTS.
# It does not claim that the witnesses passed or decide their meaning.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
grep -Fq 'OWNER-ALL-LANGUAGES-RESEARCH-20261028:BEGIN' AGENTS.md
for proof in \
  scripts/prove-repl-semantic-corpus.sh \
  tests/semantic/lisp-language-laws.lisp \
  tests/semantic/lisp-language-negative.lisp; do
  if [[ ! -s "$proof" || -L "$proof" ]]; then
    printf 'LANGUAGE_POLICY=BLOCKED reason=missing-SENS-witness path=%s\n' "$proof" >&2
    exit 1
  fi
done
bash -n scripts/prove-repl-semantic-corpus.sh
printf 'LANGUAGE_POLICY=ALL_LANGUAGES_ALLOWED SENS_SEMANTICS=OWNED_BY_SENS evidence=NOT_EXECUTED_BY_THIS_GUARD\n'
