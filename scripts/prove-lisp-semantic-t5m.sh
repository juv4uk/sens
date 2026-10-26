#!/usr/bin/env bash
# Compatibility route: the active native self-witness is the SENS structure law.
# No Python, JSON, SHA-256 generation, or silent success when a fixture is absent.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
exec bash scripts/prove-бенчмарк-структура.sh "$cli"
