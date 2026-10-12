"""Pinned proof: lower historical parallel LET to ratified D4 LAMBDA calls.

Do NOT replace old W8 LET by D6:001000 until the D6 runtime is callable.
No source comments may disappear; one commented LET remains held in forward.
This is a source-law witness, not runtime old/new parity.
"""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
OLD = re.compile(r"\(10011100(?=[\s)])")
D6_DIRECT = re.compile(r"\(001000(?=[\s)])")
SOURCES = {
    "lib/forward.lisp": (
        "f94d602b9b40668ec1f17e3b51956eaf72af74d2",
        "266b03e3503a58765f3c0021c95bb90e27136d61", 19, 18, 1
    ),
    "lib/knowledge.lisp": (
        "4f314e54da95ef9af8f51cc6b87b8d665cc65a8a",
        "1ec58fb64b1118f897737a2fd668fcceb548bdaa", 25, 25, 0
    ),
}

def old_blob(sha):
    return subprocess.run(
        ["git", "cat-file", "blob", sha], cwd=ROOT,
        capture_output=True, check=True
    ).stdout.decode("utf-8")

def source_parser():
    name = "_source_only_let_parser"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/cond-modernize.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def project(source):
    parser = source_parser()
    forms = parser.parse(source)
    rewritten = 0
    held = 0
    def emit(node):
        nonlocal rewritten, held
        original = source[node.start:node.end]
        if node.opaque or not node.children:
            return original
        head = node.children[0].atom
        if head in ("001", "00000001", "QUOTE", "quote", "як-є"):
            return original
        if head == "10011100":
            if len(node.children) != 3:
                raise AssertionError("LET requires one binding list and one body")
            bindings = node.children[1]
            if not bindings.children or any(
                len(b.children) != 2 or b.children[0].atom is None
                for b in bindings.children
            ):
                raise AssertionError("unproved LET bindings")
            if ";" in original or "#|" in original:
                held += 1
                return original
            names = [b.children[0].atom for b in bindings.children]
            if len(set(names)) != len(names):
                raise AssertionError("duplicate binder")
            values = [emit(b.children[1]) for b in bindings.children]
            body = emit(node.children[2])
            rewritten += 1
            return "((0010 (" + " ".join(names) + ") " + body + ") " + " ".join(values) + ")"
        result = original
        for child in reversed(node.children):
            start = child.start - node.start
            end = child.end - node.start
            result = result[:start] + emit(child) + result[end:]
        return result
    result = source
    for node in reversed(forms):
        result = result[:node.start] + emit(node) + result[node.end:]
    return result, rewritten, held

class LetAdmissionBoundary(unittest.TestCase):
    def test_w8_collision_is_not_current_d8_or_callable_d6(self):
        domains = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text()
        )["domains"]
        self.assertEqual(domains["D6"]["residents"]["001000"], "LET")
        self.assertEqual(domains["D8"]["residents"]["10011100"], "CADDDAAR")

    def test_exact_pinned_parallel_let_to_lambda_replay(self):
        for path, source_sha, result_sha, before_count, lowered_count, held_count in (
            (p, *v) for p, v in SOURCES.items()
        ):
            with self.subTest(path=path):
                original = old_blob(source_sha)
                current = (ROOT / path).read_text(encoding="utf-8")
                expected = old_blob(result_sha)
                projected, lowered, held = project(original)
                self.assertEqual(len(OLD.findall(original)), before_count)
                self.assertEqual(lowered, lowered_count)
                self.assertEqual(held, held_count)
                self.assertEqual(projected, expected)
                self.assertEqual(current, expected)
                self.assertEqual(len(OLD.findall(current)), held_count)
                self.assertEqual(len(D6_DIRECT.findall(current)), 0)
                self.assertIn("(00001010", current, "composite DEFMACRO still held")

    def test_current_d8_mod_does_not_alias_historic_member(self):
        domains = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text()
        )["domains"]
        self.assertEqual(domains["D8"]["residents"]["00101100"], "MOD")
        for p, n in (("lib/time.lisp", 3), ("lib/core.lisp", 2),
                     ("lib/core4.lisp", 2)):
            with self.subTest(path=p):
                source = (ROOT / p).read_text(encoding="utf-8")
                self.assertEqual(len(re.findall(r"\(00101100(?=[\s)])", source)), n)

if __name__ == "__main__":
    unittest.main()
