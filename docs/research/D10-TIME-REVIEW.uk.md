# D10: перевірка часових законів — source-grounded, без автоматичної ратифікації

Цей пакет **не додає резидентів D10**. Він відстежує 9 визначень із `lib/time.lisp` на зафіксованому Git blob `c809c8b7291841c47c4072d0371105fb6596ab34`, з точними рядками та 34 позитивними/негативними **референсними** прикладами. Канонічний `sens/main` на початок огляду: **625/1024 selected; 399 missing; 256 law-forced; 369 unplaced; 0 ratified**. Не додавати число 9 до selected до завершення семантичного review.

## Перехід джерела — 2026-10-09

- Попередній review pin: `74013e20c0c5abb9a68c62334f40095c29294a53`.
- Фактичний blob `main` перед цією правкою: `b6e8278932298e5541ac79390051000a8804d1f9`.
- Новий blob джерела після виправлення форми: `c809c8b7291841c47c4072d0371105fb6596ab34`; зміна внесена комітом `b38903a82bc257d123dbd541771860017f30264a`.

Виправлено групування вкладених форм у `lib/time.lisp`, щоб кожна клауза D3:110 мала рівно два поля `(test expression)` згідно з Contract 11.8. Збережено пояснювальні коментарі про сирий host-boundary та похідні мілісекунди. **Це структурна міграція форми, а не доказ поведінкової еквівалентності.** У JSON оновлено pin і точні рядки; усі дев'ять пропозицій залишаються не вибраними й не ратифікованими.

## Попередній відбір

- **CIVIL-FROM-DAYS**: pure Gregorian conversion, перевірити окремість від уже ратифікованого `UTC-FROM-UNIX`.
- **INTERNET-TIME-FIELDS->OBSERVATION**: accepted/rejected observation from supplied NTP fields; protocol-specific semantics may belong in TIME package rather than Core.
- **INTERNET-TIME-OBSERVATION->UTC**: possibly pure composition of `UTC-FROM-UNIX` and projection; compare exact observable outcomes before selection.
- **TIMEZONE-DECLARATIONS->OBSERVATION**: deterministic explicit source precedence, possibly application policy.
- **TIMEZONE-CONFIG**: typed validated constructor with inclusive ±86400 bound; could be derived from arithmetic and tagged lists.

**HOLD**: `INTERNET-TIME-MODE-VALID?`, `INTERNET-TIME-STRATUM-VALID?` (protocol subrules); `INTERNET-TIME-RAW->OBSERVATION`, `TIMEZONE-RAW->OBSERVATION` (tag adapters). D10 should not silently mint bits for transport, schema tags, host I/O or D2 control. User's directive: **тільки D2 керує мовою**.

## Evidence and negative tests

`tests/test_d10_time_law_review_v2.py` contains independent reference-model cases for leap years, NTP epoch/valid mode/stratum/fraction, timezone precedence, validation boundaries, tagged accepted/rejected. These are **NOT** executions of `lib/time.lisp`; no language-runtime parity is claimed. In a real `sens` checkout, `scripts/check_d10_time_law_review_v2.py --require-checkout` validates the exact Git blob SHA, every definition-line pin, and semantic-name duplicates against the full D1–D9/D10 inventories. Run the unittest suite separately:

```sh
python3 scripts/check_d10_time_law_review_v2.py --require-checkout
python3 -m unittest discover -s tests -p 'test_d10_time_law_review_v2.py' -v
```

A successful research-ledger check does **not** prove the Lisp runtime's behavior. Required Hosted CI / Vertical Day tests are still the acceptance gate for the time-library load repair.

## Agent-handoff priority

1. Execute **actual** pure-source witnesses on canonical `lib/time.lisp`, including branch-specific NTP reject shapes and negative date limitations, then compare to an independent oracle.
2. Audit reusability/derivability versus existing `UTC-FROM-UNIX`, `UTC-NOW`, D9 and D10 outcome constructors.
3. Decide whether NTP/timezone policies belong to Core D10, TIME library/island, or pure derived convenience.
4. Rank by real source migration unblock fan-out only after collecting actual blocked paths; unknown != 0. No invented positions.
