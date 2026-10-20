"""Доменна укр-проєкція SENS verify-repo: джерельні позитив і негатив.

Не видавати цю статичну перевірку за виконання SENS.
"""

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table

FILE = ROOT / "scripts" / "verify-repo.lisp"
OLD_GIT_BLOB = "8f86cf5a779e71643c46fd9ce0bff7a9975e5f49"
CHANGED_LINES = (14, 18, 34, 42, 58, 99, 118, 121, 195, 212, 217, 293, 309, 311, 419, 432, 446)
SECOND_BATCH_LINES = (20, 98, 170, 182, 192, 202, 216, 221, 230, 238, 240, 244, 250, 263, 266, 280, 282, 284, 288, 294, 329, 330, 343, 344, 373, 391, 392, 393, 394, 403, 414, 434, 436)
# Точні домени та інверсні кількості перевірені за D5/D6/D9; не сід8 за шириною.
SECOND_BATCH_RESIDENTS = {
    (5, "01010"): ("додати", 3),
    (5, "01011"): ("відняти", 1),
    (5, "10011"): ("третє", 1),
    (5, "11010"): ("менше?", 7),
    (5, "11100"): ("знайти-за-ключем", 4),
    (6, "001000"): ("нехай", 9),
    (6, "100111"): ("четверте", 1),
    (6, "101000"): ("відобразити", 1),
    (9, "110011101"): ("рядок-решта", 4),
    (9, "110011110"): ("рядок-додати", 1),
    (9, "110100010"): ("рядок-довжина", 2),
    (9, "110100011"): ("рядок-зріз", 1),
    (9, "110101000"): ("рядок-містить?", 6),
    (9, "110101010"): ("рядок-префікс?", 1),
    (9, "110101011"): ("рядок-перший", 3),
    (9, "110101111"): ("процес-запустити", 1),
}
# Key = (exact domain width, exact bits); W8/сід8 inference is prohibited.
DOMAIN_RESIDENTS = {
    (5, "11100"): ("знайти-за-ключем", 1),
    (6, "001000"): ("нехай", 5),
    (8, "11011011"): ("друкувати", 3),
    (9, "110101001"): ("читати-всі", 4),
    (9, "110110111"): ("читати-файл", 14),
}


class VerifyRepoUkrDomainCalls(unittest.TestCase):
    def current_peers(self, residents=DOMAIN_RESIDENTS):
        result = {}
        for (width, bits), (expected, _) in residents.items():
            rows = read_domain_table(ROOT / "lib" / "domains" / f"d{width}.lisp")
            peers = [row.ukr for row in rows if row.bits == bits]
            self.assertEqual(peers, [expected], f"D{width}:{bits} укр-identity")
            result[bits] = expected
        return result

    def restore_previous_source(self, content):
        lines = content.splitlines(keepends=True)
        # Спочатку зворотно відтворюємо другу, неперетинну партію; далі попередню.
        second_peers = self.current_peers(SECOND_BATCH_RESIDENTS)
        second_counts = {bits: 0 for bits in second_peers}
        for one_based in SECOND_BATCH_LINES:
            line = lines[one_based - 1]
            for bits, peer in second_peers.items():
                old_head, new_head = "(" + bits + " ", "(" + peer + " "
                occurrences = line.count(new_head)
                if occurrences:
                    second_counts[bits] += occurrences
                    line = line.replace(new_head, old_head)
            lines[one_based - 1] = line
        self.assertEqual(
            second_counts,
            {bits: n for (_, bits), (_, n) in SECOND_BATCH_RESIDENTS.items()},
            "друга партія втратила або підмінила точну викличну голову",
        )
        peers = self.current_peers()
        count = {bits: 0 for bits in peers}
        for one_based in CHANGED_LINES:
            line = lines[one_based - 1]
            for bits, peer in peers.items():
                new_head = "(" + peer + " "
                old_head = "(" + bits + " "
                occurrences = line.count(new_head)
                if occurrences:
                    count[bits] += occurrences
                    line = line.replace(new_head, old_head)
            lines[one_based - 1] = line
        self.assertEqual(
            count,
            {bits: n for (_, bits), (_, n) in DOMAIN_RESIDENTS.items()},
            "втрачена або підмінена виклична голова",
        )
        return "".join(lines)

    @staticmethod
    def blob_id(data):
        raw = data.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw
        ).hexdigest()

    def test_exact_current_domain_peers_restore_original(self):
        data = FILE.read_text(encoding="utf-8")
        old_source = self.restore_previous_source(data)
        self.assertEqual(self.blob_id(old_source), OLD_GIT_BLOB)
        self.assertIn('"verify-repo: all checks passed"', data)

    def test_wrong_peer_must_fail_closed(self):
        data = FILE.read_text(encoding="utf-8")
        original = '(читати-файл "docs/ukrainian-api.md")'
        self.assertIn(original, data)
        mutated = data.replace(original, '(читати-всі "docs/ukrainian-api.md")', 1)
        with self.assertRaises(AssertionError):
            self.restore_previous_source(mutated)
        new_head = "(рядок-містить? needle text)"
        self.assertIn(new_head, data)
        wrong_new_head = data.replace(new_head, "(рядок-додати needle text)", 1)
        with self.assertRaises(AssertionError):
            self.restore_previous_source(wrong_new_head)


if __name__ == "__main__":
    unittest.main()
