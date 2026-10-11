# D10: CHANGE-CLASS — кандидат із історичного CLOS

**Статус:** selected research / очікує рішення власника. Це не ратифікація, не координата й не дозвіл кодувати executable `.sens`.

## Першоджерело

[ANSI Common Lisp HyperSpec — CHANGE-CLASS](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_change-class.html). Зафіксовано запис **CLOS-03** у `knowledge/d10-historical-clos-interlisp-residual-review-v1.json` (blob `df8ed73011df39f9ec689046ce6936cc00892215`), дослідження #4842.

## Незалежний спостережуваний закон

`CHANGE-CLASS(instance, target-class)` змінює клас уже наявного екземпляра та зберігає тотожність того самого об’єкта. Значення спільних за іменем слотів лишаються доступними; спільні слоти, що були незв’язаними, не стають зв’язаними лише через зміну класу.

Це не еквівалентно `DEFCLASS` (опис класу), `MAKE-INSTANCE` (створення об’єкта) або `SLOT-VALUE` (спостереження/доступ до слота). Спеціальні lifecycle hooks під час переходу не виділяються тут як окремі семантичні резиденти.

## Свідки та межі тверджень

- SBCL/CLOS reference fixture перевіряє EQ-ідентичність до/після, цільовий клас, збереження спільного значення та незв’язаність спільного слота.
- Python checker перевіряє точне джерело, відсутність дублювання імені в D1–D9/поточному D10, облік 648/1024 і SHA-ланцюг переходів.
- Це історичний Common Lisp reference oracle, **не** доказ реалізації цього закону в SENS runtime.

## Рішення про місце

Додається рівно один selected research candidate: `648/1024`, unplaced `392`, remaining `376`, ratified `0`. Координата залишається `null`; D1–D9, D2, physical format та production codec не змінюються. Власник має окремо вирішити, чи достатньо закон незалежний від композиції вже наявних класових і слотних операцій.
