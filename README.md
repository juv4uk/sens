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
[![Domain tables](https://github.com/juv4uk/sens/actions/workflows/domain-tables.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/domain-tables.yml)

**Українська — перша мова проєкту.** Англійська й німецька — допоміжні.

</div>

---

## Що таке SENS

SENS — експериментальна мова програмування і лабораторія формальної семантики. Її поточна конституція — **Contract 11.8 і owner-ratified драбина точних доменів D1–D9**: D7 має 126/128 semantic residents із двома owner-reserved координатами, D8 — 256/256, D9 — 512/512.

Історично проєкт розвивався під робочою назвою `my-lisp`. Старі матеріали зберігаються як provenance розвитку ідей, але не визначають чинну семантичну модель.

Канонічне розширення вихідного коду — **`.lisp`**. `.wsm` і `.my` зберігаються лише як **legacy aliases** для сумісності зі старими матеріалами та інструментами; вони не визначають окрему семантику.

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

Поточний машинно-читаний контракт: [`language-contract.lisp`](language-contract.lisp), Contract **11.8**.

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

Це важлива різниця. **Сам факт, що бітова координата механічно представна в певній ширині, не надає їй meaning.** Для current D1–D9 meaning/occupancy задають уже ратифіковані domain laws; для майбутніх або research-доменів стан **UNKNOWN** лишається чесним і корисним — він означає, що admission law ще не знайдений або не прийнятий.

### Конкретний приклад: селектори

У ратифікованому D3 є два selector-корені:

```text
100  CAR
011  CDR
```

Для першого розгортання selector-family доведений локальний закон:

```text
suffix 0 → compose CAR
suffix 1 → compose CDR
```

Тому D4-селектори породжуються механічно:

```text
1000  CAAR
1001  CADR
0110  CDAR
0111  CDDR
```

Цей конкретний D4-закон **не надає автоматичної влади D5+**. Глибші selector-family у D5, D6 і D8 допускаються лише там, де для них є окремо прийнята карта/закон і немає конфлікту з уже ратифікованими residents. Схожість бітового рисунка сама по собі нічого не ратифікує.

Це і є бажаний тип росту SENS: **корені + доведений закон → відтворювана родина**, але лише в межах, де закон пройшов falsifier і не суперечить іншим ратифікованим доменам.

---

## Домени як будинки, а біти як адреси кімнат

Найпростіша інтуїція SENS така: **кожен домен — це окремий будинок, а точна бітова координата — адреса кімнати всередині нього**.

```text
SENS
  |
  +-- D1: будинок на 2 кімнати
  +-- D2: будинок на 4 кімнати
  +-- D3: будинок на 8 кімнат
  +-- D4: будинок на 16 кімнат
  +-- D5: будинок на 32 кімнати
  +-- D6: будинок на 64 кімнати
  +-- D7: будинок на 128 кімнат
  +-- D8: будинок на 256 кімнат, 256/256 ратифіковано
```

У домені `Dn` є рівно `2^n` можливих адрес. Але сама адреса ще не створює мешканця. **Закон домену визначає, хто має право жити в кімнаті і що цей мешканець означає.**

Тому однакова на вигляд адреса в різних будинках не означає одну й ту саму річ:

```text
D1: 1
D2: 01
D3: 001
D4: 0001
```

Це різні будинки, різні кімнати і різні semantic identities.

### D1 — найменший будинок: «ні» і «так»

У D1 лише дві кімнати:

```text
0  → NO  / НІ
1  → YES / ТАК
```

Це PredicateBit — точна відповідь предиката. Тут немає третього стану і structural `()` не є «ні».

### D2 — будинок структури

D2 має чотири кімнати, в яких живуть елементи структурної граматики:

```text
00 → separator
01 → close
10 → open
11 → dot
```

Тобто D2 вже не відповідає «так/ні». Він описує **форму запису**.

### D3 — фундаментальний будинок Core

У D3 вісім кімнат:

```text
000 → ()
001 → QUOTE
010 → ATOM
011 → CDR
100 → CAR
101 → EQ
110 → COND
111 → CONS
```

Тут уже живе фундамент мови: порожня структура, quotation, перевірка атома, селектори, рівність, умовний вибір і побудова пари.

### D4 — перший повний bootstrap-будинок

D4 має 16 кімнат, і всі вони зайняті ратифікованими residents:

```text
0000 APPLY      0001 EVAL
0010 LAMBDA     0011 DEFINE
0100 NOT        0101 NULL
0110 CDAR       0111 CDDR
1000 CAAR       1001 CADR
1010 LOOKUP     1011 BIND
1100 EVCON      1101 EVLIS
1110 LIST       1111 APPEND
```

Це вже «будинок, у якому мова починає обслуговувати сама себе»: тут є evaluation, визначення функцій, environment-механізми, похідні селектори та list operations.

### D5, D6, D7 — більші будинки

Далі принцип не змінюється — змінюється лише місткість і закони заселення:

```text
D5 → 32 кімнати, 32/32 ратифікованих residents
D6 → 64 кімнати, 64/64 ратифікованих residents
D7 → 128 кімнат, 126/128 admitted; 2 координати зарезервовані
```

D5 і D6 вже містять ширші функціональні родини та локальні algebra/generator laws. D7 переважно є Sound7/Text7-доменом: його мешканці — не «ще більше opcode-ів Core», а об'єкти власного семантичного будинку.

### D8 — повний восьмибітний будинок

D8 має 256 можливих восьмибітових адрес і **owner-ratified 256/256 semantic residents під #3960**. Це не робить усі 256 residents автоматично callable: semantic residency і runtime mechanism лишаються різними осями.

Тому правильна картина не така:

```text
є вільна кімната → поселимо туди функцію
```

а така:

```text
знайшли закон
      ↓
довели / ратифікували його
      ↓
закон визначив resident
      ↓
resident отримав точну кімнату
```

Отже, SENS — це не один великий будинок із 256 opcode-кімнатами. Це **драбина окремих доменних будинків**, де кожен має власну ширину, власні правила і власних мешканців.

> **Домен — будинок. Біти — адреса кімнати. Закон — правило заселення. Semantic object — мешканець.**

---

## D1–D9: одна драбина, різні закони

| Домен | Ширина | Поточна роль |
|---|---:|---|
| **D1** | 1 біт | PredicateBit: точне YES/NO |
| **D2** | 2 біти | структурна граматика |
| **D3** | 3 біти | фундамент Core |
| **D4** | 4 біти | bootstrap і перше розгортання законів |
| **D5** | 5 бітів | typed domain; резиденти визначаються власними законами |
| **D6** | 6 бітів | typed domain; ширша область для доведених незалежних факторів |
| **D7** | 7 бітів | owner-ratified #3572, 126/128: Sound7/Text7 + окремі role laws; 2 координати owner-reserved/pinned |
| **D8** | 8 бітів | owner-ratified #3960, 256/256 semantic residents; callability окрема від residency |
| **D9** | 9 бітів | owner-ratified #4008, 512/512 semantic residents; 128 law-forced + 384 owner-ratified gauge |

### Канонічні таблиці доменів

Human surfaces живуть **по одному домену на файл**:

```text
lib/domains/d1.lisp
lib/domains/d2.lisp
lib/domains/d3.lisp
lib/domains/d4.lisp
lib/domains/d5.lisp
lib/domains/d6.lisp
lib/domains/d7.lisp
lib/domains/d8.lisp
```

У кожному файлі порядок колонок однаковий:

```text
ук → укр → san → en → LISP → sym
```

- `ук` — компактна українська програмна поверхня;
- `укр` — повна українська розшифровка;
- `san` — санскритська surface без програмних маркерів `?` / `!`;
- `en` — англійська програмна surface;
- `LISP` — історичне/reference Lisp spelling, якщо воно доречне;
- `sym` — символічна/гліфова projection, якщо вона є.

Маркери синхронні в програмних поверхнях: **предикати мають `?` у `ук/укр/en`**, destructive/in-place операції мають **`!` у `ук/укр/en`**. D7 містить 126 semantic rows; `0100001` і `0101010` owner-reserved і навмисно не отримують фальшивої семантики.

Ці таблиці — human-readable projections над уже ратифікованими exact-domain identities. Вони не замінюють domain law і не створюють semantic identity самі.

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

Українська — головна surface-мова проєкту. У current domain tables дві українські колонки мають різні ролі:

```text
ук   = коротке програмне ім'я
укр  = повна українська розшифровка
```

Скорочення мають бути передбачуваними, а не телеграфними. Ми скорочуємо **структуру**, не калічимо корені слів: `п/р` для selector-path (`п=перше`, `р=решта`), `?` для предикатів, `!` для destructive/in-place операцій, усталені `нсд/нск` для математичних назв. Наприклад:

```text
ук             укр
п-р            перше-від-решти
видалити!      видалити-на-місці!
нсд            найбільший-спільний-дільник
```

Маркери `?` і `!` синхронізуються в `ук/укр/en`; `san` їх не використовує. Усі чинні semantic residents D1–D9 мають заповнені `ук`, `укр` і `san`.

Surface може бути зручним, красивим і читабельним. Але машинна семантика має пережити повне перейменування surface без зміни програми.

Деталі:

- [`docs/uk-surface-naming.md`](docs/uk-surface-naming.md)
- [`docs/ukrainian-api.md`](docs/ukrainian-api.md)
- [`docs/program-surface-translator.md`](docs/program-surface-translator.md)
- [`docs/domain-surfaces-d7.md`](docs/domain-surfaces-d7.md)
- [`docs/domain-surfaces-d8.md`](docs/domain-surfaces-d8.md)
- [`lib/domains/`](lib/domains)

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

- Contract 11.8 з domain-qualified identity;
- owner-ratified драбина D1–D9; D7 126/128, D8 256/256, D9 512/512;
- exact-width carrier/packing механізми;
- D1 PredicateBit;
- D2 structural grammar;
- D3 foundation;
- D4 bootstrap;
- D5/D6 ratified domain laws і executable guards;
- D7 owner-ratified 126/128 Sound7/Text7 domain + окрема LocalOrdinal role;
- D8 owner-ratified 256/256 під #3960 із окремою runtime-callability віссю;
- D9 owner-ratified 512/512 під #4008: 128 law-forced selector coordinates + 384 owner-ratified S4 gauge;
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

1. [`docs/README.md`](docs/README.md) — карта актуальної документації;
2. [`docs/domain-paradigm.uk.md`](docs/domain-paradigm.uk.md) — навіщо існують домени і як мова росте;
3. [`language-contract.lisp`](language-contract.lisp) — машинна конституція Contract 11.8;
4. [`lib/domains/`](lib/domains) — канонічні human-readable таблиці D1–D9, один домен = один файл;
5. [`docs/language-core.md`](docs/language-core.md) — точна domain identity;
6. [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md) — порядок семантичної влади;
7. [`docs/uk-surface-naming.md`](docs/uk-surface-naming.md) — правила `ук/укр`, `?`, `!`, selector-скорочень;
8. [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) — observable conformance;
9. [`AGENTS.md`](AGENTS.md) — правила роботи агентів.

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

SENS is an experimental language whose current Contract 11.8 ratifies exact-width domains D1–D9. D7 has 126/128 admitted residents with two owner-reserved coordinates; D8 is owner-ratified 256/256 under #3960; D9 is owner-ratified 512/512 under #4008.

Its central idea is not “smaller opcodes”. A canonical semantic object is:

```text
exact bits + exact domain + proved/ratified law
```

The language is intended to **grow generatively**: a small basis of roots plus executable laws should derive larger semantic families. Free bit patterns do not automatically acquire meaning, and UNKNOWN is an epistemic state rather than spare allocation space.

Human-language names and execution backends are projections/mechanisms. They do not own semantic identity.

Start with [`docs/domain-paradigm.uk.md`](docs/domain-paradigm.uk.md) and [`language-contract.lisp`](language-contract.lisp).

## Deutsch · Kurzfassung

SENS ist eine experimentelle Sprache mit ratifizierten Exact-Width-Domänen D1–D9. D7 enthält 126/128 semantische Residents; D8 ist unter #3960 vollständig mit 256/256 Residents ratifiziert.

Ein kanonisches semantisches Objekt besteht aus:

```text
exakten Bits + exakter Domäne + bewiesenem/ratifiziertem Gesetz
```

Die Sprache soll durch Gesetze wachsen, nicht durch das manuelle Belegen freier Bitmuster. Menschliche Namen und Backends sind Projektionen beziehungsweise Mechanismen und besitzen nicht die semantische Identität.

---

## Ліцензія

[ВОЛЬНІСТЬ](LICENSE)
