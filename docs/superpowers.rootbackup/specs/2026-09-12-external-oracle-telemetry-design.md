# External Oracle та доказова телеметрія — архітектурна специфікація

**Статус:** схвалений напрям із Linear `WSM-5`, деталізований перед реалізацією 2026-09-12.

## Мета

Побудувати перший відтворюваний вертикальний зріз, у якому одна фікстура з
авторитетного `tests/fixtures/conformance.my`:

1. отримує стабільний `F-…` ідентифікатор із `tests/fixtures/inventory.my`;
2. формально перекладається з my-lisp AST у Wolfram Language;
3. перевіряється незалежним зовнішнім обчислювачем;
4. порівнюється з власним `expected` корпусу окремо для кожного backend;
5. породжує machine-readable evidence;
6. лише після валідації проєктується у подію PostHog.

Перший обов'язковий witness — `F-8bc31cae9e7e39b9`:

```lisp
(/ 5 6 8 7) ; => 5/336
```

## Межа влади

`language-contract.my`, ратифіковані ADR та
`tests/fixtures/conformance.my` лишаються семантичною владою. Wolfram не
визначає значення my-lisp і не виправляє корпус. Він є незалежним свідком для
виразів, переклад яких adapter може довести структурно.

Кожен backend порівнюється з `expected`/`error` власної фікстури. Заборонено:

- проголошувати один backend оракулом для іншого;
- перетворювати `unsupported` на `pass`;
- виводити семантику оператора з його написання, якщо registry уже має його
  semantic ID;
- перефразовувати AST природною мовою перед зовнішнім обчисленням;
- створювати PostHog-подію до отримання й валідації фактичного результату.

## Розглянуті підходи

### 1. Природномовний запит до Wolfram

Відхилено. Формулювання «5/6 divided by 8/7» означає `(5/6)/(8/7)` і дає
`35/48`, тоді як my-lisp `(/ 5 6 8 7)` є лівим fold та дає `5/336`.
Зовнішній сервіс правильно обчислив іншу програму; така межа не є доказовою.

### 2. Corpus-driven `xtask` із двофазним виконанням

Обрано. Локальний детермінований етап читає corpus та registry, будує
версійований request. Зовнішній host виконує точний Wolfram Language-код.
Другий локальний етап перевіряє response, створює evidence й телеметричну
проєкцію. CI перевіряє переклад і валідацію без мережі та секретів.

### 3. Прямі Wolfram/PostHog HTTP-виклики з CI

Відкладено. Це потребує двох секретів, робить звичайні PR-перевірки залежними
від мережі та змішує детермінований semantic gate з доступністю зовнішніх
сервісів. Пізніше окремий scheduled workflow може споживати той самий протокол.

## Компоненти

### `semantic_registry_export`

Публічна механічна проєкція отримує операцію
`semantic_id_for_admitted_surface(name)`. Вона не надає операторові значення,
а лише повертає opaque ID з `lib/surface/semantic-registry.wsm`.

External adapter підтримує першу скінченну таблицю значень за semantic ID:

| Semantic ID | my-lisp операція | Wolfram-переклад |
|---|---|---|
| `0104` | сума | `Total[{…}]` |
| `1001` | віднімання/заперечення | unary `Minus[x]` або `Fold[Subtract,{…}]` |
| `1002` | добуток | `Times[…]` |
| `1003` | ділення/обернене | unary `1/x` або `Fold[Divide,{…}]` |

Таблиця належить adapter-у: вона описує доказово підтриману зовнішню
проєкцію, а не додає нові примітиви до мови.

### `xtask external-oracle export`

Команда читає `conformance.my` та `inventory.my` позиційно, як чинний
`scripts/oracle-batch.wsm`, але fail-closed перевіряє однакову кількість і
правильну форму записів. Вона відбирає лише фікстури, які:

- мають `expected`, а не `error`;
- позначені `S1`;
- містять лише exact numeric literals та підтримані arithmetic semantic IDs;
- є одним виразом без effects, bindings або host capabilities.

Для кожної підтриманої фікстури команда виводить один запис:

```lisp
(external-oracle-request
  (protocol . external-oracle/1)
  (fixture-id . "F-8bc31cae9e7e39b9")
  (source-digest . "sha256:…")
  (contract-revision . (6 0))
  (oracle . wolfram-language)
  (query . "Fold[Divide, {5, 6, 8, 7}]")
  (expected . "5/336"))
```

Непідтриманий вираз не апроксимується: команда повертає
`(outcome . unsupported)` із машинною причиною.

### `xtask external-oracle verify`

Команда приймає request і response, перевіряє `protocol`, `fixture-id`,
`source-digest`, `contract-revision`, назву oracle та точний рядок результату.
Вона формує один із чотирьох outcome:

```text
pass | mismatch | unsupported | error
```

`pass` можливий лише коли corpus `expected`, зовнішній `actual` і нормалізоване
exact-значення збігаються. Десяткове наближення не може підтвердити exact
fixture.

### Backend report

Після валідації зовнішньої відповіді команда будує матрицю спостережень, але
не вигадує відсутніх запусків:

- `native` береться зі свіжого локального виконання або з чинного
  `oracle-results.my` разом із його власними revision/digest;
- `meta-eval` береться зі свіжого виконання; corpus `meta-eval-gap` дозволяє
  лише outcome `unsupported`, ніколи не `pass`;
- `wsm-native` імпортує окремий backend evidence; corpus-статус `pending`
  проєктується як `unsupported` із причиною `no-executable-evidence`;
- `wolfram-language` є окремим external-oracle observation, а не backend
  my-lisp.

Кожен рядок несе `observation-source`: `fresh-execution`,
`recorded-evidence`, `declared-gap` або `external-response`. Старий запис із
іншим commit/contract не стає свіжим: він лишається видимим як historical і
не може задовольнити current gate.

### Evidence

Валідований результат записується за чинною конвенцією:

```text
evidence/S1/wolfram/<my-lisp-short-sha>.my
```

Запис розширює наявну форму `(evidence …)` полями `schema`, `fixture-id`,
`source-digest`, `contract-revision`, `oracle`, `oracle-query` та `run-id`.
Він містить фактичні `expected`, `actual` і `result`; `fail` так само допустимий
для коміту, як `pass`.

### PostHog projection

Після успішної валідації `xtask` уміє вивести JSONL envelope, але не знає
ключів і не здійснює мережевий виклик. Подія має ім'я
`lisp_oracle_case_completed` і такі обов'язкові properties:

```text
repository, commit_sha, contract_version,
fixture_id, expression_digest,
backend, oracle, observation_source, evidence_class,
expected, actual,
outcome, exactness,
duration_ms, run_id
```

Окремий host uploader може відправити envelope лише за явно налаштованих
`POSTHOG_HOST` і `POSTHOG_PROJECT_API_KEY`. Секрет не читається Lisp-кодом, не
зберігається у evidence й не друкується в лог.

## Потік даних

```text
conformance.my + inventory.my + semantic-registry.wsm
                         ↓
              deterministic export
                         ↓
               external-oracle/1 request
                         ↓
                 Wolfram Language host
                         ↓
               external-oracle/1 response
                         ↓
          local validation against corpus expected
                    ↙                 ↘
          WSM evidence             JSONL projection
                                         ↓
                              optional PostHog uploader
```

## Обробка помилок

- corpus/inventory drift — hard error до генерації request;
- невідомий або непідтриманий semantic ID — `unsupported`, без підстановки;
- кілька top-level форм — `unsupported` у першій версії;
- inexact value — `unsupported` для S1 exact witness;
- нульовий дільник — у першому зрізі `unsupported`, бо named-error parity є
  окремою задачею;
- response з іншим digest/revision/fixture — hard protocol error;
- синтаксично неканонічний actual — error, не string comparison;
- exact actual, що не дорівнює expected — `mismatch` і допустимий evidence;
- відсутній PostHog secret — локальний evidence лишається чинним, upload
  пропускається з явним повідомленням без витоку даних.

## Тестування

TDD починається з регресії, яка вимагає:

```text
(/ 5 6 8 7)              → Fold[Divide,{5,6,8,7}] → 5/336
(/ (/ 5 6) (/ 8 7))      → Divide[5/6,8/7]        → 35/48
```

Перша регресія падає, якщо adapter групує останні два аргументи. Далі окремі
тести покривають unary `-`, unary `/`, нуль- і багатоаргументні `+`/`*`,
вкладені точні дроби, великі цілі, surface spellings однієї semantic identity,
unsupported forms, digest/revision mismatch, exact mismatch і JSON escaping.

CLI integration test перевіряє реальні файли corpus/inventory. CI запускає:

```sh
cargo test -p xtask
cargo test -p my-lisp semantic_registry
cargo run -p xtask -- external-oracle export --fixture F-8bc31cae9e7e39b9
cargo run -p xtask -- verify
```

Живий Wolfram/PostHog smoke не блокує звичайний PR. Він стає окремим
scheduled/manual workflow після налаштування секретів.

## Заплановані файли

- `crates/my-lisp/src/lib.rs` — публічна reverse-проєкція surface → semantic ID;
- `crates/xtask/Cargo.toml` — залежності механізму;
- `crates/xtask/src/main.rs` — нові CLI subcommands;
- `crates/xtask/src/external_oracle.rs` — corpus loading, AST translation,
  protocol validation, backend report та projections;
- `crates/xtask/tests/external_oracle_cli.rs` — black-box CLI tests;
- `evidence/S1/wolfram/<sha>.my` — перший фактичний Wolfram witness;
- `.github/workflows/ci.yml` — детермінований offline gate без секретів;
- `docs/testing.md` — карта нового executable evidence.

## Критерії завершення

1. Обидва арифметичні дерева вище дають різні, правильні Wolfram-запити й
   різні результати `5/336` та `35/48`.
2. Ідентичність операції береться з registry; alternative surface не потребує
   другого hardcoded translation path.
3. Native, meta-eval та WSM-native outcomes не зливаються один з одним і не
   підміняють корпус.
4. Перший live response створює відтворюваний evidence із commit SHA,
   contract revision, source digest та query.
5. PostHog envelope виникає лише з валідованого response.
6. Повний workspace test/build/clippy та `xtask verify` проходять у штатному
   Rust/Guix середовищі без попереджень.

## Відоме середовищне обмеження поточної сесії

У Work-контейнері, де створено цю специфікацію, відсутні `cargo`, `rustc` і
`guix`. Тому жодна майбутня заява про проходження Rust-тестів не може спиратися
на цей контейнер: red/green і повні gates треба виконати через GitHub Actions
або в заявленому WSL2 + Guix середовищі репозиторію.
