#!/usr/bin/env bash
set -euo pipefail

# Current authority/doc drift guard.
# Historical research and docs/archive/** are intentionally excluded: they
# preserve provenance and are allowed to contain superseded terminology.
docs=(
  README.md
  CURRENT.md
  STATUS.md
  docs/current-binary-domain-architecture.md
  docs/language-core.md
  docs/semantic-authority-map.md
  docs/semantic-authority-map.uk.md
  docs/vision.md
  docs/benchmarks.md
)

for path in "${docs[@]}"; do
  test -f "$path" || {
    printf 'current-authority-doc-missing: %s\n' "$path" >&2
    exit 1
  }
done

require_literal() {
  local path="$1"
  local literal="$2"
  if ! grep -Fq -- "$literal" "$path"; then
    printf 'current-authority-required-text-missing: %s: %s\n' "$path" "$literal" >&2
    exit 1
  fi
}

forbid_literal() {
  local path="$1"
  local literal="$2"
  if grep -Fq -- "$literal" "$path"; then
    printf 'current-authority-stale-text: %s: %s\n' "$path" "$literal" >&2
    exit 1
  fi
}

# New binary-domain ontology must be visible in the current entry points.
require_literal CURRENT.md 'binary number'
require_literal CURRENT.md 'exact semantic domain'
require_literal CURRENT.md 'proved/admitted law'
require_literal README.md 'bits + domain + law -> meaning'
require_literal docs/current-binary-domain-architecture.md 'semantic object'
require_literal docs/current-binary-domain-architecture.md 'binary number'
require_literal docs/current-binary-domain-architecture.md 'exact domain'
require_literal docs/language-core.md 'binary number'
require_literal docs/language-core.md 'semantic domain'

# Domain, carrier and mechanism must not collapse.
require_literal CURRENT.md 'Domain != carrier != mechanism'
require_literal docs/semantic-authority-map.md 'Domain is not carrier'
require_literal docs/semantic-authority-map.uk.md 'Domain, carrier, mechanism'
require_literal README.md 'Domain, carrier, mechanism'

# Current docs must reject the old flat-SID8 ontology as current truth.
for path in README.md CURRENT.md docs/current-binary-domain-architecture.md docs/language-core.md docs/semantic-authority-map.md docs/semantic-authority-map.uk.md; do
  forbid_literal "$path" 'SENS has exactly 256 functions'
  forbid_literal "$path" 'У СЕНС є рівно 256 функцій'
  forbid_literal "$path" 'my-lisp language core — SID8-only'
done

# Free-space placement and shared mechanism are not semantic authority.
require_literal README.md 'free coordinate'
require_literal CURRENT.md 'free coordinate'
require_literal docs/semantic-authority-map.md 'free coordinate'
require_literal docs/current-binary-domain-architecture.md 'free coordinate'
require_literal docs/current-binary-domain-architecture.md 'same machine transform'

# Historical-first phase order must be explicit in current Core docs.
for path in README.md CURRENT.md docs/current-binary-domain-architecture.md docs/language-core.md docs/vision.md; do
  require_literal "$path" 'HISTORICAL-INGEST'
  require_literal "$path" 'STRUCTURAL-DISCOVERY'
  require_literal "$path" 'SENS-DERIVATION'
done

# Human names and implementation mechanisms remain projections/mechanisms.
require_literal README.md 'людська назва'
require_literal docs/current-binary-domain-architecture.md 'Human names'
require_literal docs/semantic-authority-map.md 'Human names'
require_literal docs/semantic-authority-map.uk.md 'Human surfaces'

# Reference mechanism path is sens, never the old crate path.
for path in CURRENT.md docs/semantic-authority-map.md; do
  forbid_literal "$path" 'crates/my-lisp'
  require_literal "$path" 'crates/sens'
done

# Documentation history must remain explicit rather than silently overwritten.
require_literal docs/language-core.md 'superseded'
require_literal docs/vision.md 'superseded'
require_literal docs/benchmarks.md 'preserved'

printf 'current-authority-docs-ok\n'
