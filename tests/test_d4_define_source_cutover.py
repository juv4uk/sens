#!/usr/bin/env python3
"""Незалежний доказ видалення SID8 з арності DEFINE у головному Rust Core."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "crates/sens/src/eval/special_forms/core.rs"
ORIGINAL_SHA = "8e39078056c1a1a6b8c31eaef9a1b1526ffc5be3"
OLD_IMPORT = "use crate::{Environment, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};"
NEW_IMPORT = "use crate::{Bit4, CoreD4, CoreDomainIdentity, Environment, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};"
OLD_ARITY = "    exact_sens_arity(crate::sens!(00001011), arguments, 2, span)?;"
NEW_ARITY = """    // DEFINE — точна D4:0011, а не історична W8:00001011.
    let identity = CoreDomainIdentity::D4(
        CoreD4::from_word(Bit4::new(0b0011).expect("ратифікована координата D4 DEFINE")),
    );
    exact_domain_arity(identity, arguments, 2, span)?;"""
FN_START = "/// Перевірка арності лише за точною доменною координатою."
FN_END = "/// Arity check for a SENS form inside the core:"
TEST_START = "\n#[cfg(test)]\nmod exact_d4_define_arity_tests {"


def original() -> str:
    raw = subprocess.run(
        ["git", "cat-file", "blob", ORIGINAL_SHA],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    expected = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if expected != ORIGINAL_SHA:
        raise ValueError("PIN_DRIFT: старий source blob змінився")
    return raw.decode("utf-8")


def check_source(source: str) -> None:
    if source.count(TEST_START) != 1:
        raise ValueError("TEST_GUARD_BLOCK: відсутні unit-тести D4")
    implementation, tests = source.split(TEST_START, 1)
    for required in (
        "fn визначення_діагностує_тільки_точну_d4_координату()",
        "fn правильна_арність_і_неоднакові_ширини_доменів()",
        'error.message.contains("D4:0011")',
        'error.message.contains("D3:011")',
        'exact_domain_arity(d4, &two, 2, Span::default()).is_ok()',
    ):
        if required not in tests:
            raise ValueError("TEST_GUARD_BLOCK: втрачено позитивний/негативний доказ")
    if not tests.rstrip().endswith("}"):
        raise ValueError("TEST_GUARD_BLOCK: обірвано тестовий модуль")

    if implementation.count(FN_START) != 1 or implementation.count(FN_END) != 1:
        raise ValueError("DOMAIN_ARITY_BLOCK: втрачено типізовану перевірку")
    function_start = implementation.index(FN_START)
    function_end = implementation.index(FN_END)
    function = implementation[function_start:function_end]
    for required in (
        "identity: CoreDomainIdentity",
        "identity.width()",
        "arguments.len() == expected",
        'ErrorKind::Arity',
        '"D{}:{identity}:',
    ):
        if required not in function:
            raise ValueError("DOMAIN_ARITY_BLOCK: доменну перевірку спотворено")
    implementation = implementation[:function_start] + implementation[function_end:]

    if implementation.count(NEW_IMPORT) != 1 or implementation.count(NEW_ARITY) != 1:
        raise ValueError("SOURCE_DELTA_BLOCK: зміни поза точним D4 DEFINE")
    restored = implementation.replace(NEW_IMPORT, OLD_IMPORT).replace(NEW_ARITY, OLD_ARITY)
    if restored != original():
        raise ValueError("SOURCE_DELTA_BLOCK: стороння зміна основного обчислювача")


class D4DefineSourceCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CORE.read_text(encoding="utf-8")

    def test_exact_pinned_source_delta(self):
        check_source(self.source)

    def test_negative_legacy_arity_reintroduction(self):
        changed = self.source.replace(NEW_ARITY, OLD_ARITY, 1)
        self.assertNotEqual(changed, self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            check_source(changed)

    def test_negative_wrong_domain_width(self):
        changed = self.source.replace("Bit4::new(0b0011)", "Bit4::new(0b0001)", 1)
        self.assertNotEqual(changed, self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            check_source(changed)

    def test_negative_extra_behavior_change(self):
        changed = self.source.replace("Ok(value)", "Ok(Value::Nil)", 1)
        self.assertNotEqual(changed, self.source)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            check_source(changed)


if __name__ == "__main__":
    unittest.main()
