# D10 — R6RS (2007): хеш-таблиці та гігієнічні ідентифікатори

**Стан: дослідження, без ратифікації, без координат і без додавання до 625 selected D10.**

## Джерела
- [R6RS Standard Libraries, §13 Hashtables](https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-14.html) — пункти 13.1–13.4.
- [R6RS Standard Libraries, §12 Syntax-case](https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-13.html) — пункти 12.3, 12.5, 12.6.
- Поточна нормативна основа: `knowledge/d1-d9-foundation.json` (Git blob `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`).
- Поточний D10: `knowledge/d10-v1-semantic-inventory.json` (Git blob `73dd518469f972c55411e004b70b054ba8b3ec86`).

## Підсумок
**19 історичних написань, відсутніх як точні імена в D1–D9 та в 625 вибраних D10** на зафіксованому стані. Це **0 нових вибраних D10**, 0 ратифікованих і 0 виданих двійкових кодів. Перевірено також відсутність перетину цих написань із 15 кандидатами PR #4837 та 11 кандидатами PR #4838. Відсутність назви **не доводить відсутність семантики**.

Секція 13: `MAKE-EQ-HASHTABLE`, `MAKE-EQV-HASHTABLE`, `MAKE-HASHTABLE`, `HASHTABLE-REF`, `HASHTABLE-UPDATE!`, `HASHTABLE-COPY`, `HASHTABLE-KEYS`, `HASHTABLE-ENTRIES`, `HASHTABLE-HASH-FUNCTION`, `HASHTABLE-EQUIVALENCE-FUNCTION`, `HASHTABLE-MUTABLE?`, `EQUAL-HASH`, `STRING-CI-HASH`.

Секція 12: `IDENTIFIER?`, `BOUND-IDENTIFIER=?`, `FREE-IDENTIFIER=?`, `SYNTAX->DATUM`, `DATUM->SYNTAX`, `MAKE-VARIABLE-TRANSFORMER`. **Будь-яке керування синтаксисом належить D2**, а не автономним командам D10.

## Найцінніші експерименти
1. `HASHTABLE-ENTRIES`: одне викликання повертає два узгоджені вектори як **два значення**; перевірити композицію із D8 VALUES та дослідним D10 CALL-WITH-VALUES.
2. `HASHTABLE-COPY`: копія за замовчуванням **незмінна**, але оригінал може бути змінний. Перевірити, чи вже існує цей стан у D9 MAP + D10 MAKE-HASH-TABLE.
3. `EQUAL-HASH`: для циклічної структури обчислення зобов'язане завершитися. Сам механізм обходу графа не дає права на окремий Core resident.
4. `BOUND-IDENTIFIER=?` і `FREE-IDENTIFIER=?`: побудувати два свідки з однаковим текстом, але різним лексичним контекстом; просте D3 EQ і D4 BIND не слід заздалегідь визнавати еквівалентними або недостатніми.

Повний поіменний `positive_witness_spec` / `falsifier_spec` і підозрювані вже наявні семантичні сусіди містяться в `knowledge/d10-r6rs-hashtable-hygiene-audit-v1.json`.

## Правило переходу до Core
`exact_name_absent` → **історичний предмет дослідження**, а не затверджений резидент. Далі потрібні: незалежне виконання тестів на R6RS-реалізації, зіставлення спостереження з D1–D9 і поточними D10, доведення нерозкладності або позначення projection/HOLD, ownership review у #4463 і власникове рішення. Не підміняти D2 керування, не створювати `.sens`, не змінювати ширини/координати.

Гейт: `python3 scripts/check_d10_r6rs_history_audit.py --self-test`. Якщо нормативні реєстри змінилися після pinned snapshot, гейт навмисно зупиняється для повторного зіставлення.
