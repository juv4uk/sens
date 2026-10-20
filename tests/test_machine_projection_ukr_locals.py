"""Механічний позитивний/негативний контроль українських локальних зв'язувань.

Тільки зворотне відновлення Git blob і лексичний scope. Не семантичний
емулятор SENS і не доказ допуску нативного машинного механізму.
"""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    "lib/machine/projection/x86-64.lisp": (
        "6c21f9d27a86d020cae322712efd6b0a2ec49cd5",
        {
            "effect": "ефект",
            "left": "лівий",
            "right": "правий",
            "forms": "форми",
        },
    ),
}


def rewrite_bound_atoms(text: str, words: dict[str, str]) -> tuple[str, int]:
    """Не змінювати коментарів, рядків або даних усередині (як-є ...)."""
    frames: list[dict[str, bool]] = []
    pieces: list[str] = []
    index = 0
    changes = 0
    while index < len(text):
        char = text[index]
        if char == ";":
            end = text.find("\n", index)
            if end == -1:
                end = len(text)
            pieces.append(text[index:end])
            index = end
            continue
        if char == '"':
            end = index + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                    continue
                if text[end] == '"':
                    end += 1
                    break
                end += 1
            pieces.append(text[index:end])
            index = end
            continue
        if char == "(":
            frames.append({"head": False, "quoted": False})
            pieces.append(char)
            index += 1
            continue
        if char == ")":
            if not frames:
                raise ValueError("зайва закривна дужка")
            frames.pop()
            pieces.append(char)
            index += 1
            continue
        if char.isspace():
            pieces.append(char)
            index += 1
            continue
        end = index
        while end < len(text) and text[end] not in ' \t\r\n();\"':
            end += 1
        if end == index:
            raise ValueError(f"невідомий знак у позиції {index}")
        atom = text[index:end]
        quoted = any(frame["quoted"] for frame in frames)
        if frames and not frames[-1]["head"]:
            frames[-1]["head"] = True
            if atom == "як-є":
                frames[-1]["quoted"] = True
                quoted = True
        result = atom if quoted else words.get(atom, atom)
        if result != atom:
            changes += 1
        pieces.append(result)
        index = end
    if frames:
        raise ValueError("незакриті дужки")
    return "".join(pieces), changes


def git_blob_sha1(content: str) -> str:
    blob = content.encode("utf-8")
    return hashlib.sha1(f"blob {len(blob)}\0".encode("ascii") + blob).hexdigest()


class MachineUkrainianLocalBindingTests(unittest.TestCase):
    def test_invert_exact_original_git_blobs(self):
        for path, (original, projected) in SOURCE.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                inverse = {dst: src for src, dst in projected.items()}
                restored, count = rewrite_bound_atoms(text, inverse)
                self.assertGreater(count, 0)
                self.assertEqual(git_blob_sha1(restored), original)

    def test_projection_is_idempotent(self):
        for path, (_original, projected) in SOURCE.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                after, count = rewrite_bound_atoms(text, projected)
                self.assertEqual(count, 0)
                self.assertEqual(after, text)

    def test_quoted_machine_data_and_verdict_labels_untouched(self):
        projection = (ROOT / "lib/machine/projection/x86-64.lisp").read_text("utf-8")
        parity = (ROOT / "lib/machine/dispatch/native-first-parity.lisp").read_text("utf-8")
        for literal in ("mov-r64-imm64", "rax", "rcx", "add-r64-r64",
                        "sub-r64-r64", "imul-r64-r64", "ret"):
            self.assertIn("(як-є " + literal + ")", projection)
        for literal in ("kind", "expected", "actual", "native-parity-case",
                        "execution-route", "native-or-route-mismatch"):
            self.assertIn("(як-є " + literal + ")", parity)

    def test_wrong_local_peer_does_not_restore_blob(self):
        path = "lib/machine/projection/x86-64.lisp"
        text = (ROOT / path).read_text(encoding="utf-8")
        wrong = text.replace("(функція (ефект)", "(функція (лівий)", 1)
        self.assertNotEqual(wrong, text)
        inverse = {dst: src for src, dst in SOURCE[path][1].items()}
        restored, _ = rewrite_bound_atoms(wrong, inverse)
        self.assertNotEqual(git_blob_sha1(restored), SOURCE[path][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
