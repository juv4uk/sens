# Viveka (विवेक) — D10 MAP: дванадцять законів, один точний D1 вердикт

Дата: 25.10.2026. Роль: відокремлювати виконуваний закон від
наявності запису у доменній таблиці та від недоведеного CI PASS.

## Спадкоємність, відомі підтвердження

Дякую Satya за D9:110011110 STRING-APPEND позитив/мутант,
а Ṛta і Pramāṇa — за D10 CLIPS. З аудиту останнього завершеного
CI `40158590271` (SHA `7f8dbf863edaf12714234f55dfbd663cb1b77b5d`)
зафіксовано 500 перевірок, 497 PASS, 3 RED із сімейства
D11 LIST=. Це ІСТОРИЧНИЙ CI, не доказ стану нового main.
Інші незалежні RED: host-debt0, F6 reconstruction.
Після цього колеги вже працювали над D11 LIST= (включно
з комітом `ffa2458ba467d9233fa025a3ab6c24bdbdae82c3`)
і F6 marker (`938a7b2593c69935b3b4558fcd0274a97c07bee1`).
Не дублювати ці коміти й не переносити старий RED на новий SHA.

Успіх `remint-drifted-pairs` `40157394553` має SHA
`02894a101cfc591fa1e10e14199f446a3ca28ed1`, тобто
не засвідчує поточну фізичну пару Core4.

## Конкретна причина й виправлення

До цього ходу
`tests/semantic/d10-map-derived-native-laws.lisp`
містив 12 **незалежних top-level предикатів**.
Якщо підсумковий oracle перевіряє лише фінальний
результат, перші одинадцять могли повернути D1:ні,
не відхиливши сукупний позитив. Це прогалина
доказу, а не новий opcode і не підтверджена
помилка реалізації функцій MAP.

У тесті було також голе `1`:
`(однакові? (довжина ...) 1)`, що суперечить
закону іменованих математичних D12+ значень.
Замінено саме на `число-один` SENS.

Доменні адреси **вже ратифіковані**, не вигадувати нові:
- D10:0011111100 `відобразити-ключі` — MAP-KEYS;
- D10:0011111110 `відобразити-значення` — MAP-VALUES;
- D10:0100001001 `відобразити-вилучити-з-мапи` — MAP-DISSOC;
- D10:0100001101 `відобразити-з-пари` — MAP-FROM-PAIRS.

## Реальні коміти, відправлені до main

1. `e548decd11c73c42e1f1a15ed9e94737d03abaf0`:
`tests/semantic/d10-map-derived-native-laws.lisp` перетворений
із 12 незалежних завершених форм на рівно **12 вкладених
`за-умовою`**. Кожна перевірка мусить повернути D1:так
перед переходом до наступної; інакше негайно D1:ні.
Фінальний результат має бути D1:так лише якщо усі 12
істинні. Синтаксичний баланс дужок перевірено,
нативний SENS не запускався локально.

2. `8ec84be6066f96a8db127c9deebbe5151824d006`:
`tests/semantic/d10-map-derived-native-mutant.lisp`:
порожня D9-мапа НЕ повинна містити `а`.
Очікування D1:ні, жодної хостової перевірки.

3. `9b4a4dc7e6f03061acd64c340cb16cb27a47ddc7`:
реєстрація двох маршрутів у чинному
`scripts/prove-lisp-semantic-t5m.sh`:
`d10-map-derived-twelve-positive` → 1 core4,
`d10-map-derived-empty-mutant` → 0 core4,
обидва з SHA256 джерелами.
Транспорт: direct SENS → Zig/T5M → paired SENS →
standalone SENS; власна семантика — лише SENS.

Повторним `fetch_file` перевірено:
- рівно 12 `за-умовою`, немає ` 1)`, є `число-один`;
- обидві реєстрації реально присутні у runner;
- відповідний run `40160350429` на SHA `9b4a4dc7...`
ще виконувався на момент перевірки.

## Розділення статусів

`SENS_SOURCE=tests/semantic/d10-map-derived-native-laws.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`D10_MAP_EXECUTABLE_SET=DEFINED_BUT_NOT_CERTIFIED_ON_THIS_SHA`
`CORE4_PHYSICAL_PARITY=NOT_VERIFIED_ON_LATEST_SHA`
`RELEASE=NO-GO`

Кількість тотожностей D10: 1024/1024 — це ратифікація
АДРЕС, а не доказ 1024 робочих викличних функцій. D11
каталог кандидатів також не є нативним реєстром PASS.
D1–D12+ залишається широкою незавершеною програмою.
Не створювати бутафорські DEFINE чи фальшиві PASS.

## Технічне завдання наступному агенту

P0. Взяти **один точний main/candidate SHA**; дочекатися
готового `run_case` для D10 MAP 12-true і 1-false
та отримати окремо direct, Zig-open/verify, paired, standalone
stdout/stderr, фактичні D1 біти, source та physical SHA256.
Якщо падає агрегований позитив — локалізувати номер першого
з 12 хибних підзаконів у реальному SENS, не прибирати
підзакон і не міняти очікування на 0.
Окремо перевірити на цьому ж SHA Type-свідок
`tests/semantic/d10-map-from-pairs-invalid.lisp`.

P0. Д11 LIST=: перевірити поточний стан закону,
а не повторювати `fd2e6005`, `ffa2458b`.
Відокремити правильні списки (D1) від неправильних
хвостів (D3 Type). Негативні Type мають залишатися RED
при непередбаченому успіху.

P0. D6 LET/LET*: ізолювати `D3:110 COND requires exactly
(test expression)`, дослідити результат SENS-макророзгортання,
а не додавати compatibility AST у Rust.

P0. F6: подальший діагноз після `root reconstruction rejected: 0`
і нового коміту `938a7b25`. Ніякого host fallback
для мап/пакетів. Remint F6/Core4 лише канонічним Zig/T5M
на цьому ж SHA.

P1. Продемонструвати F6, D9, D10, D11 з повними physical
квитанціями; виправити незалежні host-debt0 RED та Core4
drift без зняття охоронців. Тільки власник приймає
рішення GO на зафіксованому candidate SHA.

---
Deutsch: Zwölf D10-MAP-Prädikate bilden jetzt einen einzigen
fail-closed SENS-D1-Beweis. Native Ergebnisse sind noch offen.

English: Twelve D10 MAP checks now produce one fail-closed SENS
D1 verdict. Native Zig/T5M certification remains pending.
