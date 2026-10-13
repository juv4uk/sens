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
