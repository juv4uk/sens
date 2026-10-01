# #1970 — Інвентар припущень Function8, перший обмежений прохід

Статус: **дослідження / лише читання**. Цей звіт не змінює runtime, контракти, reader, wire-формат або таблицю функцій.

## Результат

Припущення exact-8 — це не одна річ. Перший прохід по репозиторію розділяє чотири суттєво різні випадки:

1. **Семантичні та reader-блокери** — їх потрібно змінити до того, як variable-width identity стане production-законом мови.
2. **Блокери серіалізації/схеми** — можуть співіснувати через версіонування, але новому канонічному формату потрібне variable-width представлення.
3. **Backend fast paths** — 8-бітні механізми механічно корисні й не мають зникати лише через зміну онтології.
4. **Тести/документація/історія** — важливі для ratchet-ів і ясності, але не є runtime-семантикою.

Головний закон міграції:

```text
прибрати exact-width authority
!=
прибрати кожен one-byte mechanism
```

Таблиця `Sens8 -> [Option<PrimitiveFn>; 256]` може лишитися хорошою backend-оптимізацією для legacy/anchor-функцій навіть тоді, коли канонічна identity стане bounded variable-width word/path.

## Жорсткі блокери в SENS

Перший прохід визначає прямими блокерами production variable-width identity:

- `language-contract.lisp`: `sid8-function-space` явно проголошує повний function space рівно 256 восьмибітними словами.
- `contracts/core-profile-contract.lisp`: `shared-function8` робить exact width частиною cross-Core authority.
- `scripts/sid8-only-ontology-guard.sh`: CI охороняє саме exact width, а не лише корисний закон «без named ontology».
- `crates/sens/src/sens.rs`: `Sens` зараз є alias для `Sens8`; constructor/macro вимагає рівно вісім бітів.
- `crates/sens/src/parser.rs`: binary token стає `ExprKind::Sid` лише коли `token.len() == 8`.
- `crates/sens/src/syntax.rs`: FASL/SID-представлення зберігає один packed byte.
- registry/ownership/numeric-inventory validators містять `^[01]{8}$` як schema authority.
- `knowledge/guard-reference.lisp` досі описує exact-eight identity як standing owner law.
- CI/workflow callers досі запускають кілька exact-width validators.

Їх слід мігрувати лише після ратифікації дослідницької моделі; цей аудит **не** пропонує послаблювати їх зараз.

## Cross-repository blocker: CML

Read-only аудит `juv4uk/cml` показав, що CML не просто використовує один старий adapter. Exact-8 identity зараз проходить через саму compiler boundary:

- `Expr::Sid(sens::Sid8)` в AST;
- `Ir::Sid(sens::Sid8)` у backend-neutral IR;
- direct-source parser розпізнає canonical callable identity лише за exact width 8;
- `semantic.rs` трактує весь `00000000..11111111` як function space мови;
- `build.rs` парсить registry identity в `u8`, генерує `Sid8` і форматує IDs рівно у вісім бітів;
- `upstream_sid_bridge.rs` зводить registry-owned callables у `Sid8`;
- CML має vendored старий SENS language contract із `sid8-function-space`;
- `.github/workflows/sid8-issue-lifecycle-guard.yml` автоматично перевідкриває CML issue 238, якщо закрити його «permanent SID8-only constitution».

Отже CML треба вважати **реальною consumer migration dependency** до того, як SENS почне віддавати компілятору нові variable-width callable identities.

Але це все одно **не** означає, що кожна Sid8 backend-specialization мусить зникнути. Відомі восьмибітні anchors можуть лишитися прямими fast paths після того, як CML отримає width-neutral canonical identity carrier.

## Механізми, які можуть пережити міграцію

Такі речі не доводять, що сама мова повинна залишатися exact-8:

- `PRIMITIVE_TABLE: [Option<PrimitiveFn>; 256]`;
- `packed_byte()` direct indexing;
- legacy one-byte wire/FASL Function8 frames;
- deprecated `Sid8 = Sens8` compatibility adapter;
- наявні 8-бітні generated registry rows;
- benchmark parsers для історичної таблиці;
- CML backend pattern matches для наявних Sid8 anchors.

Майбутній runtime/compiler цілком може мати:

```text
canonical variable-width identity
        |
        +-- legacy/anchor Sens8 -> O(1) / direct backend fast path
        |
        +-- longer/path identity -> generator / sparse / derived route
```

без повернення плоскої semantic ontology з 256 рівноправних функцій.

## Аудит runtime-carrier

Внутрішній Rust-шар підтвердив ще одне важливе розділення:

- `Value::Sid(Sens8)` і `ExprKind::Call(Sens8, ...)` є справжніми canonical-carrier blockers: майбутня variable-width identity не може пройти через них без втрати.
- `Environment::code_slots` зараз зводить ключ до `sid.packed_byte()`; це блокує variable-width визначення мовою навіть після узагальнення reader/AST.
- necessary-form routing також порівнює generated rows через packed byte і згодом має споживати width-neutral identity.
- host-capability registry `HashMap<Sens8, SensHostFn>` — інший випадок: він може лишитися compatibility/mechanism map для наявних host anchors, якщо майбутні variable-width identities не потребують host registration.

Це підсилює правило міграції: **спочатку узагальнюємо семантичні carriers; вузькі mechanism maps залишаємо вузькими, якщо їхній домен справді такий.**

## Порядок міграції, який випливає з evidence

Не варто мігрувати implementation знизу догори. Безпечний напрям залежностей:

```text
1. ратифікувати width-neutral identity law
2. замінити exact-width semantic/CI authority
3. ввести width-neutral canonical identity representation у SENS
4. навчити reader/AST/registry schema
5. version FASL/wire
6. відкрити нову identity через SENS API
7. мігрувати CML AST/IR/build-time registry bridge
8. зберегти або адаптувати 256-byte / Sid8 fast paths там, де вони вигідні
9. мігрувати tests/docs/bench tooling
```

Такий порядок не дозволяє механічному рефакторингу випадково стати semantic authority і не дає CML через public API знову зафіксувати SENS на старому типі.

## Координація

Це все ще bounded audit. Решту можна паралелити без production-змін:

- додаткові Rust Value/Environment/code-slot типи;
- necessary forms та semantic-registry consumers;
- FASL/wire call sites і versioning assumptions;
- інші cross-repository consumers;
- відділення archived documentation від active authority.

Machine-readable рядки лежать у `docs/research/1970-function8-assumption-inventory.tsv`.

## Принцип

**Залишаємо 8 біт там, де це корисне представлення; прибираємо 8 біт там, де це необґрунтована семантична аксіома.**
