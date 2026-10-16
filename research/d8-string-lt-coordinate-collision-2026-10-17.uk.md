# D8: розбіжність координати `10110001` (`string<?` vs `answer-not`) — доказовий ланцюг

**Дата:** 2026-10-17. **Знайдено під час спроби регенерувати `lib/core4.lisp.fasl`.**
**Статус:** доказ; зміну НЕ виконано (потрібне рішення власника про джерело істини).

## Симптом
Workflow `core4-internal-cutover.yml` падає на кроці 8
(`cargo test --test core4_migration_point`) → крок 9 `gen-fasl` **skipped** → FASL застарілий.

```
(string<? "a" "b") failed:
  LanguageError { kind: Type, message: "math requires explicit D24+ operands;
  D1-D10 bit words and unqualified numbers are not arithmetic values" }
  ← crates/sens/src/eval/arithmetic.rs:39
```

## Чотири джерела — і де вони розходяться
| джерело | твердить |
|---|---|
| `contracts/d8-ratification.lisp:212` (**авторитет**) | `resident "10110001" "STRING<" owner-ratified-s4-gauge-choice` |
| `lib/domains/d8.lisp:187` | `10110001 → string<?` |
| `lib/domains/d8.lisp:47` | `00100101 → multiple-value-bind` (**ця координата вже зайнята**) |
| `lib/surface/semantic-registry.lisp:179` | `10110001 → answer-not` |
| `crates/sens/src/semantic_registry_generated.rs:58` | `0b00100101 → string<?` (**хибно**) |
| `crates/sens/src/semantic_registry_generated.rs:198` | `0b10110001 → answer-not` |

## Що *не* є причиною (перевірено й виключено)
- **Тіло `string<?` правильне.** Живе джерело `lib/core4.lisp:568` (його й вбудовує
  `CORE_LIBRARY_SOURCE = include_str!("lib/core4.lisp")`) кличе `string<?` **за іменем**:
  `(string<? (110011101 a) (110011101 b))` — це законна рекурсія на `string-rest`.
  Старіша копія `lib/core.lisp:609` мала легасі `10110001`, але **вона не завантажується**.
- **`d8.lisp` і ратифікація — правильні**, їх чіпати не треба.
- FASL застарілий — **наслідок**, не причина (вбудований `source_hash=cf4e0e04…` ≠
  `sha256(core4.lisp)=2cbd12a9…`; тест свіжості живе в інших workflow, не в головному `ci.yml`).

## Справжня причина
**Згенерований Rust-реєстр розсинхронізований з ратифікованою драбиною:**
`string<?` отримав код `0b00100101`, який у драбині належить `multiple-value-bind`.
Живий `string<?` резолвиться через цей хибний рядок → не той механізм → арифметика → `Type`.

## Що потрібно (рішення власника)
1. Яка координата `string<?` — **`10110001`** (ратифікація + d8) чи `00100101` (generated)? Доказ
   вказує на `10110001`.
2. Якщо `10110001` — то `lib/surface/semantic-registry.lisp:179` (джерело генератора) має давати
   `10110001 → string<?`, а `answer-not` — свою D9-координату; тоді **перегенерувати**
   `semantic_registry_generated.rs` (генератор `scripts/generate-rust-semantic-registry.lisp`).
3. Перевірити, чи `answer-not` у generated теж має правильну координату (`D9:110111011`).

## Споріднене
#5856 (цей доказ), #5761 (зріз 1 LET/LET*), #5854 (похідні функції D6), #5609 (легасі-виклики).
Спільний свідок `core4_migration_point` перевіряє також `let`/`let*` — тож колізія перетинається зі зрізом 1.
