# Міграція носія `Sens8` → `CoreDomainIdentity`: точний ripple (lane CARRIER #2056)

> **Статус: план, не виконана зміна.** Цей документ нічого не міняє. Він дає
> точну карту залежностей для Rust-здатного lane, бо виконати перепис без
> компілятора правильно неможливо.

**Ревізія заміру:** `98a8592cf92e25d1da52a2ee047a937e942e6d28` (main).

## Мета

`sens.rs` більше не визначає **універсальну** тотожність як `Sens8(u8)`
(він лишається хіба що вузьким transport/backend швом). Носій семантичної
ідентичності — драбина: `CoreDomainIdentity` (D1–D9, u8) / `DomainIdentity`
(D1–D10, u16) з `crates/sens/src/domain_identity.rs`; доменні слова
(`PredicateBit`…`CoreD9`) з `domain_words.rs`.

## Замір ripple (усе `crates/sens/src`)

| токен | входжень | файлів |
|---|---:|---:|
| `Sens8` | 95 | 19 |
| `Value::Sid` | 14 | 6 |
| `ExprKind::Sid` | 25 | 8 |
| `packed_byte` | 76 | 10 |
| `from_packed_byte` | 9 | 6 |
| `SemanticId` | 16 | 1 |
| `from_exact_bits` | 2 | 2 |
| `as_sens8` / `as_sid8` | 3 / 1 | 1 / 1 |

Усього **~150–200 call-sites у ~26 файлах** (у всьому workspace `Sens8`
торкаються 26 `.rs`). Це не локальна заміна: зміна самих типів.

## Порядок міграції (кожен крок компілюється разом зі своїми споживачами)

1. **`sens.rs`** — прибрати `pub struct Sens8`, `pub type Sens`, макрос `sens!`;
   ввести domain-носій (тонкий alias/новий тип на `CoreDomainIdentity`).
   Прибрати `impl Sens8 { __from_macro_bits, from_packed_byte, packed_byte,
   from_exact_bits }` — замінити на domain-API (`from_source_word`,
   `packed_bits`, `source_word`).
2. **`semantic_registry.rs`** — `pub(crate) type SemanticId = Sens8` →
   `CoreDomainIdentity`; `Sens8::from_packed_byte(row.semantic_id)` →
   domain-конструктор; 16 входжень `SemanticId`.
3. **`value.rs`** — `Value::Sid(Sens8)` → `Value::Sid(CoreDomainIdentity)`;
   `as_sens8`/`as_sid8` → domain-аксесори; `sid.to_string()` (Display);
   `Value::Sid` порівняння (14/6).
4. **`syntax.rs` + `parser.rs`** — побудова `ExprKind::Sid(...)` (25/8),
   зокрема `crate::sens!(00001100)` → domain-координата.
5. **`lib.rs`** — реекспорт `pub use sens::{Sens, Sens8}` → domain-типи;
   `ProjectionSidInput` impl-и (8).
6. **`presentation.rs`, `eval/mod.rs`** — матчі `Value::Sid` / `ExprKind::Sid`,
   `uk_semantic_name(semantic_id: Sens8)`.

## Чому це не робиться без компілятора

Змінюється не лише ім'я, а **API**: `packed_byte` (u8) → `packed_bits`
(`CoreDomainIdentity::packed_bits() -> u8`, `DomainIdentity::packed_bits() -> u16`),
`from_packed_byte` → `from_source_word(BinarySourceWord)`. Кожен із ~200
call-sites мусить перейти узгоджено; одна пропущена — і крейт не збирається.
Тому цей крок належить середовищу з `cargo` (lane CARRIER #2056 / AST #2817),
а не «наосліп».

## Приймання (witness) після міграції

- `scripts/check-domain-ladder-identity.py --check` → розширити `CANONICAL`
  цими файлами (вони стануть 0-старих);
- `LEGACY_DEBT_MAX` (debt ratchet) для них → прибрати/зменшити до 0;
- CI: `cargo test --locked --workspace` зелений на тому ж SHA.
