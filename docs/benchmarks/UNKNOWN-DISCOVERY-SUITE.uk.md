# Unknown Discovery Suite для my-lisp / SENS

**Мета:** не довести наперед бажану тезу, а знайти властивості мови, яких ми ще не знаємо.

> Кожен прогін має породжувати не лише `PASS/FAIL`, а й новий запис: `OBSERVED`, `UNKNOWN`, `BLOCKED` або `COUNTEREXAMPLE`.

## Правила невідомого

1. **Немає мовчазного успіху.** Якщо oracle не визначений, результат — `UNKNOWN`, не `PASS`.
2. **Немає підміни семантики carrier-ом.** Rust/C/FPGA можуть бути механізмами спостереження; вони не ратифікують новий meaning.
3. **Кожен результат має provenance:** commit, authority-файл, corpus digest, toolchain, seed, межі пошуку.
4. **Контрприклад цінніший за середнє.** Перший мінімальний counterexample зберігається як regression fixture.
5. **Відсутність доказу не є false.** Невиконана гілка або недоведена еквівалентність лишається `REMAINDER`.

---

## 1. Semantic Boundary Atlas

### Питання
Які форми реально належать мові, а які лише схожі на executable forms?

### Метод
Згенерувати bounded corpus малих форм із:

- canonical binary identities;
- English / українськими / Sanskrit / symbolic surfaces;
- вкладеними application, lambda, define, quote, cond;
- порожніми й malformed tails;
- числовими та структурними аргументами.

Кожну форму проганяти через:

```text
parse → lower → admit → evaluate
```

і записувати вектор:

```text
(parse, lower, admit, callable, result, error-class)
```

### Нове знання
- перша форма, де surface стає числовим значенням;
- перша форма, де head втрачає callability;
- різниця між `parse accepted` і `semantic admitted`;
- непокриті переходи у вертикальному execution ladder.

### Falsifier
Якщо дві surfaces із тією самою identity отримують різні `admit/result` без дозволеної host-причини — `COUNTEREXAMPLE: representation dependence`.

---

## 2. Metamorphic Sovereignty Matrix

### Питання
Чи справді meaning належить identity, а не конкретному представленню?

### Перетворення
Для кожної accepted програми застосувати окремо:

- перестановку surface slots;
- EN → UKR → SA → symbolic projection;
- pack → unpack → repack;
- whitespace/comment normalization;
- canonical source → generated projection → canonical reader;
- Rust carrier → C carrier → Rust carrier.

### Oracle
Очікується не обов’язково однакова помилка, а стабільний semantic observation:

```text
same identity trace
same value/result
same admitted/rejected boundary
same UNKNOWN boundary
```

### Нове знання
- які трансформації семантично нейтральні;
- де починається host leakage;
- чи існують неочікувані representation-sensitive форми.

---

## 3. Failure Topology / Error Algebra

### Питання
Чи має мова стабільну алгебру помилок, чи різні шари випадково маскують один одного?

### Метод
Для одного базового corpus-а вводити одну помилку за раз:

- невідома surface;
- identity поза domain;
- не-callable head;
- неправильна ширина;
- відсутній slot;
- malformed pair;
- host I/O failure;
- recursion/resource exhaustion.

Будувати граф:

```text
source mutation → parser error → semantic error → carrier error → host error
```

### Нове знання
- помилки, які зараз зливаються в один клас;
- помилки, що переходять через boundary непоміченими;
- місця, де `UNKNOWN` помилково стає `FALSE` або `PASS`.

### Falsifier
Якщо mutation A і mutation B мають різний semantic cause, але однаковий observable error без explicit contract — `REMAINDER` до уточнення error semantics.

---

## 4. Phase-Transition Benchmark

### Питання
Де мова переходить у новий режим поведінки?

### Вісі
Експоненційно збільшувати по одній:

- depth nested application;
- lambda capture count;
- environment chain depth;
- list/pair width;
- numeric width;
- number of aliases per identity;
- source/package size;
- recursion depth.

### Вимірювати
Не тільки час:

```text
accepted / rejected
semantic parity
stack/heap growth
allocation count
carrier bytes
error class
first threshold N
```

### Нове знання
- перший structural cliff;
- чи існує максимальна глибина, не описана контрактом;
- чи runtime деградує плавно, чи має дискретний failure boundary;
- чи numeric identity змінює поведінку після певної ширини.

### Falsifier
Якщо threshold залежить від surface spelling, а не identity/structure — `representation dependence`.

---

## 5. Cross-Substrate Triangle

### Питання
Що є властивістю мови, а що властивістю конкретного substrate?

### Матриця
Один bounded corpus, коли доступні substrates:

```text
Rust reference | C carrier | FPGA carrier | Cyberpunk host
```

Для кожної комірки окремо:

- parse;
- identity preservation;
- lower;
- evaluate;
- host effect;
- failure behavior.

### Результат
Не один score, а conformance vector:

```text
rust: 111110
c:    111100
fpga: 110000
host: 111010
```

`0` не означає “мова неправильна”; він означає відсутній або непідтверджений шар.

### Нове знання
- перший substrate divergence;
- властивість, яку Rust reference випадково приховує;
- host effect, який помилково вважається semantic result.

---

## 6. Self-Hosting Fixed-Point Probe

### Питання
Чи може мова описати й перевірити власний semantic registry без зовнішнього oracle?

### Сходинки

```text
read registry
→ parse registry
→ lookup identity
→ validate registry
→ validate validator
→ validate result of validator
```

Кожна сходинка має окремий witness. Не дозволяти одному великиму “self-hosted pass” приховати невідомі переходи.

### Нове знання
- точна межа self-hosting;
- які операції ще позичені з Rust/Python;
- чи є circular proof, де validator лише повторює власне припущення.

---

## 7. Alias Pressure / Identity Collision Search

### Питання
Скільки surface aliases може мати одна identity до того, як з’являється ambiguity або lookup cliff?

### Метод
Для bounded identity domain поступово збільшувати:

- aliases per identity;
- Unicode normalization variants;
- near-colliding names;
- repeated language slots;
- symbolic aliases.

Перевіряти:

```text
lookup injectivity
identity stability
memory footprint
lookup time
collision diagnostics
```

### Нове знання
- практична межа alias system;
- чи є Unicode ambiguity;
- чи не перетворюється surface convenience на semantic authority.

---

## 8. Unknown-Preserving Differential Fuzzing

### Питання
Чи зберігає система невідомість під випадковим, але bounded дослідженням?

### Метод
Генерувати лише форми з відомою граматичною оболонкою, але залишати частину semantic cases без oracle. Порівнювати Rust/C/інші adapters не за forced result, а за чотирма станами:

```text
same-known
same-unknown
disagreement-known-vs-unknown
counterexample
```

### Критичне правило
`UNKNOWN` — повноцінний результат. Його не можна видаляти, замінювати нулем або трактувати як failure.

### Нове знання
- де evaluators мають різну epistemic boundary;
- які unknown-и відтворюються;
- де differential testing створює фальшиву впевненість.

---

## Пріоритет реалізації

| Порядок | Benchmark | Чому перший |
|---:|---|---|
| 1 | Semantic Boundary Atlas | Знайде конкретні невідомі переходи в evaluator |
| 2 | Failure Topology | Не дасть помилкам маскувати semantic gaps |
| 3 | Metamorphic Sovereignty Matrix | Перевірить центральну тезу representation independence |
| 4 | Phase-Transition Benchmark | Знайде реальні межі ресурсу й структури |
| 5 | Cross-Substrate Triangle | Розділить language property від host property |
| 6 | Self-Hosting Fixed-Point Probe | Перевірить незалежність semantic authority |
| 7 | Alias Pressure | Виявить межі multi-surface identity |
| 8 | Unknown-Preserving Differential Fuzzing | Поставить REMAINDER у центр автоматичного пошуку |

## Формат нового knowledge artifact

Кожен benchmark має писати:

```json
{
  "status": "OBSERVED|UNKNOWN|BLOCKED|COUNTEREXAMPLE",
  "authority_sha256": "...",
  "corpus_sha256": "...",
  "seed": 0,
  "bounds": {},
  "observations": [],
  "remainder": [],
  "minimal_counterexample": null
}
```

Це і є правильна мета: не найбільше зелених рядків, а **найменша чесна карта того, чого мова ще не знає про себе**.
