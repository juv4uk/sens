#!/usr/bin/env python3
"""Core4 width-firewall: 2046 residents, exact domains, no retired executable heads."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core4.lisp"
DOMAIN_DIR = ROOT / "lib/domains"

spec = importlib.util.spec_from_file_location("_core4_ast", ROOT / "scripts/cond-modernize.py")
if spec is None or spec.loader is None:
    raise RuntimeError("AST parser unavailable")
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)

FORBIDDEN_ACTIVE = {
    "00001010",  # historical W8 DEFMACRO
    "01000111",  # historical internal DIGIT->STRING slot
    "01011010",  # historical MONO-NS slot
    "11110111",  # historical structural EQUAL slot
    "10110001",  # historical recursive STRING< slot
}
D9_REQUIRED = {
    "110011100": ("STRING-EMPTY?", "рядок-порожній?"),
    "110011101": ("STRING-REST", "рядок-решта"),
    "110011110": ("STRING-APPEND", "рядок-додати"),
    "110101011": ("STRING-FIRST", "рядок-перший"),
}


def active_heads(source: str) -> Counter:
    counts: Counter = Counter()
    stack = list(parser.parse(source))
    while stack:
        node = stack.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head is not None:
            counts[head] += 1
        if head in {"001", "00000001", "quote"}:
            continue
        stack.extend(node.children)
    return counts


def active_atoms(source: str) -> list[str]:
    atoms: list[str] = []
    stack = list(parser.parse(source))
    while stack:
        node = stack.pop()
        if node.opaque:
            continue
        if node.atom is not None:
            atoms.append(node.atom)
            continue
        if not node.children:
            continue
        head = node.children[0].atom
        if head in {"001", "00000001", "quote"}:
            if head is not None:
                atoms.append(head)
            continue
        stack.extend(node.children)
    return atoms


def domain_rows(width: int) -> dict[str, str]:
    text = (DOMAIN_DIR / f"d{width}.lisp").read_text(encoding="utf-8")
    rows: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(rf"^\s*\(([01]{{{width}}})\s+", line)
        if not m:
            continue
        lisp = re.search(r'\(LISP\s+(\(\)|"[^"]*"|[^()\s]+)\)', line)
        if lisp is None:
            raise ValueError(f"D{width} malformed LISP field at {m.group(1)}")
        name = lisp.group(1)
        rows[m.group(1)] = name[1:-1] if name.startswith('"') else name
    return rows


def domain_ukr_names(width: int) -> set[str]:
    text = (DOMAIN_DIR / f"d{width}.lisp").read_text(encoding="utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        if not re.match(rf"^\s*\([01]{{{width}}}\s+", line):
            continue
        projection = re.search(r'\(укр\s+(\(\)|"[^"]*"|[^()\s]+)\)', line)
        if projection is None:
            raise ValueError(f"D{width} missing укр projection")
        value = projection.group(1)
        names.add(value[1:-1] if value.startswith('"') else value)
    return names


def verify(source: str) -> None:
    heads = active_heads(source)
    if "t" in active_atoms(source):
        raise ValueError("Core4 still contains executable host truth T")
    for head in FORBIDDEN_ACTIVE:
        if heads[head]:
            raise ValueError("forbidden migrated head survived: " + head)

    d8 = domain_rows(8)
    for head in heads:
        if len(head) == 8 and set(head) <= {"0", "1"} and head not in d8:
            raise ValueError("active 8-bit head is not a D8 resident: " + head)

    d9 = domain_rows(9)
    for bits, (legacy_name, укр_name) in D9_REQUIRED.items():
        if heads[bits]:
            raise ValueError(f"raw D9 binary head survived in Core4: {bits}")
        if heads[укр_name] < 1:
            raise ValueError(f"Core4 lost Ukrainian D9 projection: {укр_name}")
        if d9.get(bits) != legacy_name:
            raise ValueError(f"D9 authority drift: {bits} -> {d9.get(bits)!r}, expected {legacy_name}")

    # The stable-identity lookup carries domain + the ratified full Ukrainian
    # projection, not an embedded binary coordinate. Domain tables alone retain
    # the canonical coordinate registry.
    start = source.index("(визначити сталі-відповідники-за-ідентичностями")
    end = source.index("(визначити знайти-групу-відповідників-за-ідентичністю", start)
    projection_block = source[start:end]
    if re.search(r"\(д9\s+[01]{9}(?=[\s)])", projection_block):
        raise ValueError("stable D9 identity map still contains a binary coordinate literal")
    named_rows = re.findall(r"^\s*\(д9\s+([^\s()]+)\s+\(([^\s()]+)\)\)\s*$",
                            projection_block, flags=re.MULTILINE)
    if len(named_rows) != 20:
        raise ValueError(f"expected 20 named D9 projections, found {len(named_rows)}")
    if any(key != alias for key, alias in named_rows):
        raise ValueError("stable D9 identity key differs from its Ukrainian alias projection")
    authoritative_ukr = domain_ukr_names(9)
    unknown_names = sorted(key for key, _alias in named_rows if key not in authoritative_ukr)
    if unknown_names:
        raise ValueError("stable D9 keys are not full-column укр projections: " + ", ".join(unknown_names))

    if heads["монотонний-наносекунди"] != 1:
        raise ValueError("Core4 must retain exactly one honest MONO-NS mechanism boundary")
    if domain_rows(10).get("0011110110") != "MONO-NS":
        raise ValueError("D10 MONO-NS authority drifted")


class Core4WidthFirewall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_all_2046_d1_d10_residents_are_dense_exact_width(self):
        total = 0
        for width in range(1, 11):
            rows = domain_rows(width)
            expected = {f"{n:0{width}b}" for n in range(1 << width)}
            self.assertEqual(set(rows), expected, f"D{width} must be complete exact-width authority")
            total += len(rows)
        self.assertEqual(total, 2046)

    def test_core4_obeys_domain_width_firewall(self):
        verify(self.source)

    def test_stable_d9_identity_map_uses_ukrainian_names_not_binary_literals(self):
        start = self.source.index("(визначити сталі-відповідники-за-ідентичностями")
        end = self.source.index("(визначити знайти-групу-відповідників-за-ідентичністю", start)
        block = self.source[start:end]
        self.assertNotRegex(block, r"\(д9\s+[01]{9}(?=[\s)])")
        named_rows = re.findall(r"^\s*\(д9\s+([^\s()]+)\s+\(([^\s()]+)\)\)\s*$",
                                block, flags=re.MULTILINE)
        self.assertEqual(len(named_rows), 20)
        for key, alias in named_rows:
            self.assertEqual(key, alias)
            self.assertNotRegex(key, r"^[01]{9}$")

    def test_seven_macros_are_language_owned_not_w8_defmacro(self):
        heads = active_heads(self.source)
        self.assertEqual(heads["00001010"], 0)
        self.assertEqual(heads["макрос"], 7)
        # Визначення мають бути реальними формами в AST, а не рядковими
        # фрагментами SENS, продубльованими у Python.
        definitions = {
            form.children[1].atom
            for form in parser.parse(self.source)
            if len(form.children) >= 2 and form.children[0].atom == "визначити"
        }
        for name in ["та", "або", "нехай", "нехай-послідовно", "потік-перший", "потік-останній",
                     "матеріалізувати-сталі-відповідники"]:
            self.assertIn(name, definitions)

    def test_negative_old_macro_head_is_rejected(self):
        # Міняємо точний токен голови визначення, не зберігаємо SENS-код
        # як строковий шаблон усередині Python.
        definition = next(
            (form for form in parser.parse(self.source)
             if len(form.children) >= 2 and form.children[0].atom == "визначити"
             and form.children[1].atom == "та"),
            None,
        )
        self.assertIsNotNone(definition)
        head = definition.children[0]
        mutated = self.source[:head.start] + "00001010" + self.source[head.end:]
        with self.assertRaisesRegex(ValueError, "forbidden migrated head"):
            verify(mutated)

    def test_negative_cross_width_collision_is_rejected(self):
        mutated = self.source.replace("(рядок-перший", "(11100000")
        with self.assertRaisesRegex(ValueError, "lost Ukrainian D9 projection"):
            verify(mutated)

    def test_negative_host_truth_is_rejected(self):
        # Шукаємо справжній виклик предиката над цитованим D3:(),
        # змінюємо його AST-діапазон, не переносимо SENS-семантику в тест.
        stack = list(parser.parse(self.source))
        victim = None
        while stack:
            form = stack.pop()
            if form.opaque or not form.children:
                continue
            if (len(form.children) == 2
                    and form.children[0].atom == "порожній?"
                    and len(form.children[1].children) == 2
                    and form.children[1].children[0].atom == "як-є"
                    and form.children[1].children[1].atom is None
                    and not form.children[1].children[1].children):
                victim = form
                break
            stack.extend(form.children)
        self.assertIsNotNone(victim)
        mutated = self.source[:victim.start] + "t" + self.source[victim.end:]
        with self.assertRaisesRegex(ValueError, "host truth"):
            verify(mutated)


if __name__ == "__main__":
    unittest.main()
