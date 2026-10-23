#!/usr/bin/env python3
"""Structural/name-erasure guard for #3386/#3402/#3434 world authority."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
si = (root / "lib/si.lisp").read_text(encoding="utf-8")
axioms = (root / "knowledge/world-axioms.lisp").read_text(encoding="utf-8")
laws = (root / "knowledge/world-model-laws.lisp").read_text(encoding="utf-8")
witness = (root / "tests/fixtures/exact-quantity-arithmetic-witness.lisp").read_text(encoding="utf-8")

surface_marker = "(surface-projections"
assert surface_marker in axioms
axiom_canonical, axiom_surface = axioms.split(surface_marker, 1)

# Canonical axiom section must survive erasing every human SI spelling.
assert "si:" not in axiom_canonical
for human in (
    "cesium", "speed-of-light", "planck", "elementary-charge",
    "boltzmann", "avogadro", "luminous-efficacy",
):
    assert human not in axiom_canonical

expected = {
    "000": ("9192631770", "(-1 0 0 0 0 0 0)", "si:defining-cesium-frequency"),
    "001": ("299792458", "(-1 1 0 0 0 0 0)", "si:defining-speed-of-light"),
    "010": (
        "132521403/200000000000000000000000000000000000000000",
        "(-1 2 1 0 0 0 0)",
        "si:defining-planck-constant",
    ),
    "011": (
        "801088317/5000000000000000000000000000",
        "(1 0 0 1 0 0 0)",
        "si:defining-elementary-charge",
    ),
    "100": (
        "1380649/100000000000000000000000000000",
        "(-2 2 1 0 -1 0 0)",
        "si:defining-boltzmann-constant",
    ),
    "101": (
        "602214076000000000000000",
        "(0 0 0 0 0 -1 0)",
        "si:defining-avogadro-constant",
    ),
    "110": ("683", "(3 -2 -1 0 0 0 1)", "si:defining-luminous-efficacy"),
}

assert "(id-semantics . opaque-stable-id-not-function-number)" in axiom_canonical
assert "(dimension-basis-ids . (000 001 010 011 100 101 110))" in axiom_canonical
assert axiom_canonical.count("(exactness . exact-by-definition)") == 8  # common + seven objects

for axiom_id, (value, dim, record) in expected.items():
    assert f"({axiom_id}\n      (value . {value})" in axiom_canonical
    assert f"(dimension-vector7 . {dim})" in axiom_canonical
    assert record in axiom_surface
    # Ordinary source digits are admitted as exact D24+ values. A rational
    # is constructed by the ratified D5:10111 operation, not read from a N/D
    # token or a hidden width tag.
    # Чинна форма: si.lisp будує ці раціонали через ratified Д5 частку над
    # ІМЕНОВАНИМИ сталими (чисельник/знаменник), а не літеральними цифрами.
    source_value = {
        "000": "сі-число-частота-цезію",
        "001": "сі-число-швидкість-світла",
        "010": "(частка сі-число-планківська-константа-чисельник сі-число-планківська-константа-знаменник)",
        "011": "(частка сі-число-електричний-заряд-чисельник сі-число-електричний-заряд-знаменник)",
        "100": "(частка сі-число-больцман-чисельник сі-число-больцман-знаменник)",
        "101": "сі-число-авогадро",
        "110": "сі-число-шістсот-вісімдесят-три",
    }.get(axiom_id, value)
    assert source_value in si

# Model-law dependencies must use canonical axiom ids, not SI names.
assert surface_marker in laws
law_canonical, law_surface = laws.split(surface_marker, 1)
assert "si:" not in law_canonical
assert "(axiom-dependencies . (010))" in law_canonical
assert "(axiom-dependencies . (001))" in law_canonical
assert law_canonical.count("(binary-function-number . (D5 10110))") == 2
assert 'relation . "E = h * nu"' in law_surface
assert 'relation . "d = c * t"' in law_surface

# Свідок переписано на чинний укр-варіант точної арифметики розмірностей
# (старі planck/speed-shape форми виведено разом із переписуванням).
assert "свідок-арифметики-розмірностей" in witness
assert "quantity-arithmetic (status pass)" in witness

print("WORLD-KNOWLEDGE-AUTHORITY: PASS")
print("axioms=7 name-erased=yes model-laws=2 function=D5:10110")
