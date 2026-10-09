# D10 — історичні закони бітових полів та хеш-таблиць (636 → 638)

Статус **SELECTED RESEARCH, 0 ratified, 0 нових координат**. Відновлено після змін інших агентів у `main`. Не повторює `DPB`, `ARRAY-DISPLACEMENT`, CLOS, Gray, Bayes чи GF(2).

- **DEPOSIT-FIELD** / `вписати-вирівняне-поле`: [ANSI CL HyperSpec](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_deposit-field.html). На відміну від `DPB`, бере біти нового числа вже вирівняні до відповідних позицій; випадок `10, width=2, position=1, target=0` дає 2 (для DPB 4).
- **HASHTABLE-ENTRIES** / `пари-хеш-таблиці`: [R6RS Standard Libraries §13](https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-14.html). Два вектори відповідних ключів/значень, однакової довжини; порядок не визначений.

Монотонна перевірка: **636 старих рядків відтворюються byte-for-byte**, SHA звірений з попереднім Git blob `292ef3086114ad0dfe71776c831c2a31b39352a8`. Реєстр 638/1024, unplaced=382, remaining=386, force-coordinates=256, ratified=0. Попередні переходи 625→627→630→...→636 залишаються непорушними. Контракт і 10 негативних випадків — `scripts/check_d10_historical_second_tranche.py --self-test`.

Незалежний R6RS/Common Lisp oracle — [#4872](https://github.com/juv4uk/sens/issues/4872); bounded reference Python — не живий інтерпретатор. Координація: [#4013](https://github.com/juv4uk/sens/issues/4013), [#4463](https://github.com/juv4uk/sens/issues/4463). Ратифікацію й T5 не чіпати.
