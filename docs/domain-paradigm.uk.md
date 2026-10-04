# Нова парадигма SENS: домени, закони і генеративний ріст

**Статус:** пояснювальний документ до Contract 11

**Семантична влада:** цей текст не замінює `language-contract.lisp` і ратифіковані domain laws.

## 1. Навіщо взагалі потрібна нова парадигма

SENS починався як дослідження компактної двійкової identity. Але проста таблиця «код → функція» має фундаментальну межу: вона **перелічує**, а не **пояснює**.

Якщо ми вручну призначили сто кодів, ми знаємо сто фактів. Ми ще не знаємо, чому вони розташовані саме так, які з них незалежні, які породжуються іншими і що має з'явитися на наступній ширині.

Нова парадигма ставить інше питання:

> **Яка найменша система коренів і законів може породити семантичну структуру мови?**

Це перетворює domain layout із довідника на предмет математичного дослідження.

---

## 2. Канонічний semantic object

Contract 11 задає базову формулу:

```text
semantic object
    =
exact binary object
  + exact domain
  + proved / ratified law
```

У цієї формули три незалежні частини.

### Exact bits

Біти мають точну довжину. `001` — не те саме, що `00000001`.

### Exact domain

Домен є межею інтерпретації. Однаковий payload може легально існувати в кількох доменах і мати різний зміст.

### Law

Закон говорить, чому координата є resident, що вона означає, як вона поводиться і як це відтворити.

Без закону координата не отримує семантики лише від того, що вона синтаксично існує.

---

## 3. D1–D8 — не вісім таблиць

Ратифікована драбина:

```text
D1  1 bit
D2  2 bits
D3  3 bits
D4  4 bits
D5  5 bits
D6  6 bits
D7  7 bits
D8  8 bits
```

Ємність Dn дорівнює `2^n`, але **capacity ≠ occupancy**.

Треба відрізняти:

```text
capacity
resident
derivable resident
callable resident
implemented resident
```

Це дозволяє не плутати математичну конституцію мови зі станом конкретного runtime.

---

## 4. Закон важливіший за номер

Найкращий semantic placement — той, який можна відтворити з коротшого пояснення.

Наприклад, selector-family має два D3-корені:

```text
101  CAR
110  CDR
```

і закон продовження:

```text
append 0 → compose CAR
append 1 → compose CDR
```

Звідси механічно:

```text
1010  CAAR
1011  CADR
1100  CDAR
1101  CDDR
```

Наступний біт знову подвоює родину.

Для такого resident ми можемо зберегти не лише координату, а й **generation certificate**:

```text
root
+ suffix path
+ law version
→ resident
```

Тоді компілятор, тест або інший агент може сам повторити доказ походження.

---

## 5. Generative compression

Якщо одна формула породжує багато residents, це не лише економія документації.

Це **semantic compression**.

У selector witness:

```text
selector_owned(Dn) = 2^(n-2)
capacity(Dn)       = 2^n
selector_share     = 1/4
```

Тобто родина росте експоненційно, але закон залишається малим.

Ключове: це не означає «автоматично зайняти чверть кожного майбутнього домену». Це означає, що якщо law admission чинний для певного домену, ці координати вже не потребують незалежного ручного винаходу.

---

## 6. UNKNOWN — повноцінний науковий стан

У SENS вільна координата не є запрошенням до allocation.

```text
UNKNOWN
```

означає:

- немає достатнього закону;
- або немає достатнього evidence;
- або координата може належати іншій ще невідомій family;
- або вона може залишитися навмисно незайнятою.

UNKNOWN захищає від numerology.

Красивий патерн бітів, симетрія чи схожість на інший код можуть бути підказкою для гіпотези, але не є доказом.

---

## 7. Що вважати хорошим новим законом

Сильний candidate law має:

1. **малий basis** — небагато незалежних roots;
2. **точну операцію** — жодних словесних «майже так само»;
3. **domain typing** — зрозуміло, до яких об'єктів закон застосовується;
4. **передбачення** — закон породжує ще не вручну записані cases;
5. **replay** — certificate можна перевірити програмно;
6. **falsifier** — відомо, що могло б спростувати закон;
7. **collision test** — дві незалежні семантики не зливаються випадково;
8. **non-contagion** — закон не поширюється на сусідній домен без окремого доказу.

Якщо закон лише красиво пояснює вже відому таблицю, але нічого не передбачає, це слабше за закон, що генерує нові перевірювані наслідки.

---

## 8. Факторизація і «корені» функцій

Один із найцікавіших напрямів — побудувати точну алгебру над semantic objects.

Припустімо, визначена операція композиції `∘` і точне поняття рівності функцій.

Якщо знайдено:

```text
G ∘ G = F
```

то в цій алгебрі `G` можна досліджувати як композиційний квадратний корінь `F`.

Або ширше:

```text
factor(F)      → {A, B}
compose(A, B)  → F
inverse(F)     → G
meet(A, B)     → C
join(A, B)     → D
```

Найцікавіший випадок — коли незалежне математичне виведення приходить **точно до вже існуючого domain resident**.

Тоді ми отримуємо не «вдалий номер», а свідчення прихованої структури.

Але слово «корінь» не можна використовувати метафорично в коді. Перед ратифікацією треба зафіксувати:

- алгебру;
- операцію;
- domain;
- equality;
- область визначення;
- witness;
- counterexamples.

---

## 9. Core-Math і Core — не одне й те саме

Математичний research track може знаходити красиві операції, фактори та закономірності.

Але:

```text
Core-Math evidence
≠ автоматичне Core occupancy
```

Математика може запропонувати candidate law. Потрапляння до мовного домену потребує окремого семантичного admission.

Ця межа потрібна, щоб не перетворити гарну аналогію на приховане allocation rule.

---

## 10. Граф доменів

Зручна модель SENS — не масив таблиць, а граф:

```text
roots
  │
  ├── law A ──→ descendants
  │
  ├── law B ──→ descendants
  │
  └── bridge ─→ object in another domain
```

У графі можна вимірювати:

- кількість незалежних roots;
- depth derivation;
- branching factor;
- coverage;
- residue;
- число unexplained coordinates;
- collision count;
- shortest certificate;
- instruction cost;
- encoding cost.

Це дозволяє порівнювати дві концепції не за смаком, а за структурною простотою та перевірюваністю.

---

## 11. Семантичне дерево програми

AST має нести semantic identity, а не англійську назву чи backend opcode.

Бажана форма pipeline:

```text
surface token
    ↓
mechanical projection
    ↓
DomainIdentity { domain, exact_bits, law_ref }
    ↓
AST
    ↓
law-aware lowering
    ↓
IR
    ↓
backend
```

Після lowering backend уже не повинен вгадувати domain із payload.

Це робить компілятор простішим концептуально: human surface від'єднаний від identity, а physical representation від'єднаний від semantics.

---

## 12. Бінарна source-мова

Точна ширина має пережити reader.

Наприклад:

```text
10 001 01
```

де:

```text
10   = D2 open
001  = exact W3 word
01   = D2 close
```

Тут важливо не те, що всі шматки складаються з нулів і одиниць. Важливо, що grammar зберігає **межі й domain context**.

Бінарність без boundaries неоднозначна. Boundaries без domain law — лише синтаксис. Значення виникає тільки на повному ланцюгу.

---

## 13. Backend не має семантичної влади

Rust enum, C ABI, GPU instruction, FPGA LUT або BRAM layout — механізми.

Вони можуть оптимізувати:

- packing;
- dispatch;
- arithmetic;
- memory;
- parallelism;
- timing.

Вони не можуть сказати:

> «Оскільки це фізично 8 бітів, це один і той самий semantic object».

Звідси принцип:

```text
semantic_width
≠ physical_width
```

Особливо це важливо для FPGA.

---

## 14. Як оцінювати дві ідеї

Якщо є два candidate laws, порівнювати треба не лише їхню красу.

Корисні метрики:

### Семантичні

- roots;
- generated residents;
- unexplained residue;
- collisions;
- certificate length;
- independent laws;
- falsifier strength.

### Компіляторні

- AST nodes;
- IR instructions;
- lowering steps;
- branches;
- decoder complexity.

### Representation

- source bits;
- packed bits;
- metadata;
- parse/decode time.

### Runtime

- execution time;
- memory;
- cache behavior.

### FPGA

- LUT;
- FF;
- BRAM;
- DSP;
- routing;
- Fmax;
- latency;
- power.

Мета — знайти структуру, яка одночасно **проста семантично, добре доводиться і чесно реалізується**.

---

## 15. Ратифікація і реалізація

SENS навмисно дозволяє семантичному закону існувати раніше, ніж усі backends його реалізують.

Тому статуси треба тримати окремо:

```text
RATIFIED
PROVED
GENERATED
IMPLEMENTED
BENCHMARKED
OPTIMIZED
```

Наприклад, domain може бути ратифікований, а Rust carrier ще не мати спеціального newtype. Це implementation gap.

Навпаки, host може мати зручну функцію, але без domain law це ще не canonical SENS semantic object.

---

## 16. Практичне правило для агентів

Перед тим як додати новий resident, запитайте:

1. Чи це незалежний root?
2. Чи він уже виводиться з чинного law?
3. Чи існує менший basis?
4. Чи можна породити його certificate?
5. Що спростує цю гіпотезу?
6. Чи не змішую я domains через однаковий payload?
7. Чи не видаю physical representation за semantics?
8. Чи не заповнюю UNKNOWN лише тому, що координата вільна?
9. Чи є objective benchmark для competing mechanisms?
10. Чи може інший агент повторити доказ з репозиторію?

Якщо відповідей немає — краще залишити UNKNOWN і поставити research task.

---

## 17. Коротка формула SENS

Старий стиль проєктування:

```text
таблиця → коди → реалізація
```

Нова парадигма:

```text
roots
  + laws
  + exact domains
  + executable evidence
        ↓
semantic graph
        ↓
AST / compiler / backends
        ↓
objective measurements
```

Найцінніший результат — не ще одна функція в таблиці.

Найцінніший результат — **закон, через який ця функція більше не потребує ручного призначення**.
