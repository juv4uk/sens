#!/usr/bin/env bash
# Історична точка входу без міграційних мутацій.
# Активний гейт використовує лише версійовані shell-перевірки.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
bash scripts/check-language-policy-archive.sh
scripts/check-bilingual-docs
