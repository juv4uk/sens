# Режими проєкту SENS

Дата: 12.10.2026.

Цей документ фіксує **режими фізичного представлення SENS**. Вони не
створюють окремих мов або семантик: усі допустимі носії мають відновити ті
самі точні доменні слова SENS і передати їх тому самому canonical
reader/evaluator.

## Нормативна матриця

| Режим | Носій | Статус | Вибір | Призначення |
|---|---|---|---|---|
| **T5M / General** | `.sens` | production/default | явно за `.sens` / T5M command | типовий канонічний фізичний transport; legacy T5 — лише явний маршрут |
| **F3C / Tiny Portable** | `.senc` | production explicit | явно за `.senc` / F3C command; внутрішній marker `0xF3` | самодостатній компактний carrier для дуже малих програм |
| **F3M / Micro Rank** | `.f3m` | bounded proven/research, не default production | сімейство явно як F3M; конкретний профіль **тільки довжиною** | максимальна щільність для скінченного канонічного каталогу коротких програм |
| **Envelope E1/E2/E3** | research carriers | research/history | тільки явний research decoder | self-contained metadata/integrity envelopes |

## Режим T5M / General

- Чинний канонічний загальний фізичний шлях і production default SENS.
- Розширення: `.sens`.
- Legacy T5 доступний лише через явний compatibility-маршрут.
- Ніякого автоматичного переходу в F3C/F3M за вмістом файла.
- Чинні migration/file-authority ворота перевіряють саме T5M там,
  де перевіряють canonical `.sens`.
- F3M/F3C не змінюють semantic identity програми.

## Режим F3C / Tiny Portable

- Явний компактний **самодостатній** carrier.
- Розширення: `.senc`.
- Історична коротка назва CLI/коду: `F3`; нормативна назва: **F3C**.
- Marker `0xF3` лишається частиною повного фізичного файла.
- Поточна обережна production-policy: розглядати F3C для T5M-програм не
  більше 16 байтів і вибирати його тільки якщо **повний F3C файл**
  строго менший за T5M та exact roundtrip успішний.
- Decode failure є помилкою; fallback/sniffing у T5M заборонений.

## Режим F3M / Micro Rank

F3M не платить внутрішній байт за magic/version. Сімейство `.f3m`
вибирається зовнішнім маршрутом, але конкретний профіль визначає **лише
точна фізична довжина payload**:

| Довжина | Профіль | Локальний rank-space | Активний стан доказу |
|---:|---|---:|---|
| 1 байт | **F3M-1** | 256 | dense **256/256** unique; exhaustive evaluator + historical legacy-T5 witness parity |
| 2 байти | **F3M-2** | 65 536 | dense **65 536/65 536** exhaustive encode/decode roundtrip |
| 3 байти | **F3M-3** | 16 777 216 | dense rank window; boundary/sample roundtrip, real evaluator witnesses, exhaustive final-64K search |
| 4 байти | **F3M-4** | 4 294 967 296 | dense rank window; algebraic capacity proof, 65 536 stratified roundtrip samples, real evaluator witness `DE AD BE EF` |
| 5 байтів | **F3M-5** | 1 099 511 627 776 | prefix-stable extension-space; 65 536 stratified roundtrips + executable all-basis witness `03 B1 C7 07 93`; dedicated proof 38234038310 GREEN |
| 0 або 6+ | — | — | fail-closed до окремого рішення |

### Єдиний canonical order

F3M-1, F3M-2, F3M-3 і F3M-4 не мають окремих таблиць із дублями. Вони займають
**неперетинні послідовні вікна одного глобального enumerator**:

- F3M-1: global ranks `0..255`;
- F3M-2: наступні `65 536`;
- F3M-3: наступні `16 777 216`;
- F3M-4: наступні `4 294 967 296`.

**F3M-5 не перенумеровує жодне з цих чотирьох вікон.** Його 40-бітовий
локальний rank-space задає окремий extension enumerator `frame3_micro_v5.rs`;
`EQ(ATOM,ATOM)` і замкнений `LAMBDA0` — нові конструктори. Dedicated
proof **38234038310 — SUCCESS**: boundary + 65 536 stratified roundtrips,
старі F3M1–4 byte regressions і real-evaluator witnesses пройшли разом.
Це не означає exhaustive evaluator sweep 2^40 і не перетворює F3M на
default production-route.

Encoder повертає найкоротший допустимий профіль. Для canonical mapping
виконується `encode(decode(payload)) == payload`.

### Поточні F3M witnesses

- **F3M-1 `3E`** → `CAR(CONS(1,NIL))`; 1 фізичний байт.
- **F3M-3 `2F 18 59`** → реальна програма з COND; evaluator повертає `1`.
- **F3M-3 `16 3C 63`** → найраніший global-rank witness, який уже містить
  усі 6 capability-класів поточної microgrammar:
  `QUOTE + ATOM + CONS + CAR + CDR + COND`.
- **F3M-3 `FF FB 37`** → переможець exhaustive-пошуку серед останніх
  65 536 кодів `FF 00 00..FF FF FF` за метрикою:
  capability diversity → COND count → encoded-operation count → depth →
  exact-word count → node count → later rank.
  Він має 6/6 capability-класів; сам `FF FF FF` має лише 4/6 і без COND.
- **F3M-4 `DE AD BE EF`** → 12-вузлова виконувана програма `ATOM(CONS(ATOM(CDR(CONS(QUOTE(0),CAR(CONS(NIL,QUOTE(0)))))),ATOM(ATOM(ATOM(QUOTE(NIL))))))`; evaluator повертає `0`.
- **F3M-5 `03 B1 C7 07 93`** → 11-node / 61-word executable witness із
  **QUOTE+ATOM+CONS+CAR+CDR+EQ+COND+LAMBDA**; evaluator повертає exact D1 `0`.

**F3M-5:** dedicated F3M proof run **38234038310 — SUCCESS**. Профіль має
повний 40-bit local rank-space, але **не** заявляє exhaustive 2^40 evaluator
sweep і лишається explicit bounded F3M route, а не новим default-кодеком.

### F3M-5λ research candidate: справжня nameless LAMBDA

Окремий модуль `frame3_micro_v5_lambda.rs` **не змінює чинний F3M-5 mapping**.
Він досліджує наступний канонічний 40-бітний простір, де параметри LAMBDA
представлені de-Bruijn references, а не текстовими символами:

- `BOUND(0)` — найближчий binder;
- `BOUND(1)` — binder на один рівень вище;
- вільний `BOUND(n)` за межами lexical depth відхиляється fail-closed;
- `λx.x`, `λy.y`, `λfoo.foo` мають одну nameless форму `λ.BOUND(0)`.

Proof run **38242173136 — SUCCESS**:
- усі boundary + 65 536 stratified 40-bit roundtrips PASS;
- `0000000000` → `λ.BOUND(0)` (I);
- `0000000010` → K = `λ.λ.BOUND(1)`;
- `000000000F` → KI = `λ.λ.BOUND(0)`;
- beta-witnesses I/K/KI PASS;
- all-basis witness `056169CB4A` має 11 micro-nodes і несе
  QUOTE+ATOM+CONS+CAR+CDR+EQ+COND+LAMBDA.

Наступний proof run **38260383334 — SUCCESS** прибрав останню важливу
умовність toy-evaluator-а. Nameless candidate тепер lower-иться прямо в
чинний SENS runtime:

- `BOUND(n) → ExprKind::Local { depth: n, index: 0 }`;
- `LAMBDA → D4:0010`;
- `0000000000` реально створює SENS closure і beta-редукується як I;
- K та KI проходять через справжні вкладені SENS closure/call frames;
- `056169CB4A` виконується canonical SENS evaluator-ом і повертає exact D1 `0`;
- жодне ім'я `x/y/foo` не входить у semantic body або фізичний payload.

Поточний Closure allocator все ще потребує evaluator-private slot token для
арності/створення кадру. Він має NUL-prefixed службове написання, не
зчитується з source, не входить у rank/payload і не використовується
`BOUND`-посиланнями; семантика залежить тільки від `Local(depth,index)`.


### F3M-5λA: application уже всередині п'яти байтів

Окремий research-модуль `frame3_micro_v5_lambda_app.rs` не змінює ні
production F3M-5, ні заморожений F3M-5λ v1. Він додає один структурний
constructor:

- `APPLY(function, argument)` — це **D2 call framing**, не новий domain resident;
- `LAMBDA` лишається D4:0010;
- `BOUND(n)` лишається nameless lexical reference;
- D1/D3 операції лишаються тими самими exact-domain механізмами.

Через це β-редукція тепер може бути частиною самого 40-бітного payload, без
зовнішнього підкладання аргументу:

- `00 00 00 02 4B` → `APPLY(λ.BOUND(0),1)` → exact **D1:1**;
- `00 00 0D 06 4F` → `APPLY(APPLY(λ.λ.BOUND(1),1),0)` → exact **D1:1**.

Обидва witnesses виконані **реальним SENS evaluator**, не лише research
evaluator. `0000000000` і далі означає `λ.BOUND(0)`, тому найкоротша
nameless identity не зрушилась.

Новий combinatorial space має **683 904 239 271** extension-термів через
12 micro-nodes і **9 019 588 596 096** через 13, тому повністю покриває
всі `2^40` payloads усередині 13-node шару. 65 536 deterministic stratified
roundtrips по 40-бітному простору пройшли. Це не exhaustive `2^40`
semantic sweep і не production admission.

Proof run **38263454497 — SUCCESS**.

#### B/C/S/W — чотири нові п'ятибайтові замкнені комбінатори

Це **дослідний** ранкер F3M-5λA; жодна з наведених байтових послідовностей
не змінює production F3M-5 і не створює нових канонічних резидентів.

| Комбінатор | Payload, рівно 5 байтів | Закон (зовнішні тестові аргументи) | Micro-nodes |
|---|---|---|---:|
| B: композиція | `00 00 3F EA 96` | `B I I x = x` | 8 |
| C: перестановка | `00 00 3F F9 F2` | `C K 0 x = x` | 8 |
| S: підстановка | `00 27 73 55 DA` | `S K K x = x` | 10 |
| W: дублювання | `00 00 05 24 5D` | `W K x = x` | 7 |

Закони перевірено для **обох точних D1-значень** засобами наявного SENS
evaluator; Rust у цьому тесті відповідає за механічні rank/unrank і
передачу AST, а **не встановлює нову семантику**. Самі B/C/S/W займають
по 40 біт; тестове `S K K x` **не заявляється** однією 5-байтовою програмою.

- [Автоматичний proof run 38471870869 — SUCCESS](https://github.com/juv4uk/sens/actions/runs/38471870869):
  один існуючий `ci.yml`, `test_id=frame3-bcsw-five-bytes`, точковий тест PASS.
- Реалізація та перевірка:
  [`frame3_micro_v5_lambda_app.rs`](../crates/sens/src/frame3_micro_v5_lambda_app.rs),
  `five_byte_bcsw_exact_sens_reduction`.
- Відтворення: `cargo test --locked -p sens --lib frame3_micro_v5_lambda_app::tests::five_byte_bcsw_exact_sens_reduction -- --exact --nocapture`.


Межа: de-Bruijn `BOUND(n)` поки research-semantic constructor і ще не має
окремо ратифікованої exact SENS-domain identity. Тому кандидат не може
підмінити production F3M-5, доки не буде прийнято закон lexical reference.

Green evidence:
- dense base proof: GitHub Actions run **38194615315**;
- final-page/full-capability search: GitHub Actions run **38195272188**.
- F3M-4 32-bit dense proof: GitHub Actions run **38197907496** — SUCCESS.

**Межа доказу:** ще не заявляється exhaustive evaluator sweep усіх
16 777 216 F3M-3 чи 4 294 967 296 F3M-4 програм. Для F3M-4 доведено
алгебраїчну достатність каталогу, boundary cases, 65 536 stratified
roundtrip samples і реальний evaluator witness. Повний 32-бітний semantic
sweep є окремим proof gate.

## Envelope E1/E2/E3

Це не «Frame3 v1/v2/v3».

- **E1** — historical S3/v1: RAW/REPEAT + metadata + CRC32.
- **E2** — historical S3/v2: E1 + bounded grammar-rank.
- **E3** — historical S3/v3: domain-aware envelope з explicit D24+.

Вони лишаються research/self-contained envelopes і не беруть участі в
default project-mode selection.

## Fail-closed routing

1. `.sens` → T5M (default); T5 — лише явний legacy-маршрут.
2. `.senc` → F3C.
3. `.f3m` → F3M family, а **payload length 1/2/3/4/5** → F3M-1/2/3/4/5 відповідно; F3M-5 proof-admitted у bounded F3M route, але не є default production-кодеком.
4. Content sniffing не дозволений.
5. Decode failure не дозволяє спробувати інший codec.
6. Один фізичний файл не трактується одночасно в кількох режимах.

## Що означає «режими проєкту»

Це режими **фізичного носія й маршрутизації**, не режими семантики мови.
Binary domain laws, D2 structure, evaluator і semantic identity лишаються
спільними. T5M — default/general; legacy T5 — explicit compatibility; F3C — explicit tiny portable; F3M —
explicit bounded micro-rank; E1–E3 — research envelopes.
