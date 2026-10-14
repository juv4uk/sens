# SENS-owned semantic tests

These are executable language-owned semantic witnesses, not host-language
semantic oracles.

`d1-d3-control-law.bits` contains only exact-width 0/1 domain words plus D2
framing. Correct D1/D3 semantics reaches exact D1 `1`. A wrong ATOM, EQ, or
COND decision routes into an intentionally non-callable D1 head so SENS itself
rejects the witness.

`d1-d3-control-law.sens` is the canonical physical T5 form of exactly those
words.

Rust, Python and shell are allowed to transport bytes, invoke SENS, and retain
evidence. They do not define the expected logic of this witness.

`result-status-d1-law.bits` extends the same rule into the reasoning outcome
layer. Its executable heads include exact D9 `RESULT-TAGGED?` and
`MAKE-PROVED`, while D3 `COND/EQ/QUOTE` and D1 `0/1` carry the verdict.
If either the true or false result law is wrong, SENS takes an intentionally
non-callable D1 branch and rejects its own witness. The host runner therefore
does not need an expected semantic value.

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
