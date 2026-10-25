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

---

# Додаток (Apekṣā, 2026-10-25): карта прогалин — чотири, а не одна

## Повний скан `lib/**/*.lisp`

```
усього: 404
  з кодом і з парою/виглядом: 374
  comment-only (пара не потрібна): 9
  З КОДОМ, АЛЕ БЕЗ ПАРИ Й ВИГЛЯДУ: 21
```

## Уточнення: виконуване проти даних

Розрізнив за наявністю `(визначити …)` — це **виконувані** файли; решта — **дані**.

**Усі `lib/domains/d1.lisp` … `d11.lisp` — ДАНІ** (0 `визначити` у кожному, попри
1026 рядків у `d10`). Тобто вони — **ратифіковані колонки**, а не програми, і пари
не потребують. Те саме: `lib/generated/function-table.lisp`,
`lib/machine/intel-core-i5-6400.lisp`, `lib/machine/profile/current-domain-x86-64.lisp`,
`lib/surface/semantic-registry.lisp`, `lib/surface/uk-sa-coverage.lisp`,
`lib/domains/archive/d11-rejected-43.lisp`.

**ВИКОНУВАНИХ без пари — ЧОТИРИ:**

| файл | `визначити` | `функція` |
|---|---|---|
| `lib/yantra.lisp` | **79** | 70 |
| `lib/d11-srfi1-append-map.lisp` | 4 | 5 |
| `lib/d11-srfi1-find-last-value-presence.lisp` | 5 | 5 |
| `lib/d11-srfi1-list-index-presence.lisp` | 5 | 6 |

## Отже прогалина не одна

`yantra` — **не виняток, а найбільший із чотирьох**. Три `d11-srfi1-*` — його брати:
**виконувані, без пари, без вигляду, поза перевіркою**.

І це **не випадковість**: `prove-lisp-semantic-t5m.sh:575` уже використовує
`lib/d11-srfi1-find-tail.lisp` (у якого пара **є**). Тобто **частина родини
`srfi1` має пари, а частина — ні**. Це та сама хвороба, що й `core4`: **пара
існує там, де хтось її створив, і не існує там, де не створив**.

## Що це додає до передачі

Раніше я казав: «перевір, чи `yantra` потребує пари». Тепер точніше:
**перевір чотири файли** — і з'ясуй, чому в `d11-srfi1-find-tail` пара **є**, а в
трьох його сусідів — **немає**. **Відповідь на це «чому» і є остання прогалина.**

## Deutsch

Vier ausführbare Dateien ohne Paar — nicht eine.

## English

Four executable files without a pair — not one.
