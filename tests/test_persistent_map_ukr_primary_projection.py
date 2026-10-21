"""Точкова перевірка повної укр-проєкції для persistent-map."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("map-empty", "мапа-порожній", "101100011"),
    ("map-insert", "мапа-вставити", "101101110"),
    ("map-get", "мапа-отримати", "101100101"),
    ("map-contains?", "мапа-містить?", "101100010"),
    ("map->list", "мапа-список", "101001100"),
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class PersistentMapUkrPrimaryProjectionTests(unittest.TestCase):
    def test_primary_names_match_ratified_d9_rows_without_legacy_aliases(self):
        source = read("lib/persistent-map.lisp")
        # Англійські назви — тільки en-колонка домену як дані.
        # Сучасний Core4 не створює додаткової викличної поверхні Latin.
        core4 = read("lib/core4.lisp")
        d9 = read("lib/domains/d9.lisp")

        for english, ukrainian, bits in TARGETS:
            with self.subTest(english=english, bits=bits):
                self.assertEqual(len(bits), 9, "D9 address width must stay 9")
                rows = [
                    line for line in d9.splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(len(rows), 1, f"D9 row missing/duplicated: {bits}")
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(укр {ukrainian})", rows[0])

                self.assertEqual(
                    len(re.findall(
                        rf"(?m)^\(визначити\s+{re.escape(ukrainian)}(?=\s|\))",
                        source,
                    )),
                    1,
                    f"{ukrainian}: expected exactly one primary definition",
                )
                self.assertNotRegex(
                    source,
                    rf"(?m)^\(визначити\s+{re.escape(english)}\s+(?=\(функція|\(як-є)",
                    f"{english}: English must not remain primary",
                )
                self.assertNotRegex(
                    core4,
                    rf"(?m)^\s*\(визначити\s+{re.escape(english)}(?=\s|\))",
                    f"{english}: історичний англійський DEFINE не має повертатися",
                )

        for name, target in (
            ("внутрішня-мапа-порожній", "мапа-порожній"),
            ("внутрішня-мапа-вставити", "мапа-вставити"),
            ("внутрішня-мапа-отримати", "мапа-отримати"),
            ("внутрішня-мапа-містить", "мапа-містить?"),
            ("внутрішня-мапа-список", "мапа-список"),
        ):
            with self.subTest(internal=name):
                self.assertIn(f"(визначити {name} {target})", source)

        for _english, _ukrainian, bits in TARGETS:
            self.assertNotRegex(
                source,
                rf"(?m)^\s*\({bits}(?:\s|\))",
                "source must not introduce a raw D9 binary call-head",
            )

    def test_primary_d9_projection_does_not_change_domain_tables(self):
        for english, ukrainian, bits in TARGETS:
            self.assertEqual(len(bits), 9)
            row = next(
                line for line in read("lib/domains/d9.lisp").splitlines()
                if line.lstrip().startswith(f"({bits} ")
            )
            self.assertIn(f"(en {english})", row)
            self.assertIn(f"(укр {ukrainian})", row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
