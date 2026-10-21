"""Guard SENS full-укр projection: static source/authority tests, not Python eval."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/guard.lisp"
ALIAS_MARKER = "; Історичні викличні поверхні Guard — ті самі closure, без дублювання."

# Authority is the actual domain table at this repository commit, never W8/сід8.
NATIVE = {
    3: {"001": "як-є", "010": "атом?", "011": "решта",
        "100": "перше", "101": "тотожне?", "110": "за-умовою"},
    4: {"0010": "функція", "0011": "визначити",
        "0100": "хибне?", "1001": "друге", "1110": "список"},
    5: {"11100": "знайти-за-ключем"},
}
D9 = {
    "000010001": ("guard-decision?", "захист-рішення?"),
    "000000000": ("guard-evidence-status?", "захист-доказ-стан?"),
    "000001000": ("guard-unknown-routes", "захист-невідоме-маршрути"),
    "000100100": ("make-guard-finding", "створити-захист-висновок"),
}


def translate(source: str, heads: dict[str, str],
              symbols: dict[str, str] | None = None) -> tuple[str, dict[str, int]]:
    """Only source tokens, not comments/strings. Heads require opening '('."""
    symbols = symbols or {}
    output, counts = [], {}
    i, prev = 0, None
    while i < len(source):
        ch = source[i]
        if ch == ";":
            j = source.find("\n", i)
            j = len(source) if j == -1 else j
            output.append(source[i:j])
            i = j
        elif ch == '"':
            j = i + 1
            while j < len(source):
                if source[j] == "\\":
                    j += 2
                elif source[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            output.append(source[i:j])
            i, prev = j, "string"
        elif ch in "()":
            output.append(ch)
            prev = ch
            i += 1
        elif ch.isspace():
            output.append(ch)
            i += 1
        else:
            j = i
            while j < len(source) and not (source[j].isspace()
                                            or source[j] in '();\"'):
                j += 1
            if j == i:
                output.append(ch)
                i, prev = i + 1, ch
                continue
            token = source[i:j]
            replaced = symbols.get(token, heads.get(token) if prev == "(" else None)
            output.append(replaced if replaced is not None else token)
            if replaced is not None:
                counts[token] = counts.get(token, 0) + 1
            prev, i = "atom", j
    return "".join(output), counts


class GuardProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_peer_names_are_exact_ratifed_domain_rows(self):
        for domain, table in NATIVE.items():
            data = (ROOT / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
            for bits, name in table.items():
                with self.subTest(domain=domain, bits=bits):
                    self.assertRegex(data, re.compile(
                        r"^\s*\(" + bits + r"\s+\(ук\s+[^()]+\)\s+\(укр\s+"
                        + re.escape(name) + r"\)", re.MULTILINE))
        data = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        for bits, (english, ukr) in D9.items():
            with self.subTest(bits=bits):
                row = re.search(r"^\s*\(" + bits + r"\s+.*$", data, re.MULTILINE)
                self.assertIsNotNone(row)
                self.assertIn("(укр " + ukr + ")", row.group())
                self.assertIn("(en " + english + ")", row.group())

    def test_current_guard_program_is_ukrainian_primary_not_old_blob(self):
        # Чинний доказ: структура програми, а не історичний Git blob з
        # коментарями, пробілами й застарілою політикою заморожування.
        for name in (
            "захист-рішення?", "захист-доказ-стан?",
            "захист-невідоме-маршрути", "створити-захист-висновок",
            "захист-порівняти", "захист-синхронізувати-вікно",
            "захист-знайти-запис", "захист-еталон-поле",
        ):
            with self.subTest(name=name):
                self.assertIn("(визначити " + name + "\n", self.text)
        self.assertIn("(сторожа--рівні? очікуване спостережене)", self.text)
        self.assertIn("(захист-знайти-запис поле (решта посилання))", self.text)
        self.assertIn("(визначити guard-sync-window захист-синхронізувати-вікно)",
                      self.text)
        self.assertNotIn("(визначити guard-sync-window\n", self.text)
        self.assertNotIn("#d1:", self.text)

    def test_all_native_guard_heads_migrated(self):
        stripped, _ = translate(self.text, {}, {})
        # Tokens in string/comment data must not be counted as executable heads.
        masked = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"', "", stripped)
        native_bits = {bit for table in NATIVE.values() for bit in table}
        remaining = set(re.findall(r"\(\s*([01]+)(?=[\s(])", masked))
        self.assertTrue(native_bits.isdisjoint(remaining), remaining)
        start = self.text.find("(визначити захист-еталон-поле\n")
        self.assertGreaterEqual(start, 0)
        end = self.text.find("\n(визначити ", start + 1)
        self.assertGreater(end, start)
        guard_field = self.text[start:end]
        self.assertIn("(функція (поле посилання)", guard_field)
        self.assertIn("(функція (запис)", guard_field)
        for old_binding in ("(функція (field reference)", "(функція (entry)", "(друге entry)"):
            self.assertNotIn(old_binding, guard_field)
        # The current Lisp law recursively finds a field; the old D5 helper
        # remains ratified but is no longer a required call in this source.
        self.assertIn("(визначити захист-знайти-запис\n", self.text)
        self.assertIn("(захист-знайти-запис поле (решта посилання))", guard_field)
        self.assertIn("((сторожа--рівні? ключ (перше запис)) запис)", self.text)
        self.assertNotIn("(знайти-за-ключем ", self.text)
        for table in NATIVE.values():
            for ukr in table.values():
                if ukr != "знайти-за-ключем":
                    self.assertIn("(" + ukr, self.text)

    def test_english_names_only_in_explicit_compatibility_aliases(self):
        migrated = self.text.split("\n" + ALIAS_MARKER, 1)[0]
        for _, (english, ukr) in D9.items():
            with self.subTest(english=english):
                self.assertIn("(визначити " + ukr + "\n", migrated)
                self.assertNotIn("(" + english + " ", migrated)
                self.assertNotIn("(визначити " + english + "\n", migrated)
                self.assertEqual(
                    self.text.count(f"(визначити {english} {ukr})"), 1)

    def test_quoted_guard_advice_and_exact_d1_surfaces(self):
        self.assertIn("((route ask-agent)", self.text)
        self.assertIn("(when ecosystem-local-or-component-owned)", self.text)
        self.assertIn("(verify citations-and-access-date)", self.text)
        self.assertNotIn("#d1:", self.text)
        # Словникові імена D1 існують у таблиці, але не є
        # незв'язаними виконуваними змінними українського Guard.
        code = "\n".join(line for line in self.text.splitlines()
                         if not line.lstrip().startswith(";"))
        self.assertNotRegex(code, r"(?<![\w-])(так|ні)(?![\w-])")
        self.assertGreaterEqual(code.count("(атом? (як-є ()))"), 20)
        self.assertGreaterEqual(code.count("(атом? (як-є (())))"), 5)
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)

    def test_ukrainian_language_policy_is_primary_not_legacy_alias(self):
        # Політика мовних ролей виконується українськими визначеннями.
        for name in ("захист-мова-дозволена?", "захист-мовне-рішення"):
            with self.subTest(name=name):
                self.assertIn("(визначити " + name + "\n", self.text)
        self.assertIn("(захист-мова-дозволена? мова роль)", self.text)
        self.assertNotIn("(визначити guard-language-decision", self.text)
        # Не припускаємо D9-ратифікацію лише з локального імені функції.
        self.assertIn("(визначити guard-sync-window захист-синхронізувати-вікно)",
                      self.text)

    def test_no_python_semantic_simulation(self):
        # Exact source round-trip and peer binding, not a fake Python Lisp eval.
        self.assertNotIn("Rust", self.text.split(ALIAS_MARKER)[-1])
        self.assertNotIn("(визначити guard-decision?\n", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
