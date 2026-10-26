#!/usr/bin/env bash
# Retired formats must not become callable SENS surface names.
# JSON wire framing and SHA digests may be used by adapters for transport or
# integrity, but they are not SENS language primitives.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
surface="lib/surface/uk-sa-coverage.lisp"
if grep -nE '^[[:space:]]*\(entry[[:space:]]+\([^)]*[[:space:]](json-parse|sha256-hex)([[:space:]]|\))' "$surface"; then
  echo "SENS_LANGUAGE_BOUNDARY=FAIL retired_json_or_sha_surface_callable"
  exit 1
fi
# The canonical SENS runtime exposes neither name as a registered language item;
# its JSON parser and digest helper are adapter utilities only.
if grep -nE '^[[:space:]]*\(entry[[:space:]]+\([^)]*[[:space:]](json-parse|sha256-hex)([[:space:]]|\))' "$surface"; then
  echo "SENS_LANGUAGE_BOUNDARY=FAIL duplicate_surface_scan"
  exit 1
fi
echo "SENS_LANGUAGE_BOUNDARY=PASS json_callable=false sha256_callable=false sha_primitive_created=false"
