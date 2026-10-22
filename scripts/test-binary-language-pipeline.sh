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

# Перевірки нижче користуються assert: оптимізований Python їх прибирає.
# Fail-closed до запуску будь-якого доказового кроку.
run python3 -c 'import sys; sys.exit("BINARY-LANGUAGE-PIPELINE: BLOCKED — Python -O/PYTHONOPTIMIZE вимикає assert") if not __debug__ else None'

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
# Негативний свідок: автономний валідатор не може обійти self-test.
run python3 - <<'PY'
import subprocess
import sys
result = subprocess.run(
    [sys.executable, "-O", "scripts/check-binary-domain-format.py", "--self-test"],
    capture_output=True, text=True, check=False,
)
if result.returncode == 0 or "BINARY-DOMAIN-FORMAT: BLOCKED" not in result.stderr:
    raise SystemExit("BINARY-DOMAIN-FORMAT: FAILED — optimized Python bypassed evidence")
if "binary-domain-selftest-ok" in result.stdout:
    raise SystemExit("BINARY-DOMAIN-FORMAT: FAILED — false optimized PASS")
print("BINARY-DOMAIN-FORMAT: optimized Python named rejection PASS")
PY
run python3 scripts/check-binary-domain-format.py --self-test

# Canonical domain ladder replaces the retired flat-eight identity guard.
# Both self-test mutation controls and Rust/Python/C/Lisp source checks must
# finish successfully; provenance-only historical sources are not admitted.
run python3 scripts/check-domain-ladder-identity.py --self-test
run python3 scripts/check-domain-ladder-identity.py --check

# Explicit negative controls required by #4268.
run python3 - <<'PY'
import importlib.util
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit("BINARY-LANGUAGE-NEGATIVE-CONTROLS: BLOCKED — Python -O вимикає assert")

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

# D7 keyboard/v2: the ratified owner table admits all 128 *data* cells.
# Width is exact: 7-bit D7 identity cannot collapse to equal integer payload
# at D6 or D8, and occupancy never supplies a callable mechanism.
d7_rows = domain_tables.read_domain_table(ROOT / "lib/domains/d7.lisp")
admitted_d7 = {BinaryWord(row.bits) for row in d7_rows}
all_d7 = {BinaryWord(f"{n:07b}") for n in range(128)}
assert len(d7_rows) == 128
assert len(admitted_d7) == 128
assert admitted_d7 == all_d7
assert all(word.width == 7 for word in admitted_d7)
assert BinaryWord("0100001") in admitted_d7
assert BinaryWord("0101010") in admitted_d7
assert BinaryWord("0000001") != BinaryWord("000001")
assert BinaryWord("0000001") != BinaryWord("00000001")

# Current domain tables retain exact D1/D2/D3 widths.
d1 = domain_tables.read_domain_table(ROOT / "lib/domains/d1.lisp")
d2 = domain_tables.read_domain_table(ROOT / "lib/domains/d2.lisp")
d3 = domain_tables.read_domain_table(ROOT / "lib/domains/d3.lisp")
assert [r.bits for r in d1] == ["0", "1"]
assert [r.bits for r in d2] == ["00", "01", "10", "11"]
assert [r.bits for r in d3] == [f"{n:03b}" for n in range(8)]
assert (d1[1].width, d1[1].bits) != (d3[1].width, d3[1].bits)

# Physical .sens execution must stay on decoded typed binary words, not a text projection.
cli_source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
route_start = cli_source.index("fn eval_physical_t5(")
route_end = cli_source.index("\nfn main()", route_start)
physical_route = cli_source[route_start:route_end]
# Zig ABI v2 is the only default physical ingress: Rust cannot decode
# physical T5 directly, even as an implicit fallback after Zig rejection.
ingress_start = cli_source.index("fn decode_physical_t5_words(")
ingress_end = cli_source.index("\nfn eval_physical_t5(", ingress_start)
ingress = cli_source[ingress_start:ingress_end]
assert 'return zig_transport::decode_t5_exact_words(bytes)?' in ingress
assert '#[cfg(feature = "zig-transport")]' in ingress
assert '#[cfg(not(feature = "zig-transport"))]' in ingress
assert "no Rust fallback" in ingress
assert "sens::decode_ternary_words(bytes)" not in ingress
assert "let words = decode_physical_t5_words(bytes)?;" in physical_route
assert "sens::PhysicalT5Program::from_exact_domain_words_owned(words)" in physical_route
assert ".execute(&mut pure)" in physical_route
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

# The production T5M ingress delegates physical restoration to Zig, then
# passes exact domain words into the SENS-owned reader/evaluator. The Rust
# library must not expose a physical-byte evaluator shortcut.
trit_source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
trit_start = trit_source.index("fn eval_t5_bytes_core4(")
trit_end = trit_source.index("\n/// Diagnose a physical packed T5 file", trit_start)
trit_route = trit_source[trit_start:trit_end]
assert "zig_transport::decode_t5_exact_words(bytes)?" in trit_route
assert "sens::PhysicalT5Program::from_exact_domain_words_owned(words)" in trit_route
assert ".execute(&mut session)" in trit_route
assert "sens::PhysicalT5Program::decode(bytes)" not in trit_route
assert "sens::eval_t5_program(" not in trit_route
assert "sens::decode_ternary_program(bytes)" not in trit_route
assert "sens::pack_binary_source_words" not in trit_route
assert "sens::parse_canonical_packed_words" not in trit_route
assert "sens::open_ternary_program(bytes)" not in trit_route
assert "sens::parse_canonical_binary(&visible)" not in trit_route

binary_execution_source = (ROOT / "crates/sens/src/binary_execution.rs").read_text(encoding="utf-8")
assert "pub fn decode(physical: &[u8])" not in binary_execution_source
assert "pub fn eval_t5_program(" not in binary_execution_source

# Transport validation itself must keep D2 grammar on the same direct typed words,
# rather than serialize and immediately decode a second packed payload.
transport_start = transport_source.index("pub(crate) fn parse_t5_domain_words(")
transport_end = transport_source.index("\n}", transport_start)
transport_route = transport_source[transport_start:transport_end]
assert "crate::parse_canonical_word_sequence(words)" in transport_route
assert "pack_binary_source_words" not in transport_route

print("SENS-TRIT-DIRECT-TYPED-WORDS: PASS")
print("PHYSICAL-T5M-ZIG-TO-EXACT-WORDS: PASS")
print("BINARY-LANGUAGE-NEGATIVE-CONTROLS: PASS")
print("leading-zero collapse: blocked")
print("width/domain confusion: blocked")
print("raw delimiter collision: blocked")
print("semantic admission from width alone: blocked")
print("exact D1/D2/D3 widths: preserved")
PY

printf '\nBINARY-LANGUAGE-PIPELINE: PASS\n'
