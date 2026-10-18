"""Позитивні/негативні свідки українських локальних TCP-зв'язувачів і map-closure."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_ukr_callsite_migration.py"
spec = importlib.util.spec_from_file_location("ukr_tcp_map_scanner", SCRIPT)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)

TCP_BEFORE = "28ae808fbfe0669cc1f9eb9530826304e01f3f29"
MAP_BEFORE = "b6b84716702e7546cb2c0f031524210cb7d7b956"

# Перейменування лише зв'язаних лексичних символів, без SID8/D8 трактування.
TCP_ALPHA = {
    "address": "вхідна-адреса",
    "port": "мережевий-порт",
    "bytes": "вхідні-байти",
    "decoded": "декодований-вміст",
    "connection": "мережеве-підключення",
    "text": "вхідний-текст",
    "written": "записано-байтів",
}
TCP_COUNTS = {
    "address": 2, "port": 4, "bytes": 2, "decoded": 5,
    "connection": 6, "text": 7, "written": 1,
}
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
MAP_INVERSE = {
    "мапа-отримати": "map-get",
    "внутрішня-мапа-вставити": "map-insert",
}


def git_blob_sha(content: str) -> str:
    data = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def restore_tcp(source: str):
    reverse = {value: key for key, value in TCP_ALPHA.items()}
    counted = Counter()

    def change(match):
        token = match.group()
        old = reverse.get(token)
        if old is None:
            return token
        counted[old] += 1
        return old

    return TOKEN.sub(change, source), counted


def restore_map(source: str):
    # Тільки голова виконуваного виклику, ніколи binding/value/QUOTE.
    heads = list(scanner.candidate_heads(scanner.parse(source)))
    count = Counter(token.text for token in heads if token.text in MAP_INVERSE)
    offsets = [0]
    offsets.extend(match.end() for match in re.finditer("\n", source))
    edits = [(offsets[token.line - 1] + token.column - 1,
              token.text, MAP_INVERSE[token.text])
             for token in heads if token.text in MAP_INVERSE]
    restored = source
    for index, present, old in sorted(edits, reverse=True):
        assert restored[index:index + len(present)] == present, (index, present)
        restored = restored[:index] + old + restored[index + len(present):]
    return restored, count


class UkrainianTcpMapCurrentTests(unittest.TestCase):
    def test_tcp_alpha_inverse_and_lexical_negative(self):
        source = (ROOT / "lib/tcp.lisp").read_text(encoding="utf-8")
        restored, counts = restore_tcp(source)
        self.assertEqual(dict(counts), TCP_COUNTS)
        self.assertEqual(git_blob_sha(restored), TCP_BEFORE)
        scanner.parse(source)
        self.assertIn('"0.0.0.0"', source)  # IPv4 data is untouched
        self.assertIn("(tcp-listen-raw вхідна-адреса мережевий-порт)", source)
        self.assertIn("(tcp-read-raw мережеве-підключення)", source)
        self.assertIn("(tcp-write-raw мережеве-підключення", source)
        # Помилковий peer або незв'язаний латинський аргумент має зламати inverse.
        mutant = source.replace("(tcp-listen-raw вхідна-адреса мережевий-порт)",
                                "(tcp-listen-raw мережевий-порт мережевий-порт)", 1)
        reconstructed, _ = restore_tcp(mutant)
        self.assertNotEqual(git_blob_sha(reconstructed), TCP_BEFORE)

    def test_map_local_binding_exact_inverse_and_wrong_peer(self):
        source = (ROOT / "lib/persistent-map.lisp").read_text(encoding="utf-8")
        restored, counted = restore_map(source)
        self.assertEqual(dict(counted), {
            "мапа-отримати": 2,
            "внутрішня-мапа-вставити": 1,
        })
        self.assertEqual(git_blob_sha(restored), MAP_BEFORE)
        self.assertIn("(визначити мапа-отримати внутрішня-мапа-отримати)", source)
        self.assertIn("(визначити внутрішня-мапа-вставити map-insert)", source)
        heads = [t.text for t in scanner.candidate_heads(scanner.parse(source))]
        self.assertNotIn("map-get", heads)
        self.assertNotIn("map-insert", heads)
        wrong = source.replace("(мапа-отримати key entries)",
                               "(мапа-містить? key entries)", 1)
        inverse, _ = restore_map(wrong)
        self.assertNotEqual(git_blob_sha(inverse), MAP_BEFORE)

    def test_ratified_d9_identity_does_not_mint_missing_map_insert_callable(self):
        table = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        self.assertRegex(table,
            r"\(101100101 \(ук мапа-отримати\) \(укр мапа-отримати\)")
        self.assertRegex(table,
            r"\(101101110 \(ук мапа-вставити\) \(укр мапа-вставити\)")
        source = (ROOT / "lib/persistent-map.lisp").read_text(encoding="utf-8")
        self.assertNotIn("(визначити мапа-вставити ", source)
        self.assertIn("(визначити внутрішня-мапа-вставити map-insert)", source)


if __name__ == "__main__":
    unittest.main()
