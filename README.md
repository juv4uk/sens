<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="sens — exact-width domain language" width="100%">

# sens (СЕНС)

**Експериментальна мова, що росте з точних двійкових доменів і математичних законів**

*An experimental language grown from exact-width binary domains and executable laws*

<p><a href="https://github.com/juv4uk/sens/releases/latest/download/sens-cli-web.html"><strong>▶ Спробувати sens у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/sens/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml)
[![Surface drift](https://github.com/juv4uk/sens/actions/workflows/surface-drift-check.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/surface-drift-check.yml)

**Українська — перша мова проєкту.** Англійська й німецька — допоміжні.

</div>

---

## Що таке SENS

SENS — експериментальна мова програмування і лабораторія формальної семантики. Її поточна конституція — **ратифікована драбина точних доменів D1–D8**.

Основна ідея не в тому, щоб зменшити звичні інструкції до меншої кількості бітів. І не в тому, щоб заповнити таблицю кодами.

Основна ідея така:

> **семантичний об'єкт має точну двійкову координату, належить точному домену і отримує значення лише від доведеного або ратифікованого закону.**

У скороченій формі:

```text
semantic object
    =
exact bits
  + exact domain
  + proved / ratified law
```

Тому однаковий числовий payload у різних доменах — не одна й та сама річ:

```text
D1 1  ≠  D2 01  ≠  D3 001  ≠  D4 0001
```

Width входить в identity, але **width сам по собі не створює значення**.

Поточний машинно-читаний контракт: [`language-contract.lisp`](language-contract.lisp), Contract **11.0**.

Докладний опис парадигми: [`docs/domain-paradigm.uk.md`](docs/domain-paradigm.uk.md).

---

## Нова парадигма за 30 секунд

Звичайна таблиця каже:

```text
візьмемо вільний код → призначимо йому функцію
```

SENS намагається робити навпаки:

```text
знайти корінь
    ↓
довести закон перетворення
    ↓
породити наслідок
    ↓
перевірити witness / falsifier
    ↓
лише тоді допустити semantic resident
```

Тобто мова має **рости**, а не просто накопичувати записи.

Це важлива різниця. Координата, яка синтаксично поміщається в D5 або D8, ще нічого не означає. Стан **UNKNOWN** — чесний і корисний: він говорить, що закон ще не знайдений або не доведений.

### Конкретний приклад: селектори

У D3 є два корені:

```text
101  CAR
110  CDR
```

Для selector-family вже існує генеративний закон:

```text
suffix 0 → compose CAR
suffix 1 → compose CDR
```

Тому наступний рівень не треба винаходити вручну:

```text
1010  CAAR
1011  CADR
1100  CDAR
1101  CDDR
```

А ще один біт породжує наступне покоління селекторів.

Це і є бажаний тип росту SENS: **мала кількість коренів + закон → велика відтворювана родина**, де кожен нащадок має generation certificate.

---

## D1–D8: одна драбина, різні закони

| Домен | Ширина | Поточна роль |
|---|---:|---|
| **D1** | 1 біт | PredicateBit: точне YES/NO |
| **D2** | 2 біти | структурна граматика |
| **D3** | 3 біти | фундамент Core |
| **D4** | 4 біти | bootstrap і перше розгортання законів |
| **D5** | 5 бітів | typed domain; резиденти визначаються власними законами |
| **D6** | 6 бітів | typed domain; ширша область для доведених незалежних факторів |
| **D7** | 7 бітів | Sound7 / текстово-фонологічний і provenance-простір за власним законом |
| **D8** | 8 бітів | точний Core domain, окремий від будь-якої історичної 8-бітної схеми |

Важливо розрізняти п'ять речей:

```text
carrier exists
≠ coordinate is occupied
≠ object is derivable
≠ object is callable
≠ runtime implements it
```

Ратифікація домену не означає, що кожна з його `2^N` координат автоматично має функцію. І навпаки: відставання конкретного Rust/backend механізму не скасовує ратифікований закон мови.

---

## Як SENS має рости

Нова функція або інший semantic resident бажано з'являється одним із трьох шляхів:

1. **Корінь** — справді незалежний об'єкт, який не виводиться з уже прийнятих.
2. **Наслідок закону** — об'єкт механічно породжується з кореня/коренів і має replayable certificate.
3. **Міст між доменами** — окремо доведений закон пов'язує об'єкти різних доменів без їхнього злиття.

Не допускається логіка:

```text
"тут вільно"
"біти схожі"
"так було в старій таблиці"
"цей host enum має те саме число"
→ отже це та сама семантика
```

### Математичне дослідження

Окремий напрям SENS — шукати алгебру над функціями та доменами.

Наприклад, якщо в чітко визначеній функціональній алгебрі виявиться:

```text
G ∘ G = F
```

то `G` можна досліджувати як композиційний «корінь» `F`. Якщо незалежний математичний шлях приведе до вже відомого semantic object, це значно цікавіше за ручне призначення коду: ми знайшли **структурний закон**.

Але математична краса не замінює доказу. Потрібні:

- точне означення операції;
- типи/domain boundaries;
- witness;
- falsifier або negative cases;
- відсутність колізій;
- відтворюваність.

Саме так SENS може поступово стати мовою, структура якої пояснює сама себе.

---

## Семантична влада

README пояснює проєкт, але не визначає його семантику.

```text
language-contract.lisp
        ↓
ратифіковані domain laws
        ↓
executables / witnesses / conformance fixtures
        ↓
reference implementation
        ↓
інші backends
        ↓
README / tutorials / historical research
```

Якщо код суперечить чинному закону — це **implementation debt**, а не нова семантика.

Якщо старий документ суперечить Contract 11 або пізнішому ратифікованому закону — це історія дослідження.

Повна карта: [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).

---

## Бінарна форма — не байтовий контейнер

SENS не вважає, що все треба спочатку перетворити на 8-бітне слово.

Канонічний reader має зберігати точну ширину. Наприклад:

```text
10 001 01
```

можна читати як:

```text
D2 open
D3 exact word 001
D2 close
```

Тут `001` не є «байтом із нулями зліва». Це точне трьохбітове слово.

Packed transport може фізично складати біти щільніше або зберігати їх у ширших машинних словах, але фізичне пакування не має права змінити semantic identity.

---

## AST, compiler і backend

Наслідок нової парадигми для компілятора простий:

```text
surface
   ↓
domain-qualified AST
   ↓
law-aware lowering
   ↓
IR
   ↓
backend mechanism
```

Людська назва потрібна для читання й письма, але не є semantic authority.

Backend може бути Rust, C, WASM, GraalVM, FPGA чи іншим. Він отримує вже визначений semantic object і вибирає механізм виконання. Backend не має права відновлювати значення з номера opcode, byte value або host type.

### FPGA

Для FPGA особливо важливо розділяти:

```text
semantic_width
≠
physical_width
```

D3 залишається D3 навіть якщо конкретний BRAM фізично зберігає його в ширшій комірці.

FPGA-бенчмарки відповідають на питання **«скільки це коштує залізу?»**, а не **«що це означає?»**.

---

## Українська, English, Sanskrit і символи

Людські surface-мови — це проєкції над уже визначеною семантикою.

```text
людське spelling
      ↓
surface projection
      ↓
exact domain identity
```

Тому українська, англійська, санскритська й символічна поверхні не створюють чотири різні функції.

Українська — головна surface-мова проєкту. Наприклад:

```lisp
(визначити квадрат
  (функція (число)
    (помножити число число)))
```

Surface може бути зручним, красивим і читабельним. Але машинна семантика має пережити повне перейменування surface без зміни програми.

Деталі:

- [`docs/ukrainian-api.md`](docs/ukrainian-api.md)
- [`docs/program-surface-translator.md`](docs/program-surface-translator.md)
- [`lib/surface/uk-acceptance.lisp`](lib/surface/uk-acceptance.lisp)

---

## Одна мова, різні execution substrates

SENS не вимагає, щоб одна реалізація найкраще робила все.

```text
                    SENS
           domains / laws / AST
                      |
       +--------------+--------------+
       |              |              |
      Rust           FPGA          kernels
                                     |
                         +-----------+-----------+
                         |           |           |
                       Prolog      Datalog      CLIPS
```

Common Lisp, Prolog, Datalog, CLIPS, C, WASM, FPGA чи інший substrate може мати власний сильний механізм. Але жоден substrate не стає власником semantic identity мови.

Принцип:

> **Мова визначає що це. Backend визначає як це виконати.**

---

## Що вже є в репозиторії

- Contract 11 з domain-qualified identity;
- ратифікована драбина D1–D8;
- exact-width carrier/packing механізми;
- D1 PredicateBit;
- D2 structural grammar;
- D3 foundation;
- D4 bootstrap;
- D5/D6 domain-law research і executable guards;
- D7 Sound7 / local-ordinal evidence;
- D8 як окремий exact domain у конституції;
- selector generation witnesses;
- domain graph / factor / residue / closure experiments;
- one-way migration guard, який забороняє новому exact-width коду повертатися до старої flat-identity моделі;
- Rust, WASM, C та інші execution paths;
- FPGA exact-width benchmark/evidence lane.

### Важлива чесність про реалізацію

**Ратифікована семантика і стан реалізації — не одне й те саме.**

У source tree ще існує migration debt: старі workflows, compatibility paths, назви типів і backend adapters. Вони можуть бути потрібні для відтворення історичних доказів або поступового cutover.

Вони **не визначають сучасну модель SENS**.

---

## UNKNOWN — це не порожня клітинка для заповнення

Одна з найважливіших дисциплін проєкту:

> **UNKNOWN означає «ми ще не маємо достатнього закону», а не «сюди можна щось покласти».**

Це захищає SENS від numerology — спокуси оголосити законом красивий бітовий рисунок лише тому, що він красивий.

Хороший новий закон має пояснювати більше, ніж одну координату, і робити перевірювані передбачення.

---

## Як перевіряти нову ідею

Для нового domain law або generative family корисний мінімальний цикл:

```text
1. сформулювати закон
2. записати мінімальний basis / roots
3. згенерувати наслідки
4. перевірити відомі cases
5. шукати counterexample
6. перевірити collisions
7. виміряти compression / instruction cost
8. лише потім пропонувати ratification
```

Для performance-ідей додатково потрібні об'єктивні числа:

- кількість semantic/IR instructions;
- encoded bits;
- parse/decode cost;
- execution time;
- memory footprint;
- FPGA LUT/FF/BRAM/DSP;
- Fmax/latency після реального vendor flow.

Ефективність не ратифікує семантику, але допомагає вибрати кращий механізм для вже коректної семантики.

---

## Локальний запуск

Потрібен Rust toolchain. У репозиторії також є Guix manifest для відтворюваного середовища.

```bash
# REPL
cargo run -p sens --example repl
# або
cargo run -p sens-cli

# виконати файл
cargo run -p sens-cli -- path/to/file.lisp

# перевірки workspace
cargo test --workspace
cargo build --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

Канонічне розширення source — **`.lisp`**.

---

## З чого читати проєкт

Якщо ви бачите SENS уперше:

1. [`docs/domain-paradigm.uk.md`](docs/domain-paradigm.uk.md) — навіщо існують домени і як мова росте;
2. [`language-contract.lisp`](language-contract.lisp) — машинна конституція;
3. [`docs/language-core.md`](docs/language-core.md) — точна domain identity;
4. [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md) — порядок семантичної влади;
5. [`scripts/research-2322-generative-domain-forecast.py`](scripts/research-2322-generative-domain-forecast.py) — приклад генеративного закону;
6. [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) — observable conformance;
7. [`AGENTS.md`](AGENTS.md) — правила роботи агентів.

Для історії й research-археології дивіться `docs/research/` та `docs/archive/`, але датований документ не переважає чинний контракт.

---

## Мовна політика

1. Українська — перша і головна.
2. Англійська й німецька — допоміжні.
3. Текстові файли репозиторію — UTF-8.
4. Нові коментарі в коді — українською кирилицею.
5. Точні API, protocol literals, identifiers, filenames і upstream-назви не перекладаються довільно.

Машинно-читана політика: [`knowledge/language-policy.lisp`](knowledge/language-policy.lisp).

---

## English · short summary

SENS is an experimental language whose current constitution is the exact-width domain ladder D1–D8.

Its central idea is not “smaller opcodes”. A canonical semantic object is:

```text
exact bits + exact domain + proved/ratified law
```

The language is intended to **grow generatively**: a small basis of roots plus executable laws should derive larger semantic families. Free bit patterns do not automatically acquire meaning, and UNKNOWN is an epistemic state rather than spare allocation space.

Human-language names and execution backends are projections/mechanisms. They do not own semantic identity.

Start with [`docs/domain-paradigm.uk.md`](docs/domain-paradigm.uk.md) and [`language-contract.lisp`](language-contract.lisp).

## Deutsch · Kurzfassung

SENS ist eine experimentelle Sprache mit einer ratifizierten Exact-Width-Domänenleiter D1–D8.

Ein kanonisches semantisches Objekt besteht aus:

```text
exakten Bits + exakter Domäne + bewiesenem/ratifiziertem Gesetz
```

Die Sprache soll durch Gesetze wachsen, nicht durch das manuelle Belegen freier Bitmuster. Menschliche Namen und Backends sind Projektionen beziehungsweise Mechanismen und besitzen nicht die semantische Identität.

---

## Ліцензія

[ВОЛЬНІСТЬ](LICENSE)
