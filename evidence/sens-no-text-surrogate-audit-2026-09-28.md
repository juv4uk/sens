# SENS-NO-TEXT-SURROGATE-AUDIT

**Дата:** 2026-09-28  
**Issue:** #1590  
**SHA бази:** `91643841bae238883bf303e55c0896c0b7997583` (main на момент аудиту)  
**Статус:** partial — ядро вже binary; залишковий борг лише в surface/bench/display

## Метод

Переглянуто `crates/sens/src/{sens,sid,parser,syntax,value}.rs` і fasl/wire модулі в `syntax.rs`.
Питання: де `00001100` (вісім символів) підміняє ідентичність замість 1 байта?

## Класифікація

| Місце | Форма | Клас | Вердикт |
|-------|--------|------|--------|
| `parser.rs` token `len==8` лише `0/1` → `ExprKind::Sid(Sens8)` | 8 char source → packed | **reader surface** | OK — source/UI, не identity у рантаймі |
| `sens.rs` `from_exact_bits` / `sens!` macro | 8 char → `Sens8(u8)` | **reader/macro surface** | OK — bridge only; identity = bits |
| `syntax::fasl` `TAG_BINARY` + `sid.packed_byte()` | 1 byte | **transport** | OK — true 8-bit |
| `syntax::fasl` decode `from_packed_byte` | 1 byte | **transport** | OK |
| `syntax::wire` `TAG_BINARY` + packed byte | 1 byte | **transport** | OK |
| `ExprKind::Call(Sens8, …)` після lower | 1 byte in AST | **core** | OK |
| `ExprKind::Sid(Sens8)` | typed | **core** | OK |
| `Value::Sid(Sens8)` / `as_sens8` | typed | **core** | OK |
| `Display` for `Sens8` → `{:08b}` | 8 char string | **projection** | OK — display ≠ identity |
| `Value` print path `sid.to_string()` | 8 char | **projection** | OK |
| `sid.rs` deprecated `Sid8`/`sid!` | alias | **compat** | OK — deprecated until cml migrates |
| Bench #1413 text form `00001100` as source | 8 char | **bench surface** | OK as source; binary fasl path already measured (×3.76 load) |
| Bench harness that *only* feeds text SENS for “identity” claims | 8 char | **debt** | Documented in `benchmarks/sens-surface/.../20260927-three-way` — corrected to binary for true claim |

## Findings

1. **Семантичне ядро не тримає SENS як текст.** Після reader усе типізовано `Sens8` (1 байт). FASL і wire кодують `TAG_BINARY` + один байт.
2. **8-символьний `0/1` у source — легітимна surface**, аналог `sens!(00001100)`: це спосіб *написати* біти людині/файлу, не друга identity.
3. **Display `00001100` — проєкція**, не канонічна identity (аксіома 3 з `knowledge/sens-primary.lisp`).
4. **Немає** другого parallel ID layer у value/AST (немає string SID поруч із `Sens8` у `ExprKind` / `Value`).
5. **Реальний виграш binary** уже виміряний (2026-09-27 three-way): load ×3.76 vs English text; execute ×1.196 vs English names same binary.

## Що *не* є боргом

- Reader accepts `00001100` in source files.
- Printing Sens8 as eight binary digits for humans/logs.
- Historical McCarthy names as surface spellings in registry.

## Залишковий борг (не блокує P0)

| Борг | Де | Наступний крок |
|------|-----|----------------|
| CI bench default може лишатися на text forms для порівняння en vs sens | `benchmarks/sens-surface/`, workflow `sens-bench.yml` | P1: default evidence path = binary SENS wire/fasl for identity claims |
| `cml` ще може тягнути deprecated `Sid8` | `sid.rs` | зовнішній споживач; deprecate path already marked |
| M8: runtime lookup `+`/`-` як імен | eval lower | окрема задача SENS-LOWER-REDEFINABLE |

## Acceptance цього аудиту

- [x] Список місць із класифікацією
- [x] Ядро підтверджено binary (fasl + wire)
- [x] Reader 8-char позначено як surface, не bug
- [x] Залишковий борг винесено в P1, не замасковано

## Наступне

**SENS-BINARY-TRANSPORT-ONLY (P1):** переконатися, що публічні evidence/CI claims про «SENS identity» завжди використовують 1-byte path (fasl/wire), а text 8-char — лише як source surface у порівнянні форм.
