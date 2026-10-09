# L1–L7 — спадкові конструкції → канон (міграційне рішення власника)

Дата: 2026-10-09. Межа: міграція джерел; не нова онтологія мови.
Авторитет значень: `language-contract.lisp`, D1–D9 таблиці й ратифіковані закони.
D10 — **research only**, координат і callability мігратор не призначає.

| Правило | Рішення | Механічне виконання / межа |
| --- | --- | --- |
| L1 | Тільки `(test expression)`; результат тесту — exact D1 PredicateBit `1/0`. Вичерпання — структурне `()` (D3 `000`) | AST перевіряє форму і явно доведені джерела exact D1. Не виводить загальну truthiness, не створює штучну default-клаузу. Недоведене → BLOCK. |
| L2 | `(t <expr>)` → `(1 <expr>)`; `t` не спеціальний | Перетворюється лише голий `t` як тест COND; зв'язаний `t` → BLOCK, без припущення про істинність. Цитовані дані не змінюються. |
| L3 | Виконуване ім'я → точне слово з admitted D1–D9 таблиць | Невідомий head → BLOCK + `d10_proposal` з `coordinate: null`; лексично зв'язані Text7 назви розглядає існуючий reader/encoder; жодного вигаданого коду. |
| L4 | `equal?`/`null` → доведений D8 resident або law-generated розгортка D3 | Без D8-доказу чи наявного перевіреного генератора — BLOCK. Жодної ручної рекурсивної заміни. |
| L5 | `structural-kind`/`identity-relation` вилучити з виконуваного корпусу, занести в археологію | Мігратор позначає BLOCK + archaeological review. Видалення/переміщення — окрема контрольована зміна, не side effect парсера. Цитовані дані не видаляються. |
| L6 | Стара фікстура → регенерація чинним канонічним інструментом | Вхідні fixture/provenance не редагувати AST-патчами. Перегенерувати й перевірити незалежним oracle. |
| L7 | Файл не парситься → не чіпати | Існуючий reader видає помилку; окремий рядок `blocked`, вихід не публікується. |

## Єдиний конвеєр

```text
scripts/migrate.py preview
   -> migrate-t5-batch.py --decision-table l1-l7
   -> існуючий strip_comments + tokenize + Parser AST
   -> L1–L7 normalizer (тільки ця таблиця рішень)
   -> існуючий Resolver/encode exact domain
   -> T5 codec + typed-word SHA256 (preview, НЕ admission)
   -> reviewed, source-pinned admit-t5-migration.py
   -> незалежні historical Python / current Rust oracle witnesses
   -> pinned physical/typed SHA256 + observable parity
   -> VERIFIED_NOT_WRITTEN або BLOCK (без guessed PASS)
```

`scripts/migrate.py` — **єдиний офіційний вхід**. Режим `preview` не пише фізичні `.sens`.
`admit` із незмінним історичним джерелом і фіксованими доказами також використовує L1–L7 перед семантичною перевіркою.
Прямі старі низькорівневі виклики `migrate-three-pass.py`/`migrate-t5-batch.py`
зберігають legacy-режим для відтворюваності історичних експериментів і **не є** канонічним admission.

## Обов'язкова перевірка

1. Компіляція/вхід AST: COND має рівно два поля у кожній proper clause; одинока `t` поза відповідним контекстом не перетворюється; у Quote жодних замін.
2. Неканонічні тести `nil`, `()`, числа, довільні текстові умови — BLOCK; D1 `0` ≠ D3 `000`.
3. D8 bridge лише за наявності exact-domain допуску; D10 proposal ніколи не є coordinate assignment.
4. `preview` — typed + physical round-trip; **не семантичне свідоцтво**.
5. `admit` — незмінні хеші source/witness/target, independent historical/current oracles й observable parity.
6. `cargo test --workspace`, `python3 -m unittest tests.test_l1_l7_decisions` (або запуск файла напряму), Hosted CI зелені перед злиттям у `main`.

Ні parser, ні Rust runtime, ні таблиці D1–D9, ні вже затверджені fixture не змінюють мову самі по собі. Міграція є застосуванням чинного Contract 11.8 до старого корпусу; якщо чинних законів недостатньо, відповідь — `BLOCK`, а не здогад.
