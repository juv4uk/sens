
<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="sens — exact-width domain language" width="100%">

# SENS (СЕНС)

**Експериментальна мова програмування, у якій двійкова координата є частиною семантики.**

<p><a href="https://github.com/juv4uk/sens/releases/latest/download/sens-cli-web.html"><strong>▶ Спробувати SENS у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/sens/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml)

**Українська — перша мова проєкту.**

</div>

---

Current authority: Contract 11.9 · D1–D10 owner-ratified (D10 whole-domain) · D24+ numeric owner-ratified · D10 F1/F2/F3/T5 pending

> **Операційний стан на 12.10.2026:** каталог D10 ратифіковано цілісно (1024/1024), але це не відкриває автоматично фізичне виконання. Nano-SENS має відтворювані два чисті прогони для конкретного compiler-artifact baseline, однак повний мінімальний seed ще не виміряно. Бенчмарк-лабораторія перевищила масштаб одного README: generated index зараз містить 54 зареєстровані стенди й 7 явних винятків для support-каталогів (це не стенди); ще 109 каталогів лишаються некласифікованими до завершення backfill #4172. [Повний статус, межі доказів і план лабораторії](docs/project-reality-2026-10-12.uk.md). Останній повний sweep на `ea156c1d` охопив **54/54 стенди: 53 PASS / 0 FAIL / 1 BLOCKED**. STORE/AIR тепер пройшов: поточні українські source-head-и (`як-є`, `перше`) ідуть через `parse_mixed_exact_domain`, їхні lowered trace/value/output збігаються з canonical binary. Фізичний T5 benchmark також має PASS із 8/8 source→T5 bytewise checks та execution parity. Єдиний blocker — cross-language: актуальний Contract 11.9 корпус з незалежним oracle ще не реалізований; відсутність Guix теж заважає старому replay, але сама його установка не перетворить historical Function8/FASL на поточний proof. [Історія sweep-ів і raw evidence](evidence/benchmark-sweep-2026-10-12.json).

## SENS у двох словах

SENS — це не «звичайна мова з бітовими opcode».

У SENS **точна двійкова послідовність + точна ширина + закон домену** утворюють semantic identity.

~~~text
D1 1  ≠  D2 01  ≠  D3 001  ≠  D4 0001
~~~

Число, яке можна отримати з бітів, — лише похідне представлення. 168 не стає семантичним значенням замість 10101000.

І так само байт, u8, FPGA-комірка чи інший carrier не визначає meaning.

Поточна нормативна база — **Contract 11.9**: ратифіковані D1–D9, цілісний домен **D10 1024/1024** (акт 12.10.2026), а також окреме числове сімейство **D24/D48/D96/…**. Докази F1/F2/F3 для резидентів D10 і фізичне T5-виконання ще не допущені. Перехід самого `language-contract.lisp` до canonical visible-binary source ще триває в **#4248**; цей README описує цільову binary-source модель, а не оголошує незавершений cutover завершеним.

---

**Заміряний спринт 09.10.2026 (GitHub-hosted, без нової семантики):** потокове T5-кодування — **109 → 70 нс/виклик** для 1 D3 QUOTE і **48 896 → 47 852 нс/виклик** для 1024 форм (побайтова тотожність до заміру, same-run paired control); доменна зайнятість D3 — **25,069 → 3,746 нс/звернення**, D7 — **132,771 → 5,326 нс/звернення** (D3–D7 бітмаски та O(1) lookup, але *різні* hosted-прогони, не контрольований A/B). [SHA, p50/p95, T5 raw evidence](benchmarks/physical-sens-runtime/streaming-t5-baseline-2026-10-09.md) · [SHA та методика occupancy](docs/benchmarks/2026-10-09-domain-occupancy-bitmask.uk.md). **Це швидкість окремих механізмів, не всієї мови; червоні Hosted CI/Vertical Day не скасовані.**

### Файлова та виконавча влада

Канонічне розширення вихідного коду — **`.lisp`**. У поточній українській проєкції це людський запис `ук`; семантичну тотожність задають точні двійкові слова, ширини та ратифіковані домени, а не назви функцій.

**`.wsm`** і **`.my`** — історичні псевдоніми розширення (*legacy aliases*) для сумісності. Вони не створюють інших семантичних законів.

**Rust — референсна реалізація** (*reference implementation*) для перевірюваного виконання, кодера/декодера й тестових оракулів. Rust, компілятор і жоден backend **не** визначають семантику SENS: її влада походить від ратифікованих законів і виконуваних свідчень; див. [карту семантичної влади](docs/semantic-authority-map.md).

## Фізичні кодеки: семантика SENS одна, носії різні

Фізичний кодек **не створює іншу мову**. T5, Frame3 Carrier (F3C) і
Frame3-Micro (F3M) мають відновити ті самі точні доменні слова; після
декодування вони передаються тому самому канонічному SENS reader/evaluator.

| Назва | Носій | Статус / роль |
|---|---|---|
| **T5** | `.sens` | загальний канонічний фізичний transport |
| **Frame3 Carrier (F3C)** | `.senc` | явно вибраний компактний carrier для дуже малих програм; історичні CLI/докази ще використовують коротку назву `F3` |
| **Frame3-Micro (F3M)** | `.f3m` | bounded micro-profile із зовнішньо відомим профілем; для доведеного класу справжня виконувана програма SENS може займати **рівно 1 байт** |
| **Envelope E1/E2/E3** | research carriers | самодостатні metadata-heavy оболонки, історично `S3/v1-v3`; це **не версії Frame3** |

Однобайтовий доказ не є моделлю іншої семантики: committed файл
`research/framed3/fixtures/car-cons-one-nil.f3m` містить **один байт
`0x45`**, F3M-декодер відновлює точні слова
`10 100 10 111 1 000 01 01`, а реальний SENS evaluator виконує їх як
`CAR(CONS(1,NIL))` з паритетом до T5. Отже це **фізичне кодування SENS**,
а не окрема мова.

Межа доказу принципова: F3M має зовнішньо вибраний профіль і не містить у
цьому одному байті magic/version/checksum; доведено 45 допустимих програм із
256 байтових кодів конкретної мікрограматики, а не «будь-яка SENS-програма
в одному байті». Повна номенклатура: [назви фізичних кодеків](docs/codec-naming-2026-10-12.uk.md).

---

## `.sens`: трійкова межа всередині, звичайний пробіл назовні

**Мова залишається строго двійковою.** Для файлового кодера `.sens` обрано T5 (транспортні трити 0/1/2, п'ять тритів на фізичний байт). `2` означає лише внутрішню межу доменних слів: коли файл відкритий через декодер, бачимо **звичайні пробіли**. **Окремого завершувача `22` немає:** кінець визначає сам файл, у фінальному байті можуть бути лише 0–4 трити `2` для доповнення.

~~~text
Двійкові слова:  10 | 001 | 00 | 000 | 01
Перегляд .sens:  10 001 00 000 01
~~~

~~~shell
cargo run -q -p sens-cli --bin sens-trit -- encode path/program.lisp
cargo run -q -p sens-cli --bin sens-trit -- open path/program.sens

# Фізична двійкова програма виконується без текстового Lisp-парсера:
cargo run -q -p sens-cli --bin sens -- tests/fixtures/migration-quote-cohort-main/quote-legacy.sens

# Еквівалентний явно викликаний чистий evaluator:
cargo run -q -p sens-cli --bin sens-trit -- eval tests/fixtures/migration-quote-cohort-main/quote-legacy.sens
~~~


**Поточна виконавча межа:** `sens file.sens` читає фізичні T5-байти, перевіряє канонічну D2-структуру й передає точні доменні слова чинному SENS-виконавцю **без** текстового Lisp-reader, неявного Core4-bootstrap або host capabilities. `sens-trit open file.sens` тільки показує бітовий перегляд, не виконує його. `sens-trit eval-core4 file.sens` є окремим *явним* запитом завантажити Core4, а не наслідком відкриття файлу. Недопущені закони чи дефектне T5 викликають відмову; чистий CLI-запуск сам по собі не є доказом історичної/української semantic-oracle parity. Перевірка механіки — [Physical binary SENS CLI smoke](.github/workflows/physical-binary-sens-cli.yml).

**Правило міграції репозиторіїв:** існуючий `каталог/назва.lisp` має відповідник `каталог/назва.sens`, який містить справжні T5-байти з транспортною `2` лише між точними двійковими словами. Створювати **третій однойменний файл `каталог/назва` без розширення** як похідний перевірюваний перегляд точних бітових слів `0/1`, розділених **одним ASCII-пробілом**, із одним завершальним LF. Не зберігати текст `0/1/2` у `.sens` і не підміняти фізичні T5-байти видимим бітовим записом. `.lisp`, `.sens` і файл-view мають проходити спільний перевірений roundtrip; сам лише транспортний view **не підтверджує семантичного допуску**. [Міграція `.lisp → .sens`](docs/SENS-LISP-TO-T5-MIGRATION-2026-10-08.uk.md), [координація агентів #4449](https://github.com/juv4uk/sens/issues/4449).

Файл `.sens` **фізично двійковий**, не ASCII. `open/view` декодує його у текст для людини; звичайному редактору потрібен окремий codec provider або file association. Деталі й обмеження: [T5 `.sens` — відображення пробілів](docs/sens-t5-space-view.uk.md). Формальна ратифікація всього wire-v1, зокрема EOS, лишається окремою задачею #4444.

Файл `.sens` **фізично двійковий**, не ASCII. `open/view` декодує його у текст для людини; звичайному редактору потрібен окремий codec provider або file association. Деталі й обмеження: [T5 `.sens` — відображення пробілів](docs/sens-t5-space-view.uk.md). Формальна ратифікація всього wire-v1, зокрема EOS, лишається окремою задачею #4444.

---
## Історична мить: Rule B — 10 жовтня 2026

**Перше слово (`10`) злите з відкриваючою дужкою, останнє (`01`) — із закриваючою.**  
Транспортна `2` стоїть **лише між внутрішніми словами**.

Це правило (Rule B) замінює попереднє Rule A (`10 2 … 2 01` з `2` між усіма). Результати на 5000 валідних D2-програм (1–5 рівнів вкладеності):

| Кодек | Розмір | Економія vs T5 | Перемоги |
|---|---|---|---|
| T5 (канонічний `.sens`) | 46 327 Б | — | 0/5000 |
| **Frame3 Carrier (`.senc`, F3C; історично F3)** | **37 837 Б** | **−18.3%** | **5000/5000** |

- Мінімальна рамка: **4 трити** (`1001` → `F3 00`) — порожня структура `10 01`.
- 1 байт тіла (`F3 XX`): 4–8 трит, **94 програми** (атоми 1–4 біт).
- 2 байти (`F3 XX YY`): 9–14 трит, **39 276 програм** — повноцінні D2-форми з 2–5 внутрішніми атомами.
- Канонічний T5 для `(10 10 00 01 01)` = 16 трит (4 Б); Frame-3 = 12 трит (3 Б) — **3× стиснення**.

Дослідницький Frame3 Carrier живе в `research/framed3/` (Rule B). Канонічний `.sens` (T5) **не змінено** — залишається Rule A (`2` між усіма словами). Етап Б #5438 (перенос у `crates/sens/src/codec/`) очікує еволюції стража #5442.

---
## Незалежна перевірка: які програми справді поміщаються в один байт

**Результат обмеженого, вичерпно перевіреного профілю: 45 програм / 256 можливих кодів байта.** Нижче наведено кожне прийняте значення, його програму, точні слова source і розмір тієї самої програми в канонічному T5.

### Що саме доведено — і чого це не доводить

- Це **окремий дослідний перелічувальний профіль `.f3m`**, описаний у [Rust-свідку](crates/sens/examples/frame3_one_byte_research.rs). Він стискає скінченну граматику з трьох значень `0`, `1`, `000` і вузького набору форм. Байтовий код сам собою не містить заголовка; декодер/профіль має бути вибраний зовні. Файл [`car-cons-one-nil.f3m`](research/framed3/fixtures/car-cons-one-nil.f3m) — рівно один байт `45` hex і кодує `CAR(CONS(1, NIL))`.
- Свідок перебирає усі 256 значень байта; для кожного з 45 прийнятих кодів перевіряє канонічний Rust D2 parser, реальне виконання, зворотний ранг та паритет із фізичним T5-кодуванням/читанням/виконанням. Тому таблиця нижче — вичерпна **для цього мікропрофілю**, а не для довільних програм SENS.
- **Це не самодостатній Frame3 Carrier F3C (`.senc`) і не канонічний `.sens`.** Оригінальний `.senc` містить маркер профілю `0xF3`, отже навіть один байт тіла означає щонайменше два фізичні байти всього файла. Поточне рішення проєкту: T5 лишається загальним `.sens`, а оригінальний F3 можна вибрати лише явно й коли повний файл коротший за T5 ([#5439](https://github.com/juv4uk/sens/issues/5439)). Немає автоматичного fallback між форматами.
- Число **94** в [дослідній таблиці місткості F3](research/framed3/README.md) — верхня межа транспортних послідовностей довжини 4–8 тритів, а не 94 доведені виконувані програми. Чинний канонічний D2 reader трактує `00` як роздільник, `01` як CLOSE, `10` як OPEN і `11` як DOT із вимогами до структури. Загальні рангові обчислення не скасовують цих правил.

### Повний перелік однобайтового мікропрофілю `.f3m`

У таблиці `0x..` — **код транспортного профілю**, не семантичне значення SENS. Колонка «Точні слова» зберігає ширину кожного слова та початкові нулі. «T5, байтів» — розмір тих самих слів у канонічному T5 без службових метаданих; це контрольне порівняння, а не обіцянка, що `.f3m` є виробничим кодеком.

| Байтовий код `.f3m` | Програма (людська проєкція) | Точні слова SENS | T5, байтів |
|---:|---|---|---:|
| `0x00` | `0` | `0` | 1 |
| `0x01` | `1` | `1` | 1 |
| `0x02` | `NIL` | `000` | 1 |
| `0x10` | `ATOM(0)` | `10 010 0 01` | 3 |
| `0x11` | `ATOM(1)` | `10 010 1 01` | 3 |
| `0x12` | `ATOM(NIL)` | `10 010 000 01` | 3 |
| `0x20` | `CONS(0, 0)` | `10 111 0 0 01` | 3 |
| `0x21` | `CONS(0, 1)` | `10 111 0 1 01` | 3 |
| `0x22` | `CONS(0, NIL)` | `10 111 0 000 01` | 3 |
| `0x23` | `CONS(1, 0)` | `10 111 1 0 01` | 3 |
| `0x24` | `CONS(1, 1)` | `10 111 1 1 01` | 3 |
| `0x25` | `CONS(1, NIL)` | `10 111 1 000 01` | 3 |
| `0x26` | `CONS(NIL, 0)` | `10 111 000 0 01` | 3 |
| `0x27` | `CONS(NIL, 1)` | `10 111 000 1 01` | 3 |
| `0x28` | `CONS(NIL, NIL)` | `10 111 000 000 01` | 4 |
| `0x40` | `CAR(CONS(0, 0))` | `10 100 10 111 0 0 01 01` | 5 |
| `0x41` | `CAR(CONS(0, 1))` | `10 100 10 111 0 1 01 01` | 5 |
| `0x42` | `CAR(CONS(0, NIL))` | `10 100 10 111 0 000 01 01` | 5 |
| `0x43` | `CAR(CONS(1, 0))` | `10 100 10 111 1 0 01 01` | 5 |
| `0x44` | `CAR(CONS(1, 1))` | `10 100 10 111 1 1 01 01` | 5 |
| `0x45` | `CAR(CONS(1, NIL))` | `10 100 10 111 1 000 01 01` | 5 |
| `0x46` | `CAR(CONS(NIL, 0))` | `10 100 10 111 000 0 01 01` | 5 |
| `0x47` | `CAR(CONS(NIL, 1))` | `10 100 10 111 000 1 01 01` | 5 |
| `0x48` | `CAR(CONS(NIL, NIL))` | `10 100 10 111 000 000 01 01` | 6 |
| `0x60` | `CDR(CONS(0, 0))` | `10 011 10 111 0 0 01 01` | 5 |
| `0x61` | `CDR(CONS(0, 1))` | `10 011 10 111 0 1 01 01` | 5 |
| `0x62` | `CDR(CONS(0, NIL))` | `10 011 10 111 0 000 01 01` | 5 |
| `0x63` | `CDR(CONS(1, 0))` | `10 011 10 111 1 0 01 01` | 5 |
| `0x64` | `CDR(CONS(1, 1))` | `10 011 10 111 1 1 01 01` | 5 |
| `0x65` | `CDR(CONS(1, NIL))` | `10 011 10 111 1 000 01 01` | 5 |
| `0x66` | `CDR(CONS(NIL, 0))` | `10 011 10 111 000 0 01 01` | 5 |
| `0x67` | `CDR(CONS(NIL, 1))` | `10 011 10 111 000 1 01 01` | 5 |
| `0x68` | `CDR(CONS(NIL, NIL))` | `10 011 10 111 000 000 01 01` | 6 |
| `0x80` | `EQ(0, 0)` | `10 101 0 0 01` | 3 |
| `0x81` | `EQ(0, 1)` | `10 101 0 1 01` | 3 |
| `0x82` | `EQ(0, NIL)` | `10 101 0 000 01` | 3 |
| `0x83` | `EQ(1, 0)` | `10 101 1 0 01` | 3 |
| `0x84` | `EQ(1, 1)` | `10 101 1 1 01` | 3 |
| `0x85` | `EQ(1, NIL)` | `10 101 1 000 01` | 3 |
| `0x86` | `EQ(NIL, 0)` | `10 101 000 0 01` | 3 |
| `0x87` | `EQ(NIL, 1)` | `10 101 000 1 01` | 3 |
| `0x88` | `EQ(NIL, NIL)` | `10 101 000 000 01` | 4 |
| `0xA0` | `QUOTE(0)` | `10 001 0 01` | 3 |
| `0xA1` | `QUOTE(1)` | `10 001 1 01` | 3 |
| `0xA2` | `QUOTE(NIL)` | `10 001 000 01` | 3 |

### Відтворення

З кореня репозиторію запустити:

```bash
cargo run -p sens --example frame3_one_byte_research
```

Очікуваний висновок свідка: `45/45` прийнятих замкнених виразів, перевірка всіх 256 можливих байтів, семантичний паритет із T5 та підтверджений фізичний розмір одного байта для `.f3m`. Для дослідної Рамки-3 окремо див. [опис F3](research/framed3/README.md), [ранговий простір канонічного D2](research/framed3/CANONICAL-D2-RANK.md) та [віртуальну рамку](research/framed3/VIRTUAL-FRAME-UNIVERSAL.uk.md).

---

## Подивімося на саму мову

Ось маленька програма, у якій **весь executable source можна побачити як точні двійкові слова**.

Людська форма:

~~~lisp
(CAR (CONS () ()))
~~~

Це означає:

> взяти CAR від пари, у якій обидва елементи — порожня структура.

Канонічна видима двійкова форма:

~~~text
10 100 00 10 111 00 000 00 000 01 01
~~~

Тут немає ні #b..., ні рядків "101", ні десяткових semantic IDs.

Розбираємо послідовність:

~~~text
10    D2 open
100   D3 CAR
00    D2 separator

10    D2 open
111   D3 CONS
00    D2 separator
000   D3 empty
00    D2 separator
000   D3 empty
01    D2 close

01    D2 close
~~~

Тобто структура програми видно прямо з бітів:

~~~text
10 [100 00 10 [111 00 000 00 000] 01] 01
~~~

А semantic words мають **різну ширину там, де цього вимагає домен**:

~~~text
D2 = 2 біти
D3 = 3 біти
~~~

Результат цієї програми — D3 000, тобто порожня структура.

### Те саме іншою surface-мовою

Людські surface names — лише проекції. Наприклад, current Ukrainian surface може записати ту саму операцію як:

~~~lisp
(перше (сполучити () ()))
~~~

Семантична програма при цьому не стає іншою. Після canonical lowering вона приходить до тієї самої двійкової identity.

---

## Чотири фундаментальні речі

### 1. D2 задає форму

D2 не містить Core-функцій. Він описує структуру source:

~~~text
00  separator
01  close
10  open
11  dot
~~~

Наприклад:

~~~text
10 100 00 000 01
~~~

має відкрити форму, покласти туди D3-word 100 і закрити її.

11 — саме D2 dot. Воно не є «ще одним opcode».

### 2. D3 задає фундамент мови

Поточний D3:

| Біти | Meaning | Surface |
|---|---|---|
| 000 | порожня структура | `()` |
| 001 | QUOTE | як-є |
| 010 | ATOM | атом? |
| 011 | CDR | решта |
| 100 | CAR | перше |
| 101 | EQ | тотожне? |
| 110 | COND | за-умовою |
| 111 | CONS | сполучити |

Ці координати — **current authority**, а не старі prefix-tree експерименти.

### 3. Ширина є частиною identity

Не можна зробити так:

~~~text
001 → 1 → byte 1
~~~

і потім забути, що це був D3.

Правильно:

~~~text
(D1, 1)
(D2, 01)
(D3, 001)
(D4, 0001)
~~~

— чотири різні exact-width identities.

### 4. Carrier не є семантикою

У пам'яті D3 може фізично лежати в u8.

На FPGA D3 може потрапити у ширшу BRAM word.

У WASM воно може пройти через integer type.

Це нічого не змінює:

~~~text
semantic width  ≠  physical carrier width
~~~

---

Історія назви: проєкт починався під робочою назвою `my-lisp`, поточне ім'я — SENS. Ратифікація D9: **owner-ratified #4008**. Чинні таблиці людських поверхонь: [D1](lib/domains/d1.lisp), [D8](lib/domains/d8.lisp), [D9](lib/domains/d9.lisp). Для D10 нормативні координати й декларації законів наведено в [канонічному інвентарі](knowledge/d10-v18-semantic-inventory.json), а статус рішення — в [акті власника](knowledge/d10-owner-whole-domain-ratification-20261012.json). Це не надає автоматичного допуску T5.

## D1–D10 та D24+

SENS будує не одну плоску таблицю opcode, а **драбину доменів**.

| Домен | Ширина | Роль |
|---|---:|---|
| D1 | 1 | точний PredicateBit |
| D2 | 2 | структура source |
| D3 | 3 | фундамент Core |
| D4 | 4 | bootstrap |
| D5 | 5 | наступний exact-width semantic domain |
| D6 | 6 | наступний exact-width semantic domain |
| D7 | 7 | Sound7/Text7 та окремі role laws |
| D8 | 8 | повний owner-ratified domain |
| D9 | 9 | повний owner-ratified domain |
| D10 | 10 | весь каталог 1024/1024 ратифіковано; F1/F2/F3/T5 залишаються відкритими |
| D24+ | 24·2^n | ратифіковані числові домени D24/D48/D96/D192/… |

Поточна owner-ratified картина:

~~~text
D7 = 126/128 admitted; 2 координати reserved
D8 = 256/256
D9 = 512/512
D10 = 1024/1024, whole-domain owner-ratified, T5 not admitted
D24+ = owner-ratified numeric ladder
~~~

D9 має окремий runtime-carrier ланцюг. Це механізм розміщення, а не привід звести D9 назад до D8/SID8.

---

## Як виглядає справжня binary source

Канонічний source має містити **лише видимі біти та синтаксичні розділення**.

Добре:

~~~text
10 100 00 10 111 00 000 00 000 01 01
~~~

Не є канонічним semantic source:

~~~text
#b100
"100"
4
168
Sid8(168)
Function8(...)
~~~

Останні форми можуть існувати як compatibility, tooling або host representation, але вони не повинні ставати authority для current SENS source.

---

## Чому 00, 01, 10, 11 не плутаються з D3

Двобітні слова належать **D2**.

Трибітні слова належать **D3**.

Тому:

~~~text
10  ≠  010
01  ≠  001
11  ≠  111
~~~

10 — D2 open.

010 — D3 ATOM.

11 — D2 dot.

111 — D3 CONS.

Саме тому SENS не намагається вирівняти все до одного 8-бітного поля.

---

## Як мова росте

SENS не хоче вручну роздати meaning кожному вільному бітовому шаблону.

Потрібен закон:

~~~text
корінь
  ↓
закон
  ↓
породження
  ↓
witness
  ↓
falsifier / negative cases
  ↓
ratification
~~~

Для selector-family це особливо наочно. У current D3:

~~~text
100 = CAR
011 = CDR
~~~

Але подальший selector не можна призначати тільки через «схожість бітів». Кожна family-law має бути окремо доведена або ратифікована.

Отже:

> **геометрія допомагає знайти закон; вона не замінює закон.**

---

## Канонічний pipeline

~~~text
human / symbolic surface
        ↓
domain-aware parser
        ↓
exact-width semantic objects
        ↓
domain laws / evaluator
        ↓
IR / lowering
        ↓
Rust / WASM / C / FPGA / other substrate
~~~

Назва CAR, перше, aṇu або інша surface-форма не є semantic authority.

Так само backend не має права сказати:

> «у мене opcode 100, отже це CAR».

Правильний напрямок інший:

> «семантика вже визначила exact D3:100; backend лише обирає механізм виконання».

---

## Українська surface

Українська — основна surface-мова SENS.

Поточні короткі програмні імена:

~~~text
порожнє
як-є
атом?
решта
перше
тотожне?
за-умовою
сполучити
~~~

Повні назви та інші поверхні зберігаються окремо:

~~~text
ук → укр → san → en → LISP → sym
~~~

Surface можна повністю перейменувати без зміни semantic identity.

---

## Інструменти для двійкової мови

У репозиторії вже є корисне tooling-ядро.

### Єдина команда для міграції `.lisp` → фізичний `.sens`

**Запускайте з кореня репозиторію:** `scripts/migrate.py` — перевірений
маршрутизатор до вже реалізованих трьохпрохідного мігратора, T5-кодека,
Git-атестації й справжнього SENS Rust-оракула. Він не додає нових функцій
мови, не конвертує непідтверджені символи за схожістю назв і не пише в
`main` автоматично.

~~~bash
# 1. Назви конкретних ще не допущених файлів та причини, БЕЗ запису
python3 scripts/migrate.py candidates --report /tmp/sens-candidates.json

# 2. Пробний запуск справжнього мігратора на ОДНОМУ старому файлі
python3 scripts/migrate.py preview benchmarks/lists.lisp \
  --mirror /tmp/sens-preview --report /tmp/sens-preview.json
# Якщо повернуло BLOCKED — потрібний доказ/закон, а НЕ вимкнення захисту

# 3. Збірка чинного Rust D2 рідера
cargo build -p sens-cli --bin sens-trit

# 4. Допуск тільки після незалежно доведеного source→T5→oracle
python3 scripts/migrate.py admit \
  --manifest /tmp/approved-original-proof.json \
  --mirror /tmp/sens-approved \
  --reader target/debug/sens-trit \
  --report /tmp/sens-admission.json

# 5. Лише якщо попередній звіт VERIFIED_NOT_WRITTEN
python3 scripts/migrate.py admit \
  --manifest /tmp/approved-original-proof.json \
  --mirror /tmp/sens-approved \
  --reader target/debug/sens-trit \
  --report /tmp/sens-written.json --write
~~~

`preview` ніколи не має `--write`. Публікація доступна **тільки**
через `admit --write`: маніфест фіксує вихідний Git blob,
фізичний SHA256, typed-word SHA256 і команди незалежного оракула.
Запис — лише нового файла `name.sens` у зовнішньому mirror; старий
`name.lisp` зберігається, перезапис заборонено. Результат
`BLOCKED` не вважати міграцією. Нові контрольні приклади не рахувати
як перенесення старих файлів.

Для агентів обов'язкові три окремі класи доказів: **правильні T5-байти,
валідна D2-структура, семантична еквівалентність у незалежному оракулі**.
Деталі маніфесту: [допуск міграції](docs/ADMIT-T5-MIGRATION.uk.md);
[координація #4449](https://github.com/juv4uk/sens/issues/4449).

### Компіляція з наявної трифайлової проєкції

Для вже канонічного україномовного джерела обмеженої підтриманої підмножини
три відповідники створює `scripts/publish_verified_uk_triplets.py`:
джерело `.lisp`, фізичний T5 `.sens` і файл-view без розширення. Запис
відбувається у зовнішнє дзеркало транзакційно. Цей генератор доводить
узгодженість проєкцій та кодека, **але сам не надає semantic-oracle admission**.

~~~bash
python3 scripts/publish_verified_uk_triplets.py \
  --mirror /tmp/sens-triplet-mirror \
  --report /tmp/sens-triplet-report.json \
  --write examples/migrated/smoke-quote.lisp

cargo xtask compiler-compile \
  --triplet /tmp/sens-triplet-mirror/examples/migrated/smoke-quote.sens \
  --out /tmp/smoke-quote-compiler-artifact.bin
~~~

`compiler-compile --triplet` звіряє всі три проєкції після exact-domain
lowering і викликає компіляторний корпус у `lib/compiler-nucleus.lisp`.
`--input` лишається окремим входом для канонічних SW1-байтів; режими
взаємовиключні, без format-sniffing чи fallback. Результат зараз —
канонічний backend-neutral compiler artifact, **не native executable** і
не доказ self-host fixed point C1→C2. Повний опис та acceptance gates:
[історія Nano-SENS/compiler](docs/research/nano-sens-size-frontier-20261011.uk.md).

**Виміряний стан Nano-SENS (12.10.2026):** два clean runs на pinned checkpoint пройшли по **189/189 тестів**, а C1/C2 executable і compiler-artifact output побайтно збіглися. Динамічний C1/C2: **92 248 Б на диску**, **85 685 Б PT_LOAD**, **70 655 Б executable sections**. Відомий partial operational-input subtotal останнього checkpoint — **36 033 737 Б**, але це **не** повний seed-total і не доказ мінімальності: source closure, Git metadata, toolchain/OS/shared libraries та межа vendor pruning ще не замкнені. Окремий K1 static-link/strip експеримент збільшив C1 до **792 544 Б**; його не прийнято як оптимізацію розміру. Цей Nano checkpoint прив'язаний до SENS source SHA `d0787a40fcea36501747732aa61b6de19fe29c70` / Contract 11.8; він доводить відтворюваність саме цієї pinned lineage, **не виконання D10 за Contract 11.9**. Окремий статичний аудит source edges завершився SUCCESS на snapshot `a825e5d3` (77 Rust-файлів / 111 ребер), але це не повний seed closure; [довготривалий receipt аудиту](evidence/nano-sens-static-source-edges-2026-10-12.json). Деталі, межі та raw runs: [повний журнал seed-v0](docs/research/nano-sens-seed-v0-20261012.uk.md) і [машинні докази baseline](evidence/nano-sens-seed-v0-2026-10-12.json).

### Exact-width witness-и

Корисні дослідницькі скрипти:

~~~text
scripts/research-2077-binary-word-law.py
scripts/research-2092-word-algebra.py
~~~

Вони досліджують exact binary words, width-preserving identity, prefix-vs-equality та зовнішнє framing.

Старі research witness-и в research-1962-*, research-2023-*, research-2034-* можуть містити історичні координати. Їхні алгоритми корисні, але їхні старі бітові карти не є current authority.

---

## Запуск

Потрібен Rust toolchain.

~~~bash
# REPL
cargo run -p sens-cli

# або приклад REPL
cargo run -p sens --example repl

# файл
cargo run -p sens-cli -- path/to/file.lisp

# тести
cargo test --workspace

# build
cargo build --workspace

# clippy
cargo clippy --workspace --all-targets -- -D warnings
~~~

Канонічне розширення source-файлів — **.lisp**.

.wsm та .my залишаються legacy aliases для старих матеріалів.

---

## Де дивитися далі

**Семантика:**

- [language-contract.lisp](language-contract.lisp)
- [docs/domain-paradigm.uk.md](docs/domain-paradigm.uk.md)
- [docs/language-core.md](docs/language-core.md)
- [docs/semantic-authority-map.md](docs/semantic-authority-map.md)

**Домени:**

- [lib/domains/](lib/domains)

**Conformance:**

- [tests/fixtures/conformance.lisp](tests/fixtures/conformance.lisp)

**Binary tooling:**

- [scripts/migrate-to-sens-codes.py](scripts/migrate-to-sens-codes.py)
- [scripts/research-2077-binary-word-law.py](scripts/research-2077-binary-word-law.py)
- [scripts/research-2092-word-algebra.py](scripts/research-2092-word-algebra.py)

**Правила для агентів:**

- [AGENTS.md](AGENTS.md)

---

## Що SENS намагається зробити

Не:

~~~text
зробити стару мову трохи компактнішою
~~~

і не:

~~~text
покласти всі функції у 8-бітну таблицю
~~~

А:

~~~text
визначити точні домени
        ↓
знайти закони між ними
        ↓
отримувати semantic objects з цих законів
        ↓
переносити одну семантику між різними substrates
~~~

Тому головний об'єкт SENS — не opcode.

**Головний об'єкт SENS — точна семантична identity, яку можна перенести з мови в мову, з backend у backend і з carrier у carrier, не змінюючи того, чим вона є.**

---

## English

SENS is an experimental programming language built around **exact-width binary domains**.

A semantic object is:

~~~text
exact bits + exact domain + proved/ratified law
~~~

Width is part of identity. A byte or u8 carrier is only storage.

Current Contract 11.9 preserves D1–D9, owner-ratifies D10 as a single 1024-code domain and keeps separately ratified D24+ numeric domains. Per-row D10 evidence and physical T5 admission remain pending. D2 owns source structure; D3 and higher domains own semantic residents according to their own laws.

Canonical binary source is visible binary, not decimal IDs, #b..., quoted binary strings, or host opcode wrappers.

The project is designed so that the same semantic identity can be executed by different substrates without making any backend the owner of language meaning.

---

## License

[ВОЛЬНІСТЬ](LICENSE)
