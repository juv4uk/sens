# Pramāṇa (प्रमाण) — D10 CLIPS EQUAL, фізичні SENS-свідки · 25.10.2026

## Спадкоємність і роль

Pramāṇa — доказ, відмінний від наміру й припущення. Дякую Nyāya
за попереднє SENS-виправлення D6 MIN-LIST/MAX-LIST і
Hetu за упорядкування CI.

У цьому ході семантика змінена **лише SENS** у `lib/core4.lisp`.
Rust/Zig/codec/opcode/координати не редагувалися.
Новий тестовий маршрут тільки використовує чинний Zig/T5M runner.

## Відтворена причина

Історичний CI `40146703790`, job `121029486408`,
падіння `core4_ukrainian_clips_shortcut_truth_tables_execute_in_sens`:

`test_id=CORE4-CLIPS-D1 layer=SENS input=(твердження-кліпс?
(як-є (assert а))) expected=D1:true actual_error=eq expects two atoms`

Ратифіковані D10 функції:

- `D10:0100100110` — `твердження-кліпс?`, CLIPS-ASSERT-FORM?.
- `D10:0100100111` — `виведення-кліпс?`, CLIPS-PRINTOUT-FORM?.

Обидві зберігають `атом?` для зовнішньої голови, але порівнюють
цитовані структурні значення лише чинним SENS `однакові?`,
а не вузьким атомним `тотожне?`, який фізично породжував
`eq expects two atoms`.

У SENS:
`((атом? (перше форма)) (однакові? (перше форма) (як-є assert)))`
та відповідна форма `printout`. Жодного нового D10 opcode,
формальної ратифікації чи зміни D3 EQ.

## Коміти, успішно відправлені до main

1. `ed3747a9a6075bbfe6858142832b97ec8332b759` —
   `lib/core4.lisp`, замінено рівно дві форми порівняння.
2. `b1664b7fd55bba2d0d79b3a1ab8454afa978a951` —
   `tests/semantic/d10-clips-equal-head-law.lisp`.
   Точний позитив D1:так для `assert`, `printout`;
   хибний вкладений `((assert) ...)` чи `((printout) ...)`
   має дати D1:ні. Невдале твердження спричиняє CAR NIL.
3. `4cd6efede2a193742b829bc9317ebcab0df4469d` —
   `tests/semantic/d10-clips-equal-head-mutant.lisp`.
   Очікування D1:ні: `printout` не є `assert`.
4. `a9fdf0b31c5f02fb11925d1cdaf19b22107dba90` —
   `scripts/prove-lisp-semantic-t5m.sh`:
   `d10-clips-equal-head-positive` та
   `d10-clips-equal-head-mutant` додані до `run_case run_law`,
   очікувані біти 1/0, з `core4`, SHA-квитанцією трьох джерел.

Перевірено з GitHub: поточний blob `lib/core4.lisp` зберігає
обидві зміни; runner зберігає обидва нові маршрути. Стан
`main` після четвертого коміту:
`a9fdf0b31c5f02fb11925d1cdaf19b22107dba90`.

## Чесний статус і незалежні RED

- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`.
- `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`.
- `PHYSICAL_CORE4=STALE_UNTIL_CANONICAL_REMINT`.
- `RELEASE=NO-GO`.

Нативний SENS не запускався окремо у цьому чаті: підключений
віддалений комп'ютер недоступний. GitHub CI для нового SHA
запущений, але ще не мав завершеного результату.
Ні статичний аналіз, ні GitHub commit не є SENS PASS.

Окремі причини, видимі у старому CI:

- D6 LENGTH-ONTO: очікуваний D3 CAR Type проти фактичного CDR Type.
- D6 MIN/MAX: нові `число?`-свідки, не переносити старі RED на новий SHA.
- Core4: `SENS_CORE4_PHYSICAL_DRIFT`, `lib/core4.sens` не відповідає джерелу.
- F6: producer→physical consumer pipeline assertion.
- `core4_named_numeric_values_are_exact_and_source_literal_free`:
  фактичне `(64 265/4 15625/1024)` проти очікуваного
  `(64 66 15)` на старому SHA; це окремий D12+ numerical issue.
- `core4_point_witness_crosses_predicates_strings_macros_and_fresh_symbols`:
  відсутня прив'язка `->` у старому CI; це не CLIPS проблема.
- Жодного старого червоного workflow не перезапускати без чіткої потреби.

## Точний наступний таргет Swarm

1. Зафіксувати SHA голови main й запускати нативні binary `sens`
   і `sens-trit` чинним
   `scripts/prove-lisp-semantic-t5m.sh` на одному SHA.
   Перевірити нові D10 позитив D1:1 і мутант D1:0 у direct,
   paired Zig/T5M, standalone. Додати stdout/stderr,
   source/physical SHA256, фактичні Type.
2. Зняти на реальному SENS 22 наявні закони
   `tests/semantic/d10-clips-derived-laws.lisp` для всіх
   чотирьох функцій CLIPS, без повторного визначення домену.
   Якщо `однакові?` не приймає носіїв — точна діагностика
   на фізичному слові й ремонт у SENS.
3. Remint `lib/core4.sens` та `lib/core4` лише штатним
   Zig/T5M, не правити фізичні байти вручну, не підміняти
   стендовими Python-тестами.
4. Після D10 CLIPS повертатися до D6 LENGTH-ONTO CAR/CDR,
   D6 NTH/MAPLIST та D5/D12 exact-number bug, зі своєю
   першопричиною для кожного RED.
5. D1 — істина, D2 — рамка, D3 — CAR/CDR/EQ/CONS,
   D4 — DEFINE/COND/LAMBDA, D5 — математика/порівняння,
   D6 — композиція, D7 — текст, D10 — ратифіковані 1024
   тотожності, D11 — похідні кандидати, D12+ — числа.
   Не плутати нативну доведеність із адресною ратифікацією.
6. RELEASE GO тільки за повним proof на candidate SHA та
   рішенням власника.

`SENS_SOURCE=lib/core4.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`RELEASE=NO-GO`


## Доповнення цього ходу: строга D3-термінація всього CLIPS сімейства

Нова незалежна першопричина: `усі-твердження-кліпс?` і
`прибрати-виведення-кліпс` завершували рекурсію на **будь-якому**
атомі через `(атом? форми)`. Це помилково ототожнювало D1:ні із
структурним кінцем D3:(), дозволяло `ALL-ASSERTS` повернути
`так` та `DROP-PRINTOUTS` повернути усічений список.

Нові коміти на `main`:

- `d05a02f06a7ae85f04cc7ebae0ffb1f07ab2f7c9`:
  обидва SENS DEFINE спочатку перевіряють `атом?`,
  а потім через `однакові?` **лише D3:()**.
  Інший атом викидає справжню SENS Type через
  `(перше форми)`, а не тихо повертає результат.
- `47b02478118058c304fa5c500530c06d295c8a38`:
  SENS негатив `tests/semantic/d10-clips-all-asserts-improper-tail-negative.lisp`.
- `bdadfc5a93aad28ec2866d155d8488b442fcbfa6`:
  SENS негатив `tests/semantic/d10-clips-drop-printouts-improper-tail-negative.lisp`.
- `566e377f9cd6cdf367ee912589ddd4cd77f42ecd`:
  два `run_error_rejection` додані до того самого фізичного
  Zig/T5M proof-runner з точним очікуванням `Type:
  car expects a non-empty list` та SHA-квитанцією.
- `cdc613e31199919b3729e36d5d1b85292f616bc5`:
  позитивний SENS-law доповнено для
  `усі-твердження-кліпс? (як-є ())`,
  двох правильних ASSERT і фільтра
  `((assert а) (printout б) (assert в))`.

Спеціально НЕ змінено семантику D3 `тотожне?`,
D8 `однакові?`, числові D12+ значення або Rust-виконавець.
Чинні коди D10:0100101000 та D10:0100101001 залишаються
власними ратифікованими адресами, не новими D11 кандидатами.

Для наступного агента: окремо перевірити **п'ять** фізичних
маршрутів нової групи: позитив D1:1, мутант D1:0,
ALL-ASSERTS improper D3 CAR Type,
DROP-PRINTOUTS improper D3 CAR Type, а також 22 наявні
`tests/semantic/d10-clips-derived-laws.lisp` (у цьому файлі
22 окремі топ-рівневі форми, тож не прирівнювати лише останнє
значення до перевірки всіх 22 без явного fail-closed контракту).

`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`PHYSICAL_CORE4=NEEDS_CANONICAL_REMINT`
`RELEASE=NO-GO`

---
Deutsch: D10 CLIPS-Köpfe werden jetzt in SENS strukturell
verglichen. Der native Zig/T5M-Nachweis steht noch aus.

English: D10 CLIPS heads now use SENS structural equality.
Native Zig/T5M evidence and physical Core4 parity are not yet certified.
