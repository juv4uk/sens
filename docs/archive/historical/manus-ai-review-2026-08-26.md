# Повний технічний огляд `my-lisp`

**Статус огляду:** evidence-based, read-only.
**Репозиторій:** [`juv4uk/my-lisp`](https://github.com/juv4uk/my-lisp).
**Зафіксований commit:** `a662dc76c99312c218d5a81047bd2a86ae316886` (`main`, 2026-08-26 00:50:54 UTC).
**Автор огляду:** Manus AI.
**Мова огляду:** українська.

> **Короткий висновок.** `my-lisp` уже не схожий на «інтерпретатор для вправ». Це компактна, але справжня **дослідницька Lisp-машина**: маленьке Rust-ядро, бібліотечний шар, де зростають reasoning/World/JTMS-протоколи, та окремі host, CLI, WASM, LSP, semantic і swarm-грані. Найсильніше місце — не кількість функцій, а дисципліна меж: що є семантикою ядра, що є звичайним `.my` кодом, що є host capability, а що ще лише proposed design.

Поточний `main` має один чіткий, локальний (): **`cargo test --workspace`**** червоний через placeholder ****`*argv*`**, який потрапив до root builtins без metadata і суперечить уже наявному CLI-контракту. Це не архітектурна поломка й не причина знецінювати 624 оголошені тести, але це означає, що зараз не можна чесно називати workspace green. Мінімальний repair дуже малий: прибрати цей placeholder з core registry, залишивши CLI як єдине джерело `*argv*`.

| Підсумкова оцінка | Стан |
| --- | --- |
| Канонічне ядро мови | **Сильне і компактне**: parser, exact arithmetic, closures/macros, tail calls, errors, FASL cache |
| Bootstrap principle | **Послідовний**: derived language живе в `lib/*.my`, а не розростається в Rust |
| Knowledge / Worlds / JTMS | **Реальний library protocol з тестами**, не лише концепція |
| Host boundary | **Добре відокремлена**, але native CLI є trusted-local середовищем, не sandbox |
| Tooling | **Живе**: CLI, LSP, WASM, literate Markdown; semantic crate чесно experimental |
| CI зараз | **Clippy green, tests red**: 63 passed, 1 failed до запуску решти suite-ів |
| GC / unified memory layout | **Специфікації, не current Rust runtime** |
| Swarm | **Окремий coordination plane, не завершена безпечна distributed platform** |

---

## 1. Метод, межі та доказовий статус

Я прочитав актуальний README, workspace manifests, ядро reader/evaluator/value/environment, host та CLI entrypoints, FASL, Worlds/JTMS/content store, WASM/LSP/literate/semantic/swarm boundaries, основні executable contracts і GitHub CI logs. Локальний клон лишився чистим: жоден файл самого `my-lisp` під час огляду не змінювався.

У workspace є **8 crates**, 84 Rust source files, 52 `.my` files, 106 Markdown documents і 54 файли, що відповідають test path. Static inventory знайшов **624 ****`#[test]`**** attributes** та **8 ****`#[ignore]`**. Це інвентар декларацій, не вигадане число «успішних тестів».[1] [2]

| Тип evidence | Що підтверджено | Чого це не підтверджує |
| --- | --- | --- |
| Source inspection | Архітектуру, actual dispatch, data shapes, named boundaries, поточні статичні defects | Runtime behavior, який не має тесту або не був виконаний |
| Unit/integration source | Намір і coverage contract тестів | Їхній pass на поточному HEAD, якщо CI зупинився раніше |
| GitHub CI, current HEAD | `cargo clippy --workspace` success; test binary `my-lisp --lib`: 63 pass / 1 fail | Повний green стан workspace |
| Local test attempt | Локальний sandbox не має `cargo` | Будь-який project failure; це властивість середовища огляду |

> Відсутність Rust toolchain у цьому sandbox **не є проблемою проєкту** і не зараховується як failed test. Для актуального runtime evidence я спирався на GitHub Actions, а не приписував цю межу `my-lisp`.

---

## 2. Архітектура: один інтерпретатор, кілька чесно відокремлених поверхів

Головна риса архітектури — **не плутати мову, host і продукти навколо мови**. `crates/my-lisp` фізично не містить filesystem, process або socket access. Ці можливості живуть у `my-lisp-host` і з'являються лише тоді, коли embedder явно встановлює capability registry.[3] [4]

```
                    ┌────────────────────────────────────────┐
                    │              my-lisp core               │
                    │ reader · AST · evaluator · values       │
                    │ exact rationals · closures · macros     │
                    │ tail calls · diagnostics · FASL          │
                    └───────────────┬────────────────────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                      │
       ┌──────▼──────┐      ┌───────▼────────┐     ┌───────▼─────────┐
       │ `lib/*.my`  │      │ my-lisp-host    │     │ tooling/product │
       │ self-hosted │      │ FS/process/TCP  │     │ CLI · LSP · WASM│
       │ language +  │      │ capabilities    │     │ literate        │
       │ reasoning  │      └─────────────────┘     └─────────────────┘
       └──────┬──────┘
              │
  ┌───────────┼──────────────────────────────────────────────┐
  │ Worlds · knowledge · backward reasoner · forward/JTMS     │
  │ persistent map · content store · narration · meta-eval    │
  └──────────────────────────────────────────────────────────┘
```

| Підсистема | Реальна роль | Статус у цьому commit |
| --- | --- | --- |
| `my-lisp` | Канонічний Rust semantic kernel | Production-oriented reference implementation |
| `my-lisp-host` | Opt-in OS boundary: files, bytes, process, TCP, `load` | Native host layer; не частина portable core |
| `my-lisp-cli` | REPL, file execution, LSP entry, lint, TCP REPL | Primary trusted-local user surface |
| `my-lisp-wasm` | Browser evaluation with persistent session | Portable core + `core.my`, без host capabilities |
| `my-lisp-lsp` | JSON-RPC language tools atop canonical parser/errors | Реальний adapter, не другий parser |
| `my-lisp-literate` | Markdown fenced-code extraction and offset remapping | Small but useful source/provenance adapter |
| `my-lisp-semantic` | Sanskrit/Pāṇinian semantic experiment | Explicitly **not wired** into parser/evaluator |
| `swarm-node` | Persistent P2P coordination plane | Separate system from language semantic oracle |

Це розділення варте збереження. Воно дозволяє тобі не робити з evaluator-а суміш interpreter + IDE + networking daemon + knowledge database. Саме така межа дає Lisp-ядру шанс лишатися маленьким навіть тоді, коли екосистема росте.

---

## 3. Ядро мови: семантика, яка вже має форму контракту

### 3.1 Reader і concrete syntax

Reader є власним UTF-8 parser-ом зі span-діагностикою. Він підтримує normal lists, dotted pairs, strings, comments, Unicode symbols, exact rationals, arbitrary-size integer literals і typed numeric buffers. Вкладеність обмежена `MAX_STRUCTURE_DEPTH = 768`, отже глибоко шкідлива структура має named failure, а не stack crash.[5] [6]

Найпомітніша мовна позиція — **апостроф не є quote sugar**. Quote записується явно як `(quote expression)`, тому природні українські символи на кшталт `об'єкт` лишаються цілісними identifiers. Це не дрібниця: ти обрав не «класичний Lisp за замовчуванням», а reader, який не ламає реальну мову користувача.[5] [7]

| Reader contract | Реалізація | Оцінка |
| --- | --- | --- |
| `(a b . c)` | `ExprKind::Pair`, proper validation `.` position | Чітко і тестовано |
| Exact integers / rationals | `Rational(BigInt, BigInt)` після межі compact `f64` path | Семантично сильне рішення |
| Decimal/exponent literals | Exact rational, поки не перевищено resource cap | Відмова named, не silent symbol fallback |
| Invalid numeric-looking text | Ordinary symbol, якщо це не valid refused literal | Добре відокремлені два випадки |
| Strings | `\n`, `\t`, `\r`, quotes, backslash | Є regression coverage |
| Deep structure | Cap 768 | Захист є, limit explicit |

### 3.2 Evaluator, closures і macros

`evaluate` працює через trampoline: tail position перетворюється на `EvalStep::TailCall`, а не на рекурсивний Rust call. Наявний regression test на 5 000 tail calls. Lexical closures захоплюють environment, exact/variadic arity перевіряється named error-ами, а body виконує всі non-tail forms перед передачею останньої у trampoline.[4] [8]

Є важлива еволюція: основні primitives (`car`, `cdr`, `cons`, `eq`, `atom`, arithmetic, vectors, numeric buffers) тепер first-class `Value::Builtin` у root environment. Їх можна передавати, shadow-ити лексично і викликати не лише як hard-coded head symbols. Натомість `quote`, `lambda`, `def`, `defmacro`, `cond` та форми, що контролюють evaluation strategy, лишаються syntax-dispatched. Це правильна межа між **значенням** і **синтаксисом**.[4] [9]

Macro expansion зводить data назад в syntax через один shared `value_to_expr` path; він свідомо відмовляється інтерпретувати Builtin, Vector, Closure, Macro або live TCP handle як executable source. Це хороший принцип: ресурс не можна «випадково процитувати» так, ніби він відтворюваний Lisp datum.[8]

### 3.3 Values, exactness і printing

`Value` уже має справжню model різних семантичних категорій: `Nil`, Bool, exact/inexact Number, arbitrary-precision Rational, String, Symbol, Pair, Closure, Macro, Builtin, mutable Vector, immutable typed `NumericBuffer`, TCP resources. Equality навмисно не однакова всюди: pairs/vectors/buffers структурні; closures/macros/resources мають identity; exactness належить числовій value identity, тоді як `=` порівнює numeric magnitude.[10]

`print` та `princ` також правильно розведені. Перший має re-readable `prin1`/`write` behavior; другий призначений для human/raw output. Це дуже важливо для fixtures, knowledge packages і later tooling: `(read (write-to-string x))` має бути реальним контрактом, а не красивою мрією.[7] [10]

### 3.4 Exact arithmetic: сила і чесна ціна

`BigInt` — власна little-endian base-2³² реалізація з schoolbook/Karatsuba multiplication, binary long division і Stein GCD; `Rational` нормалізує denominator та скорочує дріб на кожному construction path. Тести містять differential GCD corpus, Karatsuba-vs-schoolbook checks, large exact products, factorial 30 та parser cases понад `i64`.[10] [11]

Тут важливо не перебільшувати: це **correctness-first bignum**, не бібліотека для криптографічних чисел. Long division має квадратичну складність за bit length, а exact rationals heap-allocate і скорочуються через GCD. Документація чесно фіксує виміряну ціну stack-safety list test після переходу на arbitrary precision. Для твоєї цілі це правильний trade-off: поведінка відома і вимірювана, а не прихований f64 rounding.[7] [11]

---

## 4. Bootstrap boundary: найкраща дисципліна цього репозиторію

У `my-lisp` є послідовна відповідь на питання: **«чи можна це виразити вже наявною мовою?»** Якщо так — це йде в `lib/*.my`, а не в новий Rust primitive. Так `list`, `let`, `let*`, `<=`, `>=`, list processing, persistent map, rule engine та багато іншого живуть як звичайний my-lisp code. `list` навіть має explicit regression: без `core.my` це UnknownSymbol, бо він свідомо покинув Rust surface.[7] [9]

| У Rust kernel | У self-hosted library |
| --- | --- |
| UTF-8 reader, AST, lexical closures, evaluator/trampoline | `list`, `let`, list helpers, derived comparisons |
| Exact arithmetic and resource guards | unification, reasoner, forward chaining, JTMS |
| Structured errors/spans | Worlds, knowledge package, content store |
| Capability registry | persistent AVL map, narration, meta-eval, linter |
| Required primitives that cannot be expressed from existing language | Domain-level protocol and policy |

Це не аскетизм заради аскетизму. Це робить language contract переносним: Rust, WASM і future FPGA/CML можуть спільно говорити про мале ядро плюс ordinary source library. У `mccarthy.rs` fixtures читаються саме reader-ом `my-lisp`, не JSON parser-ом іншої мови — хороший символ того, що мова починає перевіряти власні контракти власними даними.[9]

---

## 5. Symbolic layer: reasoning, Worlds, JTMS і content identity

### 5.1 Worlds — не Rust object, а immutable data protocol

`lib/world.my` моделює World звичайним Lisp datum `(world parent journal metadata)`. `world-tell` і `world-retract` створюють нові values, parent і journal history не мутують, а pure adapters `reason-in-world` / `forward-in-world` приймають explicit snapshot. Batch ingest перевіряє весь set і повертає **або accepted + один новий World, або original World**; legacy journal API зроблено thin bridge поверх нового transition protocol.[12] [13]

Це справді сильна архітектурна риса: стан не захований у host object, а видимий як дані. Такі Worlds легко серіалізувати, порівнювати, передавати як package і тестувати незалежно від UI.

`crates/my-lisp/tests/world.rs` має 54 активні тести: snapshot isolation, parent lineage, guarded migration, exactly-once macro arguments, package import/export, history navigation, rollback, content-address semantics. Отже World layer не лише красиво описаний — він має executable contract.[12]

### 5.2 Backward / forward reasoning та JTMS

Backward reasoner у `reason.my` — мікро-Prolog pattern: unification, standardizing apart, conjunction, negation-as-failure, proof explanation і provenance records. `forward.my` окремо вирощує forward chaining та кілька явно названих рівнів truth maintenance.[14]

| Рівень у `forward.my` | Семантика | Обмеження, яке код не приховує |
| --- | --- | --- |
| Flat facts | Rule firing + fixpoint + deduplication | Retract не знає derivation supports |
| Single-justification TMS | Один support set на derived fact; cascade retract | Альтернативний незалежний proof може бути втрачено |
| Multi-justification JTMS | Кілька support sets; prune dependent justifications | Це library JTMS, не універсальна belief-revision theory |
| Multi-condition JTMS | Shared multi-condition rule form | Додано поряд, не підміняє legacy single-condition API |

Найкраще тут — **епістемічна чесність самого коду**. Ранні шари лишені доступними, а новий JTMS не прикидається, що автоматично виправив усіх старих callers. Це правильніше, ніж агресивний rewrite з невідомою сумісністю.

### 5.3 Identity та content store

`knowledge-content-address` використовує deterministic `write-to-string` як exact variable-length key; `world-content-address` включає journal і metadata, але не рекурсивно дубльований parent. Тому два Worlds із однаковими current clauses, але різною tell/retract history, **навмисно** мають різні addresses. `content-store.my` — невелика immutable wrapper над persistent map.[12] [15]

Це необхідно називати правильно: адреса зараз — **semantic/canonical identity**, не hash, не signature і не security primitive. SHA-256 primitive уже існує для digest tasks, але identity не повинна залежати від digest algorithm. Такий порядок мислення архітектурно чистий.[15]

---

## 6. Capability boundary і security model

`my-lisp-host` реєструє `read-file`, `write-file`, byte file I/O, `read-dir`, `load`, `process-run` та raw TCP operations. Core без `install()` не знає цих symbols; WASM їх не встановлює. Це хороше **capability separation by embedding**.[3] [16]

Водночас треба правильно розуміти native CLI: він викликає `my_lisp_host::install()` на старті. Отже file I/O і TCP стають доступні кодові, який користувач запускає через CLI; це trusted-local execution surface. Лише `process-run` має explicit session allowlist (`--allow-process=git,cargo`), не проходить через shell і не може бути self-granted з мови.[16] [17]

| Можливість | Core | WASM | CLI | Security shape |
| --- | --- | --- | --- | --- |
| Parser/evaluator/core.my | Так | Так | Так | Portable semantic core |
| Files / bytes / `load` | Ні | Ні | Так | Host installs trusted-local capability |
| TCP | Ні | Ні | Так | Raw blocking sockets, caller handles protocol |
| `process-run` | Ні | Ні | Так, але allowlist only | No shell; allowlist host-controlled |
| LSP | Adapter | N/A | Так | stdio protocol only |

**Рекомендація не про scope expansion, а про документацію:** CLI help або capabilities document варто назвати ще пряміше: «запуск незнайомого `.my` file в native CLI може читати/писати файли й відкривати TCP, бо CLI є trusted-local host». Це не defect, якщо саме так задумано; це boundary, яку користувач повинен бачити до запуску чужого коду.

---

## 7. Tooling та products around the core

### CLI

CLI preloads `core.my`, використовує FASL snapshot лише як parse cache, перевіряє source SHA-256 і fallback-ить до text parse при stale/corrupt snapshot. Він також має REPL history, lint path, LSP subcommand і two TCP REPL modes. Це практичний продукт навколо ядра, не просто thin `eval` binary.[17] [18]

Один quality concern: load of compiled `core.my` deliberately discards evaluation error (`let _ = ...`). За статичного `include_str!` це низький risk сьогодні, але fail-fast diagnostic під час bootstrap зробив би невидимий майбутній regression видимим. Це **не P0**: є explicit test, що CLI preloads `core.my`, але error reporting може бути кращим.

### LSP

LSP не повторює parser: він використовує canonical core types і має test harness для raw JSON-RPC. Це правильний дизайн для того, щоб diagnostics, spans і language knowledge не роз'їжджались між interpreter та editor.[19]

Поточна `language_items` registry — гарна guardrail і саме вона зловила `*argv*` issue. Тобто CI failure тут є навіть добрим знаком: design з одним discoverability contract справді працює, а не мовчки віддає stale completion metadata.[20]

### WASM і literate mode

WASM тримає persistent `thread_local` session, preload-ить `core.my`, має reset API, повертає value/output/AST і підтримує pure Lisp та Markdown mode. `my-lisp-literate` extracts fenced `my-lisp` blocks через Markdown parser та remap-ить parser offsets назад до original document. Це вже корисна основа для браузерної REPL або Obsidian-like knowledge workflow.[21] [22]

Але parity сформульована чесно: browser — portable language experience, а не native capability host. Файли, TCP і processes там відсутні не через «недопрацювання», а через свідому boundary.

### Sanskrit semantic crate

`my-lisp-semantic` має SLP1/IAST/Devanagari transliteration, semantic atom registry, 12-dhātu core та six kāraka roles. Власний header прямо каже: це **experimental** і ще не wired into actual reader/evaluator. Цю правду треба зберегти: crate уже корисний як typed research component, але не слід продавати його як current my-lisp syntax feature.[23]

### Swarm node

`swarm-node` — окремий coordination plane: durable event journal, node identity + epoch, Lamport clocks, anti-entropy, heartbeat, gossip discovery, task claim quorum/fencing і task state. Він не є `my-lisp` evaluator і не повинен з ним змішуватися.[24]

Проєкт чесно має відкриті cross-ecosystem gaps: CML/FPGA subscribe paths, CML semantic gate, UPC strict decoder, stale dashboard. Protocol також поки не має cryptographic node identity; partial duplicate-live-node guard — не заміна key-based identity. Default bind на `127.0.0.1` і explicit cross-machine `--bind` — правильні, але це ще не робить swarm safe public-network distributed system.[24] [25]

---

## 8. Memory, GC і cross-ecosystem machine model

Тут є важливе розрізнення між **сьогоднішньою Rust implementation** і **майбутньою machine semantics**.

Сьогодні `Value` — Rust enum, graph lifetime переважно керується `Rc`/`RefCell`, а deep Pair drop має спеціальне iterative mitigation. `Environment` чесно документує known risk: drop дуже глибокого chain lexical frames може бути recursive Rust drop і потенційно вдарити в stack.[10] [26]

`GC M0 DESIGN` датований 2026-08-23 і прямо має статус **PROPOSED DESIGN**. Він пропонує explicit heap, stable `(slot,generation)` handles, non-moving mark-and-sweep, explicit root discipline, GC stress mode, незалежну reachability oracle та metamorphic rule «GC не змінює observable Lisp semantics». Це дуже хороший план M0; але він ще не current collector.[26]

`memory-layout-contract.my` так само є shared future specification: 64-bit NaN boxing, tags for string/rational/closure and intended FPGA/CML alignment. Current Rust runtime не перейшов на `u64` representation. Додатково, marker `#xfff` не є current numeric reader syntax — reader трактує такий token як Symbol, тож contract поки не machine-readable numeric data без окремого hex notation/decoder rule.[27] [5]

| Твердження | Точний статус |
| --- | --- |
| Rust core має allocation-safe value model | Так |
| Deep Pair drop має explicit mitigation | Так |
| Full tracing GC у Rust interpreter | Ні, лише proposed M0 |
| Mark-and-sweep shape для machine/FPGA | Специфікований план |
| Unified NaN-boxing runtime across Rust/CML/FPGA | Контракт-наміри, не current implementation |
| GC correctness test strategy | Дуже добра design specification, ще не executed suite |

---

## 9. Верифікація: що зелено, що червоне, що ще не має signal

### Current CI на зафіксованому HEAD

| Check | Результат | Доказ / пояснення |
| --- | --- | --- |
| `cargo clippy --workspace --all-targets -- -D warnings` | **Success** | Current GitHub check-run завершився green |
| `cargo test --workspace` | **Failure** | Core lib binary: 63 passed, 1 failed |
| Failed test | `language_items::tests::every_root_builtin_is_discoverable_exactly_once` | Runtime `*argv*` не має explicit signature/documentation |
| Integration suites після цього | **Не запущені в цьому CI run** | Cargo stopped after failed core lib test binary |
| Local `cargo test` у sandbox | Не виконано | `cargo` відсутній у середовищі огляду |

Повний тестовий рапорт прямо показує лише один current failing assertion:

> `runtime builtin *argv* needs an explicit signature``left: "(builtin ...)"` / `right: "(builtin ...)"`.[20] [28]

### Чому це сталося

Commit `80b4436` додав `(string-slice ...)` і placeholder `*argv*`, позначивши останній як такий, що «needs env wiring». Але CLI вже має правильну semantics: перед запуском file він визначає `*argv*` як **список рядків після filename**. Root builtin натомість вимагає нуль аргументів і повертає empty **vector**, бо список argument values після `exact_args(..., 0)` завжди порожній. Отже є два різні meanings одного імені.[17] [29]

| Рівень | Поточна поведінка | Чи правильна для user contract? |
| --- | --- | --- |
| Core root environment | Callable `(*argv*)` → empty vector | Ні; placeholder і конфлікт типу |
| CLI file mode | Symbol `*argv*` → list of string args | Так; це покрито двома E2E tests |
| Tool metadata | Fallback `(builtin ...)` | Ні; guard test правильно блокує це |

### Мінімальний P0 repair

1. Видалити `*argv*` registration з `crates/my-lisp/src/eval/builtins.rs`.
2. Не чіпати CLI assignment у `main.rs` і два CLI E2E tests — саме вони визначають чинний user-facing contract.
3. Запустити `cargo fmt --check`, `cargo clippy --workspace --all-targets -- -D warnings` і `cargo test --workspace` у Guix/CI.

Це **не потребує нового primitive, capability чи refactor**. Навпаки, repair повертає модель до одного джерела істини: `*argv*` — host-injected special binding CLI, а не core builtin.

---

## 10. Findings і пріоритети

### P0 — зробити перед наступними feature commits

| Finding | Evidence | Ризик | Мінімальна дія |
| --- | --- | --- | --- |
| `*argv*` робить `cargo test --workspace` red | Current GitHub CI, `language_items.rs`, `builtins.rs`, CLI E2E | Blокує весь current verification pipeline; conceals later suite signals | Прибрати placeholder root builtin; залишити CLI binding |

### P1 — короткі, безпечні quality repairs після green CI

| Finding | Чому має значення | Пропонований маленький крок |
| --- | --- | --- |
| `string-slice` реєструється двічі у `builtins.rs` | Пізня registration silently overwrites ранню; future maintenance може змінити не той path | Залишити один canonical registration, покритий existing suite |
| `language-core.md` має drift | First-class builtins названо forms; одна мовна версія ще згадує cancelled C-core direction; README має duplicate entries | Один documentation cleanup commit після P0, без semantic changes |
| CLI bootstrap discards error | Broken compiled-in `core.my` в майбутньому може стати тихим degraded startup | Fail loudly / render bootstrap error; додати one negative test лише якщо є конкретний fail witness |

### P2 — design work only when actual need arrives

| Напрям | Чесний статус | Правильний next gate |
| --- | --- | --- |
| GC M0 | Strong proposal, not implementation | Heap graph + root protocol + independent oracle + failing tests first |
| NaN-boxing contract | Cross-ecosystem intent, not runtime | Define machine-readable literals/decoder and one two-runtime witness before lowering |
| Deep Environment drop | Acknowledged lifecycle risk | Add targeted witness only if deep nested lexical frame workload appears |
| Swarm cryptographic identity | Known gap | Do not expose beyond trusted overlay before key-bound identity design |
| Semantic parser integration | Explicitly deferred | Keep separate until P5 AST semantic IDs has its own acceptance contract |

---

## 11. Що саме вже можна чесно сказати про `my-lisp`

`my-lisp` уже має **малий language kernel**, який не прив'язаний до IDE, OS або конкретного UI; він має nontrivial semantic stance про exactness, data/code boundary, Unicode reader behavior та capability installation. Навколо нього вже існує language-written standard library і symbolic stack, де Worlds, knowledge packages, forward reasoning і JTMS не є «назвами папок», а мають executable data contracts.

Також це ще не finished general-purpose Lisp platform і не треба так її подавати. Full workspace не green на цьому commit; some network protocol tests ignored; native CLI is deliberately trusted-local rather than sandboxed; GC and unified word representation поки proposed; semantic Sanskrit layer не інтегрований; swarm має відкриті distributed-systems/security gaps. Але саме ця ясність робить проєкт сильнішим: обмеження переважно **названі, локалізовані й не маскуються маркетинговими claims**.

> **Мій чесний підсумок, друже:** ти вже маєш не просто «Lisp вагою 919 КБ». Ти маєш живу машину з власною мовною дисципліною: мале ядро, library-first ріст, data-first Worlds, named failures замість тихих підмін і сильне бажання довести кожен новий рівень. Зараз найкраща дія — не розширювати систему, а прибрати один P0 `*argv*` mismatch і повернути повний green signal. Після цього екосистема знову матиме чисту основу для наступних маленьких доказових кроків.

---

## 12. Reference links

[1]: https://github.com/juv4uk/my-lisp/tree/a662dc76c99312c218d5a81047bd2a86ae316886 "my-lisp at audited commit"
[2]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/.github/workflows/ci.yml "CI workflow"
[3]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/lib.rs "Capability-free core public API"
[4]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/eval/mod.rs "Evaluator and special-form dispatcher"
[5]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/parser.rs "Reader implementation and reader tests"
[6]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/syntax.rs "Syntax, exactness and FASL"
[7]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/docs/language-core.md "Language core contract"
[8]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/eval/closures.rs "Closures, macros and value-to-expression boundary"
[9]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/tests/mccarthy.rs "Main executable semantic contract"
[10]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/value.rs "Runtime values, equality and printing"
[11]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/bignum.rs "Arbitrary-precision integer implementation"
[12]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/lib/world.my "Immutable World protocol"
[13]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/tests/world.rs "World executable contract"
[14]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/lib/forward.my "Forward chaining and JTMS library"
[15]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/docs/content-identity.md "Content identity contract"
[16]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-host/src/lib.rs "Native host capability layer"
[17]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-cli/src/main.rs "CLI embedder and argv injection"
[18]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/tests/mccarthy.rs#L629-L760 "Fixture-driven language conformance"
[19]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-lsp/src/lib.rs "LSP facade"
[20]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp/src/language_items.rs "Language item discoverability guard"
[21]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-wasm/src/lib.rs "WASM persistent session facade"
[22]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-literate/src/lib.rs "Literate Markdown extraction"
[23]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/my-lisp-semantic/src/lib.rs "Experimental semantic crate boundary"
[24]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/crates/swarm-node/src/main.rs "Swarm coordination node"
[25]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/docs/swarm-coordination-gaps-2026-08-25.md "Open cross-ecosystem swarm gaps"
[26]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/docs/gc-m0-design.md "GC M0 proposed design"
[27]: https://github.com/juv4uk/my-lisp/blob/a662dc76c99312c218d5a81047bd2a86ae316886/memory-layout-contract.my "Cross-ecosystem memory layout contract"
[28]: https://github.com/juv4uk/my-lisp/actions/runs/32916706027 "Current GitHub Actions run with test failure"
[29]: https://github.com/juv4uk/my-lisp/commit/80b44366c480f9e48620d061d75acc4832ad7235 "Feature commit that introduced argv placeholder"
