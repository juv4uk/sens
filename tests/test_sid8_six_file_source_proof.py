"""Pinned source-byte witness for six reviewed Lisp sources: four safe cutovers.

Compares original and resulting Git *blobs*, not mutable future source text:
future agents may keep working without invalidating this historical proof.
Only executable Lisp call heads are allowed to change, never quote data.
"""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("lib/surface/uk.lisp", "66acf2ed0723a2f7850d858b7e7c97f923f42f49", "full", 141),
    ("lib/surface/sa.lisp", "ccf74daab65bf842112f57da784582c0243b83e3", "full", 83),
    ("lib/surface/semantic-registry-api.lisp", "45f4828ea79ca00607a9368320d80c9f46b9656a", "full", 93),
    ("knowledge/guard-fact-policy.lisp", "f5f538e9072d03f7e045ebd9b2e8001cc80a140e", "full", 104),
]
# Exact result blobs from the two direct file commits and the one atomic tree.
RESULT = {
    "lib/surface/uk.lisp": "7b9ae8d3f81544f6cd9d262ebde235f294d198c2",
    "lib/surface/sa.lisp": "9b70d9b25df3cc2906f70ae4d71c7572218e117a",
    "lib/surface/semantic-registry-api.lisp": "76476394f8f22dd03b20300c8405769f4ff79f03",
    "knowledge/guard-fact-policy.lisp": "296c3333d690ea6593fb47a3f1b99b8aa89bc7fb",
}
# For the two independently committed files, RESULT stores the *commit*
# identifiers, so their actual resulting file blob is resolved via commit:path.


def git_bytes(obj):
    return subprocess.check_output(["git", "show", obj], cwd=ROOT)


def correspondence():
    rows = json.loads((ROOT / "knowledge/sens8-current-coverage-v1.json").read_text())["rows"]
    foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())["domains"]
    mapping = {}
    for row in rows:
        targets = sorted(set(re.findall(r"D([1-9]):([01]{1,9})", row.get("current_target") or "")))
        if row["classification"] not in ("DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"):
            continue
        if len(targets) != 1:
            continue
        domain, word = targets[0]
        assert word in foundation["D" + domain]["residents"]
        mapping[row["legacy_code"]] = word
    return mapping


def rewrite(source, mapping, mode):
    frames, edits = [], []
    i = 0
    quote_next = False
    while i < len(source):
        ch = source[i]
        if source.startswith("#|", i):
            depth = 1
            i += 2
            while depth and i < len(source):
                if source.startswith("#|", i):
                    depth += 1
                    i += 2
                elif source.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated block comment")
            continue
        if ch == ";":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue
        if ch == '"':
            i += 1
            closed = False
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    closed = True
                    break
                else:
                    i += 1
            if not closed:
                raise ValueError("unterminated string")
            continue
        if ch in ("'", "`") or source.startswith("#'", i):
            quote_next = True
            i += 2 if source.startswith("#'", i) else 1
            continue
        if ch == "(":
            parent = frames[-1] if frames else None
            if parent and parent["first"]:
                parent["first"] = False
            quoted = quote_next or bool(parent and (parent["quoted"] or parent["quote_children"]))
            frames.append({"first": True, "quoted": quoted, "quote_children": False})
            quote_next = False
            i += 1
            continue
        if ch == ")":
            if not frames:
                raise ValueError("unmatched closing parenthesis")
            frames.pop()
            quote_next = False
            i += 1
            continue
        if ch.isspace():
            i += 1
            continue
        if ch == ",":
            quote_next = True
            i += 2 if source.startswith(",@", i) else 1
            continue
        start = i
        while (i < len(source) and not source[i].isspace()
               and source[i] not in "()'\`\",;"
               and not source.startswith("#|", i)):
            i += 1
        if i == start:
            i += 1
            continue
        token = source[start:i]
        frame = frames[-1] if frames else None
        if frame and frame["first"]:
            frame["first"] = False
            if not frame["quoted"] and re.fullmatch(r"[01]{8}", token):
                if token == "10011100":
                    pass
                else:
                    if token not in mapping:
                        raise ValueError("unresolved historical call " + token)
                    if mode == "partial":
                        assert re.match(r"\s*\(\s*\(", source[i:i + 80])
                    edits.append((start, i, mapping[token]))
            if token in {"00000001", "001", "QUOTE", "quote", "як-є"}:
                frame["quote_children"] = True
        quote_next = False
    if frames:
        raise ValueError("unclosed list")
    output = source
    for start, end, target in reversed(edits):
        output = output[:start] + target + output[end:]
    return output, len(edits)


class InPlaceSID8Proof(unittest.TestCase):
    def test_uncallable_d6_let_is_preserved_until_runtime_witness(self):
        expected = {"lib/forward.lisp": 19, "lib/knowledge.lisp": 25,
                    "lib/surface/semantic-registry-api.lisp": 3,
                    "knowledge/guard-fact-policy.lisp": 6}
        for path, expected_count in expected.items():
            with self.subTest(path=path):
                src = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(len(re.findall(r"\\(10011100(?=\\s+\\(\\s*\\()", src)), expected_count)

    def test_ratified_mapping_and_474_original_call_heads(self):
        mapping = correspondence()
        self.assertEqual(mapping["10011100"], "001000")
        counts = []
        for path, old_sha, mode, expected_count in CASES:
            with self.subTest(path=path):
                old = git_bytes(old_sha).decode("utf-8")
                if mode == "partial":
                    # two old-LET migrations made with individually pinned commits
                    new = git_bytes(RESULT[path] + ":" + path).decode("utf-8")
                else:
                    new = git_bytes(RESULT[path]).decode("utf-8")
                rendered, amount = rewrite(old, mapping, mode)
                self.assertEqual(amount, expected_count)
                self.assertEqual(rendered.encode("utf-8"), new.encode("utf-8"))
                counts.append(amount)
        self.assertEqual(sum(counts), 421)

if __name__ == "__main__":
    unittest.main()
