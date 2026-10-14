# Тріаж червоних: код чи застарілий тест (14.10.2026)

**Що це.** Розбір 7 червоних перевірок, виведених із карантину за правилом 24 годин.
Мета — дати рою **клас причини**, а не «червоно/зелено». Джерело: логи прогонів
(run ids у таблиці), крок, що впав, і перший справжній рядок помилки.
**Це не вердикт семантики** — класифікацію підтверджує власник/рій.

## Клас A — КОД: чинний контракт D24 (одна коренева причина на три перевірки)

Помилка однакова: `math requires explicit D24+ operands; D1-D10 bit words and unqualified numbers are not arithmetic`.

| перевірка | run | крок | файл |
|---|---|---|---|
| `ci-hosted` | 38566012866 | Verify migrated user demo sources run through canonical Core | `crates/sens/tests/exact_domain_migrated_demos.rs` |
| `vertical-day-immutable-smoke` | 38566038829 | Native CPU vertical mechanism witnesses | `crates/sens-host/tests/native_cond_profile.rs:47` |
| `vertical-day-smoke` | 38566043410 | Interpreter oracle and native physical CAR/CDR agree | `crates/sens-host/tests/native_lisp_bytes.rs:557` |

Додатково у `vertical-day-smoke`: `MACHINE-ENCODE-PROBE u64-bytes: ERROR LanguageError { kind: Arity, message: "lambda: expected 1; received 0" }` — друга, окрема дрібніша помилка.

**Що це означає:** це **не застарілість**. Це живий наслідок чинного правила D24: джерела/демо/тести годують арифметику простими числами там, де потрібен явний D24-операнд. **Фікс один** — перевести ці джерела на явні D24 (або визнати, що вони більше не арифметика). НЕ послаблювати правило.

## Клас B — ЗАСТАРІЛА ІНФРАСТРУКТУРА: воркфлоу не ставить Zig

| перевірка | run | крок | причина |
|---|---|---|---|
| `audit-t5-program-syntax` | 38566007163 | Build the ACTUAL SENS binary reader | `crates/sens-cli/build.rs:24`: `zig-transport requires the pinned Zig compiler: Os { code: 2, NotFound }` |
| `physical-binary-sens-cli` | 38566028087 | Build exact binary execution and transport tools | те саме |

**Що це означає:** тест не хибний — йому бракує **передумови**. `sens-cli/build.rs` тепер вимагає пінований Zig (`.zig-version`), а ці два воркфлоу його не встановлюють. **Фікс тривіальний** — додати крок встановлення Zig 0.16.0 (як у `ci.yml`/`zig-t5-parity.yml`), або визнати воркфлоу архівом.

## Клас C — ЗАСТАРІЛИЙ ТЕСТ: змінилася передумова

| перевірка | run | крок | причина |
|---|---|---|---|
| `domain-ladder` | 38566017915 | UTF-8 точний D1 — 14 результатів | `tests/test_utf8_d1_predicate_migration.py:176`: `with self.assertRaises(ValueError)` → `AssertionError: ValueError not raised` |
| `t5-migration-inventory` | 38566033327 | Незалежний негативний свідок | `FAILED (failures=2)`; повідомлення: `'…': карантин не скасований ратифікованим двійковим свідком` |

**Що це означає:** тести перевіряють **стару** передумову (що негативні мутації кидають ValueError; що карантин знімається саме так). Або передумова змінилася, або код утратив охорону. **Треба вирішити по кожному:** оновити тест під чинний контракт **або** відновити охорону — але не «позеленити» мовчки.

## Що лишається (не в цьому тріажі)

- `narrate-d3-atom-eq-law` — валідна **заглушка** (справжні кроки вилучено як хибні, 3bb8685d9); треба відновити коректні кроки.
- `important-file-guard` — локально валідний, GitHub-ом не підтверджений (диспатч не пройшов через форму аргументу).
- `domain-semantics` — свідомо в карантині (інше правило: недозволений семантичний тест).

_Класифікація механічна (за першим справжнім рядком помилки). Нормативні рішення — за власником._
