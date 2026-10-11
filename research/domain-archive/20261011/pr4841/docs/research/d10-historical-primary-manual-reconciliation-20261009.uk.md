# D10: повторне дослідження старих незлитих гілок історичних Lisp

Дата: **2026-10-09**. **RESEARCH/HOLD**, жодного нового обраного D10, жодної координати й жодної ратифікації. Канонічний стан: `D1–D9` ратифіковано, `D10 625/1024 selected, 0 ratified`.

## Перевірені гілки і перетини
- `research/2344-historical-ledger` (19 записів, 17 збігаються за точним ім'ям із поточними D1–D9). `FUNARG` — історичне представлення замикання, але `FUNCTION` уже D5, а `LAMBDA` — D4. `TRANSFORMER` — інша поверхня поточного **D8 TRANSFORMER/HART-MACRO**, порівняти за трьома осями (raw form, caller environment, result re-expansion), не додавати за самою назвою.
- `research/2258-function-funarg-historical`: зберегти історичну перевірку; вона не є автоматично новою семантикою.
- `research/2678-historical-unplaced-handoff`, `research/2718-d1-d6-historical-gap-audit`: тодішні UNKNOWN/незатверджені межі були правильними для **старого** контракту; нинішні D5–D9 мають нову ратифікацію. Не переносити давні координати.
- `feat/d8-historical-full-occupancy`: 192 історичні non-selector names; 181 вже є за назвою в D1–D9, 5 у вибраному D10, шість не представлені за точними іменами. Проте ця *лексична* перевірка не є доказом семантичної незалежності.
- `research/d9-overflow-review-v1`: шість спірних імен — `THE`, `GENERATE-EXPANSION`, `BACKQUANTIZE`, `COUNT-LEADING-ZEROS`, `TABLESPACE`, `COLLECTION`. Повторний source-check не знайшов підстав для їхньої негайної ратифікації.

**Важливо:** `SASSOC`, `SASSQ`, `REARRAY`, `MAKE-ARRAY`, `ARRAYDIMS`, `REF-CELL`, `DEREF`, `LDB`, `MASK-FIELD` уже є в D10 selected, хоча D10 ще НЕ ратифіковано. Вони не є дублями D1–D9; їх не можна ні безпідставно викреслити з історії, ні повторно включити до лічильника.

## Першоджерела, перечитані в мережі
- [LISP 1.5 Programmer's Manual, 1962 / Software Preservation](https://softwarepreservation.computerhistory.org/LISP/lisp15_family.html).
- [MacLisp Reference Manual, 17 Dec 1975](https://softwarepreservation.computerhistory.org/LISP/MIT/MACLISP_Reference_Manual-Dec_17_1975.pdf): друковані стор. **2-27** і **2-28** (`SASSOC`, `SASSQ`, `MAKNUM`, `MUNKAM`), **2-89** (`*REARRAY`, `STORE`). `SASSOC`/`SASSQ` уже D10; `*REARRAY` не відрізняти штучно від наявного D10 `REARRAY`.
- [MIT Lisp Machine Manual (ZetaLisp)](https://tumbleweed.nu/r/lm-3/uv/chinual.html), §§3.2.2 (`LOCF`), 7.9 (`DPB`), 13 (locatives).
- [ANSI CL `ARRAY-DISPLACEMENT`](https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/fun_array-displacement.html).
- [ANSI CL `ADJUST-ARRAY`](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_adjust-array.html).
- [ANSI CL `THE`](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/speope_the.html).
- [ANSI CL `MULTIPLE-VALUE-PROG1`](https://metaspec.dev/s_multiple-value-prog1.html).

**Покриття ручних веб-перевірок не є вичерпним індексним скануванням усіх цих посібників.**

## Пропозиції на розгляд для D10

### P0 — реальні поведінкові гіпотези
1. **`ARRAY-DISPLACEMENT`: подання масиву з aliasing + зміщенням.** Порівнювати зі звичайним копіюванням: зміна відображення повинна змінити вихідний масив. Визначити, чи існуючі `MAKE-ARRAY` та `REARRAY` уже мають саме цей закон (не припускати ані yes, ані no). Два вихідні значення: масив-основа та зміщення.
2. **`DPB`: запис визначеного бітового поля.** На відміну від вже вибраних `LDB` (читання) і `MASK-FIELD` (виділення), результат має зберігати всі зовнішні біти `x`. Порівняти з композицією наявних зсувів і логічних операцій. Якщо доводиться як проєкція — не додавати резидента.

### P0/P1 — важлива відмінність, але сильне перекриття
3. **`ADJUST-ARRAY`** має додаткові закони: змінна/незмінна ідентичність під час adjustment, alias chain і `:displaced-to`. Уже є `REARRAY`: спершу перевірити, які саме випадки воно покриває.
4. **`LOCF`**: локатив до **вже існуючого** місця зберігання — не те саме, що алокація `REF-CELL`. Важливо для Lisp-машини, але голі адреси / строки життя / alias-safety можуть належати машинному острову. Форма керування — D2.
5. **`MULTIPLE-VALUE-PROG1`**: зберігає всі значення `first-form` та виконує решту ефектів. D8 `PROG1` зберігає лише первинне значення. Але evaluation/control — **виключно D2**.
6. **`THE`**: *декларація*, а не обов'язкова runtime-перевірка. Число вихідних значень не змінює. Розмежувати D10 `CHECK-TYPE` і `TYPEP`, передати D2 compiler-form review.

### P2 — семантика залежить від представлення
7–8. **`MAKNUM` / `MUNKAM`**: живе identity↔number відображення. Першоджерело MacLisp 2-28 уточнює, що на PDP-10 це адреса, а на Multics — хеш-таблиця. **Не трактувати як стабільний serialized object ID; ніколи не дозволяти підроблений integer як довільний pointer**.
9. **`COUNT-LEADING-ZEROS`**: лише для явно заданої ширини W. Уже D8 `INTEGER-LENGTH`: позитивні цілі дозволяють формулу `W - integer-length(x)`, з `CLZ(0,W)=W`. Без нового спостереження не вводити ще один Core resident.

### P3 — свідомо НЕ підтверджено джерелами
10–13. **`TABLESPACE`, `GENERATE-EXPANSION`, `BACKQUANTIZE`, `COLLECTION`** з давнього overflow ledger. Для кожної назви бракує конкретної первинної сторінки або достатньо визначеного семантичного контракту. Відсутність у retrieved manual — НЕ доказ, що такої функції не існувало. Не підміняти неперевірений пункт вигаданою операцією.

## Перевірка
`knowledge/d10-historical-primary-manual-reconciliation-20261009.json` має 13 поіменних пропозицій: джерело, власника, статус, positive witness, falsifier, наявні семантичні сусіди, **`coordinate: null`**, **`selected_d10: false`**, **`ratified: false`**.

`python3 scripts/check_d10_historical_primary_reconcile.py --self-test` звіряє pinned реєстри D1–D9/D10, історичну гілку й стару D9 overflow-шістку, відхиляє помилкову промоцію. Цей checker не замінює незалежного Lisp oracle.

**Наступний крок:** спершу `ARRAY-DISPLACEMENT` і `DPB`; далі оракульна диференціальна перевірка `ADJUST-ARRAY` та `LOCF`. Будь-який SELECT тільки через #4463 / #4013 та затвердження власника.
