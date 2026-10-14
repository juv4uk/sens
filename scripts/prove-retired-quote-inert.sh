#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: one native physical T5 self-verdict and its one-bit mutant.
# Python only packs exact T5 words; native binary SENS owns the verdict.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="target/debug/sens"
if [[ "$#" -ge 1 ]]; then cli="$1"; fi
id=retired-quote-inert-d3
law=tests/semantic/retired-quote-inert-d3-law.bits
mutant=tests/semantic/retired-quote-inert-d3-mutant.bits
if [[ ! -x "$cli" ]]; then
  echo "REGRESSION test_id=$id layer=eval kind=UNINFORMATIVE-EXECUTOR cli=$cli reproduce='cargo build --locked -p sens-cli --bin sens && bash scripts/prove-retired-quote-inert.sh'" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
python3 - "$tmp" "$law" "$mutant" <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "scripts")
from sens_t5_codec import parse_words, encode_projection, decode_bytes

directory, positive_path, negative_path = map(Path, sys.argv[1:])
p = parse_words(positive_path.read_text(encoding="ascii"))
n = parse_words(negative_path.read_text(encoding="ascii"))
if len(p) != len(n):
    raise SystemExit("T5_TRANSPORT_RED: mutant changed word count")
changed_indices = [index for index, (a, b) in enumerate(zip(p, n)) if a != b]
# The only permitted mutation is the first item of the D3-quoted two-element list.
# This is an exact D2 token position check, NOT a host semantic truth table.
if changed_indices != [14] or p[11:18] != ["001", "00", "10", "0", "00", "1", "01"] or n[14] != "1":
    raise SystemExit("T5_TRANSPORT_RED: mutate only first quoted D1 datum")
for name, words in (("law", p), ("mutant", n)):
    physical = encode_projection(" ".join(words))
    if decode_bytes(physical) != words:
        raise SystemExit("T5_TRANSPORT_RED: codec lost exact word identity")
    (directory / f"{name}.sens").write_bytes(physical)
print(f"QUOTE_INERT_T5_READY word_count={len(p)} mutant_changed_words={len(changed_indices)} semantic_pass=NOT_INFERRED")
PY

printf 'test_id=%s layer=eval executor=%s version=%s\n' "$id" "$cli" "$("$cli" --version)"
sha256sum "$cli" "$law" "$mutant" "$tmp/law.sens" "$tmp/mutant.sens"
reproduce="bash scripts/prove-retired-quote-inert.sh $cli"
printf 'reproduce=%q\n' "$reproduce"
expected="$tmp/expected"
actual="$tmp/actual"
printf '1\n' > "$expected"
if ! "$cli" "$tmp/law.sens" > "$actual" 2> "$tmp/law.stderr"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:YES actual=execution-error first_diff=unknown reproduce=%q\n' \
    "$id" "$law" "$reproduce" >&2
  cat "$tmp/law.stderr" >&2
  sha256sum "$expected" "$actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS test_id=%s expected_sha256=' "$id"
sha256sum "$expected"
printf 'NATIVE_SENS_DIGESTS test_id=%s actual_sha256=' "$id"
sha256sum "$actual"
if ! cmp -s "$expected" "$actual"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:YES actual=wrong-verdict first_diff=0 reproduce=%q\n' \
    "$id" "$law" "$reproduce" >&2
  exit 1
fi
if "$cli" "$tmp/mutant.sens" > "$tmp/mutant.actual" 2> "$tmp/mutant.stderr"; then
  printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=noncallable-rejection actual=accepted first_diff=quoted-D1 reproduce=%q\n' \
    "$id-mutant" "$mutant" "$reproduce" >&2
  sha256sum "$tmp/mutant.actual" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.stderr"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s layer=eval fixture=%s expected=D1-noncallable actual=unclassified-failure reproduce=%q\n' \
    "$id-mutant" "$mutant" "$reproduce" >&2
  cat "$tmp/mutant.stderr" >&2
  sha256sum "$tmp/mutant.stderr" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE test_id=%s kind=D1-noncallable sha256_stderr=' "$id-mutant"
sha256sum "$tmp/mutant.stderr"
printf 'NATIVE_SENS_PASS test_id=%s physical_positive=1 mutant=D1-noncallable authority=binary-SENS\n' "$id"
