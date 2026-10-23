#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: ручний доказ існуючого D4 selector/width закону.
# Only binary SENS in physical T5 decides EQ, COND and D4:1001 callability.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="target/debug/sens"
if [[ $# -eq 1 ]]; then cli="$1"; elif [[ $# -gt 1 ]]; then
  echo "usage: bash scripts/prove-d4-selector-width.sh [sens-executable]" >&2
  exit 2
fi
id="d4-selector-width"
law_bits="tests/semantic/d4-selector-width-law.bits"
mutant_bits="tests/semantic/d4-selector-width-mutant.bits"
law="tests/semantic/d4-selector-width-law.sens"
mutant="tests/semantic/d4-selector-width-mutant.sens"
replay="bash scripts/prove-d4-selector-width.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=missing-executor path=%s reproduce=%q\n' "$id" "$cli" "$replay" >&2
  exit 1
fi

# No host truth table: D2 framing, exact word identity, T5 byte equality and
# the one-bit D4 mutation are purely transport/provenance checks.
python3 - "$law_bits" "$mutant_bits" "$law" "$mutant" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from sens_t5_t5m_codec import parse_words, encode_projection, decode_bytes

law_bits, mutant_bits, law_path, mutant_path = map(Path, sys.argv[1:])
good = parse_words(law_bits.read_text(encoding="ascii"))
bad = parse_words(mutant_bits.read_text(encoding="ascii"))
if len(good) != len(bad):
    raise SystemExit("T5_TRANSPORT_RED id=d4-selector-width wrong exact word count")
changes = [(i, a, b) for i, (a, b) in enumerate(zip(good, bad)) if a != b]
if changes != [(8, "1001", "1000")]:
    raise SystemExit(f"T5_TRANSPORT_RED id=d4-selector-width expected one D4 bit at word 8; actual={changes}")
if max(map(len, good)) > 5 or max(map(len, bad)) > 5:
    raise SystemExit("T5_TRANSPORT_RED id=d4-selector-width unexpected domain word width")
for role, words, path in (("law", good, law_path), ("mutant", bad, mutant_path)):
    encoded = encode_projection(" ".join(words))
    physical = path.read_bytes()
    if physical != encoded or decode_bytes(physical) != words:
        raise SystemExit(f"T5_TRANSPORT_RED id=d4-selector-width role={role} physical T5 differs from exact-width source")
print(
    "D4_PHYSICAL_PASS id=d4-selector-width "
    f"words={len(good)} bits={sum(map(len, good))} bytes={len(law_path.read_bytes())} "
    "mutant=D4:1001-to-D4:1000 semantic_pass=NOT_INFERRED"
)
PY

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR test_id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version)"
printf 'NATIVE_SENS_REPLAY test_id=%s command=%q\n' "$id" "$replay"
sha256sum "$cli" "$law_bits" "$mutant_bits" "$law" "$mutant"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2> "$tmp/law.stderr"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=execution-error first_diff=unknown reproduce=%q\n' "$id" "$law" "$replay" >&2
  cat "$tmp/law.stderr" >&2
  sha256sum "$tmp/expected" "$tmp/actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS test_id=%s expected_sha256=' "$id"
sha256sum "$tmp/expected"
printf 'NATIVE_SENS_DIGESTS test_id=%s actual_sha256=' "$id"
sha256sum "$tmp/actual"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=wrong-verdict first_diff=0 reproduce=%q\n' "$id" "$law" "$replay" >&2
  exit 1
fi

if "$cli" "$mutant" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=eval fixture=%s expected=D1-noncallable actual=accepted first_diff=D4:1001-to-1000 reproduce=%q\n' "$id" "$mutant" "$replay" >&2
  sha256sum "$tmp/mutant.out" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant layer=eval fixture=%s expected=D1-noncallable actual=unrelated-failure first_diff=unknown reproduce=%q\n' "$id" "$mutant" "$replay" >&2
  cat "$tmp/mutant.err" >&2
  sha256sum "$tmp/mutant.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant stderr_sha256=' "$id"
sha256sum "$tmp/mutant.err"
printf 'NATIVE_SENS_PASS test_id=%s physical_positive=D1:1 mutant=D1-noncallable semantic_authority=binary-SENS\n' "$id"
