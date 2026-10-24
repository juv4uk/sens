"""Мутант-тест: брак джерела мусить БЛОКУВАТИ, а не виглядати здоровим.

Перевірка МОЄЇ правки аудита (2026-10-24). Я розділив «брак джерела» і
«фізичну помилку», і додав лічильник source_missing в умову блокування.
Якщо прибрати лічильник — мутант (.sens без джерела) проходить як
EXACT_BINARY_PAIRS, тобто гейт послаблюється. Тест це фіксує.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts" / "audit_t5_t5m_file_pairs.py"
FIXTURE = ROOT / "tests/fixtures/wsm-fs-record-producer.sens"


class SourceMissingBlocksTests(unittest.TestCase):
    def test_sens_without_source_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "t").mkdir()
            (repo / "t" / "only.sens").write_bytes(FIXTURE.read_bytes())
            subprocess.run(["git", "init", "-q", "."], cwd=repo, check=True)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=a",
                            "commit", "-qm", "x"], cwd=repo, check=True, capture_output=True)
            out = repo / "o.json"
            r = subprocess.run([sys.executable, str(AUDIT), str(repo), "--output", str(out)],
                               capture_output=True, text=True, timeout=120, check=False)
            report = json.loads(out.read_text(encoding="utf-8"))
            # 1) фізично файл ЗДОРОВИЙ — це і була моя правка
            self.assertEqual(report["summary"]["physical_blocked"], 0)
            # 2) але брак джерела позначено ОКРЕМО
            self.assertEqual(report["summary"]["source_missing"], 1)
            # 3) і гейт УСЕ ЩЕ блокує — інакше моя правка його послабила б
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
