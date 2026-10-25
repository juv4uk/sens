# Pratyakṣa (प्रत्यक्ष) — Д6 UNION: відновлення витягу визначень і суворого SENS-закону

Дата: 25.10.2026. Принцип: «SENS-джерело ≠ зібрана фізична пара ≠ нативний PASS».
Аватар: Pratyakṣa — безпосередній доказ. Дякую Anvaya за D11 LIST-TABULATE,
Viveka за D10 MAP, Satya за D9 та Ṛta за CLIPS.

## Вихідний стан та відтворена першопричина

На початку ходу main: `27e097555ab1ae5db1cdb5f796352daed1342531`.
Останній завершений CI для нього:
`https://github.com/juv4uk/sens/actions/runs/40163889233`,
job `121080887951` — **FAILURE** (Rust механізм та SENS закони).

Нативний proof-runner фактично зупинився на:
`D6_UNION_DEFINITION_NOT_ISOLATABLE function=значення-у-списку? source=lib/core4-parts/core4-language.lisp`.

Не йшлося про відсутність функції SENS або неможливість об'єднання
списків: `значення-у-списку?` існувала в
`lib/core4-parts/core4-d6.lisp`,
а `об'єднання-перевірити-правий` і `об'єднання` —
в `lib/core4-parts/core4-d6b.lisp`.
Proof-runner містив застарілі шляхи `core4-language` та `core4-codec`
після фізичного поділу Core4. Це **помилка маршруту доказу**
і її не можна «виправляти» підставним визначенням у Rust/Python.

Крім того, `tests/semantic/d6-union-proper-law.lisp` мав
**три top-level форми**, з яких остання —
`(атом? (як-є ()))` — завжди істинна.
Тому навіть виконаний нативний SENS міг видати
підсумковий D1:так без доказу попередніх двох умов,
якщо перевірка враховувала лише останню форму.
Це класична прогалина «хибнозеленого» свідка.

## Завершені коміти та push у main

1. `09a44922edc0f90f8869e87285e43d3a401f17f0`
   змінює **тільки механічні шляхи** у
   `scripts/prove-lisp-semantic-t5m.sh`:
   - `значення-у-списку?` ← `core4-d6.lisp` (D5 MEMBER);
   - `об'єднання-перевірити-правий` ← `core4-d6b.lisp`;
   - `об'єднання` ← `core4-d6b.lisp`.
   Збережено чинну fail-closed AWK перевірку рівно одного
   канонічного визначення та відокремлення порожнім рядком.
   Повторно прочитано всі три файли з GitHub й статично звірено:
   у кожному визначення знайдено **рівно один раз**,
   завершено порожнім рядком, баланс дужок **0**.
   Збережено всі чинні позитиви/мутанти/Type-свідки
   реального `SENS → Zig/T5M → SENS`.
   Не додано workflow, псевдосемантики чи другого джерела істини.

2. `3348b1fc9816639b2f1645cd68007e801b75de07`
   змінює тільки мовний
   `tests/semantic/d6-union-proper-law.lisp`:
   тепер **єдиний** вкладений SENS `за-умовою`
   перевіряє чотири істинні законні випадки:
   - UNION `(так ні)` з `(ні)` → `(так ні)`;
   - UNION `()` з `(ні)` → `(ні)`;
   - UNION `(())` з `(ні)` → `(() ні)`;
   - UNION `()` з `()` → `()`.
   Відмова будь-якого закону веде до точного D1:ні;
   остання тривіальна топ-рівнева форма видалена.
   Перевірено статичний баланс форми: 0.
   Не змінено сам чинний алгоритм UNION у SENS:
   після відновлення маршруту саме native proof має
   визначити, чи потребує алгоритм семантичного ремонту.

На момент перевірки CI
`40165662909` для `09a44922` — in_progress,
`40165827026` для `3348b1` — in_progress.
Ніякого `NATIVE_PASS` на цих SHA ще не отримано.

## Друга незалежна фактична регресія: F6

Старий, але останній завершений `40163889233`
також містить:
`producer_records_are_reconstructed_by_the_physical_f6_consumer ... FAILED`.
Фізичний SENS повернув:
`root reconstruction rejected: verdict=0 detail=((1110010 ... 1100100) (1101001 ... 1110100))`.
Ці клітинки D7 розкладаються у
`rejected` та `invalid-format`.
Отже, фактичний перший семантичний блокер
після декодування кореневої оболонки — **поле format**.

Наступний агент має ізолювати SENS-закон:
`(однакові? (фс-пакет-поле (як-є format) (прочитати (значення-у-текст (фс-корінь-пакет (фс-порожній))))) (як-є wsm-fs-root))`
і окремий контроль без READ; перевіряти реальні D3/D7 типи
поля та точне roundtrip, не припускати, що типи після
серіалізації тотожні. За потреби — мовна нормалізація
в SENS, не host переінтерпретація структур чи
відключення `invalid-format` валідації.
Обов'язкові negative malformed records залишаються.

## Граф залежностей і область D1–D12+

D1 — вердикт, D2 — керування, D3 — структурне `()`,
CAR/CDR/CONS, D4 — композиція і EQUAL у SENS,
D5 MEMBER є необхідним для D6 UNION,
D6 UNION перевіряє всю правильність правої основи.
D7 — кодові клітинки, D8 — структурна рівність і READ,
D9 — FS envelope, D10 — ратифіковані 1024 адреси,
не 1024 незалежно атестовані функції.
D11 — каталог кандидатів із окремими реалізаціями;
D12+ — математичні операнди, не приховані літерали.
Роль Zig — транспорт кодів/байтів, Rust — I/O.
D7 не повинен дублювати точний канонічний доменний код.

## Точний наступний таргет

P0. На одному свіжому candidate SHA виконати D6 UNION:
`d6-union-proper` очікує D1:так;
`d6-union-proper-mutant` D1:ні;
`d6-union-improper-tail`, `d6-union-improper-root`,
`d6-union-right-root`, `d6-union-right-tail` і
`d6-union-right-hidden-tail` — **точні Type-відмови**.
Зібрати direct SENS, Zig/T5M mint/open/verify,
paired, standalone SENS і SHA receipts.
Якщо новий доказ падає — виправити SENS-закон/функцію
за фактичним трасуванням, не змінювати очікування.

P0. F6: розрізнити `invalid-format` на транспортному
D8 READ і на безпосередньому SENS-пакеті.
Перевірити `фс-пакет-поле`, `фс-корінь-пакет`,
`рішення-щодо-кореневого-пакета-файлової-системи`
та exact `accepted` маркер на тому ж SHA.
Строгий негативний захист не видаляти.

P0. Перевірити Core4 physical pair на exact SHA
(між старими джерелом і фізикою дрейф можливий).
Не remint вручну, тільки чинним канонічним Zig/T5M.

P1. Інші відкриті D11 LIST=, LIST-TABULATE,
D10 MAP, D9 STRING-APPEND перевіряти на спільному SHA.
Тільки тоді переходити до наступної конкретної
неозначеної D11 функції; не плодити заглушки.
Рішення про GO — тільки власник.

`SENS_SOURCE=tests/semantic/d6-union-proper-law.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`F6_NATIVE=RED_ON_HISTORICAL_SHA`
`RELEASE=NO-GO`

---
Deutsch: D6 UNION findet wieder seine kanonischen SENS-Definitionen;
der positive Beweis ist jetzt fail-closed. Native Ergebnisse stehen aus.

English: D6 UNION source isolation paths now match real canonical files;
the native positive witness no longer ends in a trivially true expression.
CI certification remains pending.

## Додатковий ремонт після нативного сигналу ownership guard

У CI `40165827026` (SHA `3348b1fc9816639b2f1645cd68007e801b75de07`)
ранній крок `Власність тестів — Rust охоронець фізичних Lisp-законів`
одержав статус FAILURE. Конкретна текстова причина не була
доступна з незавершеного log на момент аудиту, проте статичний
аналіз `scripts/guard-native-test-ownership.rs` встановив
реальну прогалину маршрутизації: `routed()` перевіряє **буквальні**
шляхи `tests/semantic/*.lisp`, що потрапляють до `cat`
з точним іменованим bundle, який згодом використовує `run_case`.
Старий динамічний рядок `d6-union-$kind.lisp` не містив
буквального повного SOURCE та не міг пройти таку перевірку
для зміненого позитивного SENS файла.

Додатковий коміт
`85ff1ddcc77189cb72e8415a9accb97c17cf4282`
у `scripts/prove-lisp-semantic-t5m.sh`:
- `tests/semantic/d6-union-proper-law.lisp` →
  `$d6_union_proper_source` → `run_case run_law d6-union-proper`;
- `tests/semantic/d6-union-proper-mutant.lisp` →
  `$d6_union_mutant_source` → `run_case run_law d6-union-proper-mutant`.

Той самий канонічний `$d6_union_source` з трьох існуючих
SENS DEFINE, без нової semantics у скрипті. Негативні
`improper-tail` і `improper-root` не змінювались,
їхній фізичний маршрут зберігся.
Головний принцип: не «лікувати» червоний власний guard
його відключенням; уточнити маршрут справжнього тесту.

`NATIVE_LAW_OWNERSHIP=SOURCE_ROUTE_REPAIRED_NOT_YET_VERIFIED`.
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`.
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`.
