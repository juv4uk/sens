# D10 — CLOS: прихована прогалина життєвого циклу слотів (2026-10-09)

Джерело: ANSI Common Lisp HyperSpec 1994; історичні імена тут є лише дослідницькими мітками. Цей PR **НЕ ратифікує** D10 і не додає виконуваних ідентичностей.

## Чому не вистачає лише SLOT-VALUE

Для об'єкта можливі три незалежно спостережувані стани: **немає слота**, **слот існує, але незв'язаний**, **слот існує, містить дані ()**. Відповідь D1 YES/NO не замінює NIL як значення.

## Вісім запитань на розгляд

1. **SLOT-EXISTS-P** — існує-комірка?: Return D1 yes iff object has a slot of this exact name, regardless of whether its value is unbound. **REVIEW-SEMANTIC-CANDIDATE**. [Нормативний опис](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-exists-p.html).
2. **SLOT-BOUNDP** — має-значення-комірка?: Return D1 yes iff named existing slot has a bound value, including an explicit NIL value; unbound is distinct from nonexistence. **REVIEW-SEMANTIC-CANDIDATE**. [Нормативний опис](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-boundp.html).
3. **SLOT-MAKUNBOUND** — розв'язати-комірку: Reset an existing instance slot to an unbound state without deleting the slot, changing class or clearing unrelated slots. **REVIEW-SEMANTIC-CANDIDATE**. [Нормативний опис](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-makunbound.html).
4. **SLOT-MISSING** — обробити-відсутню-комірку: When an accessor targets a slot absent from a standard-class object, dispatch to the operation-aware method with class, object, name and operation; on read, primary returned value is observed. **HOLD-D2-EFFECT-HOOK**. [Нормативний опис](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_slot-missing.html).
5. **SLOT-UNBOUND** — обробити-незв'язану-комірку: On read of existing-but-unbound slot in a standard-class instance, dispatch to distinct hook; default signals UNBOUND-SLOT; primary handler value is used if provided. **HOLD-D2-EFFECT-HOOK**. [Нормативний опис](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_slot-unbound.html).
6. **CLASS-OF** — безпосередній-клас: Return the exact class metaobject of which an object is a direct instance, not merely an approximate type specifier. **REVIEW-SEMANTIC-CANDIDATE**. [Нормативний опис](https://www.lispworks.com/documentation/HyperSpec/Body/f_clas_1.htm).
7. **CLASS-NAME** — ім'я-класу: Return the class name symbol if present; anonymous classes have NIL and name is not identical to class-object identity. **HOLD-DERIVED-PROJECTION**. [Нормативний опис](https://franz.com/support/documentation/ansicl.94/dictentr/class-na.htm).
8. **FIND-CLASS** — знайти-клас: Resolve a symbol to a class metaobject in the explicitly applicable environment; missing with errorp false returns NIL, with default true signals error. **HOLD-D2-ENVIRONMENT**. [Нормативний опис](https://franz.com/support/documentation/10.0/ansicl/dictentr/find-cla.htm).

## Доказ і межі

- Спершу реальні позитивні й негативні спостереження (закладені в JSON). Далі незалежний Lisp oracle та derivability, не лише exact-name dedup.
- Чотири REVIEW — це тільки пріоритет. Усі 8 залишаються **поза 625 selected**, без координат, ратифікації і physical T5.
- SLOT-MISSING та SLOT-UNBOUND є подіями/хуками виконання: вимога D2-only control первинна.
- CLASS-OF повертає **клас-об'єкт**, а TYPE-OF — **типовий специфікатор**, не автоматично тотожні.
- Порівнювати з [PR #4842](https://github.com/juv4uk/sens/pull/4842), #4800 та #4837–#4839; жодне з них не містить цих восьми exact-name рядків.

## Команда перевірки

`python3 scripts/check_d10_clos_slot_state_history.py --self-test`
