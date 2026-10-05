#!/usr/bin/env python3
"""Structural guard for #3386/#3402 world-knowledge authorities."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
si = (root / "lib/si.lisp").read_text(encoding="utf-8")
axioms = (root / "knowledge/world-axioms.lisp").read_text(encoding="utf-8")
laws = (root / "knowledge/world-model-laws.lisp").read_text(encoding="utf-8")
witness = (root / "tests/fixtures/exact-quantity-arithmetic-witness.lisp").read_text(encoding="utf-8")

records = [
    "si:defining-cesium-frequency",
    "si:defining-speed-of-light",
    "si:defining-planck-constant",
    "si:defining-elementary-charge",
    "si:defining-boltzmann-constant",
    "si:defining-avogadro-constant",
    "si:defining-luminous-efficacy",
]

for record in records:
    assert record in si, f"missing SI authority record: {record}"
    assert record in axioms, f"world axiom does not reference: {record}"

assert axioms.count("(record . si:defining-") == 7
assert "WORLD_DEFINITION_AXIOM" in axioms
assert 'value-authority . "lib/si.lisp"' in axioms

assert "planck-energy-frequency" in laws
assert 'relation . "E = h * nu"' in laws
assert "MODEL_LAW" in laws
assert "dimensionally valid arithmetic alone does not create physical meaning" in laws

assert "planck-cesium-energy-shape" in witness
assert "speed-times-second-distance-shape" in witness

print("WORLD-KNOWLEDGE-AUTHORITY: PASS")
print("axioms=7 model-laws=2 existing-witnesses=2")
