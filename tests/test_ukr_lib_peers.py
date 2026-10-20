"""Статична перевірка чинної української проєкції SENS.

Покриття: narrate, time, reason, utf8, meta-eval-mutual, knowledge, forward,
clips-import, meta-eval, world, lisp-fs, linter, unify, yantra, repl-core,
unify-observe, surface/uk-{docs,inventory,sa-coverage} та scripts/{build-inventory,
check-semantic-registry, check-trilingual-surface, profile-read-file-stages,
profile-proven-byte-readfile-candidate, release, rust-retirement-valve,
rust-retirement-valve-enforce, symbol-table}.

Залишкові міжмовні прив'язки перевіряються за точною таблицею
доменних проєкцій; їхня кількість не є критерієм якості.
Окремо захищаємо виконувані файли від повернення непотрібних
історичних латинських зв'язувань. Перевіряємо структуру вихідного
тексту, не відтворюємо семантику SENS засобами Python.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
ROW = re.compile(r'^\s*\(([01]{1,11})\s+\(ук\s+' + TOKEN + r'\)\s+\(укр\s+' + TOKEN +
                 r'\)\s+\(san\s+' + TOKEN + r'\)\s+\(en\s+' + TOKEN +
                 r'\)\s+\(LISP\s+' + TOKEN + r'\)\s+\(sym\s+' + TOKEN + r'\)\)\s*$')
DEF = re.compile(r'\((?:0011|визначити)\s+([^\s()]+)\s')

MIGRATED = ("lib/time.lisp", "lib/reason.lisp", "lib/utf8.lisp",
            "lib/meta-eval-mutual.lisp", "lib/knowledge.lisp", "lib/narrate.lisp",
            "lib/forward.lisp", "lib/clips-import.lisp", "lib/meta-eval.lisp",
            "lib/world.lisp", "lib/content-store.lisp", "lib/persistent-vector.lisp", "lib/lisp-fs.lisp", "lib/linter.lisp",
            "lib/unify.lisp", "lib/yantra.lisp",
            "lib/repl-core.lisp", "lib/unify-observe.lisp",
            "lib/surface/uk-docs.lisp", "lib/surface/uk-inventory.lisp",
            "lib/surface/uk-sa-coverage.lisp", "scripts/build-inventory.lisp",
            "scripts/check-semantic-registry.lisp", "scripts/check-trilingual-surface.lisp",
            "scripts/profile-read-file-stages.lisp",
            "scripts/profile-proven-byte-readfile-candidate.lisp", "scripts/release.lisp",
            "scripts/rust-retirement-valve.lisp", "scripts/rust-retirement-valve-enforce.lisp",
            "scripts/symbol-table.lisp", "lib/tcp.lisp",
            "scripts/semantic-authority-guard.lisp", "scripts/verify-repo.lisp")


def load_rows():
    rows = {}
    for w in range(1, 12):
        p = ROOT / f"lib/domains/d{w}.lisp"
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                m = ROW.match(line)
                if m:
                    rows.setdefault(f"D{w}:{m.group(1)}", (m.group(2), m.group(3), m.group(5)))
    return rows


ROWS = load_rows()


MARKER = "; opt-in повна укр-поверхня"


def definitions(src: str):
    return {m.group(1) for m in DEF.finditer(src)}


def optin_pairs(src: str):
    """Лише суміжні DEFINE-аліаси після кожного opt-in маркера.

    Зворотні сумісні англомовні імена після переходу справжнього
    DEFINE на повну укр не є новими назвами колонки укр. Тільки
    точні пари EN→укр драбини розпізнаються як зворотні псевдоніми.
    """
    pairs = []
    in_block = False
    for line in src.splitlines():
        if MARKER in line:
            in_block = True
            continue
        if not in_block:
            continue
        match = re.fullmatch(
            r'\s*\(визначити\s+([^\s()]+)\s+([^\s()]+)\)\s*(?:;.*)?',
            line,
        )
        if match:
            left, right = match.group(1), match.group(2)
            # Після переходу самого D10-визначення на укр історичне
            # ім'я лишається DEFINE-посиланням на ту саму функцію.
            # Це зворотний сумісний псевдонім, а не новий укр-резидент.
            reverse_peer = any(
                english == left and full == right
                for _short, full, english in ROWS.values()
            )
            if not reverse_peer:
                pairs.append((left, right))
        else:
            in_block = False
    return pairs


class LibUkrPeerTests(unittest.TestCase):
    def test_remaining_peer_bindings_are_well_formed_and_unique(self):
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            defs = definitions(src)
            for ukr, en in optin_pairs(src):
                # ціль мусить бути коректним іменем; повна укр-назва мусить бути
                # ратифікованою поверхнею драбини (перевіряє наступний тест).
                self.assertTrue(en and not re.search(r"[\s()]", en),
                                f"{rel}: аліас {ukr}->{en} має некоректну ціль")
                self.assertTrue(ukr and not re.search(r"[\s()]", ukr),
                                f"{rel}: аліас {ukr}->{en} має некоректну укр-ціль")
            # жодного дубля
            names = [x.group(1) for x in DEF.finditer(src)]
            self.assertEqual(len(names), len(set(names)), f"{rel}: дубль визначення")

    def test_retired_legacy_tail_bindings_do_not_return(self):
        # Файли з українськими виконуваними іменами не повинні
        # повторно прив'язувати їх до історичної латинської поверхні.
        # Дані протоколу в лапках і таблицях залишаються незмінними.
        retired = {
            "lib/knowledge.lisp": (
                "(визначити check-conflict перевірити-конфлікт?)",
                "(визначити *knowledge-package-version* *версія-пакета-знань*)",
            ),
            "scripts/symbol-table.lisp": (
                "(визначити список LIST)",
                "(визначити значення-у-списку? MEMBER)",
                "(визначити читати-всі READ-ALL)",
                "(визначити текст-передує? STRING<)",
                "(визначити символ-у-текст SYMBOL->STRING)",
                "(визначити символ? SYMBOL?)",
                "(визначити зворот-до reverse-onto)",
            ),
            "scripts/release.lisp": (
                "(визначити відповідь-не ANSWER-NOT)",
                "(визначити список LIST)",
                "(визначити процес-запустити PROCESS-RUN)",
                "(визначити рядок-додати STRING-APPEND)",
            ),
            "lib/surface/uk-inventory.lisp": (
                "(визначити модуль abs)",
                "(визначити атом? atom?)",
                "(визначити довжина-до length-onto)",
            ),
            "lib/surface/uk-docs.lisp": (
                "(визначити порахувати-елементи count)",
            ),
            "lib/surface/uk-sa-coverage.lisp": (
                "(визначити список list)",
                "(визначити вектор vector)",
            ),
        }
        for rel, stale_forms in retired.items():
            src = (ROOT / rel).read_text(encoding="utf-8")
            for form in stale_forms:
                with self.subTest(file=rel, old_binding=form):
                    self.assertNotIn(form, src)

    def test_migrated_names_are_ratified_identities(self):
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            for ukr, en in optin_pairs(src):
                # укр-назва мусить бути ратифікованою поверхнею драбини (en-колонка
                # може мати інше написання, ніж локальне латинське імʼя-ціль)
                hit = [k for k, (_uk, u, _e) in ROWS.items() if u == ukr]
                self.assertTrue(hit, f"{rel}: {ukr} не є ratified укр-назвою драбини")

    def test_legacy_clips_alias_block_is_retired(self):
        """Старі англомовні DEFINE не повертаються як паралельні входи."""
        src = (ROOT / "lib/clips-import.lisp").read_text(encoding="utf-8")
        names = definitions(src)
        old_aliases = {
            "clips-all-asserts?",
            "clips-assert-conclusions",
            "clips-assert-form?",
            "clips-clauses-for-conclusions",
            "clips-convert-template",
            "clips-convert-template-list",
            "clips-convert-vars",
            "clips-deffacts->clauses",
            "clips-defrule->clauses",
            "clips-deftemplate-form?",
            "clips-deftemplate-name",
            "clips-deftemplate-slots",
            "clips-drop-printouts",
            "clips-fact-clause",
            "clips-facts->clauses",
            "clips-form->clauses",
            "clips-import",
            "clips-import-forms",
            "clips-lookup-slot-value",
            "clips-positional-args",
            "clips-printout-form?",
            "clips-rule-preamble-form?",
            "clips-slot-name",
            "clips-slot-names",
            "clips-split-at-arrow",
            "clips-strip-module-prefix",
            "clips-strip-rule-preamble",
            "clips-template-slot-order",
            "clips-templates-from-forms",
            "clips-var-term",
            "clips-var?",
        }
        self.assertTrue(old_aliases, "негативний список мусить бути непорожнім")
        self.assertFalse(old_aliases & names,
                         f"повернулися старі аліаси: {sorted(old_aliases & names)}")
        self.assertNotIn(MARKER, src)
        for live in ("кліпс-імпорт", "кліпс-імпорт-форми",
                     "кліпс-визначити-правило-клаузи",
                     "усі-твердження-кліпс?", "кліпс-шаблони-з-форми"):
            self.assertIn("(визначити " + live, src)
        # Сторонні ключові слова КЛІПС -- лише цитовані дані.
        self.assertIn("(як-є deftemplate)", src)
        self.assertIn("(як-є deffacts)", src)

    def test_native_clips_calls_use_full_ukrainian_surface(self):
        """Код випробувань використовує первинні голови, а не clips-* псевдоніми.

        Зовнішні цитовані форми CLIPS (defrule, deffacts, slot, assert)
        лишаються даними. Python тут НЕ імітує виконання SENS.
        """
        source = (ROOT / "crates/sens/tests/clips_import.rs").read_text(
            encoding="utf-8")
        old_heads = (
            "clips-import", "clips-split-at-arrow", "clips-all-asserts?",
            "clips-assert-conclusions", "clips-strip-rule-preamble",
            "clips-convert-vars", "clips-convert-template-list",
            "clips-defrule->clauses", "clips-lookup-slot-value",
            "quote", "def", "defmodule", "forward-in", "reason-in",
        )
        for old in old_heads:
            with self.subTest(old=old):
                self.assertNotRegex(
                    source, r"\(" + re.escape(old) + r"(?=[\s)])"
                )
        for current in (
            "як-є", "визначити", "визначити-модуль",
            "вперед-у", "міркувати-у", "кліпс-імпорт",
            "розділити-правило-кліпс", "кліпс-визначити-правило-клаузи",
            "знайти-значення-слота-кліпс",
        ):
            with self.subTest(current=current):
                self.assertIn("(" + current + " ", source)

    def test_numeric_heads_gone_from_the_alias_block(self):
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            for line in src.splitlines():
                if line.startswith("(визначити") and re.search(r"[а-яїієґ]", line):
                    self.assertNotRegex(line, r"^\(0011\b",
                                        f"{rel}: новий аліас мусить вживати визначити")


if __name__ == "__main__":
    unittest.main(verbosity=2)
