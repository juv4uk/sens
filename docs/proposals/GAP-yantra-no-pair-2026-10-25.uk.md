# ПРОГАЛИНА: `lib/yantra.lisp` — виконуваний код без фізичної пари

Автор: агент Abhāva, 2026-10-25.

## Що встановлено

| файл | рядків | КОДУ | `.sens`-пара | статус у проєкті |
|---|---|---|---|---|
| `lib/core2.lisp` | 31 | **0** | немає | `is_explicit_non_implementation` = **true** |
| `lib/core-math.lisp` | 45 | **0** | немає | **true** |
| **`lib/yantra.lisp`** | 540 | **451** | **НЕМАЄ** | **false** ← виконуваний |
| `lib/core4.lisp` | 7624 | 4752 | **є** | **true** (декларативні дані) |

Проєкт **сам** це фіксує — `crates/sens-cli/tests/active_lib_sens_completion.rs`:

```rust
// Core4 — декларативні дані. Yantra визначає виконувані функції,
// тому не може бути виключена за назвою або через JSON-рядки.
assert!(is_explicit_non_implementation("lib/core4.lisp"));
assert!(!is_explicit_non_implementation("lib/yantra.lisp"));
assert!(is_explicit_non_implementation("lib/core-math.lisp"));
assert!(is_explicit_non_implementation("lib/core2.lisp"));
```

І `lib/yantra.lisp` **справді виконується** — `crates/sens/tests/yantra.rs:20`:

```rust
eval_program(include_str!("../../../lib/yantra.lisp"), &mut session).unwrap();
```

## Розрив

- `core2` і `core-math` — **comment-only** (0 рядків коду) → відсутність пари **законна**.
- **`yantra` — 451 рядок виконуваного коду, пари НЕМАЄ**, і він **виключений** з
  автопере-карбування (`remint-drifted-pairs.yml:146`).

**Отже для `yantra` немає ні пари, ні перевірки, ні пере-карбування.** Якщо
SENS/T5M-шлях його потребує, він або падає, або береться з `.lisp` напряму — і
**ніщо цього не показує**.

## Чому це важливо для конкурсу

`core4` **був застарілий** — і це **спіймали** (bootstrap-перевірка), хоч сім
свідків і впали. `yantra` **не має пари взагалі** — і **не спіймає ніщо**, бо
**ніщо не шукає те, чого немає**. Тобто `yantra` — **тихіша** версія тієї самої
хвороби.

## Що робити (рішення власника)

1. **Визначити**, чи SENS/T5M-шлях потребує `lib/yantra.sens`. Якщо **так** —
   його треба створити й пере-карбовувати як `core4`.
2. Якщо **ні** (бо `include_str!` вбудовує `.lisp` на етапі збірки) — це треба
   **зафіксувати явно**, щоб наступний агент не шукав пару, якої не буде.
3. **Мій `check-core4-pair-together.py` цю прогалину свідомо НЕ ловить** — він
   вимагає пару лише там, де вона є. **Це чесна межа, а не недогляд.**

## Deutsch

Lücke: `lib/yantra.lisp` ist ausführbarer Code ohne physisches Paar und ohne Prüfung.

## English

Gap: `lib/yantra.lisp` is executable code with no physical pair and no check.
