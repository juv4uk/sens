"""Thirty-seven fail-closed, source-pinned D3 ATOM migrations in five Lisp scripts.

The witness checks the OLD immutable Git objects, each paired legacy branch
and its identical result, the new source Git objects, and comment preservation.
Source legality is not an independent runtime/oracle parity claim.
"""
from __future__ import annotations
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "scripts/build-inventory.lisp": (
        "cdff5b5ea8661b4856142822e4cc85e5033b979d",
        "01481d71248bc218d0ff208d7c62ab6151217845", 15),
    "scripts/build-dependency-classification.lisp": (
        "04f4796b1e883651fb7d7191ee26bb23369e4937",
        "3033d696ec2ed695eb2fdfd68ef3dcea0a2b0f98", 9),
    "scripts/generate-function-table.lisp": (
        "863d7d798aeeba2910e3f81a29dc0a54770a97a9",
        "189c417fbbc4a875b2674632321639d37f3b4461", 3),
    "scripts/generate-uk-surface-audit.lisp": (
        "84bf2961151cefa41238f90ce942a651777fe7db",
        "f7235927eab148aaf2a09c70aa7c81b338e0b30b", 7),
    "scripts/symbol-table.lisp": (
        "3f573eaef0896b8871989462b2b65277e44db4b7",
        "16ddd0b01081478be6095abd344f50f0e567f567", 3),
}

def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout

def tokenize(src):
    result = []
    i = 0
    while i < len(src):
        char = src[i]
        if char.isspace():
            i += 1
        elif char == ";":
            while i < len(src) and src[i] != "\n":
                i += 1
        elif src.startswith("#|", i):
            depth = 1
            i += 2
            while i < len(src) and depth:
                if src.startswith("#|", i):
                    depth += 1
                    i += 2
                elif src.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unclosed block comment")
        elif char in "()":
            result.append((char, i, i + 1))
            i += 1
        elif char == '"':
            start = i
            i += 1
            closed = False
            while i < len(src):
                if src[i] == "\\":
                    i += 2
                elif src[i] == '"':
                    i += 1
                    closed = True
                    break
                else:
                    i += 1
            if not closed:
                raise ValueError("unclosed string")
            result.append((src[start:i], start, i))
        else:
            start = i
            while (i < len(src) and not src[i].isspace()
                   and src[i] not in "();" and not src.startswith("#|", i)):
                i += 1
            if i == start:
                i += 1
            result.append((src[start:i], start, i))
    return result

def parse(src):
    root = {"kind": "l", "children": []}
    stack = [root]
    for word, start, end in tokenize(src):
        if word == "(":
            node = {"kind": "l", "children": [], "start": start}
            stack[-1]["children"].append(node)
            stack.append(node)
        elif word == ")":
            if len(stack) == 1:
                raise ValueError("extra closing parenthesis")
            stack.pop()["end"] = end
        else:
            stack[-1]["children"].append({"kind": "a", "value": word,
                                           "start": start, "end": end})
    if len(stack) != 1:
        raise ValueError("unclosed parenthesis")
    return root

def serialize(node):
    return ("(" + " ".join(serialize(c) for c in node["children"]) + ")"
            if node["kind"] == "l" else node["value"])

def eligible(src):
    matches = []
    def walk(node):
        if node["kind"] != "l":
            return
        children = node["children"]
        if len(children) == 4 and children[0].get("value") == "110":
            first, second, fallback = children[1:]
            if all(x["kind"] == "l" for x in (first, second, fallback)):
                a, b, c = [x["children"] for x in (first, second, fallback)]
                if (len(a) == 3 and len(b) == 3 and len(c) == 2
                    and c[0].get("value") == "t"
                    and a[0]["kind"] == "l"
                    and a[0]["children"][0].get("value") == "010"
                    and len(a[0]["children"]) == 2
                    and serialize(a[0]) == serialize(b[0])
                    and serialize(a[1]) == "()"
                    and serialize(b[1]) == "(1)"
                    and serialize(a[2]) == serialize(b[2])
                    and ";" not in src[node["start"]:node["end"]]
                    and "#|" not in src[node["start"]:node["end"]]):
                    matches.append(node)
        for child in children:
            walk(child)
    walk(parse(src))
    return matches

def migrate(src):
    edits = 0
    for _ in range(100):
        matches = sorted(eligible(src),
                         key=lambda n: n["end"] - n["start"])
        if not matches:
            break
        node = matches[0]
        a, _b, c = [x["children"] for x in node["children"][1:]]
        test = a[0]
        body = a[2]
        otherwise = c[1]
        text = lambda n: src[n["start"]:n["end"]]
        fixed = (f"(110 ({text(test)} {text(body)}) "
                 f"((010 (001 ())) {text(otherwise)}))")
        src = src[:node["start"]] + fixed + src[node["end"]:]
        edits += 1
    else:
        raise ValueError("migration progress bound exceeded")
    return src, edits

class PinnedBulkSourceMigration(unittest.TestCase):
    def test_old_to_current_sources_are_exactly_the_safe_ast_projections(self):
        self.assertEqual(sum(v[2] for v in PINS.values()), 37)
        for path, (old_sha, current_sha, count) in PINS.items():
            with self.subTest(path=path):
                old = git("cat-file", "blob", old_sha)
                now = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(git("hash-object", path).strip(), current_sha)
                expected, replacements = migrate(old)
                self.assertEqual(replacements, count)
                self.assertEqual(now, expected)
                self.assertEqual(eligible(now), [],
                                 "an old complete duplicate ATOM block survived")
                self.assertEqual(
                    [line for line in old.splitlines() if line.lstrip().startswith(";")],
                    [line for line in now.splitlines() if line.lstrip().startswith(";")],
                    "historical comments were altered"
                )

    def test_negative_control_rejects_divergent_cond_results(self):
        sample = ("(110 ((010 xs) () (001 a)) "
                  "((010 xs) (1) (001 b)) "
                  "(t (001 other)))")
        self.assertEqual(eligible(sample), [],
                         "different results must not be combined")

if __name__ == "__main__":
    unittest.main()
