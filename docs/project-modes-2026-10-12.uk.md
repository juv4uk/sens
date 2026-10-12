# Режими проєкту SENS

Дата: 12.10.2026.

Цей документ фіксує **режими фізичного представлення SENS**. Вони не
створюють окремих мов або семантик: усі допустимі носії мають відновити ті
самі точні доменні слова SENS і передати їх тому самому canonical
reader/evaluator.

## Нормативна матриця

| Режим | Носій | Статус | Вибір | Призначення |
|---|---|---|---|---|
| **T5 / General** | `.sens` | production/default | явно за `.sens` / T5 command | загальний канонічний фізичний transport |
| **F3C / Tiny Portable** | `.senc` | production explicit | явно за `.senc` / F3C command; внутрішній marker `0xF3` | самодостатній компактний carrier для дуже малих програм |
| **F3M / Micro Rank** | `.f3m` | bounded proven/research, не default production | сімейство явно як F3M; конкретний профіль **тільки довжиною** | максимальна щільність для скінченного канонічного каталогу коротких програм |
| **Envelope E1/E2/E3** | research carriers | research/history | тільки явний research decoder | self-contained metadata/integrity envelopes |

## Режим T5 / General

- Канонічний загальний фізичний шлях SENS.
- Розширення: `.sens`.
- Ніякого автоматичного переходу в F3C/F3M за вмістом файла.
- Чинні migration/file-authority ворота залишаються T5-орієнтованими там,
  де вони перевіряють canonical `.sens`.
- F3M/F3C не змінюють semantic identity програми.

## Режим F3C / Tiny Portable

- Явний компактний **самодостатній** carrier.
- Розширення: `.senc`.
- Історична коротка назва CLI/коду: `F3`; нормативна назва: **F3C**.
- Marker `0xF3` лишається частиною повного фізичного файла.
- Поточна обережна production-policy: розглядати F3C для T5-програм не
  більше 16 байтів і вибирати його тільки якщо **повний F3C файл**
  строго менший за T5 та exact roundtrip успішний.
- Decode failure є помилкою; fallback/sniffing у T5 заборонений.

## Режим F3M / Micro Rank

F3M не платить внутрішній байт за magic/version. Сімейство `.f3m`
вибирається зовнішнім маршрутом, але конкретний профіль визначає **лише
точна фізична довжина payload**:

| Довжина | Профіль | Локальний rank-space | Активний стан доказу |
|---:|---|---:|---|
| 1 байт | **F3M-1** | 256 | dense **256/256** unique; exhaustive evaluator + T5 parity |
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

1. `.sens` → T5.
2. `.senc` → F3C.
3. `.f3m` → F3M family, а **payload length 1/2/3/4/5** → F3M-1/2/3/4/5 відповідно; F3M-5 proof-admitted у bounded F3M route, але не є default production-кодеком.
4. Content sniffing не дозволений.
5. Decode failure не дозволяє спробувати інший codec.
6. Один фізичний файл не трактується одночасно в кількох режимах.

## Що означає «режими проєкту»

Це режими **фізичного носія й маршрутизації**, не режими семантики мови.
Binary domain laws, D2 structure, evaluator і semantic identity лишаються
спільними. T5 — default/general; F3C — explicit tiny portable; F3M —
explicit bounded micro-rank; E1–E3 — research envelopes.
