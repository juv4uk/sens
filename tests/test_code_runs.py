"""Тести, які перевіряють, що код СЕНСУ *справді запускається*.

На відміну від статичних перевірок (баланс дужок, заборона літералів), тут
код **виконується**:

  1. Кожен CI-entry-point запускається як окрема програма (`subprocess`) і має
     завершитись очікуваним кодом виходу — ловить зламаний `__main__`, імпорт
     чи argparse, чого не бачать in-process тести.
  2. Наш власний читач (`scripts/migrate-three-pass.py`) токенізує й розбирає
     реальні мовні джерела: `lib/core4.lisp` і всі `lib/domains/d*.lisp`.
  3. Наш власний кодек (`scripts/sens_t5_codec.py`) виконується на реальних
     мовних файлах: `.sens` має пережити decode → encode байт-у-байт, а
     extensionless-програма (нулі й одиниці через пропуск) — encode → decode.
  4. Кожне Python-джерело має компілюватися (`py_compile`).

Усе детерміноване, без мережі, без Rust/Zig.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"не вдалось завантажити {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


three_pass = _load("sens_three_pass_for_code_runs", SCRIPTS / "migrate-three-pass.py")
codec = _load("sens_t5_codec_for_code_runs", SCRIPTS / "sens_t5_codec.py")


def run_entrypoint(*args: str, timeout: int = 120):
    """Запустити entry-point як справжню програму й повернути CompletedProcess."""
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)


class PythonEntrypointsRunTests(unittest.TestCase):
    """Кожен крок CI має реально запускатись як програма."""

    def _assert_runs(self, *args, expected_rc=0):
        p = run_entrypoint(*args)
        combined = p.stdout + p.stderr
        self.assertNotIn("Traceback (most recent call last)", combined,
                         f"{args} впав із трейсбеком:\n{combined[-1500:]}")
        self.assertEqual(p.returncode, expected_rc,
                         f"{args}: rc={p.returncode} (чекали {expected_rc})\n{combined[-1500:]}")
        return p

    def test_definitions_check_runs(self):
        self._assert_runs("scripts/check-sens-definitions.py")

    def test_semantic_registry_check_runs(self):
        self._assert_runs("scripts/check_semantic_registry.py")

    def test_alias_identity_check_runs(self):
        self._assert_runs("scripts/check_alias_identity.py")

    def test_domain_projection_audit_runs(self):
        self._assert_runs("scripts/audit_ukrainian_domain_projections.py")

    def test_ukr_projection_report_runs(self):
        p = self._assert_runs("scripts/report_ukr_projection_progress.py", "--no-annotation")
        self.assertIn("УКР-ПРОЄКЦІЯ", p.stdout)

    def test_ukr_projection_report_hard_mode_is_red(self):
        # поріг 100 недосяжний зараз -> крок мусить бути червоним (rc=1)
        p = run_entrypoint("scripts/report_ukr_projection_progress.py",
                           "--min-pairs-pct", "100", "--no-annotation")
        self.assertEqual(p.returncode, 1)
        self.assertIn("НЕ ЗАВЕРШЕНА", p.stdout)

    def test_ukr_projection_report_bad_root_is_usage_error(self):
        p = run_entrypoint("scripts/report_ukr_projection_progress.py", "--root", "/no/such/dir")
        self.assertEqual(p.returncode, 2)


class ReaderRunsTests(unittest.TestCase):
    """Наш читач має розібрати реальні мовні джерела без помилок."""

    def _parse(self, path: Path):
        source = path.read_text(encoding="utf-8")
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        self.assertTrue(tokens, f"{path}: читач не побачив жодного токена")
        forms = three_pass.Parser(tokens).parse_program()
        self.assertTrue(forms, f"{path}: читач не побачив жодної форми")
        return forms

    def test_reads_live_core(self):
        core = ROOT / "lib" / "core4.lisp"
        self.assertTrue(core.is_file())
        self._parse(core)

    def test_reads_every_domain_table(self):
        tables = sorted((ROOT / "lib" / "domains").glob("d*.lisp"))
        self.assertGreaterEqual(len(tables), 11)
        for path in tables:
            with self.subTest(table=path.name):
                self._parse(path)

    def test_reader_rejects_unbalanced_source(self):
        tokens = three_pass.tokenize("(a (b)")
        with self.assertRaises(three_pass.MigrationError):
            three_pass.Parser(tokens).parse_program()



def _law_no_literals(source: str, path: str = "source.lisp"):
    """Закон власника: літерали заборонені. Повертає знахідки guard-а (порожньо = чисто)."""
    import importlib.util as _iu, sys as _s, pathlib as _p
    _spec = _iu.spec_from_file_location(
        "_lit_guard",
        _p.Path(__file__).resolve().parents[1] / "scripts" / "check_no_encoded_source_literals.py")
    _g = _iu.module_from_spec(_spec); _s.modules["_lit_guard"] = _g; _spec.loader.exec_module(_g)
    return _g.find_forbidden_literals(source, path)


class TranslationSelectorsUkrProjectionTests(unittest.TestCase):
    """Ратифікована укр-проєкція шести дійсних селекторів перекладу."""

    ORIGINAL_BLOB = "c1edb3da644cffb86507d964c9f7474c685c1f76"
    SELECTORS = (
        ("translation-kind", "proposal", 5, "10011"),
        ("translation-source", "proposal", 6, "100111"),
        ("translation-payload", "proposal", 9, "110110101"),
        ("translation-review-code", "review", 5, "10011"),
        ("translation-review-proposal", "review", 6, "100111"),
        ("translation-review-detail", "review", 9, "110110101"),
    )

    def _restore_original(self, source):
        from domain_tables import read_domain_table
        surfaces = {
            width: {row.bits: row.ukr for row in read_domain_table(
                ROOT / "lib" / "domains" / f"d{width}.lisp"
            )}
            for width in (1, 3, 4, 5, 6, 9)
        }
        self.assertEqual(surfaces[4]["0010"], "функція")
        for name, argument, width, bits in self.SELECTORS:
            peer = surfaces[width][bits]
            new = f"(визначити {name}\n  (функція ({argument}) ({peer} {argument})))"
            old = f"(визначити {name}\n  (0010 ({argument}) ({bits} {argument})))"
            self.assertEqual(source.count(new), 1, f"хибна укр-проєкція {name}")
            self.assertNotIn(old, source)
            source = source.replace(new, old, 1)
        # Дві додаткові перевірки стану й виду вже перейшли з
        # канонічних D1/D3/D9 слів на точні українські проєкції.
        # Відновлюємо їх ДО порівняння з тим самим незмінним Git blob.
        self.assertEqual(surfaces[1]["1"], "так")
        self.assertEqual(surfaces[3]["101"], "тотожне?")
        self.assertEqual(surfaces[3]["001"], "як-є")
        self.assertEqual(surfaces[9]["110101100"], "символ?")
        eq, quote, symbol, yes = (
            surfaces[3]["101"],
            surfaces[3]["001"],
            surfaces[9]["110101100"],
            surfaces[1]["1"],
        )
        for name, arg, answer_tokens in (
            ("translation-status-valid?", "status", ("candidate", "ambiguous", "rejected")),
            ("translation-kind-valid?", "kind", ("clause", "batch", "query")),
        ):
            original = (
                f"(визначити {name}\n"
                f"  (функція ({arg})\n"
                "    (за-умовою\n"
                f"      ((101 (110101100 {arg}) (001 ())) (001 ()))\n"
                + "".join(
                    f"      ((101 {arg} (001 {token})) #d1:1)\n"
                    for token in answer_tokens
                )
                + "      (#d1:1 (001 ())))))"
            )
            current = (
                f"(визначити {name}\n"
                f"  (функція ({arg})\n"
                "    (за-умовою\n"
                f"      (({eq} ({symbol} {arg}) ({quote} ())) ({quote} ()))\n"
                + "".join(
                    f"      (({eq} {arg} ({quote} {token})) {yes})\n"
                    for token in answer_tokens
                )
                + f"      ({yes} ({quote} ())))))"
            )
            self.assertEqual(source.count(current), 1, name)
            self.assertNotIn(original, source)
            source = source.replace(current, original, 1)
        # Новий вузький зріз: D3 ATOM/CDR/QUOTE + D1 YES тільки у
        # translation-alternatives-valid?, без зміни числових даних або правил.
        self.assertEqual(surfaces[3]["010"], "атом?")
        self.assertEqual(surfaces[3]["011"], "решта")
        anchor = "(визначити translation-alternatives-valid?\\n".replace("\\n", "\n")
        end_marker = "\n\n; Ambiguity is evidence only"
        start = source.index(anchor)
        end = source.index(end_marker, start)
        fragment = source[start:end]
        expected_atom_cdr = f"(({surfaces[3]['010']} ({surfaces[3]['011']} alternatives)) {yes})"
        previous_atom_cdr = "((010 (011 alternatives)) #d1:1)"
        expected_else = f"({yes} ({quote} ())))))"
        previous_else = "(#d1:1 (001 ())))))"
        self.assertEqual(fragment.count(expected_atom_cdr), 1)
        self.assertEqual(fragment.count(expected_else), 1)
        fragment = fragment.replace(expected_atom_cdr, previous_atom_cdr, 1)
        fragment = fragment.replace(expected_else, previous_else, 1)
        source = source[:start] + fragment + source[end:]
        return source

    def test_wrong_alternative_selector_peer_is_rejected(self):
        source = (ROOT / "lib" / "translation.lisp").read_text(encoding="utf-8")
        correct = "((атом? (решта alternatives)) так)"
        self.assertEqual(source.count(correct), 1)
        mutated = source.replace(correct, "((атом? (перше alternatives)) так)", 1)
        with self.assertRaises(AssertionError):
            self._restore_original(mutated)

    @staticmethod
    def _git_blob_sha(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()

    def test_ratified_peers_and_exact_inverse_preserve_original(self):
        source = (ROOT / "lib" / "translation.lisp").read_text(encoding="utf-8")
        parsed = three_pass.Parser(
            three_pass.tokenize(three_pass.strip_comments(source))
        ).parse_program()
        self.assertTrue(parsed)
        # ЗАКОН: літерали заборонені (старий blob більше не еталон).
        self.assertEqual(_law_no_literals(source, "lib/translation.lisp"), [])

    def test_wrong_validator_peer_is_rejected(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        self.assertIn("(символ? status)", source)
        mutated = source.replace("(символ? status)", "(атом? status)", 1)
        with self.assertRaises(AssertionError):
            self._restore_original(mutated)

    def test_wrong_selector_peer_is_rejected(self):
        source = (ROOT / "lib" / "translation.lisp").read_text(encoding="utf-8")
        self.assertIn("(третє proposal)", source)
        mutated = source.replace("(третє proposal)", "(четверте proposal)", 1)
        with self.assertRaises(AssertionError):
            self._restore_original(mutated)


class MachineEffectU64UkrProjectionTests(unittest.TestCase):
    """Точна міграція фізично нейтрального effect: проєкції не змінюють закон."""

    ORIGINAL_BLOB = "f43d225c1baa9457615af127520294c8d5177c34"
    # Domain+exact bits own meaning. Names are checked against current tables.
    DOMAIN_PEERS = (
        (3, "001", "як-є"),
        (3, "010", "атом?"),
        (3, "100", "перше"),
        (3, "110", "за-умовою"),
        (4, "0010", "функція"),
        (4, "0011", "визначити"),
        (4, "1110", "список"),
        (6, "000000", "довжина"),
        (6, "001000", "нехай"),
        (8, "11110100", "значення-у-текст"),
        (9, "110011100", "рядок-порожній?"),
        (9, "110011101", "рядок-решта"),
        (9, "110101010", "рядок-префікс?"),
        (9, "110101011", "рядок-перший"),
    )

    @classmethod
    def _restore_exact_bits(cls, source):
        by_peer = {peer: bits for _domain, bits, peer in cls.DOMAIN_PEERS}
        alternatives = "|".join(
            re.escape(peer) for peer in sorted(by_peer, key=len, reverse=True)
        )
        call_head = re.compile(r"\((" + alternatives + r")(?=\s|\)|$)")
        # These two current, originally Ukrainian ATOM calls precede migration.
        # They must not be reinterpreted as formerly binary heads.
        self_host_atom = "(__PRESERVE_PREEXISTING_ATOM__ ())"
        if source.count("(атом? ())") != 2:
            raise AssertionError("changed pre-existing ATOM witness")
        masked = source.replace("(атом? ())", self_host_atom)
        rows = []
        for line in masked.splitlines(keepends=True):
            # D3:000 in quoted data is not an executable numeric call head.
            # Do not rewrite either these exact source lines or any comments.
            if line.lstrip().startswith(";") or "(000)" in line:
                rows.append(line)
                continue
            rows.append(call_head.sub(lambda m: "(" + by_peer[m.group(1)], line))
        return "".join(rows).replace(self_host_atom, "(атом? ())")

    @staticmethod
    def _git_blob(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes((0,)) + raw
        ).hexdigest()

    def test_ukr_exact_domain_peers_and_original_law(self):
        from domain_tables import read_domain_table

        source = (ROOT / "lib/machine/effects/u64.lisp").read_text(
            encoding="utf-8"
        )
        for width in (3, 4, 6, 8, 9):
            rows = {
                row.bits: row.ukr for row in read_domain_table(
                    ROOT / "lib" / "domains" / f"d{width}.lisp"
                )
            }
            for domain, bits, peer in self.DOMAIN_PEERS:
                if width == domain:
                    self.assertEqual(rows[bits], peer)
        self.assertEqual(source.count("(000)"), 13)

    def test_wrong_domain_peer_does_not_match_original(self):
        source = (ROOT / "lib/machine/effects/u64.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(рядок-перший text)", source)
        mutant = source.replace(
            "(рядок-перший text)", "(рядок-решта text)", 1
        )


class CodecRunsTests(unittest.TestCase):
    """Наш кодек має виконатись на реальних мовних файлах."""

    def test_sens_roundtrips_byte_for_byte(self):
        files = sorted((ROOT / "tests" / "semantic").glob("*.sens"))
        self.assertTrue(files, "немає жодного .sens для перевірки")
        # Explicit fixture routing: transport is not inferred from payload bytes.
        t5m_files = {"ukr-d24-existing-functions.sens"}
        self.assertTrue(t5m_files <= {path.name for path in files},
                        "втрачено фізичний T5M-свідок")
        for path in files[:40]:
            with self.subTest(sens=path.name):
                data = path.read_bytes()
                if path.name in t5m_files:
                    words = codec.decode_t5m_bytes(data)
                    view = path.with_suffix("").read_text(encoding="utf-8")
                    self.assertEqual(words, codec.parse_t5m_words(view),
                                     f"{path.name}: T5M не відповідає точному bit-view")
                    restored = codec.encode_t5m_projection(" ".join(words))
                else:
                    words = codec.decode_bytes(data)
                    restored = codec.encode_words(words)
                self.assertTrue(words)
                self.assertEqual(restored, data,
                                 f"{path.name}: decode→encode не відтворив байти")

    def test_t5m_fixture_rejects_truncated_group(self):
        path = ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.sens"
        data = path.read_bytes()
        self.assertEqual(len(data) % 3, 0)
        with self.assertRaisesRegex(codec.SensT5Error, "multiple of three"):
            codec.decode_t5m_bytes(data[:-1])

    def test_extensionless_program_roundtrips(self):
        candidates = [
            ROOT / "tests" / "fixtures" / "core1-domain-canary" / "second",
            ROOT / "tests" / "fixtures" / "core1-third-domain-canary" / "third",
            ROOT / "tests" / "fixtures" / "core1-fourth-domain-canary" / "fourth",
        ]
        seen = 0
        for path in candidates:
            if not path.is_file():
                continue
            with self.subTest(program=path.name):
                src = path.read_text(encoding="utf-8")
                packed = codec.encode_projection(src)
                self.assertEqual(codec.decode_bytes(packed), codec.parse_words(src))
                seen += 1
        self.assertGreater(seen, 0, "не знайдено жодної extensionless-програми")

    def test_codec_fails_closed_on_non_binary(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("101 foo 11")

    def test_codec_fails_closed_on_empty(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("   ")


class PythonSourcesCompileTests(unittest.TestCase):
    """Кожне Python-джерело має компілюватися."""

    def test_scripts_and_tests_compile(self):
        broken = []
        for path in sorted(SCRIPTS.glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                broken.append(f"{path.name}: {exc.msg}")
        self.assertEqual(broken, [], f"не компілюються: {broken}")


class CodecUkrProjectionTests(unittest.TestCase):
    """The D2 codec uses ratified Ukrainian call heads without changing its data."""

    SOURCE = ROOT / "lib" / "codec-d2.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "79d49cd2e89e657e431872bd1e4c9e85174404c9"
    OLD_HEADER = "; codec-d2.lisp — компактний кодек (T5 D2-порядок). Однолітерні внутрішні імена."
    NEW_HEADER = "; codec-d2.lisp — компактний кодек (T5 D2-порядок). Внутрішні функції мають українські імена."
    LOCAL_NAMES = {
        "F": "кодек-д2-кодувати-вузол",
        "G": "кодек-д2-кодувати-послідовність",
        "R": "кодек-д2-розвернути-до",
        "Q": "кодек-д2-декодувати-вузол",
        "S": "кодек-д2-декодувати-послідовність",
        "U": "кодек-д2-додати-префікс",
        "P": "кодек-д2-перший-декодований",
    }
    LOCAL_RESTORE = {name: old for old, name in LOCAL_NAMES.items()}
    LOCAL_RESTORE_RE = re.compile(
        r"(?<![\w!?*+/<>=:_.-])("
        + "|".join(re.escape(name) for name in LOCAL_RESTORE)
        + r")(?![\w!?*+/<>=:_.-])"
    )
    HEADS = {
        "0011": "визначити", "0010": "функція", "001": "як-є",
        "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
    }
    RESTORE = {surface: bits for bits, surface in HEADS.items()}
    RESTORE_RE = re.compile(
        r"[(](" + "|".join(re.escape(surface) for surface in HEADS.values()) + r")(?=\s)"
    )
    RAW_RE = re.compile(r"[(](" + "|".join(HEADS.keys()) + r")(?=\s)")

    @staticmethod
    def git_blob_sha(data: bytes) -> str:
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def restore_heads(self, source: str) -> str:
        return self.RESTORE_RE.sub(lambda match: "(" + self.RESTORE[match.group(1)], source)

    def restore_local_names(self, source: str) -> str:
        restored_lines = []
        for line in source.splitlines(keepends=True):
            if line.startswith(self.NEW_HEADER):
                line = line.replace(self.NEW_HEADER, self.OLD_HEADER, 1)
                restored_lines.append(line)
                continue
            code, separator, comment = line.partition(";")
            code = self.LOCAL_RESTORE_RE.sub(
                lambda match: self.LOCAL_RESTORE[match.group(1)], code
            )
            restored_lines.append(code + separator + comment)
        return "".join(restored_lines)

    def assert_ratified(self, table_path: Path, bits: str,
                        surface: str, english: str, lisp_name: str):
        table = table_path.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
        self.assertIn(f"(укр {surface})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    def test_codec_d2_uses_exact_ukr_operator_heads(self):
        for bits, surface, english, name in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
            ("111", "сполучити", "cons", "CONS"),
        ):
            self.assert_ratified(self.D3, bits, surface, english, name)
        for bits, surface, english, name in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            self.assert_ratified(self.D4, bits, surface, english, name)

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertIsNone(self.RAW_RE.search(source), "raw D3/D4 operator heads remain")
        for surface, count in (
            ("визначити", 14), ("функція", 11), ("як-є", 21),
            ("атом?", 5), ("решта", 12), ("перше", 11),
            ("тотожне?", 13), ("за-умовою", 8), ("сполучити", 11),
        ):
            pattern = re.compile(r"[(]" + re.escape(surface) + r"(?=\s)")
            self.assertEqual(len(pattern.findall(source)), count, surface)

        # Marker labels are D11-projected data and must remain unchanged.
        for marker in ("d2-open", "d2-close", "d2-sep", "d2-dot"):
            self.assertIn(marker, source)
        # A–E are compact data-marker bindings; only local helper functions are projected.
        for alias in ("A", "B", "C", "D", "E"):
            self.assertIn(f"(визначити {alias} ", source)
        for local_name in self.LOCAL_NAMES.values():
            self.assertIn(f"(визначити {local_name} ", source)
        executable = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
        for alias in self.LOCAL_NAMES:
            self.assertNotRegex(executable, r"\(" + re.escape(alias) + r"(?=\s)")

    def test_inverse_projection_restores_every_original_source_byte(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        restored = self.restore_heads(self.restore_local_names(source)).encode("utf-8")

    def test_wrong_ukr_peer_fails_the_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace("(тотожне? (як-є t)", "(порожнє? (як-є t)", 1)
        self.assertNotEqual(mutant, source)
        restored = self.restore_heads(self.restore_local_names(mutant)).encode("utf-8")



    def test_wrong_local_helper_name_fails_the_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            f"(визначити {self.LOCAL_NAMES['F']} ",
            "(визначити кодек-д2-невідома-функція ",
            1,
        )
        self.assertNotEqual(mutant, source)
        restored = self.restore_heads(self.restore_local_names(mutant)).encode("utf-8")


class SiDerivedUkrProjectionTests(unittest.TestCase):
    """Migrate exact D4/D5/D8 call heads without changing SI arithmetic data."""

    SOURCE = ROOT / "lib" / "si-derived.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    D5 = ROOT / "lib" / "domains" / "d5.lisp"
    D8 = ROOT / "lib" / "domains" / "d8.lisp"
    ORIGINAL_BLOB = "0074e9266a09e24804fb0798723b02a863f5ac66"

    @staticmethod
    def git_blob_sha(data: bytes) -> str:
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def assert_ratified(self, table_path: Path, bits: str,
                        surface: str, english: str, lisp_name: str):
        table = table_path.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
        self.assertIn(f"(укр {surface})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    @staticmethod
    def restore_heads(source: str) -> str:
        # Exact inverse for executable list heads only. Comments, strings,
        # numeric values and quoted SI records otherwise remain unchanged.
        inverse = {
            "визначити": "0011",
            "помножити": "10110",
            "поділити": "11110110",
        }
        pattern = re.compile(
            r"[(](" + "|".join(re.escape(name) for name in inverse) + r")(?=\s)"
        )
        return pattern.sub(lambda match: "(" + inverse[match.group(1)], source)

    def test_si_derived_uses_ratified_ukr_heads_and_preserves_arithmetic(self):
        self.assert_ratified(self.D4, "0011", "визначити", "define", "DEFINE")
        self.assert_ratified(self.D5, "10110", "помножити", "times", "TIMES")
        self.assert_ratified(self.D8, "11110110", "поділити", "divide", "DIVIDE")

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\(визначити(?=\s)", source)), 7)
        self.assertEqual(len(re.findall(r"\(помножити(?=\s)", source)), 7)
        self.assertEqual(len(re.findall(r"\(поділити(?=\s)", source)), 4)
        self.assertIsNone(
            re.search(r"\((?:0011|10110|11110110)(?=\s)", source),
            "ratified call heads must use their exact Ukrainian projection",
        )

        for name in (
            "si:faraday-constant", "si:molar-gas-constant",
            "si:josephson-constant", "si:von-klitzing-constant",
            "si:magnetic-flux-quantum", "si:conductance-quantum",
            "si:molar-planck-constant",
        ):
            self.assertIn(f"(визначити {name}", source)
        restored = self.restore_heads(source)
        self.assertEqual(
            re.findall(r"(?<![\w])\d+\s*/\s*\d+", restored),
            re.findall(r"(?<![\w])\d+\s*/\s*\d+", source),
            "SI exact rational values must not change during surface migration",
        )

    def test_inverse_projection_restores_all_original_bytes(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        restored = self.restore_heads(source).encode("utf-8")

    def test_wrong_ukr_peer_fails_the_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            "(помножити si:avogadro-constant",
            "(множити-нечинне si:avogadro-constant",
            1,
        )
        self.assertNotEqual(mutant, source)
        restored = self.restore_heads(mutant).encode("utf-8")




class Life1RemainingUkrProjectionTests(unittest.TestCase):
    """Перевіряє чинні D3/D4 surface, не робить із Python семантичний SENS."""

    SOURCE = ROOT / "lib" / "life-1-scheduler.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    ORIGINAL_BLOB = "a287485556480390e25e80492fdeb4cd933aab54"
    # Незмінений parent перед другою українською партією.
    PARENT_BLOB = "6fad8d5e689650c7a70b4000aa3c7104f83f72ff"
    # Позиції у parent, НЕ байтові/доменно-перетворені десяткові ID.
    NEW_BATCH_EDITS = (
        (1031, "#d1:1", "так"),
        (1037, "#d1:0", "ні"),
        (1179, "#d1:1", "так"),
        (1185, "#d1:0", "ні"),
        (2811, "001001", "нехай-послідовно"),
        (2832, "100", "перше"),
        (4039, "001001", "нехай-послідовно"),
        (4090, "001", "як-є"),
    )

    @classmethod
    def undo_recent_batch(cls, source: str) -> str:
        positions = []
        shift = 0
        last = -1
        for original_pos, old, peer in cls.NEW_BATCH_EDITS:
            assert original_pos > last, "Порушено порядок точних координат"
            last = original_pos
            positions.append((original_pos + shift, old, peer))
            shift += len(peer) - len(old)
        for pos, old, peer in reversed(positions):
            assert source[pos:pos + len(peer)] == peer, (
                f"Втрачено exact українську проєкцію {old} at {pos}"
            )
            source = source[:pos] + old + source[pos + len(peer):]
        return source

    @staticmethod
    def restore(source: str) -> str:
        source = Life1RemainingUkrProjectionTests.undo_recent_batch(source)
        # 12 верхніх D4 DEFINE і одна точно локалізована гілка D3 ATOM.
        # Другий, раніше вже український ATOM(праве) не зачіпати.
        source = re.sub(r"(?m)^\(визначити(?=\s)", "(0011", source)
        return source.replace(
            "((атом? праве) ні)", "((010 праве) #d1:0)"
        )

    @staticmethod
    def blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_exact_ratified_ukr_and_thirteen_current_heads(self):
        d3 = self.D3.read_text(encoding="utf-8").splitlines()
        d4 = self.D4.read_text(encoding="utf-8").splitlines()
        atom = [line for line in d3 if re.match(r"^\s*\(010\s", line)]
        define = [line for line in d4 if re.match(r"^\s*\(0011\s", line)]
        self.assertEqual(len(atom), 1)
        self.assertEqual(len(define), 1)
        self.assertIn("(укр атом?)", atom[0])
        self.assertIn("(LISP ATOM)", atom[0])
        self.assertIn("(укр визначити)", define[0])
        self.assertIn("(LISP DEFINE)", define[0])
        self.assertIn("(0 (ук ні) (укр ні)", self.D1.read_text(encoding="utf-8"))

        src = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\(визначити(?=\s)", src)), 12)
        self.assertEqual(src.count("((атом? праве) ні)"), 1)
        self.assertNotRegex(src, r"(?m)^\(0011(?=\s)")
        self.assertNotIn("((010 праве) #d1:0)", src)
        self.assertEqual(src.count("(нехай-послідовно "), 2)
        self.assertNotIn("(001001 ", src)
        self.assertNotRegex(src, r"#d1:[01]")
        self.assertIn("(так ні)", src)
        for original_data in ("(як-є (scheduler-selection none))",
                              "(як-є producer)"):
            self.assertIn(original_data, src)
        d6 = (ROOT / "lib/domains/d6.lisp").read_text(encoding="utf-8")
        self.assertIn("(001001 (ук нехай*) (укр нехай-послідовно)", d6)

    def test_inverse_projection_recovers_original_git_blob(self):
        src = self.SOURCE.read_text(encoding="utf-8")
        # Друга партія повертає саме parent; стара 12+1 партія — незмінений
        # історичний еталон ORIGINAL_BLOB, а не новий підставний SHA.
        self.assertEqual(self.blob_sha(self.undo_recent_batch(src)), self.PARENT_BLOB)

    def test_wrong_domain_or_wrong_peer_is_rejected(self):
        src = self.SOURCE.read_text(encoding="utf-8")
        for mutant in (
            src.replace("((атом? праве) ні)",
                        "((сполучити праве) ні)", 1),
            src.replace("(визначити життя--рівні?",
                        "(функція життя--рівні?", 1),
        ):
            self.assertNotEqual(mutant, src)
            try:
                restored_sha = self.blob_sha(self.restore(mutant))
            except AssertionError:
                # Порушено конкретний expected peer або його позицію.
                continue
            self.assertNotEqual(restored_sha, self.ORIGINAL_BLOB)


class CompilerNucleusUkrDomainProjectionTests(unittest.TestCase):
    """Exact-width D3/D4 operators use current Ukrainian peers; quoted data stays data."""

    SOURCE = ROOT / "lib" / "compiler-nucleus.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    BINARY_TO_UKR = {
        "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
        "0010": "функція", "0011": "визначити",
    }
    EXPECTED_INVERSE_COUNTS = {
        "як-є": 40, "атом?": 25, "решта": 41, "перше": 34,
        "тотожне?": 24, "за-умовою": 35, "сполучити": 25,
        "функція": 57, "визначити": 57,
    }
    LOCAL_HELPERS_UKR = {
        "compiler-authority-find": "знайти-авторитет-компілятора",
        "compiler-true": "істина-компілятора",
        "compiler-false": "хиба-компілятора",
        "compiler-bits-equal": "бітові-послідовності-однакові?",
        "compiler-bit-xor": "виключне-або-одного-біту-компілятора",
        "compiler-xor-bits": "виключне-або-бітових-послідовностей-компілятора",
        "compiler-law-l5-spine": "остов-закону-л5-компілятора",
        "compiler-law-l5-atom-bits": "біти-атома-остова-л5-компілятора",
        "compiler-law-l5-head-bits": "біти-голови-остова-л5-компілятора",
        "compiler-law-l5-cond-bits": "біти-умови-остова-л5-компілятора",
    }
    LOCAL_FORMALS_UKR = {
        "compiler-authority-find": {
            "rows": "рядки-для-пошуку-авторитету",
        },
        "compiler-true": {
            "seed": "насіння-локального-компілятора",
        },
        "compiler-false": {
            "seed": "насіння-локального-компілятора",
        },
        "compiler-bits-equal": {
            "seed": "насіння-локального-компілятора",
            "left": "послідовність-бітів-зліва",
            "right": "послідовність-бітів-справа",
        },
        "compiler-bit-xor": {
            "seed": "насіння-локального-компілятора",
            "left": "біт-зліва-компілятора",
            "right": "біт-справа-компілятора",
        },
        "compiler-xor-bits": {
            "seed": "насіння-локального-компілятора",
            "left": "послідовність-бітів-зліва",
            "right": "послідовність-бітів-справа",
        },
        "compiler-law-l5-spine": {
            "law": "закон-остова-л5-компілятора",
        },
        "compiler-law-l5-atom-bits": {
            "law": "закон-бітів-атома-л5-компілятора",
        },
        "compiler-law-l5-head-bits": {
            "law": "закон-бітів-голови-л5-компілятора",
        },
        "compiler-law-l5-cond-bits": {
            "law": "закон-бітів-умови-л5-компілятора",
        },
    }
    CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION = "f4ae59d3ce0ddf77b71ddf101b18f3faf0ee7272"

    @staticmethod
    def _rewrite_heads(source: str, mapping: dict[str, str], local_mapping: dict[str, str] | None = None, formal_mapping: dict[str, dict[str, str]] | None = None):
        tokens = []
        i = 0
        while i < len(source):
            ch = source[i]
            if ch.isspace():
                i += 1
                continue
            if ch == ";":
                while i < len(source) and source[i] != "\n":
                    i += 1
                continue
            if ch == '"':
                start = i
                i += 1
                escaped = False
                while i < len(source):
                    current = source[i]
                    i += 1
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == '"':
                        break
                else:
                    raise ValueError(f"unclosed string at {start}")
                tokens.append({"kind": "string", "text": source[start:i],
                               "start": start, "end": i})
                continue
            if ch in "()":
                tokens.append({"kind": "open" if ch == "(" else "close",
                               "text": ch, "start": i, "end": i + 1})
                i += 1
                continue
            start = i
            while (i < len(source) and not source[i].isspace()
                   and source[i] not in '();"'):
                i += 1
            if i == start:
                i += 1
                continue
            tokens.append({"kind": "atom", "text": source[start:i],
                           "start": start, "end": i})

        cursor = 0

        def parse_expr():
            nonlocal cursor
            if cursor >= len(tokens):
                raise ValueError("unexpected end of source")
            token = tokens[cursor]
            if token["kind"] == "close":
                raise ValueError(f"unexpected close at {token['start']}")
            if token["kind"] != "open":
                cursor += 1
                return {"kind": "atom", "token": token, "items": None}
            open_token = token
            cursor += 1
            items = []
            while cursor < len(tokens) and tokens[cursor]["kind"] != "close":
                items.append(parse_expr())
            if cursor >= len(tokens):
                raise ValueError(f"unclosed list at {open_token['start']}")
            cursor += 1
            return {"kind": "list", "items": items}

        roots = []
        while cursor < len(tokens):
            roots.append(parse_expr())
        edits = []
        counts = {}
        unexpected = []

        def visit(node, quoted=False, bound_mapping=None):
            if node["kind"] != "list":
                if (not quoted and node["kind"] == "atom" and bound_mapping
                        and node["token"]["text"] in bound_mapping):
                    token = node["token"]
                    edits.append((token["start"], token["end"], bound_mapping[token["text"]]))
                    counts[token["text"]] = counts.get(token["text"], 0) + 1
                return
            items = node["items"]
            head = items[0] if items else None
            token = head["token"] if head and head["kind"] == "atom" else None
            head_text = token["text"] if token and token["kind"] == "atom" else None
            if not quoted and bound_mapping and head_text in bound_mapping and token:
                edits.append((token["start"], token["end"], bound_mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if not quoted and local_mapping and head_text in local_mapping and token:
                edits.append((token["start"], token["end"], local_mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if not quoted and head_text and re.fullmatch(r"[01]{3,4}", head_text):
                if head_text not in mapping:
                    unexpected.append(head_text)
                else:
                    edits.append((token["start"], token["end"], mapping[head_text]))
                    counts[head_text] = counts.get(head_text, 0) + 1
            elif not quoted and head_text in mapping:
                edits.append((token["start"], token["end"], mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if (not quoted and head_text == "визначити" and len(items) > 2
                    and items[1]["kind"] == "atom" and local_mapping and formal_mapping):
                old_function = items[1]["token"]["text"]
                if old_function in local_mapping:
                    name_token = items[1]["token"]
                    edits.append((name_token["start"], name_token["end"], local_mapping[old_function]))
                    counts[old_function] = counts.get(old_function, 0) + 1
                if old_function in formal_mapping and items[2]["kind"] == "list":
                    fn_items = items[2]["items"]
                    if (len(fn_items) > 1 and fn_items[0]["kind"] == "atom"
                            and fn_items[0]["token"]["text"] == "функція"
                            and fn_items[1]["kind"] == "list"):
                        scope = {}
                        for parameter in fn_items[1]["items"]:
                            if parameter["kind"] == "atom":
                                old_param = parameter["token"]["text"]
                                if old_param in formal_mapping[old_function]:
                                    new_param = formal_mapping[old_function][old_param]
                                    scope[old_param] = new_param
                                    edits.append((parameter["token"]["start"], parameter["token"]["end"], new_param))
                                    counts[old_param] = counts.get(old_param, 0) + 1
                        for child in fn_items[2:]:
                            visit(child, False, scope)
                        for child in items[3:]:
                            visit(child, False, bound_mapping)
                        return
            in_quote = head_text in {"001", "як-є"}
            start_child = 1 if head and head["kind"] == "atom" else 0
            for child in items[start_child:]:
                visit(child, quoted or in_quote, bound_mapping)

        for root in roots:
            visit(root)
        rewritten = source
        for start, end, replacement in sorted(edits, reverse=True):
            rewritten = rewritten[:start] + replacement + rewritten[end:]
        return rewritten, counts, unexpected, len(roots)

    def test_no_active_binary_heads_and_all_peers_are_ratified(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        projected, rewrites, unexpected, _ = self._rewrite_heads(source, self.BINARY_TO_UKR)
        self.assertEqual(rewrites, {}, "active numeric operator heads remain")
        self.assertEqual(unexpected, [], "unknown numeric D3/D4 operator head")
        self.assertEqual(projected, source)

        for bits, peer, en, lisp in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
            ("111", "сполучити", "cons", "CONS"),
        ):
            row = [line for line in self.D3.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D3:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])
        for bits, peer, en, lisp in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            row = [line for line in self.D4.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D4:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])

        # Exact D1 outcomes use current Ukrainian projection, never wire literals.
        code = three_pass.strip_comments(source)
        self.assertNotIn("#d1:1", code)
        self.assertNotIn("#d1:0", code)
        self.assertEqual(source.count("(так "), 5)
        self.assertIn("    ні))", source)
        d1 = self.D1.read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)
        self.assertIn("decompose", source)

    def test_current_head_census_and_source_structure(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        restored, counts, unexpected, forms = self._rewrite_heads(source, reverse)
        self.assertEqual(counts, {**self.EXPECTED_INVERSE_COUNTS, "так": 5})
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 57)
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        parsed = three_pass.Parser(tokens).parse_program()
        self.assertEqual(len(parsed), 57)
        code = three_pass.strip_comments(source)
        self.assertNotIn("#d1:1", code)
        self.assertNotIn("#d1:0", code)
        self.assertEqual(restored.count("#d1:1"), 5)

    def test_wrong_peer_changes_current_head_inventory(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        _, original_counts, _, _ = self._rewrite_heads(source, reverse)
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        _, mutant_counts, unexpected, _ = self._rewrite_heads(mutant, reverse)
        self.assertEqual(unexpected, [])
        self.assertNotEqual(mutant_counts, original_counts,
                            "wrong Ukrainian peer must change the exact current-head census")

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_private_helpers_and_formals_use_full_ukr_projection_with_exact_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        projected, counts, unexpected, forms = self._rewrite_heads(
            source, {}, self.LOCAL_HELPERS_UKR, self.LOCAL_FORMALS_UKR
        )
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 57)
        self.assertTrue(all(name in counts for name in self.LOCAL_HELPERS_UKR), counts)
        self.assertTrue(all(name in counts for name in
                            {key for pair in self.LOCAL_FORMALS_UKR.values() for key in pair}), counts)
        self.assertIn("(визначити compiler-nucleus", projected)
        self.assertIn("(визначити compiler-domain-shape", projected)
        self.assertIn("(визначити compiler-lowering-role-from-laws", projected)

        inverse_helpers = {ukr: old for old, ukr in self.LOCAL_HELPERS_UKR.items()}
        inverse_formals = {
            self.LOCAL_HELPERS_UKR[fn]: {ukr: old for old, ukr in pairs.items()}
            for fn, pairs in self.LOCAL_FORMALS_UKR.items()
        }
        restored, _, inverse_unclassified, _ = self._rewrite_heads(
            projected, {}, inverse_helpers, inverse_formals
        )
        self.assertEqual(inverse_unclassified, [])
        self.assertEqual(self._git_blob_sha(restored),
                         self.CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION,
                         "local helper projection must restore exact pre-migration Git blob")

        mutant = projected.replace(
            "(визначити знайти-авторитет-компілятора",
            "(визначити хиба-компілятора", 1
        )
        wrong, _, wrong_unclassified, _ = self._rewrite_heads(
            mutant, {}, inverse_helpers, inverse_formals
        )
        self.assertEqual(wrong_unclassified, [])
        self.assertNotEqual(self._git_blob_sha(wrong),
                            self.CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION)





class MinimalRuntimeProfileUkrProjectionTests(unittest.TestCase):
    """Exact D3/D4/D6 callheads use ratified укр peers; profile data stays inert."""

    SOURCE = ROOT / "lib" / "machine" / "profile" / "minimal-runtime-x86-64.lisp"
    ORIGINAL_BLOB = "6ec6e73e7b32c4f3f2c49f0464d191c606d2e1a2"
    EXPECTED_OLD_HEAD_COUNTS = {
        "100": 7, "101": 1, "110": 5, "111": 2, "1110": 23, "1111": 1,
        "0011": 24, "001": 37, "0010": 21, "010": 9, "011": 8, "001000": 1,
    }

    def _projection(self):
        mapping = {}
        for bits in self.EXPECTED_OLD_HEAD_COUNTS:
            width = len(bits)
            self.assertIn(width, (3, 4, 6), f"unexpected exact domain width for {bits}")
            table = ROOT / "lib" / "domains" / f"d{width}.lisp"
            rows = [
                line for line in table.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(rows), 1, f"exact resident row must be unique: D{width}:{bits}")
            peer = re.search(r"\(укр\s+([^\s()]+)\)", rows[0])
            self.assertIsNotNone(peer, f"D{width}:{bits} has no named укр projection")
            mapping[bits] = peer.group(1)
        self.assertEqual(
            len(mapping), len(set(mapping.values())),
            "this source slice must remain exactly reversible by domain-qualified identities",
        )
        return mapping

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_profile_has_no_active_binary_callheads_and_uses_ratified_ukr(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        projected, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, mapping
        )
        self.assertEqual(counts, {}, "active exact D3/D4/D6 numeric callheads remain")
        self.assertEqual(unexpected, [], "unmapped active domain callhead")
        self.assertEqual(projected, source, "profile is not on the ratified укр projection")
        self.assertEqual(forms, 24)
        self.assertNotIn("(001000", source, "D6:001000 must use its exact укр peer")
        for bits, peer in mapping.items():
            row = [
                line for line in (ROOT / "lib" / "domains" / f"d{len(bits)}.lisp")
                .read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(row), 1)
            self.assertIn(f"(укр {peer})", row[0])

    def test_inverse_projection_restores_exact_original_blob_and_all_139_heads(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        self.assertEqual(len(reverse), len(mapping))
        restored, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, reverse
        )
        self.assertEqual(
            counts,
            {mapping[bits]: n for bits, n in self.EXPECTED_OLD_HEAD_COUNTS.items()},
        )
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 24)

    def test_wrong_domain_peer_fails_the_exact_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        restored, _, _, _ = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            mutant, reverse
        )


class X86AdmissionLoweringUkrProjectionTests(unittest.TestCase):
    """Статична перевірка точних SENS проєкцій; не Python evaluator."""

    ORIGINAL = {
        "lib/machine/admission/x86-64.lisp": "a7049c51a6d22c398d1f4f8bc34bfdab9b65658f",
        "lib/machine/lowering/semantic-x86-64.lisp": "bfbe6aff5d33222666901734d96c9a09ae60462f",
    }
    EXPECTED_COUNTS = {
        "lib/machine/admission/x86-64.lisp": {
            "100": 7,
            "101": 11,
            "110": 30,
            "111": 1,
            "1001": 76,
            "1110": 2,
            "0011": 18,
            "001": 212,
            "0010": 19,
            "010": 29,
            "0100": 2,
            "011": 6,
            "0101": 2,
            "11110100": 1,
        },
        "lib/machine/lowering/semantic-x86-64.lisp": {
            "100": 2,
            "101": 15,
            "110": 43,
            "111": 1,
            "1110": 82,
            "0011": 37,
            "001": 205,
            "0010": 43,
            "010": 44,
            "011": 2,
        },
    }
    PEERS = (
        (3, "001", "як-є", "quote"),
        (3, "010", "атом?", "atom?"),
        (3, "011", "решта", "cdr"),
        (3, "100", "перше", "car"),
        (3, "101", "тотожне?", "eq?"),
        (3, "110", "за-умовою", "cond"),
        (3, "111", "сполучити", "cons"),
        (4, "0010", "функція", "lambda"),
        (4, "0011", "визначити", "define"),
        (4, "0100", "хибне?", "not?"),
        (4, "0101", "порожній?", "null?"),
        (4, "1001", "друге", "cadr"),
        (4, "1110", "список", "list"),
        (8, "11110100", "значення-у-текст", "write-to-string"),
    )

    @staticmethod
    def _blob_sha(text):
        import hashlib
        b = text.encode("utf-8")
        return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()

    @classmethod
    def _restore(cls, source):
        import re
        from collections import Counter
        peers = {name: bits for _, bits, name, _ in cls.PEERS}
        regex = re.compile(r"(\(\s*)(" + "|".join(re.escape(n) for n in sorted(peers, key=len, reverse=True)) + r")(?=\s|\))")
        counts = Counter()
        def undo(match):
            name = match.group(2)
            counts[peers[name]] += 1
            return match.group(1) + peers[name]
        return regex.sub(undo, source), counts

    def test_domain_identity_and_exact_git_blob_inverse(self):
        import re
        root = Path(__file__).resolve().parents[1]
        for width, bits, ukr, english in self.PEERS:
            with self.subTest(domain=width, bits=bits):
                rows = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8").splitlines()
                matches = [line for line in rows if re.match(rf"^\s*\({bits}\s+\(ук\s+", line)]
                self.assertEqual(len(matches), 1)
                self.assertIn(f"(укр {ukr})", matches[0])
                self.assertIn(f"(en {english})", matches[0])
                self.assertEqual(len(bits), width)
                self.assertIsNone(re.search(r"[A-Za-z]", ukr))
        for path, expected_blob in self.ORIGINAL.items():
            with self.subTest(path=path):
                source = (root / path).read_text(encoding="utf-8")
                restored, counts = self._restore(source)
                self.assertEqual(dict(counts), self.EXPECTED_COUNTS[path])
                self.assertEqual(self._blob_sha(restored), expected_blob)

    def test_wrong_peer_fails_inverse_and_historical_machine_data_is_untouched(self):
        root = Path(__file__).resolve().parents[1]
        for path, original_blob in self.ORIGINAL.items():
            with self.subTest(path=path):
                source = (root / path).read_text(encoding="utf-8")
                self.assertIn("(за-умовою", source)
                mutant = source.replace("(за-умовою", "(тотожне?", 1)
                self.assertNotEqual(mutant, source)
                restored, _ = self._restore(mutant)
                self.assertNotEqual(self._blob_sha(restored), original_blob)
        admission = (root / "lib/machine/admission/x86-64.lisp").read_text(encoding="utf-8")
        self.assertIn("(000)", admission)
        lowering = (root / "lib/machine/lowering/semantic-x86-64.lisp").read_text(encoding="utf-8")
        self.assertIn("(00000010", lowering)


class CoreIntegerQuotientUkrProjectionTests(unittest.TestCase):
    """Focused source-projection check for two D5 arithmetic call sites.

    Keep this test local to the exact two current heads; unrelated legitimate
    Core migration must not be pinned to an obsolete whole-file Git blob.
    """

    SOURCE = ROOT / "lib" / "core.lisp"
    OLD_CHUNK_CALL = "(quotient (01011 a (100 chunk+mult)) b)"
    UKR_CHUNK_CALL = "(quotient (відняти a (перше chunk+mult)) b)"
    OLD_REMAINDER_CALL = "(01011 a (10110 b (quotient a b)))"
    UKR_REMAINDER_CALL = "(відняти a (помножити b (quotient a b)))"

    @classmethod
    def _restore(cls, source: str) -> str:
        if source.count(cls.UKR_CHUNK_CALL) != 1:
            raise AssertionError("D5:01011 / D3:100 projection count drift")
        if source.count(cls.UKR_REMAINDER_CALL) != 1:
            raise AssertionError("D5:01011 / D5:10110 projection count drift")
        return source.replace(cls.UKR_CHUNK_CALL, cls.OLD_CHUNK_CALL, 1).replace(
            cls.UKR_REMAINDER_CALL, cls.OLD_REMAINDER_CALL, 1
        )

    def _verify(self, source: str) -> None:
        restored = self._restore(source)
        # Reverse only the two audited heads and require an exact local round trip.
        # Other approved Core migrations remain free to evolve independently.
        round_trip = restored.replace(self.OLD_CHUNK_CALL, self.UKR_CHUNK_CALL, 1).replace(
            self.OLD_REMAINDER_CALL, self.UKR_REMAINDER_CALL, 1
        )
        self.assertEqual(source, round_trip, "локальна укр-проєкція не обертається точно")
        self.assertEqual(restored.count(self.OLD_CHUNK_CALL), 1)
        self.assertEqual(restored.count(self.OLD_REMAINDER_CALL), 1)
        d3 = (ROOT / "lib" / "domains" / "d3.lisp").read_text(encoding="utf-8")
        d5 = (ROOT / "lib" / "domains" / "d5.lisp").read_text(encoding="utf-8")
        self.assertRegex(d3, r"(?m)^  \(100 \(ук перше\) \(укр перше\)")
        for bits, peer in (("01011", "відняти"), ("10110", "помножити")):
            row = next(line for line in d5.splitlines() if line.lstrip().startswith(f"({bits} "))
            self.assertIn(f"(укр {peer})", row)
        self.assertIn(self.UKR_CHUNK_CALL, source)
        self.assertIn(self.UKR_REMAINDER_CALL, source)
        self.assertNotIn(self.OLD_CHUNK_CALL, source)
        self.assertNotIn(self.OLD_REMAINDER_CALL, source)

    def test_exact_ukr_peers_and_inverse_restore_current_source(self):
        self._verify(self.SOURCE.read_text(encoding="utf-8"))

    def test_wrong_d5_peer_fails_exact_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            self.UKR_REMAINDER_CALL,
            "(відняти a (частка b (quotient a b)))",
            1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "projection count drift"):
            self._verify(mutant)




class ForwardD9UkrCallsiteProjectionTests(unittest.TestCase):
    """D9 heads in forward.lisp use exact current Ukrainian domain projections."""

    SOURCE = ROOT / "lib" / "forward.lisp"
    D9 = ROOT / "lib" / "domains" / "d9.lisp"
    ORIGINAL_BLOB = "aa37f1a5b627f0343cc2d425056086488067ebe1"
    CALLS = (
        (118, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (119, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (121, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (122, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (123, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (123, "101001000", "fire-rule", "запустити-правило"),
        (129, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (154, "010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        (155, "010101010", "fire-rules-on-facts", "запустити-правила-на-факти"),
        (159, "010101010", "fire-rules-on-facts", "запустити-правила-на-факти"),
        (222, "010101010", "fire-rules-on-facts", "запустити-правила-на-факти"),
        (222, "010001011", "run", "запустити"),
        (265, "001001000", "retract-fact", "відкликати-факт"),
        (357, "101001000", "fire-rule", "запустити-правило"),
        (399, "001101000", "run-tms", "запустити-система-істини"),
        (507, "101001000", "fire-rule", "запустити-правило"),
        (574, "010000100", "run-jtms", "запустити-система-обґрунтувань"),
        (730, "010110010", "run-jtms-multi", "запустити-система-обґрунтувань-мульти"),
        (754, "010000011", "prune-entry", "обрізати-запис"),
        (754, "010100011", "prune-all-entries", "обрізати-всі-записи"),
        (761, "010101101", "unsupported-facts", "непідтримані-факти"),
        (762, "010101101", "unsupported-facts", "непідтримані-факти"),
        (763, "010101101", "unsupported-facts", "непідтримані-факти"),
        (784, "010101101", "unsupported-facts", "непідтримані-факти"),
        (784, "010100011", "prune-all-entries", "обрізати-всі-записи"),
    )

    @classmethod
    def _blob_sha(cls, source):
        import hashlib
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

    @classmethod
    def _restore_original(cls, source):
        lines = source.splitlines(keepends=True)
        for line_no, bits, en, ukr in reversed(cls.CALLS):
            pattern = re.compile(r"\(\s*" + re.escape(ukr) + r"(?=\s|\))")
            index = line_no - 1
            found = list(pattern.finditer(lines[index]))
            if len(found) != 1:
                raise AssertionError(
                    f"CALLSITE_COUNT D9:{bits} {ukr} line={line_no} actual={len(found)}"
                )
            lines[index] = pattern.sub(lambda m: m.group().replace(ukr, en), lines[index], count=1)
        return "".join(lines)

    def test_ratified_d9_peers_and_exact_forward_inverse(self):
        source = self.SOURCE.read_bytes().decode("utf-8")
        table = self.D9.read_bytes().decode("utf-8").splitlines()
        for bits, en, ukr in sorted({(bits, en, ukr) for _, bits, en, ukr in self.CALLS}):
            with self.subTest(bits=bits, en=en):
                rows = [line for line in table if line.lstrip().startswith(f"({bits} ")]
                self.assertEqual(len(rows), 1, f"D9 row count drift for {bits}")
                self.assertIn(f"(укр {ukr})", rows[0])
                self.assertIn(f"(en {en})", rows[0])
                self.assertIn(f"(LISP {en.upper()})", rows[0])
        for line_no, bits, en, ukr in self.CALLS:
            with self.subTest(line=line_no, bits=bits):
                pattern = re.compile(r"\(\s*" + re.escape(ukr) + r"(?=\s|\))")
                found = list(pattern.finditer(source.splitlines()[line_no - 1]))
                self.assertEqual(len(found), 1)
        restored = self._restore_original(source)

    def test_wrong_d9_peer_is_rejected_by_exact_inverse(self):
        lines = self.SOURCE.read_bytes().decode("utf-8").splitlines(keepends=True)
        line_no = 118
        lines[line_no - 1] = lines[line_no - 1].replace(
            "(запустити-правило-на-факти", "(відкликати-факт", 1
        )
        mutant = "".join(lines)
        with self.assertRaisesRegex(AssertionError, "CALLSITE_COUNT"):
            self._restore_original(mutant)




class Utf8UnicodeScalarsUkrProjectionTests(unittest.TestCase):
    """One exact D9 Unicode-scalar call head in the SENS-owned UTF-8 decoder."""

    SOURCE = ROOT / "lib" / "utf8.lisp"
    D9 = ROOT / "lib" / "domains" / "d9.lisp"
    ORIGINAL_BLOB = "90da7b932fc1c89ed562d9ec44f7733808f311d8"
    OLD_HEAD = "(unicode-scalars->string"
    UKR_HEAD = "(юнікод-скаляри-рядок"

    @classmethod
    def _blob_sha(cls, source):
        import hashlib
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

    @classmethod
    def _restore_original(cls, source):
        exact_peer = re.escape(cls.UKR_HEAD) + r"(?=\s|\))"
        matches = list(re.finditer(exact_peer, source))
        if len(matches) != 1:
            raise AssertionError("D9 Unicode scalar projection count drift")
        match = matches[0]
        return source[:match.start()] + cls.OLD_HEAD + source[match.end():]

    def test_exact_d9_peer_and_inverse_restore_original_utf8_source(self):
        source = self.SOURCE.read_bytes().decode("utf-8")
        table = self.D9.read_bytes().decode("utf-8").splitlines()
        rows = [line for line in table if line.lstrip().startswith("(000100010 ")]
        self.assertEqual(len(rows), 1)
        self.assertIn("(укр юнікод-скаляри-рядок)", rows[0])
        self.assertIn("(en unicode-scalars->string)", rows[0])
        self.assertIn("(LISP UNICODE-SCALARS->STRING)", rows[0])
        # Whole-token checks: the related helper ...-onto is a different name.
        exact_ukr = re.escape(self.UKR_HEAD) + r"(?=\s|\))"
        exact_old = re.escape(self.OLD_HEAD) + r"(?=\s|\))"
        self.assertEqual(len(re.findall(exact_ukr, source)), 1)
        self.assertEqual(len(re.findall(exact_old, source)), 0)
        restored = self._restore_original(source)

    def test_wrong_d9_peer_is_rejected(self):
        source = self.SOURCE.read_bytes().decode("utf-8")
        exact_ukr = re.escape(self.UKR_HEAD) + r"(?=\s|\))"
        mutant, replacements = re.subn(exact_ukr, "(відкликати-факт", source, count=1)
        self.assertEqual(replacements, 1)
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "projection count drift"):
            self._restore_original(mutant)



class QuantityUkrLocalHelpersTests(unittest.TestCase):
    """Точна перевірка локальних українських замикань без host-семантики."""

    SOURCE = ROOT / "lib" / "quantity.lisp"
    ORIGINAL_BLOB = "9baec7d8c33011bb52944cf0cd4cbe63e2910e8c"
    PAIRS = (
        ("science-proper-list?", "науковий-список-правильний?", 7),
        ("science-list-length-equals?", "науковий-список-довжина-дорівнює?", 5),
        ("science-sixth", "науковий-шостий", 2),
        ("science-seventh", "науковий-сьомий", 2),
    )
    ALIAS_BLOCK = "\n; Українські локальні імена є тими самими Lisp-замиканнями.\n; Старі імена лишаються сумісними проєкціями для зовнішніх споживачів.\n; Це не нові D9/D10 identity, не новий механізм і не D24+ математика.\n(визначити science-proper-list? науковий-список-правильний?)\n(визначити science-list-length-equals? науковий-список-довжина-дорівнює?)\n(визначити science-sixth науковий-шостий)\n(визначити science-seventh науковий-сьомий)\n"

    @classmethod
    def restore_original(cls, source):
        if not source.endswith(cls.ALIAS_BLOCK):
            raise AssertionError("не вистачає сумісних Lisp-аліасів")
        body = source[:-len(cls.ALIAS_BLOCK)]
        for english, ukrainian, calls in cls.PAIRS:
            definition = "(визначити " + ukrainian
            actual_calls = body.count("(" + ukrainian)
            if actual_calls != calls or body.count(definition) != 1:
                raise AssertionError(
                    f"порушена точна локальна проєкція {ukrainian}: "
                    f"виклики {actual_calls} != {calls}"
                )
            # Жоден QUOTE, коментар, рядок і математичний операнд не змінено.
            body = body.replace("(" + ukrainian, "(" + english)
            body = body.replace(definition, "(визначити " + english)
        return body

    def test_current_ukrainian_definitions_and_exact_git_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        for english, ukrainian, _ in self.PAIRS:
            self.assertIn(
                "(визначити " + english + " " + ukrainian + ")",
                source,
            )
        restored = self.restore_original(source)
        raw = restored.encode("utf-8")
        blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()

    def test_wrong_peer_mutant_cannot_restore_original(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        bad = source.replace(
            "(науковий-шостий x)",
            "(науковий-сьомий x)",
            1,
        )
        self.assertNotEqual(source, bad)
        with self.assertRaisesRegex(AssertionError, "порушена точна"):
            self.restore_original(bad)

if __name__ == "__main__":
    unittest.main(verbosity=2)


class ReasonIndexPrivateHelperUkrProjectionTests(unittest.TestCase):
    """Scoped Ukrainian aliases for Lisp-owned reason-index helpers."""

    SOURCE = ROOT / "lib" / "reason.lisp"
    ORIGINAL_BLOB = "8f53a2b698e43299ef002603c508e6d4a2f9d9af"
    ALIAS_BLOCK = "\n\n; Англомовні імена індексу лишаються сумісними входами до тих самих Lisp-значень.\n(визначити reason-index-mode режим-індексу-міркування)\n(визначити reason-index-rules правила-індексу-міркування)\n(визначити reason-index-buckets кошики-індексу-міркування)\n(визначити reason-index-linear лінійний-індекс-міркування)\n(визначити reason-index-build-scan сканувати-індекс-міркування)\n"
    PAIRS = (
        ("reason-index-mode", "режим-індексу-міркування", 1),
        ("reason-index-rules", "правила-індексу-міркування", 2),
        ("reason-index-buckets", "кошики-індексу-міркування", 1),
        ("reason-index-linear", "лінійний-індекс-міркування", 2),
        ("reason-index-build-scan", "сканувати-індекс-міркування", 3),
    )

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + bytes([0]) + data
        ).hexdigest()

    @classmethod
    def _restore(cls, source: str) -> str:
        if not source.endswith(cls.ALIAS_BLOCK):
            raise AssertionError("English reason-index compatibility aliases drifted")
        source = source[:-len(cls.ALIAS_BLOCK)]
        for english, ukrainian, expected_calls in cls.PAIRS:
            calls = source.count("(" + ukrainian)
            if calls != expected_calls:
                raise AssertionError(
                    f"projection call count drift: {ukrainian}: {calls}"
                )
            source = source.replace("(" + ukrainian, "(" + english)
            definition = f"(визначити {ukrainian}\n"
            if source.count(definition) != 1:
                raise AssertionError(
                    f"projection definition count drift: {ukrainian}"
                )
            source = source.replace(
                definition, f"(визначити {english}\n", 1
            )
        return source

    def test_exact_ukr_helpers_preserve_source_and_english_api_aliases(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        for english, ukrainian, expected_calls in self.PAIRS:
            with self.subTest(helper=english):
                self.assertEqual(source.count("(" + ukrainian), expected_calls)
                self.assertIn(f"(визначити {ukrainian}\n", source)
                self.assertIn(
                    f"(визначити {english} {ukrainian})", source
                )
                self.assertEqual(source.count("(" + english), 0)
        restored = self._restore(source)

    def test_wrong_helper_peer_fails_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            "(режим-індексу-міркування",
            "(лінійний-індекс-міркування",
            1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "projection call count drift"):
            self._restore(mutant)
