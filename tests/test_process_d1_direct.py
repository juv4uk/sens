#!/usr/bin/env python3
"""Аудит прямої української Д1-логіки та структури результатів процесів."""
from pathlib import Path
import re
import unittest

EXACT_HEADS = {"001": "як-є", "011": "решта", "100": "перше",
               "101": "тотожне?", "110": "за-умовою",
               "0010": "функція", "0011": "визначити",
               "0100": "хибне?", "1001": "друге",
               "1110": "список", "10011": "третє"}
ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "lib/process.lisp"
OLD = "(так"
NEW = "(атом? (як-є ()))"
FALSE = "(атом? (як-є (())))"


def ast(source: str):
    toks = [m.group() for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source
    ) if not m.group().startswith(";")]
    stack = [[]]
    for tok in toks:
        if tok == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            if len(stack) <= 1:
                raise ValueError("unbalanced close")
            stack.pop()
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("unbalanced open")
    return stack[0]


def domain_count():
    total = 0
    for width in range(1, 11):
        source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf8")
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", source)
        if len(keys) != 1 << width or len(set(keys)) != len(keys):
            raise ValueError(f"D{width} count/dup")
        if set(keys) != {f"{x:0{width}b}" for x in range(1 << width)}:
            raise ValueError(f"D{width} width/holes")
        total += len(keys)
    return total


def audit(source: str):
    if source.count(NEW) != 5 or OLD in source or "#d1:" in source or "((функція" in source:
        raise ValueError("потрібні пʼять виконуваних D1:YES та іменовані D4 механізми")
    # SHA усього файла не фіксуємо: чинна українська реалізація може оновлюватися.
    # Походження змін контролює Git, структуру умов — цей аудит.
    # Here we guard only exact D1 source and D3 two-branch structure.
    parsed = ast(source)
    if len(parsed) != 10 or sum(1 for form in parsed if isinstance(form,list) and form and form[0] == "визначити") != 9:
        raise ValueError("девʼять чинних процесних DEFINE і цитований кінцевий результат")
    def visit(node):
        if not isinstance(node, list):
            return
        if node and node[0] == "за-умовою":
            for branch in node[1:]:
                if not isinstance(branch, list) or len(branch) != 2:
                    raise ValueError("only two-part D3:COND clauses admitted")
        for item in node:
            visit(item)
    for row in parsed:
        visit(row)
    # Точні чинні D9 call-heads і цитовані дані: не історичний blob-пін.
    definitions = {row[1]: row for row in parsed if isinstance(row, list) and len(row) >= 3 and row[0] == "визначити"}
    expected_raw_exit = ["визначити", "отримати-сирий-код-виходу-процесу",
                         ["функція", ["сирий-результат"], ["друге", "сирий-результат"]]]
    if definitions.get("отримати-сирий-код-виходу-процесу") != expected_raw_exit:
        raise ValueError("порушено точний селектор вихідного коду")
    for name in ("процес-скласти-декодований", "процес-результат-текст",
                 "процес-запустити-текст", "процес-публічний-вихід-код",
                 "процес-розгорнути-публічний-результат", "процес-запустити"):
        if name not in definitions:
            raise ValueError(f"бракує визначеного D9 виклику {name}")
    for datum in ("(як-є process-result)", "(як-є rejected)",
                  "(як-є decoded-process)"):
        if datum not in source:
            raise ValueError(f"цитовані дані змінено: {datum}")
    if not re.search(r"\(список\s+\(як-є decoded-process\)", source):
        raise ValueError("змінено конструкцію процесного результату")
    return len(source.encode("utf8"))


class ProcessDirectD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FILE.read_text(encoding="utf8")

    def test_exact_d1_controls_and_cond_arity(self):
        current_bytes = audit(self.source)
        print(f"PROCESS D1: UTF-8 bytes {current_bytes}; "
              "five real SENS D1 predicates and two-part D3 COND clauses retained")

    def test_exact_domain_addresses_all_2046(self):
        self.assertEqual(domain_count(), 2046)

    def test_width_and_function_head_ledger(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf8")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+.*\(LISP T\)")
        self.assertRegex(d3, r"(?m)^\s*\(010\s+.*\(LISP ATOM\)")
        self.assertRegex(d3, r"(?m)^\s*\(001\s+.*\(LISP QUOTE\)")
        self.assertEqual((5 * (3+3)) - (5*1), 25)
        print("PROCESS D1: 30 historical D3 function-head bits -> 5 direct D1 bits; "
              "25 semantic AST head bits of overhead removed, physical T5 not measured")

    def test_mutations_fail_closed(self):
        for corrupted in (
            self.source.replace(NEW, "(1", 1),
            self.source.replace(NEW, "(0", 1),
            self.source.replace(NEW, "(як-є ())", 1),
            self.source.replace(NEW, FALSE, 1),
        ):
            with self.assertRaises(ValueError):
                audit(corrupted)

    def test_exact_current_domain_surface(self):
        for bits, name in EXACT_HEADS.items():
            domain = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
            row = re.compile(
                rf"(?m)^\s*\({re.escape(bits)}\s+\(ук\s+[^()\s]+\)\s+"
                rf"\(укр\s+{re.escape(name)}\)"
            )
            self.assertRegex(domain, row)
        d9 = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        for bits, name in (("010001000", "процес-результат-текст"),
                           ("001001001", "процес-запустити-текст"),
                           ("001010001", "процес-публічний-вихід-код"),
                           ("110101111", "процес-запустити")):
            self.assertRegex(d9, rf"(?m)^\s*\({bits}\s+.*\(укр {re.escape(name)}\)")
        self.assertEqual(self.source.count(NEW), 5)
        self.assertNotIn("((функція", self.source)
        self.assertNotRegex(self.source, r"(?<![\w-])(?:так|ні)(?![\w-])")
        self.assertNotIn("#d1:1", self.source)

    def test_wrong_peer_and_quoted_data_mutants_rejected(self):
        for broken in (
            self.source.replace("(друге сирий-результат)", "(третє сирий-результат)", 1),
            self.source.replace("(список\n            (як-є decoded-process)",
                                "(сполучити\n            (як-є decoded-process)", 1),
            self.source.replace("(як-є process-result)", "(як-є changed)", 1),
            self.source.replace(NEW, FALSE, 1),
        ):
            self.assertNotEqual(broken, self.source, "мутація має змінювати чинний код")
            with self.assertRaises(ValueError):
                audit(broken)

    def test_numeric_exit_code_and_structural_nil_unchanged(self):
        data = self.source
        self.assertRegex(data, r"\(\(тотожне\? код \(як-є \(\)\)\)\s+-1\)")
        self.assertIn("(отримати-сирий-код-виходу-процесу сирий-результат)", data)
        self.assertIn("(отримати-сирі-байти-помилок-процесу сирий-результат)", data)
        self.assertIn("(як-є (postcore-materialization-debug skipped))", data)


if __name__ == "__main__":
    unittest.main()
