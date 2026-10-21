"""Exact-width Ukrainian projection checks for two mechanism audit sources.

Static source transport test, not an evaluator or semantic oracle. All admitted
D3/D4 heads must round-trip exactly; immutable historical witnesses retain
pinned Git blobs, while living sources may receive further verified projections.
"""
from __future__ import annotations
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_KEYS = {
    "001", "010", "011", "100", "101", "110", "111",
    "0010", "0011", "0100", "0101", "1001", "1110", "1111",
}
EXPECTED_PROJECTIONS = {
    "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
    "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
    "0010": "функція", "0011": "визначити", "0100": "хибне?",
    "0101": "порожній?", "1001": "друге", "1110": "список", "1111": "приєднати",
}
SOURCE_BLOBS = {
    "scripts/check-island-math-evidence.lisp": "34b0f8e950458dfdd5a2375a196b937c466d6894",
}
EXPECTED_COUNTS = {
    "scripts/check-function-table-mechanisms.lisp": {
        "100": 15, "101": 31, "110": 19, "1110": 8, "0011": 18,
        "011": 12, "001": 73, "010": 6, "0010": 10, "1001": 6,
    },
    "scripts/check-island-math-evidence.lisp": {
        "100": 7, "101": 47, "110": 23, "1110": 5, "001": 82,
        "0011": 20, "0010": 12, "010": 6, "011": 6, "1001": 5,
    },
}
TOKEN = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
DOMAIN_ROW = re.compile(
    r'^\s*\(([01]{1,11})\s+\(ук\s+' + TOKEN + r'\)\s+\(укр\s+' + TOKEN + r'\)',
)


# Д1: рівно десять виконуваних гілок «так» мають відновлюватися
# до історичного Git-відбитка без переписування цитованих полів.
DIRECT_D1_ISLAND_LINES = (22, 75, 81, 95, 105, 106, 132, 149, 161, 162)


def _undo_direct_d1_island(path: str, source: str) -> str:
    if path != "scripts/check-island-math-evidence.lisp":
        return source
    lines = source.splitlines(keepends=True)
    for number in DIRECT_D1_ISLAND_LINES:
        if len(lines) < number or lines[number - 1].count("(так ") != 1:
            raise AssertionError(f"неприпустима зміна Д1 у {path}:{number}")
        lines[number - 1] = lines[number - 1].replace("(так ", "(1 ", 1)
    return "".join(lines)


def _git_blob_sha(text: str) -> str:
    payload = text.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    ).hexdigest()


def _authority_projection() -> dict[str, str]:
    out: dict[str, str] = {}
    for width in (3, 4):
        for line in (ROOT / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8").splitlines():
            match = DOMAIN_ROW.match(line)
            if not match:
                continue
            bits, _uk, ukr = match.groups()
            if len(bits) != width or bits not in ALLOWED_KEYS:
                continue
            out[bits] = "" if ukr == "()" else json.loads(ukr) if ukr.startswith('"') else ukr
    return {bits: out[bits] for bits in ALLOWED_KEYS}


def _tokens(source: str) -> list[dict[str, object]]:
    out = []
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
            continue
        if char == ";":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue
        if char == '"':
            start = i
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append({"kind":"string","value":source[start:i],"start":start,"end":i})
            continue
        if char in "()":
            out.append({"kind":"left" if char=="(" else "right","value":char,"start":i,"end":i+1})
            i += 1
            continue
        start = i
        while i < len(source) and not source[i].isspace() and source[i] not in '();"':
            i += 1
        out.append({"kind":"atom","value":source[start:i],"start":start,"end":i})
    return out


def _parse(source: str) -> list[dict[str, object]]:
    tokens = _tokens(source)
    index = 0
    def one() -> dict[str, object]:
        nonlocal index
        token = tokens[index]
        index += 1
        kind = token["kind"]
        if kind == "right":
            raise AssertionError(f"unexpected ) at {token['start']}")
        if kind != "left":
            return {"kind":"string" if kind=="string" else "atom","token":token,"children":[]}
        children = []
        while index < len(tokens) and tokens[index]["kind"] != "right":
            children.append(one())
        if index >= len(tokens):
            raise AssertionError(f"unclosed ( at {token['start']}")
        index += 1
        return {"kind":"list","token":token,"children":children}
    out = []
    while index < len(tokens):
        out.append(one())
    return out


def _head(node: dict[str, object]):
    if node["kind"] != "list":
        return None
    children = node["children"]
    return children[0]["token"] if children and children[0]["kind"] == "atom" else None


def _walk_raw(node: dict[str, object], found: list[dict[str, object]]) -> None:
    if node["kind"] != "list":
        return
    head = _head(node)
    if head is not None and re.fullmatch(r"[01]{1,11}", str(head["value"])):
        found.append(head)
    for child in node["children"]:
        _walk_raw(child, found)


def _walk_active(node: dict[str, object], lookup: dict[str, str],
                 found: list[dict[str, object]], quote_head: str) -> None:
    if node["kind"] != "list":
        return
    head = _head(node)
    value = str(head["value"]) if head is not None else None
    if value is not None and value in lookup:
        found.append(head)
    if value == quote_head:
        return
    for child in node["children"]:
        _walk_active(child, lookup, found, quote_head)


def _transform(source: str, inverse: bool = False):
    projection = _authority_projection()
    lookup = {surface:bits for bits,surface in projection.items()} if inverse else projection
    nodes = _parse(source)
    raw, active = [], []
    for node in nodes:
        _walk_raw(node, raw)
        _walk_active(node, lookup, active, "як-є" if inverse else "001")
    line = lambda token: source.count("\n", 0, int(token["start"])) + 1
    by_line = {}
    for token in raw:
        by_line.setdefault(line(token), []).append(token)
    active_starts = {int(token["start"]) for token in active}
    if inverse:
        eligible = {line(token) for token in active if line(token) not in by_line}
    else:
        eligible = {ln for ln, heads in by_line.items() if heads and all(int(h["start"]) in active_starts for h in heads)}
    edits = [
        {"start":int(token["start"]),"end":int(token["end"]),
         "before":str(token["value"]),"after":lookup[str(token["value"])]}
        for token in active if line(token) in eligible
    ]
    output = source
    for edit in sorted(edits, key=lambda item:item["start"], reverse=True):
        output = output[:edit["start"]] + edit["after"] + output[edit["end"]:]
    counts = {}
    for edit in edits:
        counts[edit["before"]] = counts.get(edit["before"], 0) + 1
    return output, counts


def _active_surface_heads(source: str) -> list[dict[str, object]]:
    reverse = {surface:bits for bits,surface in _authority_projection().items()}
    found = []
    for node in _parse(source):
        _walk_active(node, reverse, found, "як-є")
    return found


class UkrainianMechanismCheckerProjectionTests(unittest.TestCase):
    def test_surface_matches_ratified_d3_d4_tables(self):
        self.assertEqual(_authority_projection(), EXPECTED_PROJECTIONS)

    def test_exact_inverse_restores_original_git_blobs(self):
        for path in EXPECTED_COUNTS:
            with self.subTest(path=path):
                current = (ROOT / path).read_text(encoding="utf-8")
                historical = _undo_direct_d1_island(path, current)
                original, _ = _transform(historical, inverse=True)
                projected, _ = _transform(original)
                self.assertEqual(projected, historical)
                if path in SOURCE_BLOBS:
                    self.assertEqual(_git_blob_sha(original), SOURCE_BLOBS[path])
                self.assertEqual(len(original.splitlines()), len(current.splitlines()))
                self.assertEqual(len(_parse(original)), len(_parse(current)))

    def test_exact_counts_and_negative_binary_mutant(self):
        reverse = {surface:bits for bits,surface in EXPECTED_PROJECTIONS.items()}
        for path, expected_counts in EXPECTED_COUNTS.items():
            with self.subTest(path=path):
                current = (ROOT / path).read_text(encoding="utf-8")
                historical = _undo_direct_d1_island(path, current)
                original, _ = _transform(historical, inverse=True)
                projected, counts = _transform(original)
                for bits, minimum in expected_counts.items():
                    self.assertGreaterEqual(counts.get(bits, 0), minimum, (path, bits))
                self.assertEqual(projected, historical)
                heads = _active_surface_heads(historical)
                self.assertTrue(heads)
                token = sorted(heads,key=lambda t:int(t["start"]))[0]
                start, end = int(token["start"]), int(token["end"])
                mutant = historical[:start] + reverse[str(token["value"])] + historical[end:]
                repaired, _ = _transform(mutant)
                self.assertEqual(repaired, historical)


    def test_mechanism_checker_uses_computed_d1_instead_of_unbound_legacy_truth(self):
        # Перевіряємо тільки структуру; runtime-оракул належить SENS.
        source = (ROOT / "scripts/check-function-table-mechanisms.lisp").read_text(encoding="utf-8")
        self.assertNotIn("(так ", source)
        self.assertEqual(source.count("((атом? (як-є ()))"), 19)
        # yes/no залишаються лише цитованими назвами стану.
        self.assertIn("(як-є yes)", source)
        self.assertIn("(як-є no)", source)
        # Негативний мутант знову має містити незв'язану стару голову.
        mutant = source.replace("((атом? (як-є ()))", "(так", 1)
        self.assertIn("(так ", mutant)
        self.assertNotEqual(mutant, source)

    def test_island_only_d1_direct_and_negative_numeric_mutant(self):
        path = "scripts/check-island-math-evidence.lisp"
        current = (ROOT / path).read_text(encoding="utf-8")
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(1 (ук так) (укр так)", d1)
        self.assertEqual(current.count("(так "), len(DIRECT_D1_ISLAND_LINES))
        self.assertEqual(_undo_direct_d1_island(path, current).count("(1 "),
                         len(DIRECT_D1_ISLAND_LINES))
        heads = []
        for node in _parse(current):
            _walk_raw(node, heads)
        self.assertFalse(heads, "у живому Lisp не повинно бути сирих числових голів")
        mutant = current.replace("(так ", "(1 ", 1)
        self.assertNotEqual(mutant, current)
        broken = []
        for node in _parse(mutant):
            _walk_raw(node, broken)
        self.assertTrue(broken, "числова мутація має бути виявлена")

    def test_d4_cadr_residual_batch_is_idempotent_and_byte_reversible(self):
        # D4:1001 CADR was formerly outside the test's permitted key set.
        # Same exact ratified identity, full Ukrainian projection = друге.
        for path, expected in (
            ("scripts/check-island-math-evidence.lisp", 5),
            ("scripts/check-function-table-mechanisms.lisp", 6),
        ):
            with self.subTest(path=path):
                current = (ROOT / path).read_text(encoding="utf-8")
                historical = _undo_direct_d1_island(path, current)
                original, inverse_counts = _transform(historical, inverse=True)
                projected, forward_counts = _transform(original)
                self.assertEqual(projected, historical)
                self.assertEqual(inverse_counts.get("друге"), expected)
                self.assertEqual(forward_counts.get("1001"), expected)
                self.assertEqual(_transform(current)[0], current)
                if path in SOURCE_BLOBS:
                    self.assertEqual(_git_blob_sha(original), SOURCE_BLOBS[path])
                self.assertEqual(len(_parse(original)), len(_parse(current)))
                self.assertEqual(len(original.splitlines()), len(current.splitlines()))

if __name__ == "__main__":
    unittest.main(verbosity=2)
