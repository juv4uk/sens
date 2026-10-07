#!/usr/bin/env bash
set -euo pipefail

# Двійковий pipeline: кожен крок має лише спостерігати вже наявний закон
# або перевіряти похідну проекцію. Жоден крок не створює semantic authority.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

run() {
  printf '\n==> %s\n' "$*"
  "$@"
}

# F−1/F0: нейтральний binary carrier та exact bounded word identity.
run python3 scripts/research-2106-binary-substrate.py
run python3 scripts/research-2077-binary-word-law.py

# Ratified D3/bīja3: authority -> checked structural projection.
run python3 scripts/check-bija3-current-authority.py
run python3 scripts/generate-bija3-l1-l5-structure.py --check

# Current exact-width D1–D9 human projections.
run python3 scripts/check-domain-tables.py

# Binary-domain task governance: schema, witness, falsifier and status discipline.
run python3 scripts/check-binary-domain-format.py --self-test

# One-way valve: host u8/Sid8 must not become semantic identity again.
run bash scripts/sid-binary-identity-guard.sh

printf '\nBINARY-LANGUAGE-PIPELINE: PASS\n'
