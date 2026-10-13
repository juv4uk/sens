# Проєкт: самороздільне кодування слів SENS — заміряно

Дата: 2026-10-12 · Репо `juv4uk/sens` @ `de08d69` · Автор: асистент (лейн CI/TESTS #5608)

**Що це.** Проєкт і *замір* заміни розділювача-тріта `2` на **самороздільне
(префіксне) кодування** слів — прямо на наявних фікстурах. Кодування реалізовано
й **round-trip перевірено**; семантику та жоден файл репо не змінено.

## 0. Ідея

Поточна T5-форма: слова з'єднані трітом `2`, далі 5 трітів/байт. Це дає дві плати:
(1) **тріт-пакування** — кожен біт слова пишеться як тріт, +0.6× на весь payload;
(2) **розділювач** — 1 тріт (1.6 біта) на слово. Префіксний код прибирає обидві:
ширина домену `n` кодується **префіксним тегом**, після якого йдуть рівно `n` бітів
payload — межі слів видно з самого бітстріму, розділювач не потрібен.

## 1. Коди — заміряно

- Слів усього: **628**, логічних біт: **1563** (середня ширина 2.489 біта).
- Розподіл ширин: `{1: 21, 2: 415, 3: 157, 4: 2, 7: 32, 9: 1}`
- Huffman-довжини тегів (біт на ширину): `{1: 4, 2: 1, 3: 2, 4: 5, 7: 3, 9: 5}`
- Середній тег: **1.471 біт/слово** · префіксність: **True** · round-trip: **True**

## 2. Варіанти — заміряно на 23 фікстурах

| варіант | біт | надлишок | точний домен? |
|---|--:|--:|:--:|
| поточний T5 (тріти + розділювач) | 3544 | 2.267× | так |
| фіксований 4-біт тег ширини + payload | 4075 | 2.607× | так |
| **Huffman-тег ширини + payload (B1)** | **2487** | **1.591×** | **так** |
| Huffman по повних словах (B2) | 2013 | 1.288× | ні (кодbook) |
| межа ентропії слова | 1985 | 1.270× | ні |

### 2.1 Per-fixture (поточний vs B1)

| фікстура | лог. біт | слів | T5 біт | B1 біт |
|---|--:|--:|--:|--:|
| `lib/surface/ukr-acceptance.sens` | 295 | 62 | 576 | 439 |
| `tests/fixtures/core1-domain-canary/second.sens` | 76 | 33 | 176 | 119 |
| `tests/fixtures/core1-fourth-domain-canary/fourth.sens` | 163 | 71 | 376 | 255 |
| `tests/fixtures/core1-third-domain-canary/third.sens` | 131 | 57 | 304 | 205 |
| `tests/fixtures/migration-atom-cohort/atom-empty.sens` | 12 | 5 | 32 | 19 |
| `tests/fixtures/migration-d1-cond-cohort/branch.sens` | 38 | 19 | 96 | 69 |
| `tests/fixtures/migration-d4-selector-cohort/caar.sens` | 68 | 29 | 160 | 109 |
| `tests/fixtures/migration-eq-cohort/eq-legacy-sid.sens` | 17 | 7 | 40 | 27 |
| `tests/fixtures/migration-eq-cohort/eq-lisp15.sens` | 17 | 7 | 40 | 27 |
| `tests/fixtures/migration-eq-cond-cohort/eq-cond-select.sens` | 113 | 53 | 264 | 189 |
| `tests/fixtures/migration-eq-cond-cohort/eq-cond-skip.sens` | 113 | 53 | 264 | 189 |
| `tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens` | 113 | 53 | 264 | 189 |
| `tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens` | 113 | 53 | 264 | 189 |
| `tests/fixtures/migration-multiform-cohort/two-forms.sens` | 49 | 21 | 112 | 77 |
| `tests/fixtures/migration-multiform-cohort-main/two-forms.sens` | 49 | 21 | 112 | 77 |
| `tests/fixtures/migration-pair-cohort/pair-car-cdr.sens` | 39 | 17 | 88 | 61 |
| `tests/fixtures/migration-pair-cohort/pair-cons.sens` | 35 | 15 | 80 | 55 |
| `tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens` | 39 | 17 | 88 | 61 |
| `tests/fixtures/migration-pair-cohort-main/pair-cons.sens` | 35 | 15 | 80 | 55 |
| `tests/fixtures/migration-quote-cohort/quote-legacy.sens` | 12 | 5 | 32 | 19 |
| `tests/fixtures/migration-quote-cohort/quote-lisp15.sens` | 12 | 5 | 32 | 19 |
| `tests/fixtures/migration-quote-cohort/quote-mylisp.sens` | 12 | 5 | 32 | 19 |
| `tests/fixtures/migration-quote-cohort-main/quote-legacy.sens` | 12 | 5 | 32 | 19 |

## 3. Головні знахідки

1. **Тег дешевший за розділювач.** Huffman-тег = **1.471 біт/слово** проти
   розділювача **1.600** — заміна не лише можлива, а й вигідна сама по собі, плюс
   знімає тріт-пакувальний податок. Разом: **2.267× → 1.591×** (−29.8% біт).
2. **Точний домен збережено.** B1 = тег ширини + *точний* payload-біт слова — це не
   «трансляція»: ідентичність домену лишається явною. Це відрізняє його від B2.
3. **Адаптивність критична.** Фіксований 4-біт тег дає 2.607× — **гірше** за
   поточне, бо ігнорує, що D2 домінує (415 з 628 слів). Отже тег мусить бути
   частотним (як token-threading у nibbleforth), а не фіксованим.
4. **Стеля.** Huffman по повних словах дає 1.288× — майже межа ентропії
   1.270× (H = 3.161 біт/слово). Це найкоротший можливий запис, але ціною
   кодової книги над словами (втрата принципу «ідентичність = код»).

## 4. Чесні межі

- 23 **малі** фікстури; розподіл D2-домінантний — на іншому корпусі тег зміниться.
- Код **корпус-адаптивний** (Huffman із цих фікстур), тож не універсальний;
  для стабільного формату потрібна фіксована (але частотно-зважена) канонічна таблиця.
- B2 і межа ентропії наведені як *орієнтир*, не як пропозиція — вони ламають
  принцип «точний домен = код».
- Жодних змін семантики, файлів репо, workflow чи гейтів не внесено.
