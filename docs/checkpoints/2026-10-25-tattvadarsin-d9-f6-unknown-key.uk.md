# Tattvadarśin · 25.10.2026 · D9/F6 canonical-key — checkpoint

## Архітектурний контекст
Аватар Tattvadarśin («той, хто бачить першопричину»).
Дякую Dharmaparīkṣaka за цілісний D11 LIST-TERMINATOR
(коміти `733976ac22c3`, `411f6db6b2f0`).
SENS — власник усіх функцій/даних; Zig/T5M не визначає предикат,
Rust лишається механізмом і I/O.

## Підтверджене CI
Перед виправленням HEAD був `06b762488cf50f9c5a6d075ed5a2fa4b9b4d6ccf`.
Запуск `40167865589` завершився RED:
`SENS_LAW_BENCHMARK_SUMMARY measured=529 failed=1`,
`REGRESSION checked=529 passed=528 failed=1
ids=d9-f6-package-key-canonicalization-positive`.
Окремий Rust/F6 інтеграційний тест досі RED:
`producer_records_are_reconstructed_by_the_physical_f6_consumer`,
`root reconstruction rejected: verdict=0 detail=(rejected invalid-format)`
(у машинній проєкції — точні доменні слова).
Це ДВА незалежні блокери, а не один.

## Доведена логічна суперечність у свідку
В `tests/semantic/d9-f6-package-key-canonicalization-law.lisp`
старий свідок припускав, що
`(як-є sens-unknown-key)` і
`(текст-у-символ "sens-unknown-key")` обов'язково мають бути
нерівні. Але правило протоколу гарантує ЛИШЕ те, що невідома
назва не стає новим псевдонімом жодного з десяти фіксованих
ключів. Воно не вимагає розрізнення двох тотожних за змістом
значень, якщо їх SENS-домен вже допускає порівняння.

Коміт `49bde2bb668edf2d2b9e3b9b351a30bde47bd678`
замінює некоректну вимогу на три SENS-інваріанти:
1. `фс-канонічний-ключ` лишає незмінним D7-невідомий ключ;
2. окремо лишає незмінним D8-невідомий ключ;
3. різні невідомі назви не стають еквівалентними.
Перевірку `format ≠ sens-unknown-key` і всі десять позитивів,
дублі, відсутнє/порожнє поле, malformed записи НЕ прибрано.
Виправлення стосується SENS-тестового закону, не host oracle.
Статична перевірка підтвердила одну збалансовану програмну форму.

## Межа верифікації
GitHub підтвердив commit/push: `49bde2bb...`.
CI цього SHA: https://github.com/juv4uk/sens/actions/runs/40170144153 .
На момент checkpoint — IN_PROGRESS; новий нативний PASS не заявляти.
Попередні 528/529 — ДО зміни; покращення НЕ доведене до PASS.
D1–D12+ FULL RELEASE=NO-GO. Жодного нового D11/D9 opcode.

## Наступний Swarm-агент
1. Перевірити `40170144153` на точному SHA: `d9-f6-package-key-canonicalization-positive`
   і `...-mutant`, фізичний T5M direct, mint/open/verify,
   paired, standalone; якщо RED — виділити точний SENS-предикат,
   його вхід і очікуваний/фактичний D1, не маскувати FAIL.
2. Незалежно виконати F6 root format WRITE/READ: чому
   `рішення-щодо-кореневого-пакета-файлової-системи` повертає
   `(rejected invalid-format)` після D8 READ?
   Порівняти D7/D8 значення `wsm-fs-root` через SENS,
   не текстове порівняння Rust.
3. Якщо physical `lib/lisp-fs.sens` чи
   `tests/fixtures/wsm-fs-record-producer.sens` застарілі,
   remint лише чинним SENS/Zig/T5M інструментом,
   зі source/physical SHA256 та негативними fixtures.
4. Далі підтвердити D6:000110/000111 macro environment,
   D6:101000 MAP, D10 CLIPS і невиконані D11/D12+.
   DEFINE та ратифікована адреса самі по собі не PASS.
5. Не вводити нових сирих бітових літералів, SID8 або
   довгоживучих гілок. GO лише після рішень власника.
