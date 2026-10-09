# D10 — 4 перевірені історичні значення: 625 → 629

**Дата:** 2026-10-09. **Стан:** 629/1024 selected research, 256 law-forced, **373 unplaced**, 395 remaining, **0 ratified**. D1–D9 unchanged. D2 continues exclusive control ownership. These selected research meanings are not executable T5 instructions until later law/coordinate/owner proof.

## Джерела та причина відбору

Чотири відокремлені **спостережувані закони** з [ANSI Common Lisp HyperSpec](https://www.lispworks.com/documentation/HyperSpec/Front/) та [R6RS Standard Libraries §13](https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-14.html). Дані й негативні свідки — у `knowledge/d10-historical-primary-selected-20261009.json`.

1. **`DPB` — вставити-бітове-поле / вст-біт-пл**. `(newbyte, size, position, original) → integer`: справа наліво беруться **нижні size бітів** з `newbyte`, розміщуються з позиції `position`. Усі біти `original` за межами поля зберігаються. Джерело: [CLHS DPB](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_dpb.html). Приклади з посібника: `dpb(1,1,10,0)=1024`, `dpb(-2,2,10,0)=2048`. Відрізняється від selected D10 `LDB` (читання поля), `MASK-FIELD` (виділення поля).
2. **`DEPOSIT-FIELD` — вписати-вирівняне-поле / впис-вир-пл**. На відміну від `DPB`, бере біти `newbyte` **з тих самих позицій**, що й цільове поле. [CLHS DEPOSIT-FIELD](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_deposit-field.html). Розрізнювальний тест: `newbyte=10, size=2, position=1, target=0`: `DPB=4`, `DEPOSIT-FIELD=2`. Це не синоніми.
3. **`ARRAY-DISPLACEMENT` — зміщення-подання-масиву / зм-под-мас**. [CLHS ARRAY-DISPLACEMENT](https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/fun_array-displacement.html). Два результати: **безпосередній масив-основа й зміщення**. `C` displaced-to `B`, `B` displaced-to `A`: запит `C` повертає `B`, а не сплощений `A`. Запис у `C` видно у `A`. Для звичайного не-зміщеного масиву обрана стандартна тестова модель повертає `NIL,0`, проте стандарт має implementation-dependent caveat щодо неявно створених displaced arrays. Не прирівнювати до `REARRAY` чи `ARRAYDIMS`, already D10.
4. **`HASHTABLE-ENTRIES` — пари-хеш-таблиці / пар-хеш**. [R6RS §13.3](https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-14.html) та [R6RS errata](https://r6rs.org/r6rs-errata.html). Два вектори однакової довжини з **відповідними парами за одним індексом**; порядок не визначений. Не змішувати з окремим отриманням ключів/значень та не обіцяти стабільний порядок. `GETHASH`, `MAKE-HASH-TABLE` уже є в D10, але мають іншу аргументно-результатну форму.

## Контроль

- `scripts/check_d10_historical_primary_selection.py --self-test` перевіряє взаємовідповідність donor і inventory, 625 старих + 4 нових резидентів, розмежування з ratified D1–D9, 256 незмінних примусово встановлених координат, інваріант `0 ratified`, 12 негативних metadata-мутацій.
- Бітові рівняння перевіряються **обмеженим повним перебором** (ширина 0..5, позиція 0..6, додатні та від'ємні цілі). Моделі aliasing і paired vector alignment перевіряються незалежними прикладами з фальсифікаторами. Це **не запуск SBCL/R6RS runtime** і не замінює donor-oracle тестування.
- Монотонність: D10 625 old-row stable IDs залишаються у префіксі, нові 4 — останніми. Metadata старих дослідних знімків зафіксовані історично; вони не мають бути переписані після нової selection.
- Ці 4 — **selected research candidates**, не owner-ratified machine identities. `coordinate: null`, `ratified_resident: false`, `proposal_status: pending-owner-ratification`. Немає дозволу на видачу `.sens` чи беззмістовні міграційні заглушки.

## Координація

Власник обліку: [#4013](https://github.com/juv4uk/sens/issues/4013). Правило нових функцій: [#4463](https://github.com/juv4uk/sens/issues/4463). Донори: [#4182](https://github.com/juv4uk/sens/issues/4182). Попередні source-first dossiers: [#4841](https://github.com/juv4uk/sens/pull/4841) і [#4839](https://github.com/juv4uk/sens/pull/4839).
