# E1: sweep двочастинних `cond`-клауз · 2026-09-21

## Результат / Result

**Регресія → виправлення №1: `(fib 6)` було `6`, після міграції — `8`.**
Це демонструє, що legacy two-part `cond` з exact-Q результатом `0` тихо
псував звичайну арифметику: `0` ішов через migration-only truthiness path.
Міграція не змінює значення `<`, `>`, `=`: вони лишаються exact-Q `1` / `0`.

| Регресія до міграції | Після canonical three-part `cond` | Доказ |
| --- | --- | --- |
| `(fib 6)` → `6` | `(fib 6)` → `8` | `tests/fixtures/properties-helpers.lisp` |
| reason index з 65 різними предикатами → `indexed` | → `linear` | `reason_index::too_many_distinct_predicates_fall_back_to_linear_mode` |
| `(not (planet earth) extra)` обходив validation (`()`) | → `(invalid invalid-goal (not (planet earth) extra))` | `reason_outcome_invalid::not_with_multiple_nested_forms_is_invalid` |

## Exact-Q sweep

`rg -n '^\\s*\\(\\(\\s*[<>=]' tests/fixtures/*.lisp lib/*.lisp scripts/*.lisp`
знайшов 115 рядків. Шість були двочастинними legacy clauses; усі шість
мігровано, відкладених owner-рішень немає:

| Файл:рядок (до міграції) | Намір | Зміна |
| --- | --- | --- |
| `tests/fixtures/properties-helpers.lisp:18` | base case Fibonacci | `< n 2` з expected `1` / `0` |
| `lib/reason.lisp:100` | indexed до ліміту, linear після нього | `< predicate-count max` з `1` / `0` |
| `lib/knowledge.lisp:301` | `(not goal)` має рівно один nested goal | `= length 2` з `1` / `0` |
| `lib/result-status.lisp:88` | та сама validation-межа в standalone adapter | `= length 2` з `1` / `0` |
| `lib/yantra.lisp:505` | curl exit `0` парсить body, інше дає blocked evidence | `= exit 0` з `1` / `0` |
| `scripts/program-symbol-table.lisp:22` | newline відсутній завершує split | `= pos -1` з `1` / `0` |

Решта 109 exact-Q рядків уже мають explicit expected-result domain. Їх не
редаговано. Генератори не торкалися; exact-comparison/(Б) не мінявся.

## Wider two-part inventory

AST-level scan усіх `cond`-клауз форми `(query body)`:

| Scope | Clauses | Files |
| --- | ---: | ---: |
| `tests/fixtures/*.lisp` | 178 | 12 |
| `lib/*.lisp` | 1,516 | 22 |
| `scripts/*.lisp` | 308 | 19 |

Це checklist migration bridge, а не дозвіл на bulk rewrite: кожен такий сайт
потребує окремого читання наміру. У E1 змінено лише шість exact-Q sites,
для яких fallback був явний у сусідній clause.

## Oracle syntax evidence

`./target/debug/my-lisp --oracle-check` повернув `(outcome valid)` для:

- `tests/fixtures/properties-helpers.lisp`
- `lib/reason.lisp`
- `lib/knowledge.lisp`
- `lib/result-status.lisp`
- `lib/yantra.lisp`
- `scripts/program-symbol-table.lisp`

## CI lane

Команда: `bash scripts/test-current-semantic-slice.sh`.
Fresh run завершився з **exit status `0`**. `witness_authority` пройшов
12/12, усі Rust contract suites у lane пройшли, а subsequent Lisp-owned
witness section, включно з CPU-intensive
`native-first-coverage-ledger-witness.lisp`, завершився без помилки.

## English summary

The E1 exact-Q sweep found six legacy two-part clauses. All now use explicit
`1`/`0` expected-result branches while comparisons retain exact-Q semantics.
The strongest regression is `fib 6: 6 -> 8`. The broader inventory remains a
review checklist; it was not bulk-rewritten.
