# Ṛta (ऋत) · D10 CLIPS цитовані голови, точні фізичні свідки · 25.10.2026

## Контекст

Аватар Ṛta — узгодженість між ратифікованим законом, викличною
проєкцією й фактичним виконанням. Дякую попередньому агенту
Pramāṇa за первинне відновлення D10 CLIPS і суворий D3-термінатор.
Його чекпоінт:
`docs/checkpoints/2026-10-25-pramana-d10-clips-equal-head.uk.md`.

Ролі доменів: D1 — точний біт істини; D2 — керування; D3 —
структура/CONS/CAR/CDR/EQ; D4 — предикатні форми/DEFINE;
D7 — текст; D8:11110111 `однакові?` — структурна рівність;
D10 — ратифіковані власником 1024/1024 тотожності;
D11 — каталог кандидатів/похідні функції; D12+ — числові
значення, не викличні функції лише через ширину.

## Новий реальний RED, діагностика

CI запуск `40147741071`, job `121032608773`, на
SHA `a9fdf0b31c5f02fb11925d1cdaf19b22107dba90`:

- `id=d10-clips-equal-head-positive`,
- `layer=sens-direct-type`,
- `expected=SENS-execution`,
- `actual=rejected`,
- `car expects a non-empty list`,
- `physical_form_index=0`, `physical_word_start=0`,
  `physical_word_end=205`.
- `d10-clips-equal-head-mutant` у тому ж запуску:
  `PASS result=0 native=SENS`, з етапами direct, codec-mint,
  zig-open, zig-verify, sens-paired, sens-standalone.
  Це тільки факт старого SHA, не PASS поточного source.

Складений позитив містить окремо ASSERT, PRINTOUT, вкладені
негативи та ALL-ASSERTS/DROP-PRINTOUTS. Без ізольованих свідків
цей RED **не дозволяє** стверджувати, на якій саме формі було
перше відхилення.

СЕНС-гіпотеза першопричини: `(атом? (перше форма))`
відхиляє цитовану зовнішню CLIPS-голову з D7/D2-носієм
перед D8 структурним порівнянням. Не плутати гіпотезу із
доведеним позитивом: новий CI ще не завершився.

## Коміти цього ходу, відправлені в main

1. `a9b4ccdcd724c3718aa454ce2ffb06e95a3882c9`:
   `lib/core4.lisp`, D10:0100100110
   `твердження-кліпс?` (san `clips-pratijñā-rūpa`)
   та D10:0100100111 `виведення-кліпс?`
   (san `clips-mudraṇa-rūpa`).
   Обидві SENS-функції зберігають перевірку атомності
   ЗОВНІШНЬОЇ форми, але не вимагають атомності
   ЦИТОВАНОЇ ГОЛОВИ: замість того застосовують наявний
   D8 `однакові?` до всієї голови та `(як-є assert)` або
   `(як-є printout)`. D3 `тотожне?` і Rust/Zig
   не змінювалися, нових координат немає.
2. `a55dac8c29a9c11a070c0df6cdda0d6f1a56faf2`:
   один мінімальний позитив
   `tests/semantic/d10-clips-assert-head-direct-law.lisp`;
   очікується D1:так.
3. `a96586e165c3206a7dea72df485d1b989a4d87c5`:
   окремий мінімальний позитив
   `tests/semantic/d10-clips-printout-head-direct-law.lisp`;
   очікується D1:так.
4. `68c8c55821f73ca842cd738ee75135b5ebe7b7cc`:
   `scripts/prove-lisp-semantic-t5m.sh`:
   `d10-clips-assert-head-direct-positive`,
   `d10-clips-printout-head-direct-positive`
   виконуються чинним `run_case run_law ... 1 core4`
   через native SENS/Zig/T5M. Джерела включено до
   `$evidence/d10-clips-equal-head-inputs.sha256`.
   Відмова не може бути прихована через старий один
   складений test-id. Не додавався Python/Rust оракул.

Узгоджені раніше:
`d10-clips-equal-head-positive`, `d10-clips-equal-head-mutant`,
`d10-clips-all-asserts-improper-tail`,
`d10-clips-drop-printouts-improper-tail`.
Усі лишаються в нативному маршруті й не перенесені на
фальшиві host asserts.

## Інші незакриті незалежні першопричини

За CI `40147741071`: `SENS_CORE4_PHYSICAL_DRIFT`;
F6 producer→physical consumer failure; а також
`d6-min-list-root-d1-type`,
`d6-min-list-late-poison-type`,
`d6-max-list-single-nonnumeric-type`,
`d6-nth-early-improper-tail`,
`d6-maplist-poison-d1-tail`,
`d6-length-onto-d1-root-type`,
`d6-length-onto-late-d1-tail-type`.
Зміни колег після цього запуску могли впливати на D6;
уточнювати поточний стан лише на свіжому SHA. Не
підміняти CAR Type на CDR Type заради зеленого CI.

## Наступний Swarm-таргет

P0. Знайти CI для `68c8c558...` або наступного main SHA,
відтворити обидва незалежні CLIPS-позитиви в реальних
SENS `sens` і `sens-trit` із Zig/T5M:
`bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens
target/debug/sens-trit /tmp/sens-rta-d10-clips`.
У квитанції фіксувати source SHA, physical SHA, direct,
paired, standalone та точний D1 біт. Якщо позитив знов
RED, шукати рівень D7 цитування/D8 EQUAL, а не переписувати
очікування тесту.

P0. Прогнати весь CLIPS набір: 4 позитивні/негативні
спеціалізовані свідки й 22 форми
`tests/semantic/d10-clips-derived-laws.lisp` з
окремим контролем кожного D1 вердикту.

P0. Привести `lib/core4.sens` і безрозширеневий бітовий
view у відповідність лише канонічним Zig/T5M remint
на **одному SHA**, без ручного написання фізичних байтів.

P1. Окремо завершити D6 NTH, MAPLIST і LENGTH-ONTO,
після цього D5/D12 числові невідповідності та D10 інші
функціональні резиденти. Для кожного — точна координата,
закон, механізм, SENS позитив/негатив, фізична квитанція.
D11 APPEND-MAP/FIND-TAIL-PRESENCE вже редагували інші
агенти: не дублювати їхні роботи.

P2. Рішення GO лише після перевірки candidate SHA
та дозволу власника; 1024 D10 ідентичності не означають
1024 незалежно підтверджені виконання.

`SENS_SOURCE=lib/core4.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`PHYSICAL_CORE4=NEEDS_CANONICAL_REMINT`
`RELEASE=NO-GO`

---
Deutsch: Die D10-CLIPS-Kopfprüfung verwendet jetzt direkt die
strukturelle SENS-Gleichheit; unabhängige native Beweise fehlen noch.

English: D10 CLIPS quoted heads now use SENS structural equality
without a premature atom-only gate. Independent native execution
and Core4 transport parity remain unverified.
