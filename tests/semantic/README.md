# SENS-owned semantic tests

## Новий закон: найкоротший фізичний шлях

Мовні закони пишемо в `tests/semantic/*.lisp`, а не в Rust, Zig чи Python.
Для нового `приклад-law.lisp` додаємо `приклад-mutant.lisp`:
перший мусить дійти до точного D1:1, другий — до точного D1:0.
Якщо бібліотека потрібна, складаємо її оригінальний Lisp-текст
із кожним свідком; хост не відтворює логіку.

У `scripts/prove-lisp-semantic-t5m.sh` реєструємо ОБИДВА випадки:

```bash
run_case run_law приклад-positive tests/semantic/приклад-law.lisp 1
run_case run_law приклад-mutant tests/semantic/приклад-mutant.lisp 0
```

Для залежного тесту `cat -- lib/потрібна-бібліотека.lisp tests/semantic/приклад-law.lisp > "$law_bundle"`
і `run_case run_law ... "$law_bundle" 1`; мутант має окремий бандл.
Саме `run_case` виконує direct SENS → Zig/T5M mint/open/verify →
парний SENS → фізичний SENS. Просто `echo`, коментар, успішний
`cargo test` або `semantic=NOT_CERTIFIED` не є семантичним доказом.

`scripts/guard_native_semantic_ownership.py --base BASE_SHA --head HEAD`
автоматично зупиняє новий, але незареєстрований мовний тест та відсутню
пару закон/мутант. Перевірка охоронця:

```bash
python3 -m unittest tests/test_native_semantic_ownership_gate.py -v
```

Охоронець відповідає тільки за маршрут. Семантичний PASS підтверджує
виключно сам SENS; якщо фізичний код відхилено, RED залишається RED.


These are executable language-owned semantic witnesses, not host-language
semantic oracles.

## Межі відповідальності тестів

- **Семантика, логіка й очікувані мовні результати** визначаються виконуваними
  Lisp-свідками в цьому каталозі або в `tests/fixtures/*.lisp`. Позитивний
  результат і негативна мутація мають бути вирішені самим SENS.
- **Rust** тестує поведінку Rust-механізмів: парсер/читач як реалізацію,
  обробку помилок, пам'ять, I/O, CLI та адаптери. Інтеграційний Rust-тест може
  запускати Lisp-свідок і передавати йому фактичний результат, але не повинен
  повторно реалізовувати ATOM, EQ, COND, QUOTE чи математичний закон як
  незалежний оракул.
- **Zig** тестує власні механізми: пакування та розпакування, точну бітність,
  фізичний T5/T5M, транспорт і ABI. Він не визначає значення мовних операцій.
- **CI** може маршрутизувати запуск і порівнювати зовнішній код завершення.
  Семантична відповідь має походити з Lisp/SENS-свідка; успішне пакування чи
  прийняття файлу хостом саме по собі не є доказом мовного закону.

Якщо тест одночасно потрібен для механіки та семантики, розділяємо його на
Rust/Zig-перевірку механізму і Lisp-свідок закону, а не переносимо весь тест
до однієї мови.

## Перші закони в цьому розподілі

- `усі-за-предикатом-law.lisp` / `усі-за-предикатом-mutant.lisp` перевіряють
  універсальний квантор через чинну D6-поверхню `усі?`, не перевизначаючи її.
- `існує-за-предикатом-law.lisp` / `існує-за-предикатом-mutant.lisp` перевіряють
  квантор існування через D6 `будь-яке?`; обидві пари виконуються з точними D6-визначеннями
  через SENS→Zig/T5M→SENS, а не через хостовий семантичний оракул.

- `d3-d4-ukr-native-laws.lisp` — дванадцять позитивних законів структури,
  цитування, умовного вибору та точних атомних відповідей. Один навмисно
  неправильний селектор лишається в окремому мутанті.
- `d4-selector-domain-law.lisp` — закони трьох українських селекторів.
  Rust-тест `d4_selector_domain_routing.rs` лише запускає свідка й приймає
  його названий статус; він більше не містить історичних кодових голів і
  не порівнює очікувані значення селекторів у Rust.
- `d9-core1-fifth-law.lisp` і `d9-core1-identity-law.lisp` перевіряють
  бібліотечні визначення Д9 у самому Core1. Їхні мутанти окремо спростовують
  неправильний п'ятий елемент і зміну тотожністю переданого значення; ці
  свідки карбуються з `lib/core1.lisp` як джерелом зв'язувань.
- `d8-core1-logic-law.lisp` перевіряє D8 `та`/`або`, порожні виклики,
  результат D1 та коротке обчислення небезпечної другої гілки; мутант
  окремо спростовує неправильний результат `та`. Реалізації будують D1
  через D3-предикати, тож макророзгортання не перетворює `так`/`ні` на D7.
- `exact-arithmetic-laws.lisp` — точні рівності додавання, обернення,
  дробової суми, знакового множення, віднімання й ділення. Значення задаються
  іменами та мовною арифметикою, а не числовими літералами чи кодами функцій.
  Rust-адаптер лише виконує цей свідок; класифікація `DivisionByZero`
  залишається окремою перевіркою поведінки Rust-runtime.

- `unification-occurs-check-law.lisp` і `unification-occurs-check-mutant.lisp`
  перевіряють логічну уніфікацію без Rust-оракула. CI складає чинний
  `lib/unify.lisp` зі свідком, запускає Lisp напряму, пакує той самий текст у
  фізичний SENS через T5M та перевіряє результат після незалежного Zig
  round-trip. Контрольна хибна теза має точний вердикт Д1:ні.

- `language-law-epistemic-records.lisp` та `language-mutant-epistemic-records.lisp`
  закріплюють у самому Lisp/SENS перевірки епістемічних посилань, пошкоджених
  спискових хвостів, наявності вимог і вкладеної структурної рівності. Спільний
  `epistemic-authority-witness.lisp` формує очікування та вердикт у SENS;
  Rust лишився спостерігачем reader/lowering і названого результату. Чинний
  шлях повного доказу пакує джерела з їхніми реальними залежностями у T5M,
  перевіряє Zig round-trip і запускає фізичний SENS як для закону, так і для
  хибного мутанта. До фактичного зеленого прогону це не означає PASS.

- `utf8-boundary-laws.lisp` та `utf8-quotient-laws.lisp` — мовні закони меж байтів, D1-предикатів і точної D24+ частки/остачі. Їхні негативні пари перевіряють недопущений continuation-байт і хибну частку. Усі числові операнди беруться з іменованих значень `lib/utf8.lisp`; Rust більше не містить окремих таблиць очікуваних результатів для цих двох наборів. Повний witness проходить пряме виконання SENS, Zig/T5M, paired та standalone фізичне виконання.

CI перевіряє вихідні вердикти цих Lisp-свідків справжнім SENS. Їх не можна
вважати доведеними лише за успішної компіляції адаптера чи перевірки T5M.

`d1-d3-control-law.bits` contains only exact-width 0/1 domain words plus D2
framing. Correct D1/D3 semantics reaches exact D1 `1`. A wrong ATOM, EQ, or
COND decision routes into an intentionally non-callable D1 head so SENS itself
rejects the witness.

`d1-d3-control-law.sens` is the canonical physical T5 form of exactly those
words.

Rust, Python and shell are allowed to transport bytes, invoke SENS, and retain
evidence. They do not define the expected logic of this witness.

`result-status-laws.lisp` is the authoritative source witness for reasoning outcomes. It exercises the existing `lib/result-status.lisp` constructors and validators through the Ukrainian projection; every failed case reaches a non-callable SENS branch. The native pipeline bundles the library with the witness only for execution, then runs source → T5M codec → Zig view/round-trip → physical SENS with matching verdicts.

`result-status-d1-law.bits` is retained as a legacy carrier fixture for syntax/framing inspection only. It is no longer the semantic authority and must not be edited as source; semantic changes belong in `.lisp` and must be carried through the codec.

## Вузький двійковий свідок D4:1001 та бітності

`d4-selector-width-law.bits` — виконувана двійкова SENS-програма: D4:1001
(CADR) має збігатися з D3:100(CAR) після D3:011(CDR)
на `CONS(CONS(0,1),CONS(1,QUOTE 000))`.
Другий закон вимагає, щоб `EQ(QUOTE D4:1001, QUOTE D5:01001)`
повертав D1:0 — провідні нулі та домени не зливаються. Кожен закон
сам зобов'язує SENS дійти до D1:1, а за хибного результату переходить
до невикличної гілки D1:0.

`d4-selector-width-mutant.bits` містить рівно одну зміну біта D4:1001 →
D4:1000 (CAAR), без підміни очікуваних відповідей у Rust/Python.
Парні `.sens` — канонічний фізичний T5. Виконання оракулом ще
належить підтвердити локально, без GitHub Actions.
Host Rust/Python дозволено лише для перенесення байтів, перевірки
бітових меж, запуску оракула та його статусу; не для EQ/CADR/COND-семантики.

Точковий **ручний нативний запуск** без нового workflow:

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-d4-selector-width.sh
```

`scripts/prove-d4-selector-width.sh` звіряє два готові фізичні T5
`.sens` з відповідними двійковими `.bits` без жодного перетворення
ширини: 144 слова, 312 інформаційних бітів, 91 байт фізичного T5,
два D3 COND-самовердикти. Відхилення однобітного мутанта зараховується
лише за діагностикою **D1 non-callable** від нативного SENS;
помилка читача або транспорту не може замінити семантичний негативний доказ.
Виводяться SHA-256 двійкового виконавця, обох фізичних файлів, а також
expected/actual. **До фактичного виконання — PENDING, не COVERED.**

Межа застосовності: бінарний свідок D4/CADR нічого не доводить
про **українську назву** функції та її surface-маршрутизацію.
Така архівна теза має окремий PENDING у coverage-ledger.

## D3/D4/D5 narrate: фізичний двійковий SENS

`narrate-d3-atom-eq-law.sens` — фізичне T5-пакування **наявної**
`narrate-d3-atom-eq-law.bits`, без переназначення координат чи зовнішньої
таблиці істинності. Точні бітності: D1=1, D2=2, D3=3, D4=4, D5=5.
377 слів, 822 семантичні біти, 376 транспортних розділювачів,
2 трити фізичного хвоста, 240 байтів носія. Мутаційний
`narrate-d3-atom-eq-mutant.bits` відрізняється лише D4:0111→D4:0110.

Структурна збалансованість, бітова ідентичність після T5 round-trip та
однобітність мутації перевірені без виконання семантики сторонньою мовою.
Остаточний семантичний результат має видати **лише SENS**, локально:

```sh
target/debug/sens-trit explain tests/semantic/narrate-d3-atom-eq-law.sens
target/debug/sens tests/semantic/narrate-d3-atom-eq-law.sens
```

Доки фактичне виконання SENS-оракулом не підтверджене, свідок
не вважати доказом проходження семантичного тесту. Карантинний
GitHub Actions workflow не активувати без явного дозволу власника.

## Migration source guard

The only automatic workflow is `.github/workflows/ci.yml`. Its physical SENS proof
and negative mutant own the semantic verdict. The same job's mechanical policy
script also checks the source boundary: D4 NULL and D3 ATOM(CAR) precede D3 EQ in
`lib/reason.lisp`; narration arity uses raw D1 results with D3/D4 structure,
without D6 LENGTH or D8 EQUAL. Manual benchmark workflows remain manual.

## Автоматичний SENS-закон трьох селекторів індексу міркувань

`reason-index-width-selectors-law.bits` є виконуваним джерелом **суто
двійкового SENS**; однойменний `.sens` — фізичне T5-пакування без втрати ширин.
У самому SENS через D3 EQ/COND перевіряються D4:1001 CADR, D5:10011 CADDR,
D5:10011(D3:011 CDR) на чотирипольному записі й відмінність D4:1001 від
D5:01001. D6:100111 у записі лише цитовані дані; це не допуск виклику D6.
Позитивна програма доходить до D1:1; за хибного закону викликає невикличний
D1:0. `reason-index-width-selectors-mutant.sens` відрізняється рівно одним
бітом D4:1001→D4:1000 і мусить бути відкинутий самим виконавцем SENS.
Наявний єдиний автоматичний `ci.yml` викликає `target/debug/sens` безпосередньо
для обох свідків, фіксує фізичні SHA, робить перевірку дійсних executor receipts
і блокує відсутні докази. Rust/Python можуть перевіряти лише транспорт і текст
джерела, ніколи не визначати EQ, COND або семантичний вердикт.

## Археологічний QUOTE — один точковий бінарний свідок

**Статус: PENDING native SENS, не COVERED.** Архівний тест
`crates/sens/tests/meta_eval.rs::quote_returns_data_unevaluated`
повертав іменований атом `radio` через метаобчислювач; нова пара
**не** доводить повну meta-eval або D7/surface еквівалентність.

- `retired-quote-inert-d3-law.bits` — 43 точні двійкові слова:
  D3 QUOTE утримує інертний список `(D1:0 D1:1)`; D3 CAR
  вибирає перший елемент, D3 EQ порівнює його з D1:0, а D3 COND
  обирає D1:1 або навмисно не-callable гілку. Усі мовні
  очікування визначено виконуваною бінарною SENS-програмою.
- `retired-quote-inert-d3-mutant.bits` змінює рівно один біт даних
  `D1:0 → D1:1`, без зміни ширини чи D2-граматики.
- `scripts/prove-retired-quote-inert.sh` механічно пакує T5 через
  чинний codec, запускає native `target/debug/sens`, фіксує SHA-256,
  вимагає прийняття самовердикту та відхилення однобітного мутанта.
  Відхилення мутанта має містити діагностику саме невикличного D1;
  сторонній parse/CLI/transport збій дає `UNINFORMATIVE-NEGATIVE`, не PASS.

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-retired-quote-inert.sh
```

Механічний T5-вектор: 26 байтів positive, SHA-256
`e2550941eb34e6e86baaf20025570c0aa2afc7c59355c5ec480310c46ff4506f`;
26 байтів mutant, SHA-256
`f97a1abd6a9a120be5b76806424a81dc0939c2823fdaa2d835b45526f133ac31`.
Дайджести **не** є semantic PASS. До фактичного виконання SENS
та доведення повної рівноцінності старого твердження рядки
coverage-ledger лишаються PENDING.

## D3 EQ/COND — дві найкоротші точкові самоперевірки

**Стан: лише структурна/транспортна перевірка; native semantic PASS відсутній.**
Жодна з цих пар не відновлює історичного восьмибітного виклику або
неявної істинності. Всі голови — точні домени, роздільники — D2.

- `retired-d3-cond-law.bits`: 21 точне слово, 40 семантичних бітів,
  12 фізичних байтів T5. D3:110 COND повинен пропустити гілку з D1:0
  і виконати гілку з D1:1, яка повертає цитований D1:1.
  Мутант змінює рівно першу умову D1:0→D1:1 (слово 4), після чого
  саме SENS має відхилити виклик D1:0 з першої гілки.
- `retired-d3-eq-law.bits`: 35 точних слів, 70 семантичних бітів,
  21 фізичний байт T5. D3:101 EQ порівнює два цитовані D1:0;
  D3 COND обирає позитивний самовердикт. Мутант змінює один
  цитований операнд D1:0→D1:1 (слово 16): EQ мусить дати D1:0,
  після чого обирається гілка з невикличним D1:0.
- `scripts/prove-retired-d3-laws.sh` — лише ручний запуск чинного
  `sens` на T5-файлах, з exact-width round-trip, SHA-256 виконавця
  та входів, expected/actual SHA-256, і перевіркою саме діагностики
  D1 non-callable для негативного свідка.

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-retired-d3-laws.sh
```

Механічні SHA-256 фізичного T5, не підтвердження семантичного PASS:

| Свідок | Фізичний SHA-256 |
|---|---|
| COND закон | `5878043ba9a4df76bb6f84d8b551f8087f83e3276ed2d1a6058b8f0d7eb6226f` |
| COND мутант | `ecc84138081edc86726fefd5c93df46c4754dd55868079a642a4ab71754ebcb8` |
| EQ закон | `f1c3149cf9294e27ea27e083d7f11b2e85f1a7d3a890be9a3d7df9747ef61941` |
| EQ мутант | `8254c800ee1dc46b4f3c00a1a4ac19e3b2567bbaab5821726d984a18d8a45065` |

Археологічні твердження `binary_sids_keep_quote_and_cond_as_syntax`
та `historical_truthiness_rows_cannot_reenter_current_tier1_authority`
не зводяться до цих мініатюрних програм: для статусу `COVERED`
потрібні точне зіставлення тверджень, захист від не-D1 керування
і фактичний native SENS receipt. До того часу — `PENDING`.

## Meta-eval D1: чотири двійкові самовердикти D4 LAMBDA

`meta-eval-mutual-d4-law.bits` — **наявні** чотири незалежні SENS
самоперевірки D4:0010 LAMBDA, D3:101 EQ, D3:110 COND і точних
однобітних результатів D1. Фізичні T5 відтворюються з кожного рядка
без втрати ширини. Це свідок **підкладки lambda / лексичного
зв'язування**, а не повного `my-eval-program-with-groups` та не
доказ рівноцінності вилученим Rust-тестам meta-eval.

`meta-eval-mutual-d4-mutant.bits` відрізняється від першого рядка
закону **одним бітом** — D1:1 → D1:0 у цитованому аргументі
(слово 41 за нульовою індексацією). За неправильної рівності
виконуваний D3 COND веде до невикличного D1. Негативний результат
вважається семантичним свідченням лише коли саме нативний SENS
видав помилку `D1 non-callable`; parse/codec/runtime crash — не доказ.

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-meta-eval-mutual-d4.sh
```

Механічний аудит: 4 позитивні форми з відповідно 77/77/103/91
точних слів, 207/207/286/233 біт і 57/57/78/65 байт T5;
мутант — 77 слів, 207 біт, 57 байт T5, одна зміна D1.
Це **не** підтверджений нативний PASS.

Окреме виправлення **живого коду SENS**, не доведене цим D4-свідком:
`my-group-closure?` в `lib/meta-eval.lisp` і
`lib/meta-eval-mutual.lisp`, а також негативні гілки
`my-lambda-def-form?` у mutual повертають точне `#d1:0` замість
структурного `()`. Оскільки їхні результати керують D3 COND, це
усуває виявлене порушення чинного one-bit контракту. Щоб позначити
ці функції `COVERED`, потрібен окремий **SENS-owned** свідок, який
викликає саме їх із реальним завантаженим модулем, плюс нативний receipt.
Не плутати структурну Python-перевірку
`scripts/test-meta-eval-mutual-d1-bitness.py` із таким свідченням.

## Meta-eval: живі D1-предикати проти структурного ()

`lib/meta-eval.lisp` містив чотири негативні гілки, що замість
однобітного `#d1:0` повертали структурне `(001 ())`: `my-macro?`,
`my-closure?`, `my-recursive-closure?`, `my-rest-param?`. Це
порушувало контракт керування двопольного D3:110 `COND`, коли
їхні результати ставали умовами. В основному файлі виправлено саме
результати цих предикатів, без нових доменних координат.

`my-arity-ok?` окремо тепер має явні D1:NO-гілки для
невдалої арності. Його ширша математична залежність потребує
окремого нативного доказу: цей новий свідок **не** покриває її.

`meta-eval-predicates-d1-law.lisp` — SENS-програма із D3 EQ/COND,
яка викликає **реальні поточні бібліотечні функції**, а не
переписані у host truth table механізми. Чотири негативні результати
мають бути точним D1:NO; інакше викликається невикличний D1:NO.
`meta-eval-predicates-d1-mutant.lisp` змінює один біт D1
у першому EQ-очікуванні: `#d1:0 → #d1:1`.

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-meta-eval-predicates-d1.sh
```

Ручний скрипт збирає чинну бібліотеку і виконуваний SENS-закон у
тимчасовий `.lisp`, фіксує SHA-256 виконавця/джерел, expected і
actual та вимагає **специфічного** D1 non-callable для мутанта.
Він не створює workflow, не ратифікує нових функцій і не замінює
семантичний оракул стороннім кодом.

Важлива межа: ці helper-імена ще є частиною живого meta-eval
інтерфейсу, тому це SENS-source bridge, а **не повністю безіменний
фізичний T5**. Самі очікування визначені D1/D3 SENS, але
до фактичного нативного запуску статус `PENDING`, не `COVERED`.

## Meta-eval dependency graph: точний D1 на порожніх випадках

Живий `lib/meta-eval.lisp` перевіряє лексичні залежності та
граф визначень. Структурний D3 `()` **не** може бути
негативною відповіддю у D3:110 COND: предикат повинен
повернути саме однобітне `#d1:0` або `#d1:1`.

Після точкового виправлення `my-cond-has-migration-clause?`,
`my-params-bind-name?`, `my-forms-reference-name?`,
`my-form-references-name?`, `my-lambda-def-references-name?`
і `my-graph-dependencies-reach?` повертають точний D1
у розглянутих негативних випадках. Дубльований тест
у `my-cond-has-migration-clause?` замінено справжнім fallback.

`meta-eval-graph-d1-law.lisp` — **виконувана SENS-програма**
із сімома вкладеними D3 EQ/COND самовердиктами над чотирма
живими бібліотечними функціями. Вона перевіряє порожній
граф, порожній список форм, порожні/атомні параметри,
зв'язане ім'я і одну клаузу неправильної арності.
`meta-eval-graph-d1-mutant.lisp` відрізняється одним бітом
у першому очікуваному D1:0 → D1:1, не торкається джерела
алгоритму. Жоден числовий або англійський SID8-виклик
не вводиться.

```sh
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-meta-eval-graph-d1.sh
```

Ручний запуск пакує живий `lib/meta-eval.lisp` із
самовердиктом в один тимчасовий Lisp-source, фіксує SHA-256
виконавця/програм, expected/actual і вимагає саме
помилки невикличного D1 від мутанта. Він не створює
нових GitHub workflow.

Межі: це міст з іменованими бібліотечними helper-функціями,
**не безіменний фізичний T5**. Наразі не охоплено окремими
нативними перевірками гілки `my-form-references-name?`
і `my-lambda-def-references-name?`. Механічна перевірка
не означає нативного PASS; усі історичні рядки ledger
лишаються PENDING до exact-claim порівняння та
фактичного SENS-run receipt.

## Meta-eval: цитування й лексичне затінення

Це наступна вузька перевірка після `meta-eval-graph-d1`:
`my-form-references-name?` і `my-lambda-def-references-name?`
мають розрізняти *вільне використання імені*, *цитоване дане*
та *локальний формальний параметр*. Вісім **незалежних** SENS-самовердиктів
у `meta-eval-lexical-shadow-d1-law.lisp` містять:

- D3 QUOTE приховує згадування імені, але прямий символ залишається залежністю;
- D4 LAMBDA з однаковим параметром затінює зовнішню змінну;
- інший параметр не приховує вільне посилання;
- QUOTE всередині LAMBDA не створює вільного посилання;
- три аналогічні випадки у даних `D4:0011 DEFINE`.

Очікування викладені восьми окремими SENS-програмами через D3
`EQ/COND` і точні D1:0/D1:1. Перший історичний
`meta-eval-lexical-shadow-d1-mutant.lisp` збережено як
однобітний негативний свідок для першої форми.
`meta-eval-lexical-shadow-d1-mutants.lisp` містить **вісім**
негативних форм у тому самому порядку. Кожна відрізняється
від відповідної позитивної форми **рівно одним бітом** D1
у порівнюваному операнді `EQ` (зміни 0→1 або 1→0),
не зачіпаючи вхідних даних, доменів і структури D2.
Кожен мутант має дати саме помилку невикличного D1,
а не сторонній збій.

```sh
# Механічна перевірка фікстур без нативного виконавця:
bash scripts/prove-meta-eval-lexical-shadow-d1.sh --check-fixtures

# Семантичний доказ — лише фактичне виконання SENS:
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-meta-eval-lexical-shadow-d1.sh
```

`scripts/prove-meta-eval-lexical-shadow-d1.sh` — ручний
транспорт: точна різниця одного біта, баланс D2-дужок
текстового bridge, SHA-256 усіх джерел/виконавця,
expected/actual та конкретна native SENS діагностика мутанта.
Кожна з восьми позитивних форм і **кожен з восьми однобітних
мутантів** виконується окремо, із власним `test_id`, SHA-256
точного вхідного `.lisp` та командою відтворення.
Механічний Python-крок звіряє всі 8 пар, визначеність
іменованих викликів у **чинному** `lib/meta-eval.lisp`,
відповідність старому першому мутанту та SHA-256 **кожного**
точного тимчасового входу `cat library + newline + form + newline`.
Прапорець `--check-fixtures` запускає це окремо й повідомляє
`semantic_pass=NOT_RUN`, а не нативний PASS.
Формальний механічний контроль додатково вимагає **рівно одного**
кореневого D2-виразу з двома гілками D3 COND, головою D3 EQ,
точним D1-очікуванням і невикличним D1:0 на негативному шляху;
це структурна перевірка бітових слів, **не** інтерпретація їхньої
семантики стороннім кодом. Сам контроль перевіряється п'ятьма
синтетичними пошкодженнями: зайва верхньорівнева форма, змінена
голова COND, змінена голова EQ, змінена D1-гілка та незакрита D2.
Пошкодження мають бути відхилені із `META_LEXICAL_TRANSPORT_RED`,
а контроль має надрукувати `META_LEXICAL_GUARD_SELFTEST_PASS`.
Лише сам SENS вирішує EQ/COND.
Жодного глобального HOLD чи нового автоматичного workflow.

**Межа доказу:** helper-імена ще живуть у текстовому шарі
`lib/meta-eval.lisp` і не є ратифікованими бінарними
резидентами; не створювати вигаданого D10 для цих функцій.
Ця пара — SENS-owned source self-verdict, **не** безіменний T5
і **не** повний доказ історичних Rust-тестів lexical closure.
До нативного запуску та перевірки точної еквівалентності —
тільки `PENDING`; Python не визначає семантику мови.
