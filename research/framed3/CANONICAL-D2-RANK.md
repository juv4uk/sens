# Універсальна «Рамка-3»: точний ранговий простір D2 (дослід)

**Дата:** 11.10.2026. **Статус:** доказовий корпус для канонічного Rust-читача, не файловий формат і не production-енкодер. Жодних нових Git-гілок або змін у поточному Rust-кодеку.

## Проблема, яку виправлено

Старий `grammar_rank_research.py` помилково зараховував D2:00 і D2:11 до звичайних двобітних атомів. Чинний Rust `canonical_reader.rs` визначає **всі** D2-слова як структурні:

| Точне D2 | Семантика читача |
|---|---|
| `00` | довільна кількість пропусків між виразами та біля CLOSE/DOT |
| `01` | закрити поточний список; на зовнішньому рівні — помилка |
| `10` | відкрити вкладений список |
| `11` | крапкова пара після щонайменше однієї голови і з **рівно одним** хвостом |

`W1` та `W3…W9` зберігають **точні ширини, біти й початкові нулі**; D3 `000` — порожнє значення, але все одно один вираз. Вільні координати доменів не переводяться автоматично в допустимі виклики.

## Реалізовано

- [`canonical_d2_rank_research.py`](canonical_d2_rank_research.py) — DP за залишком бітів і стеком чотирьох контекстів: `EMPTY`, `ITEMS`, `DOT_TAIL`, `DOT_CLOSE`. Ранг визначено за точною шириною, потім unsigned-значенням слова. `rank` та `unrank` взаємно обернені у підтримуваному однорамковому просторі.
- [`test_canonical_d2_rank_research.py`](test_canonical_d2_rank_research.py) — **незалежний рекурсивний оракул** D2 і вичерпний перебір усіх типованих послідовностей із сумарною внутрішньою довжиною `0…8` біт, а також позитивні/негативні вкладені, крапкові й `QUOTE`-фікстури.
- [`canonical_d2_rank_research.rs`](../../crates/sens/tests/canonical_d2_rank_research.rs) — незалежний Rust-паритет справжнього `parse_canonical_binary` проти того ж обмеженого структурного корпусу (обидва реалізовані окремо); перевірка D1 і D3…D9 та exact-width.
- Обидві перевірки Python (`python3` і `python3 -O`) та Rust запускаються через наявний [`framed3-research.yml`](../../.github/workflows/framed3-research.yml).

Для **однорамкового** об'єкта з фіксованими зовнішніми словами `10 … 01` і відомою ззовні **точною сумою бітів внутрішніх слів** відтворений повний корпус має такі місткості:

| Бітів усередині | Усі типовані послідовності | Синтаксично допустимі D2 |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 2 | 2 |
| 2 | 8 | 5 |
| 3 | 32 | 20 |
| 4 | 128 | 82 |
| 5 | 512 | 292 |
| 6 | 2048 | 1092 |
| 7 | 8192 | 3996 |
| 8 | 32768 | 14793 |
| 9 | 131072 | 54422 |
| 10 | 523264 | 199362 |

Перші дев'ять рядків (`0…8`) підтверджено повним незалежним перебором; `9…10` — точні значення рекурентного DP, **не** вичерпно перевірені другим переліком. Межа реалізації — **20 внутрішніх бітів** (поза нею fail-closed). Вона не встановлює межу фізичного універсального кодека.

## Важлива межа надлишковості

Цей рівень вилучає **доведено неможливі D2-структури**, а не всі семантично неможливі програми. `((АТОМ))` канонічний D2 може синтаксично розібрати, але це **недопустима виконувана програма** через арність `АТОМ`. Натомість `(QUOTE ((АТОМ)))` має зберігати вкладене дерево як **дані**. Доказ контекстної арності наведено окремо у [`semantic_redundancy_research.py`](semantic_redundancy_research.py). Не робити `not-proven-impossible` тотожним `executable`.

Ранг тут **зберігає кожне слово `00` дослівно**. Незалежний читач дозволяє багато еквівалентних за AST послідовностей із різним числом роздільників; без нового явного контракту їх не можна згорнути, якщо вимагається lossless exact typed words. Ці варіанти **не** називаємо «усунутою структурною надлишковістю».

## Фізична межа

`rank_bytes_at_known_length` вираховує **лише тіло**, за умови, що точне `inner_bits` вже відоме декодеру. Це не готовий `.sens`: там потрібні незалежне обмеження програми, версія, profile, lengths, кількість коренів, padding, CRC/автентичність та безпечний EOF. Приклад для `inner_bits=0`: нуль байтів тіла **не** означає нуль байтів фізичного файла. Кошики старої моделі **118 на байт** не доводять 118 виконуваних SENS-програм і не переносяться в новий профіль.

Наступний крок для єдиного Rust-власника [#5439](https://github.com/juv4uk/sens/issues/5439): інтегрувати цей D2-контракт із контекстами `code/data`, підтримати атомарні й багатокореневі файли, довести ранг по **всіх** кандидатних режимах разом зі службовими байтами, виміряти спільний Rust corpus/CI. Дослід не замінює чинні `RAW/REPEAT`.

## Відтворення

```sh
python3 -m unittest discover -s research/framed3 -p 'test_canonical_d2_rank_research.py' -v
python3 -O -m unittest discover -s research/framed3 -p 'test_canonical_d2_rank_research.py' -v
cargo test --manifest-path crates/sens/Cargo.toml --test canonical_d2_rank_research -- --nocapture
```


## Rust candidate module in core (11.10.2026)

The algorithm is now ported from the Python research oracle to
[crates/sens/src/frame3_grammar.rs](../../crates/sens/src/frame3_grammar.rs)
and exported from `sens::frame3_grammar`. This is a strictly bounded
**grammar candidate**, not a new production mode. It provides:

- ExactWord(width, bits), preserving 1..9-bit identities and leading zeros.
- count_inner, rank_single_root and unrank_single_root using the exact D2
  separator/open/close/dot states; fixed outer 10/01 frame.
- encode_body_at_known_length / decode_body_at_known_length with strict
  integer-range and byte-width checks; the exact inner bit length MUST
  be provided by an authenticated/bounded external envelope.
- rank_binary_source_words / unrank_binary_source_words for direct
  in-process `BinarySourceWord` exchange. No textual bit rendering,
  no 8-bit truncation of D9, no historical symbol names.

[crates/sens/tests/frame3_grammar_rank.rs](../../crates/sens/tests/frame3_grammar_rank.rs)
independently compares **all exact 0..8 inner-bit word streams** against
the actual canonical Rust reader and checks dense 0-based rank coverage.
It also tests every width/value D1–D9, separators, dotted pairs, nested
quotation data, unused codes, truncation and invalid bounds.

[Focused Rust CI #38124757032](https://github.com/juv4uk/sens/actions/runs/38124757032)
is **SUCCESS**, including the new Rust tests, `cargo clippy -D warnings`,
and existing Universal Frame3 codec tests. This does not override
separate failing Hosted CI or physical-file authority gates.

**Do not silently switch .sens to this profile:** the live
`universal_frame3.rs` codec still supports RAW/REPEAT only. Future
codec work needs a versioned mode with full-file length/word-count/
integrity overhead, explicit code/data semantic admission, atom-only
and multiple roots, and paired physical byte/performance evidence.
`((ATOM))` is structurally parseable but not executable; a quote of
it remains valid data, not an executable-call witness. The Rust grammar
rank does not yet remove these semantically impossible calls.


## Conservative D3 executable-code witness in Rust

The same crate now exports
[crates/sens/src/frame3_semantic.rs](../../crates/sens/src/frame3_semantic.rs)
as `sens::frame3_semantic`. `check_executable_code(&Expr)` reads the
canonical D2 AST and uses **only ratified exact D3 function bits**:

- QUOTE(001), ATOM(010), CDR(011), CAR(100): exactly one argument;
- EQ(101), CONS(111): exactly two arguments;
- QUOTE data is **never recursively checked as executable code**;
- bad evaluated operands of the other five fixed-arity forms may prove a
  call impossible, as can an impossible evaluated nested head;
- COND(110), dynamic heads, higher domains and unknown forms remain
  `NotProvenImpossible`, **not valid by implication**.

Negative/positive Rust tests live in
[frame3_grammar_rank.rs](../../crates/sens/tests/frame3_grammar_rank.rs)
next to the actual D2 reader and typed-identity parity tests. For
example, `((ATOM))` is rejected **as executable code**, while
`(QUOTE ((ATOM)))` is retained **as data**.

This is an *admissibility witness*, **not yet a semantics-aware dense
rank over only valid programs**. No physical code points are removed
until a formally countable executable profile with distinguishable
code/data contexts exists. In particular the structural rank stays
lossless for ALL syntactically accepted D2 data.
