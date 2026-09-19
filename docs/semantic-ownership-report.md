# Звіт про семантичну власність

> Згенеровано детерміновано з `knowledge/semantic-ownership.lisp`.
> Звіт рахує **аудитовані поведінки/відповідальності**, а не LOC і не повноту всієї мови.
> Жодне число нижче не є «відсотком self-hosting».

## Підсумок

- Аудитованих ownership rows: **34**
- Підтверджених ownership rows: **34**
- Часткових ownership rows: **0**
- Підтверджених host/Rust→Lisp semantic migrations: **2**
- Підтверджених записів migration ledger загалом: **8**
- Залишкових host semantic-policy candidates: **0**
- Підтверджених host mechanism/observation/authorization rows, не позначених policy candidate: **7**
- Ownership rows зі статусом unknown: **0**

## Класи власності

| категорія | аудитовані рядки |
|---|---:|
| `canon-ground` | 1 |
| `canon-operation` | 7 |
| `derived-tooling` | 1 |
| `host-authorization` | 3 |
| `host-mechanism` | 3 |
| `host-observation` | 1 |
| `lisp-owned` | 16 |
| `necessary-form` | 2 |

## Шари

| категорія | аудитовані рядки |
|---|---:|
| `bootstrap` | 3 |
| `canon` | 8 |
| `host-capability` | 6 |
| `knowledge` | 3 |
| `reasoning` | 5 |
| `self-hosting` | 1 |
| `stdlib` | 6 |
| `tooling` | 2 |

## Епістемічний статус

| категорія | аудитовані рядки |
|---|---:|
| `confirmed` | 34 |

## Кандидати на перевірку host-policy ownership

- немає

## Підтверджений журнал міграцій

- `canon-surface-authority` — `host-hardcoded` → `registry-data` у `668794caf6f3e2e1d0d6c8e740f218cc6ef04db9`: Canon stable surface routing перенесено у shared numeric semantic registry projection
- `core-host-capability-split` — `core-os-code` → `host-adapter` у `f565f6692c36a97f80afe0233f0bdb8dca506b81`: OS-touching filesystem/process/TCP операції перенесено з my-lisp core у my-lisp-host
- `defmacro-fallback-to-lisp` — `host-mechanism` → `lisp-owned` у `3fff9e9fbb7171a81ba128baedd68f093fc0c65b`: Rust defmacro evaluator fallback видалено; поведінкою володіє language macro path
- `list-rust-to-lisp` — `host-mechanism` → `lisp-owned` у `efdd9252fd4ca4af4503b219ab3ae79130ef0e64`: Rust special form list видалено; list визначено в lib/core.lisp
- `macro-peer-surface-authority` — `host-hardcoded` → `registry-data` у `baa03b7acf0793bec3184a48099c484231922bea`: 00001010 stable і compatibility peer names перенесено з loader literals у registry admission
- `necessary-form-surface-authority` — `host-hardcoded` → `registry-data` у `3fa2ae1f5e5786cd5c0b41489648a23bb1f405f5`: LAMBDA/DEFINE stable surface routing перенесено з Rust spelling tables у numeric registry projection
- `peer-builtin-surface-authority` — `host-hardcoded` → `registry-data` у `dd4d9ae7d7bccbe465a0ae8ceb1b2f17f5f80f4e`: Arithmetic/comparison peer names перенесено з Rust arrays у registry-derived bindings
- `tooling-human-key-to-semantic-id` — `human-spelling-tooling` → `semantic-id-tooling` у `e8f60f659199686205376ca4fd1c570034c05de6`: Tooling syntax discovery перенесено з human spelling keys на semantic identities

## Аудитовані поведінки

| key | semantic id | owner | layer | status | поведінка |
|---|---|---|---|---|---|
| `backward-reasoning` | `—` | `lisp-owned` | `reasoning` | `confirmed` | Backward-chaining пошук доказу й побудова provenance |
| `canon-atom` | `00000010` | `canon-operation` | `canon` | `confirmed` | ATOM: first-class канонічна операція |
| `canon-car` | `00000101` | `canon-operation` | `canon` | `confirmed` | CAR: канонічна операція проєкції першого елемента |
| `canon-cdr` | `00000110` | `canon-operation` | `canon` | `confirmed` | CDR: канонічна операція структурного залишку |
| `canon-cond` | `00000111` | `canon-operation` | `canon` | `confirmed` | COND: канонічна short-circuit syntax |
| `canon-cons` | `00000100` | `canon-operation` | `canon` | `confirmed` | CONS: канонічна операція побудови |
| `canon-empty-list` | `—` | `canon-ground` | `canon` | `confirmed` | Canon 0: порожній список як ground object |
| `canon-eq` | `00000011` | `canon-operation` | `canon` | `confirmed` | EQ: канонічна операція тотожності |
| `canon-quote` | `00000001` | `canon-operation` | `canon` | `confirmed` | QUOTE: evaluator meaning і зарезервована surface resolution |
| `filesystem-authorization` | `—` | `host-authorization` | `host-capability` | `confirmed` | Per-session filesystem read/write scope і host canonicalization enforcement |
| `gensym` | `—` | `lisp-owned` | `stdlib` | `confirmed` | Політика свіжого символу складена в Lisp зі string-операцій і monotonic observation |
| `immutable-worlds` | `—` | `lisp-owned` | `knowledge` | `confirmed` | Immutable world snapshots і явні переходи стану світу |
| `knowledge-journal` | `—` | `lisp-owned` | `knowledge` | `confirmed` | Append-only журнал знань і guarded knowledge admission |
| `list-constructor` | `—` | `lisp-owned` | `stdlib` | `confirmed` | Варіадичний list-конструктор виведений із lambda/rest семантики самої мови |
| `macro-definition` | `00001010` | `lisp-owned` | `bootstrap` | `confirmed` | Поведінка визначення макросів виведена у lib/macro.lisp поверх вузького make-macro substrate |
| `meta-evaluator` | `—` | `lisp-owned` | `self-hosting` | `confirmed` | Lisp-owned metacircular evaluator witness; усі 34 required parity rows підтверджені machine evidence matrix |
| `monotonic-clock` | `—` | `host-observation` | `host-capability` | `confirmed` | Monotonic nanosecond observation без calendar policy |
| `necessary-define` | `00001001` | `necessary-form` | `bootstrap` | `confirmed` | DEFINE: evaluator-controlled immutable binding form |
| `necessary-lambda` | `00001000` | `necessary-form` | `bootstrap` | `confirmed` | LAMBDA: evaluator-controlled побудова closure |
| `outcome-narration` | `—` | `lisp-owned` | `reasoning` | `confirmed` | Людське пояснення поверх структурованих reasoning outcomes |
| `process-authorization` | `—` | `host-authorization` | `host-capability` | `confirmed` | Per-session process allowlist, який Lisp-код не може видати собі сам |
| `process-public-result` | `—` | `lisp-owned` | `stdlib` | `confirmed` | Публічна інтерпретація process-run result поверх process-run-raw |
| `process-run-raw` | `—` | `host-mechanism` | `host-capability` | `confirmed` | OS process execution і захоплення raw bytes |
| `reason-index` | `—` | `lisp-owned` | `reasoning` | `confirmed` | Скінченний immutable predicate index із точним linear fallback |
| `reasoning-outcomes` | `—` | `lisp-owned` | `reasoning` | `confirmed` | Data-only outcome algebra: proved/unknown/partial/blocked/disputed/invalid |
| `surface-registry-projection` | `—` | `host-mechanism` | `tooling` | `confirmed` | Rust projection/index mechanism читає numeric surface authority, не володіючи людськими spelling |
| `tcp-authorization` | `—` | `host-authorization` | `host-capability` | `confirmed` | Per-session connect/listen allowlists, перевірені до OS-операції |
| `tcp-resource-representation` | `—` | `host-mechanism` | `host-capability` | `confirmed` | Concrete TcpStream/TcpListener storage is confined to core Value; semantics and OS operations remain host-only; opaque Rc<dyn Any> experiment proves representation can be erased when a real portability trigger appears |
| `tcp-text-semantics` | `—` | `lisp-owned` | `stdlib` | `confirmed` | Публічне декодування TCP text поверх raw socket bytes |
| `time-semantics` | `—` | `lisp-owned` | `stdlib` | `confirmed` | UTC/calendar/deadline meaning виводиться в Lisp із raw clock observations |
| `tooling-syntax-discovery` | `—` | `derived-tooling` | `tooling` | `confirmed` | Tooling metadata ключується semantic identity, а spelling отримує з registry |
| `translation-review` | `—` | `lisp-owned` | `knowledge` | `confirmed` | Валідація зовнішніх translation candidates і admission review |
| `unification` | `—` | `lisp-owned` | `reasoning` | `confirmed` | Уніфікація логічних змінних з occurs-check |
| `utf8-interpretation` | `—` | `lisp-owned` | `stdlib` | `confirmed` | Валідація та інтерпретація UTF-8 bytes → text |

## Правило інтерпретації

Знаменник кожного числа — лише checked-in аудитований інвентар вище. Більша кількість `lisp-owned` сама по собі не є прогресом, а host-owned observation чи authorization boundary сама по собі не є боргом. Зміна ownership є прогресом лише тоді, коли вона прибирає дубльовану семантичну владу або переносить policy до шару, який може нею володіти без послаблення evidence.
