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
# Key = (exact domain width, exact bits); W8/SID8 inference is prohibited.
DOMAIN_RESIDENTS = {
    (5, "11100"): ("знайти-за-ключем", 1),
    (6, "001000"): ("нехай", 5),
    (8, "11011011"): ("друкувати", 3),
    (9, "110101001"): ("читати-всі", 4),
    (9, "110110111"): ("читати-файл", 14),
}


class VerifyRepoUkrDomainCalls(unittest.TestCase):
    def current_peers(self):
        result = {}
        for (width, bits), (expected, _) in DOMAIN_RESIDENTS.items():
            rows = read_domain_table(ROOT / "lib" / "domains" / f"d{width}.lisp")
            peers = [row.ukr for row in rows if row.bits == bits]
            self.assertEqual(peers, [expected], f"D{width}:{bits} укр-identity")
            result[bits] = expected
        return result

    def restore_previous_source(self, content):
        lines = content.splitlines(keepends=True)
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


if __name__ == "__main__":
    unittest.main()
