# Двійкове/десяткове і D24: одне визначення замість двадцяти

**Статус:** інженерний висновок, **не** семантика. Рішення — за власником.
**Питання власника:** «скільки ми раз перевизначаєм двійкове і десяткове, можливо потрібно визначити в одному місці і все».

## 1. Одне місце вже Є — але його майже ніхто не читає

**Авторитет:** `contracts/numeric-domains-ratification.lisp` (owner-ratified 2026-10-11):
- `first-domain . D24`, `initial-width . #d24`, `next-width . double`,
- `domain-rule . "D(24 * 2^n), n >= 0"`,
- `canonical-domain-names . (D24 D48 D96 D192)`,
- `normative-map . "knowledge/number-width-ratified.json"`,
- і повний набір законів (arithmetic-exclusivity, same-domain-natural-addition/multiplication/subtraction/division, base-natural-occupancy, signed/rational-composition, canonicalization, composite-growth, deferred, runtime-status).

**Хто його читає:** лише `language-contract.lisp` і `scripts/check-numeric-domain-ratification.py`.
**Тобто:** правило має одного автора, але **код його не успадковує — код його переписує.**

## 2. Скільки разів переписано (заміряно grep-ом)

Ширини 24/48/96/192 і «десяткове» живуть у **~20+ файлах** чотирма мовами:

| мова | файли (приклади) |
|---|---|
| Rust | `crates/sens/src/binary_number.rs`, `domain_numeric.rs`, `eval/arithmetic.rs`, `eval/d6_arithmetic.rs`, `parser.rs`; тести `math_domain_exclusivity.rs`, `axiom_corpus_function_description.rs`, `binary_number_live.rs` |
| Zig | `research/zig-codecs/domain_ladder.zig`, `domain_e3_numeric.zig` |
| Lisp | `language-contract.lisp`, `lib/domains/d*.lisp`, `contracts/numeric-domains-ratification.lisp` |
| Python | `scripts/check-numeric-domain-ratification.py`, `scripts/domain_tables.py`, `scripts/migrate-three-pass.py`, `scripts/check-core4-d24-migration.py` |
| бенчмарки | `benchmarks/core-number-q-product-ladder/run.py` (77), `core-number-width-ladder/run.py` (53), `core-coremath-q-final-fit/run.py` (40) |

**Наслідок:** зміна правила (нова ширина, новий закон, зміна `next-width`) вимагає правки в 20+ місцях чотирма мовами — і будь-яке з них може **розійтися** з контрактом. Це і є та «ціна перевизначення», про яку ти кажеш.

## 3. Що зробити (консолідація)

1. **Джерело — контракт.** `contracts/numeric-domains-ratification.lisp` + `knowledge/number-width-ratified.json` лишаються єдиною правдою. Не переносити правило в код «ще раз».
2. **Генератор.** Розширити наявний механізм (`scripts/generate-domain-owner-registry.py` / `generate-domain-width-certificate.py`) так, щоб він **емітив** машинно-вживані константи з контракту:
   - Rust: `pub const NUMERIC_DOMAINS: &[u16] = &[24,48,96,192];` + `next = 2 * w`;
   - Zig: той самий масив для `domain_ladder.zig`/`domain_e3_numeric.zig`;
   - Python: спільний модуль (замість копій у `scripts/*` та бенчмарках).
   Код імпортує згенероване — не повторює числа.
3. **Чекер як гейт.** `check-numeric-domain-ratification.py` уже існує; розширити його так, щоб він **валів на розходженні**: будь-який споживач, що має власну копію чисел/правила, мусить збігатися із контрактом, інакше fail-closed.
4. **Один вихід, багато входів.** «Двійкове vs десяткове» теж описати **в контракті** (зараз воно розсіяне: `language-contract.lisp`, `my-lisp-constitution.lisp`, `RELEASE-EVIDENCE.md`, `tasks.lisp`, бенчмарки), а не в кожному документі окремо.

## 4. Межі

- Це **не** пропозиція змінити саму семантику D24/D48/… — лише **прибрати дублювання** його визначення.
- Генерація стосується **машинно-вживаних** чисел/ширин. Прозаїчні пояснення в документах можуть лишатися, але мусять посилатися на контракт, а не переписувати правило.
- Нормативні рішення (що саме є авторитетом, які ширини канонічні) — за власником; тут лише карта дублювання й план.
