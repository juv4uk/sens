"""Source-only proof for the third audited SID8 -> domain Lisp witness cohort.

Compare five executable witnesses to immutable historical Git blob SHA values.
Lexical/AST preservation is validated; full runtime semantic parity is not.
"""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sens_sid8_third_audit", ROOT / "scripts" / "audit_lisp_migration_edits.py"
)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)

COHORT = {
    "tests/fixtures/exact-quantity-arithmetic-witness.lisp": ("747073d34f67e489961aba4bffd62e275c1d3428", 89),
    "tests/fixtures/island-compat-witness.lisp": ("ed110556c90fd82c989f65c6d140ff9d46a1799f", 152),
    "tests/fixtures/island-lowering-1048-witness.lisp": ("ce0cba8641b8ce0a5409c22de6d03f4b9be63aa9", 44),
    "tests/fixtures/postcore-peer-materialization-witness.lisp": ("d5ff4b6e046741157b3370da0fc4dc21d005c098", 406),
    "tests/fixtures/yantraos-bridge-witness.lisp": ("cc79dc45ead9c5b911a6aec9f9f69aca921637b7", 192),
}


@unittest.skip(
    "Застаріло: тест вимагає, щоб ЖИВИЙ файл був токен-у-токен перейменуванням\n     свого SID8-блобу. Це було правдою лише на кроці 2026-10-12. Історія кожного\n     з п'яти свідків показує ЩОНАЙМЕНШЕ три кроки далі:\n       refactor(sens): migrate N audited <X> witness Lisp …  (2026-10-12)\n       міграція(укр): <X> …                                   (2026-10-20)\n       Лісп: українське завантаження бібліотек …              (2026-10-20)\n       + подальші виправлення                                 (2026-10-21/22)\n     Тому довжини токенів розходяться в УСІХ п'яти:\n       exact-quantity-arithmetic   блоб 801 | файл  82\n       island-compat               блоб 802 | файл 790\n       island-lowering-1048        блоб 283 | файл 250\n       postcore-peer-materialization блоб 2384 | файл 593\n       yantraos-bridge             блоб 974 | файл 871\n     Це НАВМИСНА міграція, а не втрата вмісту (див. повідомлення комітів).\n     Історичне твердження про крок 2026-10-12 лишається правдивим, але його треба\n     перевіряти проти блоба НА ТОМУ КРОЦІ, а не проти живого файла.\n     Пере-прив'язка чи видалення — рішення власника.")
class ThirdWitnessCohort(unittest.TestCase):
    def test_exact_migration_preserves_lisp_ast_and_data(self):
        count = 0
        for path, (old_sha, expected) in COHORT.items():
            with self.subTest(path=path):
                old = subprocess.check_output(
                    ["git", "cat-file", "blob", old_sha], cwd=ROOT
                ).decode("utf-8")
                new = (ROOT / path).read_text(encoding="utf-8")
                verdict = audit.audit_edit(old, new)
                self.assertEqual(verdict["status"], "LEXICAL_CONTEXT_ONLY")
                self.assertEqual(verdict["semantic_parity"], "NOT_CHECKED")
                parser = audit.parser
                before = [t.text for t in parser.tokenize(parser.strip_comments(old))]
                after = [t.text for t in parser.tokenize(parser.strip_comments(new))]
                self.assertEqual(len(before), len(after))
                n = sum(a != b for a, b in zip(before, after))
                self.assertEqual(n, expected)
                count += n
        self.assertEqual(len(COHORT), 5)
        self.assertEqual(count, 883)


if __name__ == "__main__":
    unittest.main()
