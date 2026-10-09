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
run python3 scripts/sens_binary_language_model.py --self-test

# Ratified D3/bīja3: authority -> checked structural projection.
run python3 scripts/check-bija3-current-authority.py
run python3 scripts/generate-bija3-l1-l5-structure.py --check

# Current exact-width D1–D9 human projections.
run python3 scripts/check-domain-tables.py

# Binary-domain task governance: schema, witness, falsifier and status discipline.
run python3 scripts/check-binary-domain-format.py --self-test

# One-way valve: host u8/Sid8 must not become semantic identity again.
run bash scripts/sid-binary-identity-guard.sh


# Explicit negative controls required by #4268.
run python3 - <<'PY'
import importlib.util
import sys
from pathlib import Path

ROOT = Path.cwd()
SCRIPTS = ROOT / "scripts"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses with postponed annotations resolve their defining module
    # through sys.modules. Register before execution or the binary foundation
    # gate crashes instead of checking exact-width words (Python 3.12+).
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module

word_law = load(
    "research_2077_binary_word_law",
    SCRIPTS / "research-2077-binary-word-law.py",
)
substrate = load(
    "research_2106_binary_substrate",
    SCRIPTS / "research-2106-binary-substrate.py",
)
domain_tables = load("domain_tables", SCRIPTS / "domain_tables.py")
BinaryWord = word_law.BinaryWord

# Leading-zero collapse must remain impossible.
assert BinaryWord("1") != BinaryWord("01")
assert BinaryWord("01") != BinaryWord("001")
assert len({BinaryWord("1"), BinaryWord("01"), BinaryWord("001")}) == 3

# Width/domain participates in identity even when numeric payload agrees.
assert int("1", 2) == int("001", 2)
assert BinaryWord("1") != BinaryWord("001")
assert (1, "1") != (3, "001")

# A raw bit delimiter collides with unrestricted payload.
assert substrate.test_raw_delimiter_impossibility(max_delim_width=6) > 0
internal = BinaryWord("101001001")
assert "00" in internal.bits and internal.bits != "00"

# Valid width alone does not imply semantic admission. Use the live
# ratified D7 table rather than a synthetic subset: Contract 11.8 admits
# 126/128 D7 coordinates, leaving exactly two owner-reserved/unadmitted words.
d7_rows = domain_tables.read_domain_table(ROOT / "lib/domains/d7.lisp")
admitted_d7 = {BinaryWord(row.bits) for row in d7_rows}
all_d7 = {BinaryWord(f"{n:07b}") for n in range(128)}
missing_d7 = all_d7 - admitted_d7
assert len(admitted_d7) == 126
assert len(missing_d7) == 2
unknown_same_width = next(iter(missing_d7))
assert unknown_same_width.width == 7
assert unknown_same_width not in admitted_d7

# Current domain tables retain exact D1/D2/D3 widths.
d1 = domain_tables.read_domain_table(ROOT / "lib/domains/d1.lisp")
d2 = domain_tables.read_domain_table(ROOT / "lib/domains/d2.lisp")
d3 = domain_tables.read_domain_table(ROOT / "lib/domains/d3.lisp")
assert [r.bits for r in d1] == ["0", "1"]
assert [r.bits for r in d2] == ["00", "01", "10", "11"]
assert [r.bits for r in d3] == [f"{n:03b}" for n in range(8)]
assert (d1[1].width, d1[1].bits) != (d3[1].width, d3[1].bits)

# Physical .sens execution must stay on the packed-byte path, not a text projection.
cli_source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
route_start = cli_source.index("fn eval_physical_t5(")
route_end = cli_source.index("\nfn main()", route_start)
physical_route = cli_source[route_start:route_end]
assert "sens::decode_ternary_words(bytes)" in physical_route
assert "sens::parse_canonical_word_sequence(&words)" in physical_route
assert "sens::pack_binary_source_words" not in physical_route
assert "sens::parse_canonical_packed_words" not in physical_route
assert "open_ternary_program" not in physical_route
assert "parse_canonical_binary" not in physical_route

transport_source = (ROOT / "crates/sens/src/ternary_transport.rs").read_text(encoding="utf-8")
decode_start = transport_source.index("pub fn decode_ternary_words(")
decode_end = transport_source.index("/// Вертикальний вигляд", decode_start)
physical_decoder = transport_source[decode_start:decode_end]
assert "parts.join(" not in physical_decoder
assert "parse_binary_source_words(&visible)" not in physical_decoder

# The alternate sens-trit entrypoint must obey the same direct packed path.
trit_source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
trit_start = trit_source.index("fn eval_t5_bytes_core4(")
trit_end = trit_source.index("\n}\n", trit_start) + 3
trit_route = trit_source[trit_start:trit_end]
assert "sens::decode_ternary_words(bytes)" in trit_route
assert "sens::parse_canonical_word_sequence(&words)" in trit_route
assert "sens::decode_ternary_program(bytes)" not in trit_route
assert "sens::pack_binary_source_words" not in trit_route
assert "sens::parse_canonical_packed_words" not in trit_route
assert "sens::open_ternary_program(bytes)" not in trit_route
assert "sens::parse_canonical_binary(&visible)" not in trit_route

# Transport validation itself must keep D2 grammar on the same direct typed words,
# rather than serialize and immediately decode a second packed payload.
transport_start = transport_source.index("pub(crate) fn parse_t5_domain_words(")
transport_end = transport_source.index("\\n}", transport_start)
transport_route = transport_source[transport_start:transport_end]
assert "crate::parse_canonical_word_sequence(words)" in transport_route
assert "pack_binary_source_words" not in transport_route

print("SENS-TRIT-DIRECT-TYPED-WORDS: PASS")
print("PHYSICAL-T5-DIRECT-TYPED-WORDS: PASS")
print("BINARY-LANGUAGE-NEGATIVE-CONTROLS: PASS")
print("leading-zero collapse: blocked")
print("width/domain confusion: blocked")
print("raw delimiter collision: blocked")
print("semantic admission from width alone: blocked")
print("exact D1/D2/D3 widths: preserved")
PY

printf '\nBINARY-LANGUAGE-PIPELINE: PASS\n'
