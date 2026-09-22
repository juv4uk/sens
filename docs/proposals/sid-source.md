# Пропозиція: 8-бітний SID як вихідна форма

**Статус:** PROPOSED · не є зміною `language-contract.lisp`.

## Форма reader

`lib/surface/semantic-registry.lisp` задає восьмибітний SID як канонічну
ідентичність: наприклад, `define` має `00001001`. Рівно вісім цифр `0`/`1` утворюють SID без заголовка чи reader-режиму:

```lisp
(00001001 x 41) ; SID 9: define
(00000100 x ()) ; SID 4: cons
```

Рівно вісім цифр `0`/`1` утворюють SID token. У позиції голови списку routed SID є
виконуваною identity; у даних або під `quote` той самий token лишається
бінарним значенням. Отже `00000000` є SID нуль у голові списку і 8-бітним
значенням поза нею.

Коротші числа, зокрема `1` і `42`, лишаються звичайними exact decimal literals.
`=9` не допускається: це був би другий lexer format і він розмив би обіцянку
byte SID.

## Межа поточного core-slice

Цей зріз робить виконуваними SID-и Canon та evaluator-owned necessary forms,
не змінюючи їхньої семантики. Людські aliases (`визначити`, `define`,
symbolic surface-и) лишаються рівноправними поверхнями тієї самої identity.

Перед поширенням на решту registry owner має ратифікувати:

1. які SIDs поза Canon/necessary forms стають executable;
2. error для malformed або unknown SID;
3. рівність observable behavior між surface call і SID call;
4. правило quoted data: `(quote (00001001 x 1))` лишається даними, доки
   не повернеться в reader/eval як list head.

Масово переписувати `.lisp`-файли варто лише після цих SID dispatch-ів та
еквівалентних witnesses. Звичайний текстовий replace непридатний: він не
відрізняє код від коментарів і quoted program data.

## English summary

This is a proposal, not a language-contract change. A SID file uses bare tokens of exactly eight binary digits without a reader declaration. A routed SID
is executable only in list-head position; elsewhere it remains binary data.
Shorter decimal literals remain ordinary exact numbers. The current core slice
covers Canon and evaluator-owned necessary forms; broader registry dispatch
requires owner ratification and surface-to-SID equivalence witnesses.
