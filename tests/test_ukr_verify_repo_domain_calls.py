"""Доменна укр-проєкція SENS verify-repo: джерельні позитив і негатив.

Не видавати цю статичну перевірку за виконання SENS.

Свідок перебазовано на стан, до якого застосовано повну міграцію голів
(f9d5b02f…): попередній оригінал 8f86cf5a… був структурно іншим
(перейменування fail/провал і інша кількість рядків), тож його peer->bits
інверсія вже не відтворювала.
"""

import hashlib
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table

FILE = ROOT / "scripts" / "verify-repo.lisp"
OLD_GIT_BLOB = "f9d5b02fecc8f127fe74f74c708bb98d147d0778"
# Рядки, на яких повна міграція замінила сирий виклик ратифікованою поверхнею.
CHANGED_LINES = (172, 173, 188, 205, 215, 229, 246, 251, 252, 253, 254, 256, 258, 262, 299, 301, 303, 317, 328, 333, 352, 353, 354, 361, 372, 389, 401, 405, 406, 407, 409, 410, 412, 413, 421)
# (width, bits) -> (укр-поверхня, точна кількість на цих рядках)
RESIDENTS = {
    (5, "01010"): ("додати", 2),
    (5, "10011"): ("третє", 1),
    (5, "11010"): ("менше?", 1),
    (6, "001000"): ("нехай", 2),
    (8, "11100000"): ("код-символу", 1),
    (8, "11101110"): ("символ-у-текст", 4),
    (8, "11110100"): ("значення-у-текст", 4),
    (8, "11110111"): ("однакові?", 21),
    (9, "110011100"): ("рядок-порожній?", 5),
    (9, "110011101"): ("рядок-решта", 1),
    (9, "110100010"): ("рядок-довжина", 1),
    (9, "110101000"): ("рядок-містить?", 1),
}


class VerifyRepoUkrDomainCalls(unittest.TestCase):
    def current_peers(self, residents=RESIDENTS):
        result = {}
        for (width, bits), (expected, _) in residents.items():
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
                # Межа після поверхні: пробіл, дужка АБО кінець рядка.
                pattern = re.compile(r"\(" + re.escape(peer) + r"(?=[\s)])")
                line, occurrences = pattern.subn("(" + bits, line)
                if occurrences:
                    count[bits] += occurrences
            lines[one_based - 1] = line
        self.assertEqual(
            count,
            {bits: n for (_, bits), (_, n) in RESIDENTS.items()},
            "втрачена або підмінена виклична голова",
        )
        return "".join(lines)

    @staticmethod
    def blob_id(data):
        raw = data.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw
        ).hexdigest()

    def test_exact_current_domain_peers_restore_previous(self):
        data = FILE.read_text(encoding="utf-8")
        old_source = self.restore_previous_source(data)
        self.assertEqual(self.blob_id(old_source), OLD_GIT_BLOB)
        self.assertIn('"verify-repo: all checks passed"', data)

    def test_wrong_peer_must_fail_closed(self):
        data = FILE.read_text(encoding="utf-8")
        # Підміна ратифікованої поверхні іншою мусить провалитися закрито.
        self.assertIn("(однакові?", data)
        wrong = data.replace("(однакові?", "(рядок-додати")
        with self.assertRaises(AssertionError):
            self.restore_previous_source(wrong)
        # Втрата поверхні також має провалитися.
        missing = data.replace("(рядок-порожній?", "(рядок-додати")
        with self.assertRaises(AssertionError):
            self.restore_previous_source(missing)


if __name__ == "__main__":
    unittest.main()
