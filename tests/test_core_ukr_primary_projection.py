"""Точкова перевірка повної української проєкції основних Core-файлів.

Перевіряє актуальні українські визначення та точні ширини доменів.
Назви з таблиць є проєкціями; цей тест не надає координатам викличності.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class CoreUkrPrimaryProjectionTests(unittest.TestCase):
    def test_meta_registry_diagnostic_uses_ukrainian_name_without_false_readiness(self):
        script = source("scripts/generate-meta-semantic-registry.lisp")
        self.assertIn(
            "(визначити готовність-породження-метасемантичного-реєстру",
            script,
        )
        self.assertNotIn("(визначити generate-meta-semantic-registry-ready", script)
        # Сталі зовнішні імена генератора та протокольні позначки не
        # перейменовуються як викличні голови до міграції споживачів.
        self.assertIn("(як-є (generate-meta-semantic-registry (status not-verified)", script)
        self.assertNotIn("(status verified)", script)
        self.assertNotIn("(status pass)", script)
        self.assertEqual(script.count("(визначити готовність-породження-метасемантичного-реєстру"), 1)

    def test_retired_function_table_generator_cannot_pretend_to_execute(self):
        # Історична восьмибітна таблиця — дані, а не чинний код чи генератор.
        generator = source("scripts/generate-function-table.lisp")
        machine = source("lib/generated/function-table.lisp")
        document = source("docs/generated/function-table.md")
        lines = [line.strip() for line in generator.splitlines() if line.strip()]
        self.assertTrue(lines)
        self.assertTrue(all(line.startswith(";") for line in lines))
        self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", generator)
        self.assertIn("Не свідок. Не якір.", generator)
        self.assertNotIn("(status pass)", generator)
        self.assertIn("Чинна таблиця функцій — не окрема плоска восьмибітна нумерація.", machine)
        self.assertIn("lib/surface/semantic-registry-api.lisp", machine)
        self.assertIn("(прочитати-семантичний-реєстр)", machine)
        self.assertNotRegex(machine, r"(?m)^\\s*\\([01]{8}\\s")
        self.assertIn("історична міграційна проєкція", document)
        self.assertNotIn("Відтворити:", document)
        self.assertNotIn("cargo run -p sens-cli --bin sens -- scripts/generate-function-table.lisp", document)

    def test_constitution_example_is_current_sens_not_host_racket(self):
        # Перевірка вихідних форм і незмінності цитованих даних.
        # Справжній SENS runtime/ T5M-зворотність — окремий доказ.
        program = source("racket/examples/constitution.lisp")
        self.assertFalse(program.startswith("#lang "))
        self.assertNotRegex(program, r"(?m)^\s*\((?:displayln|defmacro|def|quote|cond)\b")
        self.assertNotIn("defmacro", program)
        self.assertNotIn("`(if", program)
        # Усі 12 первісних обчислень тепер є значеннями одного Lisp-списку,
        # а не неіснуючим host-друком: виконання перевіряє нативний SENS.
        self.assertIn("(визначити результати-конституції\n  (список", program)
        self.assertNotIn("(друкувати", program)
        for math in ("(частка 5 336)", "(частка 5.0 2)"):
            with self.subTest(math=math):
                self.assertIn(math, program)
        for quoted in ("constitution", "a", "лісп", "лісп-працює"):
            with self.subTest(quoted=quoted):
                self.assertIn(f"(як-є {quoted})", program)
        self.assertIn("(як-є (x))", program)
        self.assertIn("(як-є (a b))", program)
        self.assertIn("(як-є (b))", program)
        # Цитовані D7-слова — дані, а D3 EQ приймає тільки атоми.
        self.assertIn("(тотожне? (як-є атом?) (як-є тотожне?))", program)
        self.assertNotIn("(тотожне? (як-є a)", program)
        self.assertIn("((атом? (як-є ())) (як-є ()))", program)
        self.assertNotIn("(так ", program)
        self.assertNotIn("(так\n", program)
        self.assertIn("(як-є лісп-працює)", program)
        self.assertIn("(перше (решта (решта результати-конституції)))", program)
        # Перевірка не вважає відновлення коментарів умовою оберненості.
        guide = source("racket/README.md")
        self.assertIn("sens-cli --bin sens -- racket/examples/constitution.lisp", guide)
        self.assertNotIn("racket examples/constitution.lisp", guide)

    def test_core_sources_follow_full_ukrainian_projection_without_changing_domain_identity(self):
        core = source("lib/core.lisp")
        core4 = source("lib/core4.lisp")
        surface = source("lib/surface/uk.lisp")

        with self.subTest(file="lib/core.lisp"):
            # Поточний Core — українська виклична поверхня, без
            # приписування старому ASCII псевдоніму машинного значення.
            for head in ("тотожність", "друге", "третє", "четверте"):
                self.assertIn(f"(визначити {head}", core)
            self.assertIn("(перше (решта значення-функції))", core)
            self.assertIn("(третє (решта значення-функції))", core)
            for retired in ("second", "third", "fourth"):
                self.assertNotRegex(core, rf"\(визначити\s+{retired}\b")

        with self.subTest(file="lib/core4.lisp"):
            # Допоміжний двоелементний список і D8 «пара» — різні закони.
            self.assertIn(
                "(визначити створити-список-із-двох-значень\n  (функція (лівий-аргумент правий-аргумент)",
                core4,
            )
            self.assertIn(
                "(визначити пара\n  (функція (ліві праві)\n    (спарувати-послідовності ліві праві)))",
                core4,
            )
            self.assertNotIn("(визначити pair\n  (функція", core4)
            self.assertNotIn("(визначити pair пара)", core4)
            self.assertNotIn("(визначити second друге)", core4)
            self.assertNotIn("(визначити third третє)", core4)
            # Д6:100111 — ратифікована тотожність. Допоміжне
            # визначення не повинне дублюватися в Core4; перевіряємо
            # закон композиції, а не випадкове ім'я формального параметра.
            # Окремий SENS runtime oracle перевіряє саме виконання.
            self.assertRegex(
                core,
                r"\(визначити\s+четверте\s+\(функція\s+\(([^()\s]+)\)\s+"
                r"\(третє\s+\(решта\s+\1\)\)\)\)",
            )
            self.assertNotRegex(core4, r"(?m)^\(визначити\s+четверте(?=\s|\))")

        with self.subTest(file="lib/surface/uk.lisp"):
            # Чинна компактна поверхня — проєкція, а не файл
            # зі старими англомовними DEFINE-дублями.
            self.assertIn("не створює псевдонімів", surface)
            self.assertIn("T5M", surface)
            self.assertNotIn("(визначити ", surface)

        # Internal helpers remain internal; their executable names are Ukrainian
        # in both bootstrap/core4 copies and every live caller. No alias or new
        # domain resident is introduced by this lexical migration.
        helpers = (
            ("класифікувати-рядкове-значення", "string-membership-helper"),
            ("порівняти-рядки-за-кодовими-точками", "string-order-helper"),
            ("класифікувати-непорожність-рядка", "nonempty-string-membership-helper"),
            ("знайти-пару-підстановки", "sublis-pair"),
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
            ("знайти-найбільший-блок-частки", "largest-chunk"),
            ("перевірити-неспадання-значень?", "nondecreasing-from?"),
            ("перевірити-незростання-значень?", "nonincreasing-from?"),
        )
        # Core4 owns these remaining internal helper definitions. The smaller
        # Ukrainian core.lisp no longer carries duplicate number-rendering code.
        for ukrainian, legacy in helpers:
            with self.subTest(file="lib/core4.lisp", helper=ukrainian):
                self.assertIn(f"(визначити {ukrainian}", core4)
                self.assertNotIn(f"({legacy} ", core4)
        self.assertNotIn("взяти-десятковий-символ", core4)
        self.assertNotIn("number->string-onto", core4)
        self.assertIn("(визначити число-рядок", core4)
        self.assertNotIn("(визначити number->string число-рядок)", core4)
        self.assertNotIn("(визначити list список)", core4)
        self.assertNotRegex(core4, r"(?m)^\(визначити\s+[A-Za-z]")
        live_callers = (
            "lib/yantra.lisp",
            "lib/translation.lisp",
        )
        for filename in live_callers:
            code = source(filename)
            with self.subTest(file=filename, migration="string classification"):
                self.assertIn("класифікувати-рядкове-значення", code)
                self.assertNotIn("(string-membership-helper ", code)

        # Старий Rust-генератор лишається явним якорем, а не живим
        # генератором чи доказом успішності/готовності.
        registry_anchor = source("scripts/generate-rust-semantic-registry.lisp")
        with self.subTest(file="scripts/generate-rust-semantic-registry.lisp",
                          migration="retired generator stays unverified"):
            # Вилучений генератор не є ні програмою, ні доказовим якорем.
            self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", registry_anchor)
            self.assertIn("Не свідок. Не якір.", registry_anchor)
            self.assertNotRegex(registry_anchor, r"(?m)^\s*\(")
            self.assertNotIn("(status pass)", registry_anchor)
            self.assertNotIn("класифікувати-рядкове-значення", registry_anchor)
        inventory = source("lib/surface/uk-inventory.lisp")
        # Чинна форма є виконуваним українським визначенням, яке
        # повертає цитовані дані; старі SID8-рядки більше не є контрактом.
        self.assertEqual(len(re.findall(r"(?m)^\(визначити\s+інвентар-укр(?=\s|\))", inventory)), 1)
        self.assertIn("(функція ()", inventory)
        self.assertIn("(сполучити (як-є uk-inventory)", inventory)
        self.assertIn("(як-є (визначити функція за-умовою тотожне? як-є перше решта список))", inventory)
        self.assertIn("(інвентар-укр)", inventory)
        self.assertNotIn("(визначити uk-inventory", inventory)
        self.assertNotIn("(current-projection ukr)", inventory)
        self.assertNotIn("(sid8-call-heads retired)", inventory)
        self.assertNotIn("(necessary-forms ", inventory)

        # These three helpers deliberately have no D-domain resident names:
        # keep them internal, Ukrainian, and exactly reversible at the callsite.
        for ukrainian, legacy in (
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
        ):
            self.assertIn(f"(визначити {ukrainian}", core4)
            self.assertNotIn(f"({legacy} ", core4)
        # Інвентар не дублює внутрішні визначення й не створює
        # жодної окремої машинної адреси для допоміжних функцій.

        with self.subTest(file="racket/boot/core.lisp", migration="Ukrainian D1 bootstrap"):
            racket_core = source("racket/boot/core.lisp")
            # За поточним Contract 11.9 це українське джерело, не
            # старий Racket-host alias реєстр і не доказ SENS runtime.
            self.assertIn("(визначити тотожність", racket_core)
            self.assertIn("(визначити друге", racket_core)
            self.assertIn("(визначити третє", racket_core)
            self.assertIn("(визначити четверте", racket_core)
            self.assertIn("(визначити готовність-ядра-ракет", racket_core)
            self.assertIn("(визначити двійковий-опис", racket_core)
            self.assertIn("(значення ні)", racket_core)
            self.assertIn("((атом? (як-є ())) так)", racket_core)
            self.assertNotIn("(так ", racket_core)
            self.assertNotIn("(так\n", racket_core)
            self.assertNotRegex(racket_core, r"\(визначити\s+[A-Za-z]")
            self.assertNotRegex(racket_core, r"\(t(?:\s|\))")
            self.assertNotIn("(визначити cadddr", racket_core)
            self.assertNotIn("number->string-onto", racket_core)

        dependency_classifier = source("scripts/build-dependency-classification.lisp")
        with self.subTest(file="scripts/build-dependency-classification.lisp",
                          migration="українська виклична поверхня"):
            self.assertIn("(визначити класифікувати-залежності-збірки", dependency_classifier)
            self.assertIn("(класифікувати-залежності-збірки)", dependency_classifier)
            self.assertNotIn("(визначити build-dependency-classification", dependency_classifier)
            self.assertNotRegex(dependency_classifier, r"\([01]{3,11}(?=\s|\))")
            # Чинний цитований інвентар посилається на УКР-проєкцію;
            # старі ідентичності не проходять навіть як нібито status.
            self.assertIn("(виклики-укр чинні)", dependency_classifier)
            self.assertNotIn("(sid8-call-heads retired)", dependency_classifier)

        # Numeric iteration workers remain ordinary Ukrainian library helpers.
        for ukrainian, legacy in (
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
        ):
            self.assertIn(f"(визначити {ukrainian}", core4)
            self.assertNotIn(f"({legacy} ", core4)

        # Exact keys and full Ukrainian labels come from their owning domains.
        # In particular, D6:100111's label "четверте" is only a projection;
        # this test does not admit direct D6 execution.
        for path, width, bits, label in (
            ("lib/domains/d4.lisp", 4, "1001", "друге"),
            ("lib/domains/d5.lisp", 5, "10011", "третє"),
            ("lib/domains/d6.lisp", 6, "100111", "четверте"),
        ):
            with self.subTest(domain=path, bits=bits):
                self.assertEqual(
                    len(bits), width,
                    f"{path}: ширина ключа має належати своєму домену D{width}",
                )
                matching = [
                    line for line in source(path).splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(
                    len(matching), 1,
                    f"{path}: очікував єдиний точний ключ {width}-бітової ширини: {bits}",
                )
                self.assertRegex(
                    matching[0], rf"\(укр\s+{re.escape(label)}\)"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
