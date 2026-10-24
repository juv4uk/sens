"""Доказ мовних законів СПРАВЖНІМ sens — або чесний пропуск.

Це тест, який я не міг виконати в пісочниці (немає Rust/Zig). Він НЕ вдає, що
виконався: якщо `target/debug/sens` відсутній, тест ПРОПУСКАЄТЬСЯ з причиною.
Коли бінарник є (у CI після `cargo build`), тест справді запускає 14 законів і
перевіряє, що звіт містить 28 випадків і 14 пар law&mutant.

Це замикає ланцюг: ЗБІРКА → ВИКОНАННЯ → ЗВІТ, і жодна ланка не лишається
«оголошеною».
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SENS = ROOT / "target" / "debug" / "sens"
SENS_TRIT = ROOT / "target" / "debug" / "sens-trit"
PROVE = ROOT / "scripts" / "prove-lisp-language-laws.sh"


class ProveWithRealSens(unittest.TestCase):
    def test_proof_runs_and_reports_28_cases(self):
        if not (SENS.is_file() and SENS_TRIT.is_file()):
            self.skipTest(
                "native sens/sens-trit відсутні (немає Rust/Zig у пісочниці) — "
                "тест ПРОПУЩЕНО, а не видано за успіх")
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "proof.json"
            r = subprocess.run(["bash", str(PROVE), str(SENS), str(report)],
                               capture_output=True, text=True, timeout=900, check=False)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            self.assertIn("NATIVE_SENS_SUITE_PASS", r.stdout)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "sens-language-law-proof/v1")
            cases = data["cases"]
            laws = {c["test_id"] for c in cases if c["kind"] == "law"}
            mutants = {c["test_id"] for c in cases if c["kind"] == "mutant"}
            self.assertEqual(len(laws), 14, "мусить бути 14 законів")
            self.assertEqual(len(mutants), 14, "мусить бути 14 мутантів")
            self.assertEqual(len(laws & mutants), 14, "14 пар law&mutant")
            self.assertEqual(len(cases), 28, "28 випадків")


if __name__ == "__main__":
    unittest.main()
