# Архів PR #1066 — Lisp-реалізація semantic ownership checker

**Статус: ARCHIVE-ONLY / PARITY NEEDED.**

Чотири branch-head файли зі SHA 09a65bd6f55358de8c9a4b023c3df5d1e555abaa збережено точно під source/. PR пропонував замінити/дублювати semantic-ownership.py Lisp checker-ом, але додавав тимчасовий differential workflow. Поточний main має чинний scripts/semantic-ownership.py; scripts/semantic-ownership.lisp у main відсутній. Паралельний checker не можна активувати лише на підставі заяви про parity.

Щоб відновити це як чинну міграцію, треба: відтворити весь набір Python acceptance/negative cases, deterministic report bytes, malformed inputs і SHA pairing; запустити обидві реалізації на однаковому поточному inventory; після доказу перемкнути callers і прибрати differential workflow в одному узгодженому потоці #553/#5041. Архів зберігає унікальний candidate code, але не змінює активну владу. Нова гілка не створювалась.
