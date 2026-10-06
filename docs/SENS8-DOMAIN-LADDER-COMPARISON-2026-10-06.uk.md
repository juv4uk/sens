# Sens8 проти чинної драбини D1–D7

**Дата зрізу:** 2026-10-06  
**Статус:** аналітична інвентаризація / migration evidence. **НЕ semantic authority.**  
**Чинна семантична влада:** `language-contract.lisp`, `knowledge/d1-d7-foundation.json`, ратифіковані domain laws та джерела, перелічені в `CURRENT.md`.

## Навіщо цей документ

Цей зріз відповідає на два окремі питання:

1. що з історичної плоскої 8-бітної таблиці Sens8 отримало доведеного наступника в чинній exact-width драбині;
2. які старі Sens8-операції не ввійшли до ратифікованого ядра D1–D7.

Ключове правило: **чинна драбина не є просто стисненим Sens8**.

```text
Sens8:
    один 8-бітний простір
    ↓
    функції, бібліотека, I/O, час, логіка, host-операції жили поруч

D1–D7:
    exact bits
    + exact domain
    + admitted/proved law
```

Однакова фізична ширина або історична назва не створює сучасної semantic identity.

## Джерела цього зрізу

Підрахунок зроблено з чинного `main`:

- `knowledge/d1-d7-foundation.json` — ратифіковані D1–D7;
- `crates/sens/src/semantic_registry_generated.rs` — 256 історичних Sens8 slot-ів і їхні surface-проєкції;
- `crates/sens/src/semantic_registry.rs` — явні legacy successor mappings;
- `crates/sens/src/eval/necessary_forms_generated.rs` — successor для необхідних форм LAMBDA/DEFINE;
- `contracts/core1-historical-sid-map.lisp` — незалежне історичне name/provenance evidence;
- `scripts/migrate-three-pass.py` — чинний алгоритм трьох проходів міграції.

## Загальна арифметика

Історичний Sens8 має 256 фізичних slot-ів.

```text
256 total Sens8 slots
183 assigned / named historical slots
 73 unused / empty slots

із 183 зайнятих:
 49 старих SID мають доведеного чинного наступника
134 зайняті старі SID не мають доведеного наступника в D1–D7

49 mapped old SIDs
→ 46 unique current semantic objects
```

Різниця між 49 і 46 виникає через злиття історичних дублетів/синонімів.

## Драбина зараз

| Домен | Ширина | Occupancy | Роль | Пряме спадкування Sens8 |
|---|---:|---:|---|---:|
| D1 | 1 | 2/2 | `NO`, `YES` | 0 |
| D2 | 2 | 4/4 | `OPEN`, `CLOSE`, `SEPARATOR`, `DOT` | 0 |
| D3 | 3 | 8/8 | фундамент Lisp/SENS | 8 |
| D4 | 4 | 16/16 | compact bootstrap/evaluator | 13 old SIDs → 11 unique current objects |
| D5 | 5 | 32/32 | розширена мова | 12 old SIDs → 11 unique current objects |
| D6 | 6 | 64/64 | алгоритмічна композиція | 16 |
| D7 | 7 | 126/128 | Sound/Text, digits, punctuation | 0 |

D1, D2 і D7 не є «перенесеними секторами» Sens8. Вони виникли як окремі exact-domain ролі.

## D3: історичне зерно пережило перехід повністю

```text
Sens8 00000000 empty-list → D3 000 EMPTY
Sens8 00000001 quote      → D3 001 QUOTE
Sens8 00000010 atom?      → D3 010 ATOM
Sens8 00000110 cdr        → D3 011 CDR
Sens8 00000101 car        → D3 100 CAR
Sens8 00000011 eq?        → D3 101 EQ
Sens8 00000111 cond       → D3 110 COND
Sens8 00000100 cons       → D3 111 CONS
```

Особливо важливо: сучасне `D3:000 EMPTY` не тотожне історичному 8-бітному payload `00000000` лише через числову форму. Зв'язок тут встановлений migration/provenance evidence, а сучасну identity визначає домен D3.

## Злиття старих SID у сучасній системі

### DEFINE

```text
Sens8 00001001 define ─┐
                       ├→ D4 0011 DEFINE
Sens8 00001011 def ────┘
```

### QUOTIENT

```text
Sens8 00001111 divide ───┐
                         ├→ D5 10111 QUOTIENT
Sens8 00010100 quotient ─┘
```

### NULL

```text
Sens8 00111100 string-empty? ─┐
                              ├→ D4 0101 NULL
Sens8 10101011 null? ─────────┘
```

Ці випадки показують, чому кількість історичних SID не дорівнює кількості сучасних semantic objects.

## Що не ввійшло до ратифікованої драбини

Нижче — 134 **зайняті** Sens8 identity без доведеного successor у чинних D1–D7.

Це не означає «134 втрачені примітиви». Велика частина старого Sens8 змішувала core semantics із бібліотечними, host, I/O, time, collection і knowledge-layer операціями.

| Старий пласт Sens8 | Кількість | Приклади |
|---|---:|---|
| macro mechanism | 1 | `defmacro` |
| математика / порівняння | 10 | `sqrt`, `isqrt`, `equalp?`, `<=`, `>=`, `divmod` |
| type predicates | 4 | `symbol?`, `string?`, `numeric-buffer?` |
| list conveniences | 5 | `pair`, `second`, `third`, `fourth`, `fifth` |
| text operations | 13 | `string-append`, `string-length`, `string-slice`, conversions |
| reader / printer | 5 | `print`, `princ`, `read`, `read-all`, `write-to-string` |
| environment | 1 | `env` |
| vector / numeric buffers | 11 | `vector-ref`, `i32-buffer`, `numeric-buffer-map` |
| time / timezone / deadline | 18 | `mono-ns`, `utc-now`, `timezone-detect`, deadlines |
| map / persistent vector | 11 | `map-get`, `map-insert`, `vec-conj`, `vec-nth` |
| knowledge / logic / proof | 33 | `unify`, `prove-goal`, `reason`, `evidence?`, `intent?` |
| language conveniences | 6 | `identity`, `gensym`, `and`, `or`, `->`, `->>` |
| host / system | 10 | JSON, SHA-256, process, TCP, file I/O |
| historical answer layer | 6 | `answer-not`, `answer-and`, `answer-or`, ... |
| **Разом** | **134** | |

## Повний залишок Sens8 без successor

### 1. Macro mechanism — 1

- `defmacro`

### 2. Математика / порівняння — 10

- `sqrt`
- `isqrt`
- `largest-chunk`
- `equalp?`
- `not-greaterp?` / `<=`
- `not-lessp?` / `>=`
- `nondecreasing-from?`
- `nonincreasing-from?`
- `equal?`
- `divmod`

### 3. Type predicates — 4

- `symbol?`
- `string?`
- `string<?`
- `numeric-buffer?`

### 4. List conveniences — 5

- `pair`
- `second`
- `third`
- `fourth`
- `fifth`

### 5. Text operations — 13

- `string-append`
- `string-length`
- `string-prefix?`
- `string-contains?`
- `string-first`
- `string-rest`
- `string-slice`
- `symbol->string`
- `string->symbol`
- `codepoint->string`
- `string->codepoint`
- `number->string`
- `digit->string`

### 6. Reader / printer — 5

- `print`
- `princ`
- `read`
- `read-all`
- `write-to-string`

### 7. Environment — 1

- `env`

### 8. Vector / numeric buffers — 11

- `vector`
- `make-vector`
- `vector-length`
- `vector-ref`
- `vector-set!`
- `i32-buffer`
- `f32-buffer`
- `numeric-buffer-type`
- `numeric-buffer-length`
- `numeric-buffer-ref`
- `numeric-buffer-map`

### 9. Time / timezone / deadline — 18

- `mono-ns`
- `unix-time-now`
- `ntp-query-raw`
- `timezone-declarations-raw`
- `utc-now`
- `utc-from-unix`
- `unix-time-observation->utc`
- `milliseconds-from-nanoseconds`
- `mono-ms`
- `timezone-name`
- `timezone-detect`
- `timezone-offset-seconds`
- `deadline-reached?`
- `deadline-reached-at?`
- `elapsed-ns`
- `deadline-from`
- `deadline-after-ns`
- `internet-time-sync`

### 10. Map / persistent vector — 11

- `map-empty`
- `map-get`
- `map-insert`
- `map-contains?`
- `map->list`
- `vec-empty`
- `vec-conj`
- `vec-count`
- `vec-nth`
- `vec->list`
- `vec-from-list`

### 11. Knowledge / logic / proof — 33

- `is-fact?`
- `describe`
- `collect-facts-about`
- `contains-atom?`
- `forward-in`
- `reason-in`
- `check-conflict?`
- `module-known?`
- `module-clauses-now`
- `prove-goal`
- `prove-goals`
- `explain-proof`
- `source-of`
- `provenance`
- `reason`
- `reason-explain`
- `unify`
- `logic-var`
- `var?`
- `apply-subst`
- `walk`
- `occurs-check?`
- `claim?`
- `claim-statement`
- `claim-review`
- `evidence?`
- `evidence-method`
- `evidence-outcome`
- `observation?`
- `observation-statement`
- `intent?`
- `intent-goal`
- `supporting-evidence`

### 12. Language conveniences — 6

- `identity`
- `gensym`
- `and`
- `or`
- `thread-first` / `->`
- `thread-last` / `->>`

### 13. Host / system — 10

- `json-parse`
- `sha256-hex`
- `process-run`
- `tcp-read`
- `tcp-write`
- `tcp-listen`
- `read-file`
- `write-file`
- `invoke`
- `binary`

### 14. Historical answer layer — 6

- `answer-not`
- `answer-and`
- `answer-or`
- `answer-weaken`
- `answer-atom`
- `answer-eq`

## Що це означає архітектурно

Старий Sens8 дозволяв таку плоску сусідність:

```text
CAR
sqrt
TCP-WRITE
timezone-detect
prove-goal
string-length
sha256-hex
MAP
```

Усі вони були просто жителями одного 8-бітного простору.

Чинна драбина робить інше:

```text
D1  predicate truth
D2  structure
D3  semantic seed
D4  bootstrap / evaluator
D5  extended language
D6  algorithmic composition
D7  Sound / Text
```

Отже, вихід 134 старих операцій із ядра — не автоматично втрата функціональності. Це переважно **розділення semantic core і library/host capabilities**.

## D7 не є новим місцем для старої string-library

D7 містить Sound/Text residency: звуки, текстові знаки, digits, punctuation і пов'язані текстові ролі.

Це не означає, що старі:

- `string-length`
- `string-slice`
- `print`
- `read`
- `symbol->string`

автоматично стають D7-функціями.

**Text object / text representation ≠ library operation over text.**

Так само старий Sens8-код не можна автоматично перенести в D8 лише тому, що D8 має ширину 8 біт.

## Research observation: knowledge/logic cluster

Найбільший цілісний залишок — **33 knowledge/logic/proof операції**.

Вони утворюють виразний історичний кластер:

```text
logic-var
    ↓
unify / apply-subst / occurs-check
    ↓
prove-goal / prove-goals
    ↓
reason / reason-explain
    ↓
evidence / observation
    ↓
intent
```

Це лише **research observation**. Воно не ратифікує нового домену, не резервує бітів і не надає цим операціям current semantic identity.

Коректний наступний крок для такого кластеру — спочатку незалежно знайти закони, залежності й мінімальний базис, а вже потім перевіряти, чи взагалі потрібна окрема exact-width residency.

## Висновок

Перехід Sens8 → D1–D7 краще описувати не як compression, а як **semantic factorization**:

```text
плоска таблиця 8-bit functions
              ↓
розділення ролей
              ↓
exact-width domains
              ↓
core ≠ library ≠ host ≠ text ≠ knowledge system
```

Найстійкіша частина історичного Sens8 — D3 Lisp seed. Далі нова драбина все менше копіює стару таблицю і все більше формується законами та структурою самої мови.
