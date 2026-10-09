# D10: перевірка часових законів — source-grounded, без автоматичної ратифікації

Цей пакет **не додає резидентів D10**. Він переводить 9 знайдених у `lib/time.lisp` визначень у перевірювані пропозиції з current source Git blob SHA `48fd4014e3126858913d02641ede07ac71b0b4f2`, точними рядками і 34 позитивними/негативними **референсними** прикладами. Канонічний `sens/main` на початок: **625/1024 selected; 399 missing; 256 law-forced; 369 unplaced; 0 ratified**. Не додавати число 9 до selected до завершення семантичного review.

## Перехід джерела (2026-10-09)

Початковий зафіксований source blob: `74013e20c0c5abb9a68c62334f40095c29294a53`. Після міграції Contract 11.8 поточний blob: `48fd4014e3126858913d02641ede07ac71b0b4f2`. Міграція прибрала трипольні `D3:110 COND (test expected expression)` клаузи з активного `lib/time.lisp`, перевівши їх на двопольні `(D1-test expression)` та явні D1:1 fallback-и. Стара SHA збережена в `knowledge/d10-time-law-review-v2.json` у `source_history`; позиції визначень оновлено.

**Це не є доказом поведінкової еквівалентності.** `behavior_equivalence_proven` лишається `false`, незалежний мовний свідок лишається `PENDING`, власницький огляд — `PENDING-REVIEW`; кількість резидентів D10, selected та ratified не змінилася (0 додано).

## Попередній відбір

- **CIVIL-FROM-DAYS**: pure Gregorian conversion, перевірити окремість від уже ратифікованого `UTC-FROM-UNIX`.
- **INTERNET-TIME-FIELDS->OBSERVATION**: accepted/rejected observation from supplied NTP fields; protocol-specific semantics may belong in TIME package rather than Core.
- **INTERNET-TIME-OBSERVATION->UTC**: possibly pure composition of `UTC-FROM-UNIX` and projection; compare exact observable outcomes before selection.
- **TIMEZONE-DECLARATIONS->OBSERVATION**: deterministic explicit source precedence, possibly application policy.
- **TIMEZONE-CONFIG**: typed validated constructor with inclusive ±86400 bound; could be derived from arithmetic and tagged lists.

**HOLD**: `INTERNET-TIME-MODE-VALID?`, `INTERNET-TIME-STRATUM-VALID?` (protocol subrules); `INTERNET-TIME-RAW->OBSERVATION`, `TIMEZONE-RAW->OBSERVATION` (tag adapters). D10 should not silently mint bits for transport, schema tags, host I/O or D2 control. User's directive: **тільки D2 керує мовою**.

## Evidence and negative tests

`tests/test_d10_time_law_review_v2.py` contains independent reference-model cases for leap years, NTP epoch/valid mode/stratum/fraction, timezone precedence, validation boundaries, tagged accepted/rejected. These are **NOT** executions of `lib/time.lisp`; no language-runtime parity claimed. In a real `sens` checkout, `scripts/check_d10_time_law_review_v2.py` additionally validates the exact Git blob SHA and definition-line pins and checks semantic name duplicates against full D1–D9/D10 inventories.

## Перевірка в поточному репозиторії

Запусти перевірки у checkout `juv4uk/sens`: 

```sh
python3 scripts/check_d10_time_law_review_v2.py
python3 -m unittest discover -s tests -p 'test_d10_time_law_review_v2.py' -v
```

Then create a research-only PR referencing #4013 / #4463 / #4162. Do not increment `knowledge/d10-v1-semantic-inventory.json` or `knowledge/d10-fill-v1-state.json` until independent old/current executable parity and owner review prove an additional D10 meaning. Keep separate from +9 pending unification branch.

## Agent-handoff priority

1. Execute **actual** pure-source witnesses on canonical `lib/time.lisp`, including branch-specific NTP reject shapes and negative date limitations, then compare to independent oracle.
2. Audit reusability/derivability versus existing `UTC-FROM-UNIX`, `UTC-NOW`, D9 and D10 outcome constructors.
3. Decide whether NTP/timezone policies belong to Core D10, TIME library/island, or pure derived convenience.
4. Rank by real source migration unblock fan-out only after collecting actual blocked paths; unknown != 0. No invented positions.
