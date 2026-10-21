"""Живі українські поверхні TCP і сталої мапи після повної міграції.

Це перевірка вихідних викликів і точних координат, не Python-обчислювач
семантики SENS. Справжня негативна перевірка арності TCP — у sens-host.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

from scripts.report_ukr_projection_progress import ALLOWED

ROOT = Path(__file__).resolve().parents[1]
TCP = ROOT / "lib/tcp.lisp"
MAP = ROOT / "lib/persistent-map.lisp"
HOST = ROOT / "crates/sens-host/src/lib.rs"
D9 = ROOT / "lib/domains/d9.lisp"

TCP_PROJECTIONS = (
    ("001101001", "протокол-передавання-читати-байти-текст"),
    ("010100110", "протокол-передавання-слухати-на"),
    ("010110110", "протокол-передавання-записати-текст-байти"),
    ("101000101", "протокол-передавання-записати-через-сирий"),
    ("110110011", "протокол-передавання-записати"),
    ("110111101", "протокол-передавання-слухати"),
    ("110111110", "протокол-передавання-читати"),
)
RAW_CAPABILITIES = (
    ("протокол-передавання-сире-слухання", "register_capability", "evaluate_tcp_listen_raw"),
    ("протокол-передавання-сире-читання", "register_evaluated_capability", "evaluate_tcp_read_raw"),
    ("протокол-передавання-сирий-запис", "register_capability", "evaluate_tcp_write_raw"),
)
MAP_PROJECTIONS = (
    ("101100011", "мапа-порожній"),
    ("101101110", "мапа-вставити"),
    ("101100101", "мапа-отримати"),
    ("101100010", "мапа-містить?"),
    ("101001100", "мапа-список"),
)


def exact_row(table: str, bits: str, spelling: str) -> bool:
    lines = [line.strip() for line in table.splitlines()
             if line.lstrip().startswith(f"({bits} ")]
    return len(lines) == 1 and f"(укр {spelling})" in lines[0]


class UkrainianTcpMapCurrentTests(unittest.TestCase):
    def test_tcp_complete_keyboard_projection_and_ratified_d9(self):
        source = TCP.read_text(encoding="utf-8")
        table = D9.read_text(encoding="utf-8")
        self.assertTrue(source.strip())
        self.assertEqual({c for c in source if c not in ALLOWED}, set())
        for bits, name in TCP_PROJECTIONS:
            with self.subTest(name=name):
                self.assertTrue(exact_row(table, bits, name))
                self.assertEqual(len(re.findall(
                    rf"(?m)^\(визначити\s+{re.escape(name)}(?=\s|\))",
                    source,
                )), 1)
        for old in ("tcp-listen-raw", "tcp-read-raw", "tcp-write-raw"):
            self.assertNotIn(old, source)
        for name, _, _ in RAW_CAPABILITIES:
            self.assertEqual(source.count(f"({name} "), 1)
        self.assertIn('"0.0.0.0"', source)
        # Цей тест лише охороняє форму; виконання перевіряє справжній SENS.
        # У чинному Lisp недопустимі анонімна голова і незв'язане так.
        self.assertNotIn("((функція ", source)
        self.assertNotRegex(source, r"(?m)^\\s*\\(так(?:\\s|\\))")
        self.assertEqual(source.count("(визначити протокол-передавання-обробити-декодоване"), 1)
        self.assertIn("(протокол-передавання-обробити-декодоване\\n", source)
        self.assertIn("((атом? (як-є ()))\\n       декодований-вміст)", source)
        self.assertIn("(друге\\n      (список\\n        (протокол-передавання-сирий-запис", source)

    def test_tcp_host_capability_aliases_keep_real_handlers_and_arity_witness(self):
        source = HOST.read_text(encoding="utf-8")
        for name, registration, handler in RAW_CAPABILITIES:
            with self.subTest(name=name):
                if registration == "register_evaluated_capability":
                    expected = f'{registration}("{name}", 1, {handler});'
                else:
                    expected = f'{registration}("{name}", {handler});'
                self.assertIn(expected, source)
        self.assertIn("fn ukrainian_tcp_raw_names_preserve_fail_closed_arity()", source)
        self.assertIn("assert_eq!(error.kind, ErrorKind::Arity", source)

    def test_immutable_map_full_ukr_closures_match_d9(self):
        source = MAP.read_text(encoding="utf-8")
        table = D9.read_text(encoding="utf-8")
        self.assertEqual({c for c in source if c not in ALLOWED}, set())
        for bits, name in MAP_PROJECTIONS:
            with self.subTest(name=name):
                self.assertTrue(exact_row(table, bits, name))
                self.assertEqual(len(re.findall(
                    rf"(?m)^\(визначити\s+{re.escape(name)}(?=\s|\))",
                    source,
                )), 1)
        self.assertIn("(визначити внутрішня-мапа-вставити мапа-вставити)", source)
        self.assertIn("(внутрішня-мапа-вставити ключ значення (решта записи))", source)
        self.assertNotRegex(source, r"\(map-(?:insert|get|empty)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
