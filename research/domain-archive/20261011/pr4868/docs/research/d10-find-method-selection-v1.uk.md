# D10: FIND-METHOD — відбір історичного значення CLOS (не ратифікація)

Джерело: **Common Lisp HyperSpec**, [FIND-METHOD](https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/stagenfun_find-method.html), та [CLtL2](https://www.cs.cmu.edu/Groups/AI/html/cltl/clm/node311.html). У вже злитому досьє `knowledge/d10-historical-clos-interlisp-residual-review-v1.json` це CLOS-01. Нижні D1–D9 і чинні 625 значень перевірено на **точну тотожність імені**; поведінковий висновок — конкретний пошук методу за кваліфікаторами та спеціалізаторами не є визначенням методу чи пошуком його застосовності до довільних runtime-аргументів.

## Незалежний закон

`(generic, ordered-qualifiers, specializers, optional errorp)` повертає **саме зареєстрований об'єкт методу**, не викликаючи його. Неправильна кількість required-specializers — помилка незалежно від errorp. Відсутність точної сигнатури дає NIL лише при errorp=false; стандартно — помилка через чинну владу D2. Порядок кваліфікаторів важливий. Реєстраційний порядок без зміни множини методів не змінює результат точного пошуку.

Задля незалежного свідка є два рівні перевірки: Python bounded reference-model із дев'ятьма adversarial тестами та **реальний SBCL/CLOS oracle** `tests/fixtures/d10-find-method-real-cl-oracle.lisp` (method-body invocation count=0, різниця між BASE/CHILD, помилка арності й відсутність). Вони перевіряють історичний **еталон**, а не стверджують, що SENS уже реалізував функцію. Гілка додає лише один SELECTED-RESEARCH, не призначає координату, не дозволяє .sens і не змінює D2.

## Правило координації

Лише цей рядок `FIND-METHOD` пишеться в inventory у даному PR. Паралельні агенти окремо працюють над SLOT-BOUNDP, SLOT-MAKUNBOUND, REMOVE-METHOD і Xerox LOOPS. Перед злиттям узгодити лічильники з актуальним main та дочекатися всіх CI. Залишкова перевірка: незалежний *SENS runtime oracle* і рішення власника щодо остаточної ратифікації.
