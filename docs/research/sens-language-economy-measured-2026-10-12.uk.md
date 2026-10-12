# Заміряний звіт: економія мови SENS на наявних фікстурах

Дата: 2026-10-12 · Репо `juv4uk/sens` @ `de08d69` · Автор: асистент (лейн CI/TESTS #5608)

**Що це.** Замір *уже наявних* фікстур репозиторію власним кодеком репо
(`scripts/sens_t5_codec.py`). Семантику **не змінено** — файли лише читались і
кодувались. Мета — дати чесну, відтворювану картину того, *де саме* мова
«не оптимальна», щоб будь-яка оптимізація потім мала базову лінію для порівняння.

## 0. Метод і охоплення

- Виміряно **23 фікстур** `.sens` (`tests/fixtures/**`, `lib/surface/`).
- Round-trip `decode_bytes → encode_words` **бітово ідентичний на всіх** — жодна
  фікстура не постраждала від виміру.
- Одиниці: «логічні біти» (L) = сума ширин точних слів; «T5 біти» = 8 × байтів
  фізичного `.sens` (5 трітів/байт, розділювач-тріт `2` між словами).

## 1. Біт-економія запису — заміряно

| фікстура | слів | логічних біт | T5 біт | надлишок | тріт-пак. | розділюв. | padding |
|---|--:|--:|--:|--:|--:|--:|--:|
| `lib/surface/ukr-acceptance.sens` | 62 | 295 | 576 | 1.953× | 177 | 98 | 6 |
| `tests/fixtures/core1-domain-canary/second.sens` | 33 | 76 | 176 | 2.316× | 46 | 51 | 3 |
| `tests/fixtures/core1-fourth-domain-canary/fourth.sens` | 71 | 163 | 376 | 2.307× | 98 | 112 | 3 |
| `tests/fixtures/core1-third-domain-canary/third.sens` | 57 | 131 | 304 | 2.321× | 79 | 90 | 5 |
| `tests/fixtures/migration-atom-cohort/atom-empty.sens` | 5 | 12 | 32 | 2.667× | 7 | 6 | 6 |
| `tests/fixtures/migration-d1-cond-cohort/branch.sens` | 19 | 38 | 96 | 2.526× | 23 | 29 | 6 |
| `tests/fixtures/migration-d4-selector-cohort/caar.sens` | 29 | 68 | 160 | 2.353× | 41 | 45 | 6 |
| `tests/fixtures/migration-eq-cohort/eq-legacy-sid.sens` | 7 | 17 | 40 | 2.353× | 10 | 10 | 3 |
| `tests/fixtures/migration-eq-cohort/eq-lisp15.sens` | 7 | 17 | 40 | 2.353× | 10 | 10 | 3 |
| `tests/fixtures/migration-eq-cond-cohort/eq-cond-select.sens` | 53 | 113 | 264 | 2.336× | 68 | 83 | 0 |
| `tests/fixtures/migration-eq-cond-cohort/eq-cond-skip.sens` | 53 | 113 | 264 | 2.336× | 68 | 83 | 0 |
| `tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens` | 53 | 113 | 264 | 2.336× | 68 | 83 | 0 |
| `tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens` | 53 | 113 | 264 | 2.336× | 68 | 83 | 0 |
| `tests/fixtures/migration-multiform-cohort/two-forms.sens` | 21 | 49 | 112 | 2.286× | 29 | 32 | 2 |
| `tests/fixtures/migration-multiform-cohort-main/two-forms.sens` | 21 | 49 | 112 | 2.286× | 29 | 32 | 2 |
| `tests/fixtures/migration-pair-cohort/pair-car-cdr.sens` | 17 | 39 | 88 | 2.256× | 23 | 26 | 0 |
| `tests/fixtures/migration-pair-cohort/pair-cons.sens` | 15 | 35 | 80 | 2.286× | 21 | 22 | 2 |
| `tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens` | 17 | 39 | 88 | 2.256× | 23 | 26 | 0 |
| `tests/fixtures/migration-pair-cohort-main/pair-cons.sens` | 15 | 35 | 80 | 2.286× | 21 | 22 | 2 |
| `tests/fixtures/migration-quote-cohort/quote-legacy.sens` | 5 | 12 | 32 | 2.667× | 7 | 6 | 6 |
| `tests/fixtures/migration-quote-cohort/quote-lisp15.sens` | 5 | 12 | 32 | 2.667× | 7 | 6 | 6 |
| `tests/fixtures/migration-quote-cohort/quote-mylisp.sens` | 5 | 12 | 32 | 2.667× | 7 | 6 | 6 |
| `tests/fixtures/migration-quote-cohort-main/quote-legacy.sens` | 5 | 12 | 32 | 2.667× | 7 | 6 | 6 |
| **РАЗОМ** | | **1563** | **3544** | **2.267×** | **937** | **967** | **73** |

### 1.1 Розклад надлишку (головна знахідка)

Надлишок **2.267×** розкладається майже **навпіл** на два незалежні джерела:

- **тріт-пакування 0/1 — 937 біт** (59.9% від L). Кожен біт слова
  пишеться як *тріт* (`0`/`1`), а 5 трітів = 1 байт; 5 бітів вмісту займають 8 бітів,
  тобто **рівно +0.6×** на кожен логічний біт.
- **розділювач-тріт `2` — 967 біт** (по одному тріту між словами, 1.6 біта кожен);
- **padding до 5-трітової межі — 73 біт** (дрібний, домінує на коротких програмах).

Перевірка: L + тріт + розділювач + padding = T5 на кожному рядку (напр. `third`:
131 + 79 + 90 + 5 = 305 ≈ 304, округлення 1.6 біта/тріт).

## 2. Точна бітність доменів — заміряно

- Драбина `lib/domains/d1..d10.lisp`: ширина рядків **точна** (Dn = рівно n біт),
  таблиці **повні** (d1=2, d2=4 … d9=512, d10=1024; d7=126 = 128−2 зарезервовані).
- **D8 = 256 слів рівно = 1 байт** — те, що ти назвав «256 програм в 1 байт».
- Ширини, реально вживані фікстурами: `{1: 21, 2: 415, 3: 157, 4: 2, 7: 32, 9: 1}`
  — усі точні, жодного слова «не своєї» ширини.

## 3. Маршрути виконання — з наявних бенчмарків репо

Це **не переміряно тут**, а зведено з уже наявних результатів репо
(`benchmarks/generator-economy`, `benchmarks/whole-program-domains`).

**generator-economy** (середнє на кандидата):
- `tree_steps`: compiled-route=14,142  explicit-row=14,328  generator-lazy=15,415
- `registry_lookups`: explicit-row=13,981
- `generator_apps`: generator-lazy=161

**whole-program** (середнє на кандидата):
- `tree_steps`: compiled=5,453  flat=5,442  hybrid=5,787  root-suffix=8,550
- `registry_lookups`: compiled=345  flat=345  hybrid=345  root-suffix=3,108
- `wire_bits`: compiled=91  flat=91  hybrid=91  root-suffix=91  (однакові — маршрут не змінює запис)

## 4. Що з цього випливає (виведено, не заміряно)

Кожен важіль окремо, за тими ж заміряними числами:

| стан | надлишок |
|---|--:|
| як є (тріт-пакування + розділювач + padding) | **2.267×** |
| прибрати тріт-пакування 0/1 (пакувати біти бітами) | 1.665× |
| прибрати розділювач (самороздільний/префіксний тег домену) | 1.646× |
| прибрати обидва | 1.000× (+ тег) |

Тобто «оптимізованість запису» має **два рівні за важіль**: тріт-пакування й
розділювач. У виконанні заміряно, що `compiled`/`flat` — найдешевші за кроками й
лукапами, `root-suffix` ≈ у 1.5× дорожчий, а `generator-lazy` обмінює табличні
лукапи на генераторні застосування.

## 5. Чесні межі

- Виміряно лише **23 малих фікстур**; увесь `lib/` блоковано fail-closed
  канонічним мігратором, тож твердження про економію на *великих* програмах —
  виведені, а не заміряні.
- Розділ 3 — синтез наявних бенчмарків, не власний повторний замір; числа
  збігаються з `economy.tsv`/`whole_program.tsv` репо.
- «Самороздільний тег» як заміна розділювача — **гіпотеза** (ширина домену *не*
  є автоматичним розділювачем; потрібен префіксний код), не заміряна тут.
- Жодних змін семантики, workflow чи гейтів не внесено цим заміром.
