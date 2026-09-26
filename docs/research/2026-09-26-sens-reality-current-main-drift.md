# SENS-REALITY-2 — current-main drift audit, slice 1

**Задача:** #1433  
**Зріз:** `main@0f5d324dbe4682a68329e28f113127a82c8a6366`  
**Дата:** 2026-09-26  
**Метод цього slice:** читання current source/projections/CI + точні структурні підрахунки. Старі часові виміри не перевикористовуються як current proof.

Цей документ не виправляє runtime і не робить нового твердження про швидкість без нового виміру. Його мета — відділити факти, які досі живі, від уже виправлених або застарілих тверджень #1433/#1413.

## 1. Що вже змінилося після початкового виміру

| Початкове твердження #1433 | Стан на current main | Current evidence | Наступний доказ |
| --- | --- | --- | --- |
| Англійська голова резолвиться заново на кожному виклику | **частково superseded** | `eval/lower.rs` одноразово зводить immutable surface heads у `ExprKind::Call(Sens8, ...)`; shadowable heads навмисно лишаються списками | повторити surface-vs-SENS benchmark на current main і окремо розділити immutable/shadowable |
| Lisp wrappers над примітивами коштують 2.4–3.8× | **історичний вимір** | цифри належать SHA `33bfb53a`; current lowering/runtime змінилися | fresh Guix benchmark |
| `Value`/AST мають 64/80-byte layout | **потрібен повторний вимір** | current `Rational` використовує власний `BigInt`; `ExprKind` уже має `Call(Sens8, Rc<[Expr]>)` | current `size_of::<...>()` witness |
| cold start = 4.78 млрд інструкцій | **історичний вимір** | число зберігається в historical benchmark data, але current bootstrap змінився | current `sens-bench`/cold-start measurement |
| tail call клонує `Expr` | **current, підтверджено кодом** | `eval/closures.rs`: `EvalStep::TailCall { expression: last.clone(), ... }` | вимірити частку вартості на recursive workload |
| `meta_eval_mutual` 79–291 s/file | **історичний вимір** | немає current-main повтору в цьому slice | fresh Guix run |
| код мови: 25 790 named calls | **число застаріло** | current ratchet baseline містить **25 832** named source calls | live `non_sens_code_inventory` потрібен ще й для current exact-SENS count |

## 2. Reality gaps: що виправлено, що лишилося

| Початкове твердження | Стан | Current evidence |
| --- | --- | --- |
| `(00001111 ...)` панікує | **FIXED** | `canon.rs::prim_00001111` напряму викликає `division_on_values`; `unreachable!` path більше не є маршрутом exact SENS division |
| named `+` — окремий Rust builtin, а `00001100` інша функція | **FIXED / superseded #1440** | current `canon.rs` має exact-SENS primitive table; current `builtins.rs` більше не містить окремих arithmetic named builtins |
| `< > =` не мають bare-SENS механізму | **FIXED** | primitive table містить `00011010`, `00011011`, `00011100` |
| `(< 2 1) -> 0`, а старий 2-part `cond` трактує 0 truthy | **потрібен current executable witness** | comparisons і досі повертають exact 1/0; canonical Core4 `cond` є 3-part exact-result matching, але migration-only 2-part bridge існує окремо |
| 67 language functions працюють name-only | **старе число; current gap ще реальний** | current `PRIMITIVE_TABLE` має 13 механізмів; інші language-defined functions ще не callable exact-SENS на current main. #1455 готує slot bridge, але ще не landed |
| runtime surfaces поза exact SENS = 326 | **current ratchet baseline** | `non-sens-code-baseline.tsv`: 326 runtime rows. Це **surface rows**, не 326 distinct functions |
| generated function table = 169 rows | **старе число, але drift лишився в іншій формі** | current registry = **256** rows; generated projection = **255** rows |
| `atom?/eq?/not?` rollback | **current registry уже з ?** | registry має `atom?`, `eq?`, `not?`; stale witness `atom` винесено в #1464 |
| machine lowering: 61 rows / 8 executable transitions | **потрібен повторний аудит після #1436** | current machine lowering значно змінився і містить нові exact-SENS rows та bounded executable witnesses |

### Нова current-main знахідка: 255/256

`scripts/generate-function-table.lisp` досі виконує `(cdr registry-rows)` зі старим поясненням, що `00000000` — `()`/ground value. Це суперечить Contract 9 і completed #1403: `()` є структурним значенням поза 256 функціями, а `00000000` — окрема функція СЕНС.

Факт current main:

- authority registry: **256** exact 8-bit rows;
- generated `lib/generated/function-table.lisp`: **255** rows;
- omission: `00000000`;
- виправлення винесене окремо в **#1469**, бо #1433 є research-only.

## 3. Сучасні технології: current code audit

| Технологія | Current стан | Клас доказу |
| --- | --- | --- |
| tracing/generational GC | core values/environments використовують `Rc` / `RefCell`; tracing GC у core не знайдений | **підтверджено читанням коду** |
| compact tagged/NaN-boxed value | current `Value` — Rust enum з `Rational`, Rc handles, vectors/TCP handles; старий byte-size треба переміряти | **структура підтверджена; розмір — невідомий current** |
| general JIT/Cranelift/LLVM backend | Cranelift references у repo search: 0; LLVM hits належать Android toolchain/Clasp docs, не SENS evaluator. Є bounded власний x86 lowering | **підтверджено пошуком + кодом; не твердження про майбутню архітектуру** |
| SIMD | machine projection згадує AVX2 specialization як можливість, але current general SIMD execution coverage тут не доведено | **неповний доказ; потрібен executable inventory** |
| evaluator parallelism | core `Environment`/`Value` використовують `Rc`, тому core session values не є загальним cross-thread payload; threads існують у CLI/swarm/host tests | **підтверджено читанням коду; не плутати з відсутністю threads у всьому repo** |
| benchmark CI | **вже є** `.github/workflows/sens-bench.yml`: Valgrind instruction-count base-vs-change, 11 workloads × EN/SENS | **FIXED/superseded старий пункт** |
| property-based/fuzz frameworks | repo code search: `proptest`, `quickcheck`, `cargo-fuzz` — 0 hits | **пошуковий negative evidence; не глобальна гарантія відсутності** |

## 4. Current structural counters

Сирі значення з цього SHA винесено поруч у `docs/research/data/1433-current-main-0f5d324d.tsv`.

| Метрика | Current |
| --- | ---: |
| registry exact-SENS rows | 256 |
| generated function-table rows | 255 |
| exact-SENS Rust primitive table entries | 13 |
| named source call ratchet baseline | 25 832 |
| runtime non-SENS surface rows baseline | 326 |

Важливе обмеження: baseline **не зберігає** загальну current кількість exact-SENS source heads. Її друкує живий тест `non_sens_code_inventory`; тому не вигадуємо число без run.

## 5. Що треба переміряти, а не обговорювати

Перший current benchmark batch після стабілізації prerequisite PR-ів:

1. `surface vs exact-SENS` окремо для immutable lowered heads і shadowable heads;
2. cold bootstrap instruction count;
3. `size_of<Value/ExprKind/Expr>` на current Rust;
4. `meta_eval_mutual` current runtime;
5. machine exact-SENS lowering: declared rows vs реально executable transitions;
6. named-source / exact-SENS live inventory після M0→M7.

До цих вимірів старі числа лишаються **historical evidence**, а не current performance facts.

## 6. Висновок slice 1

Найважливіша зміна від #1413: проблема вже не описується чесно як «усі імена шукаються на кожному виклику» або «арифметика name-path і SENS-path — дві різні функції». Частину цих розривів уже прибрано.

Current bottlenecks, які можна стверджувати без нового timing run:

- tail-position `Expr` clone лишається;
- значний named-source debt лишається (baseline 25 832);
- exact-SENS coverage для language-defined functions на current main ще неповне до landing #1455;
- generated function-table projection фізично пропускає `00000000` (#1469);
- core runtime representation досі Rc/RefCell-heavy;
- performance цифри після великих змін потребують нового вимірювання.

Це **slice 1** #1433, не закриття задачі: acceptance #1433 вимагає fresh measured impact і нових знахідок у всіх трьох категоріях.
