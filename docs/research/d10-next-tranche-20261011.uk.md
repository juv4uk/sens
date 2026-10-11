# D10 — наступна дослідницька порція (2026-10-11)

**Статус:** `RESEARCH-PENDING-REVIEW`. Це intake восьми джерельно прив'язаних пропозицій у ledger, не відбір до семантичного інвентарю.

## Незмінна межа

Вихідний стан на `c67db6cdd820dea8d3a110caed359507c0a2d7a4`: **647/1024** вибраних research-кандидатів, 256 law-forced координат, 391 вибраний без координати, 377 ще не відібраних, 0 ратифікованих D10 residents. Після цього PR очікуваний облік інвентарю лишається тим самим: `selected_added=0`, `coordinates_added=0`, `ratified_added=0`.

Усі вісім нових рядків мають `pending-review`, `ratified=0`, `coordinate=null`, `physical_t5_authorized=false`. D1–D9 та вибраний D10 дедуп навмисно позначено **PENDING**, а не вигаданим `NO-MATCH`. Жодне ім'я в цьому пакеті не отримує виконуваної ідентичності чи дозволу мігрувати `.lisp` у `.sens`.

## Кандидати і наступні гейти

| ID | Закон | Чому корисно дослідити | Утримання до рішення |
|---|---|---|---|
| `D10P-503110` ADJUST-ARRAY | Зміна розмірів/подання з точною ідентичністю змінного масиву та ланцюгом displacement | CLHS дає спостережувану семантику, яку можна порівняти з історичним MacLisp `*REARRAY` | `HOLD-DIFFERENTIAL-REVIEW`: довести незалежність від уже вибраних `MAKE-ARRAY`, `REARRAY`, `COPY-ARRAY`, `ARRAY-DISPLACEMENT` |
| `D10P-503111` WRAP | Вставити делегуючу обгортку перед функцією із збереженням базової функції та порядку | PSL Users Manual §8.2.2 | `HOLD-CONTROL-AND-TOOLING`: перевірити, чи не є це інструментальним wrapper/tracing законом або композицією поточних функцій |
| `D10P-503112` REMOVE-WRAPPER | Зняти обгортку заданого типу, зберігаючи інші | Той самий обмежений історичний донор PSL-1997 | `HOLD-COMPOSABLE-TOOLING`: похідність від WRAP і стану wrapper chain |
| `D10P-503113` FINITE-CODE-UNIQUE-DECIPHERABILITY | Вирішити однозначність декодування скінченного маркованого бінарного кодбука | Sardinas–Patterson (1963), пізніша формалізація (1967) | `HOLD-PENDING-BEHAVIORAL-DERIVABILITY`: окремо від D2 reader/structure та транспорту; не вводити форматне правило |
| `D10P-503114` ALLEN-INTERVAL-RELATION | Класифікація двох інтервалів рівно одним із 13 відношень Аллена | Allen, *Maintaining Knowledge about Temporal Intervals* (1983) | `HOLD-CORE-DERIVABILITY`: порівняння/COND можуть уже виразити закон |
| `D10P-503115` ATMS-CONSISTENT-LABEL-JOIN | Join середовищ підтримки з nogood-відсіюванням і мінімізацією до антинанцюга | Doyle (1979), de Kleer (1986) | `HOLD-D9-LOGIC-DERIVABILITY`: порівняти з JTMS, D6 set laws і поточними законами доказу |
| `D10P-503116` FINITE-CONVOLUTION | Лінійна, а не циклічна згортка над точними коефіцієнтами | Коефіцієнтний закон; NumPy лише для звірення термінів/прикладів | `HOLD-CORE-MATH-DERIVABILITY`: імовірна бібліотечна композиція MAP/REDUCE + арифметика |
| `D10P-503117` PHASE-UNWRAP | Накопичення найменших конгруентних різниць із точно визначеним правилом нічиєї | Дослідницький cross-check поведінки NumPy; не донор нормативності | `HOLD-CORE-MATH-DERIVABILITY`: може бути fold над MODULO; фізична траєкторія не виводиться лише з відліків |

## Фальсифікатори перед будь-яким selection

- **Масиви:** змінний масив мусить зберігати ідентичність; ланцюг `A→B→C` не можна сплющувати, якщо це змінює спостереження `A`.
- **Функціональні обгортки:** вилучення типу A не має прибирати тип B чи базову функцію; порядок делегування перевіряється на вкладених wrapper-ах.
- **Однозначне декодування:** `[(a,0),(b,01)]` є однозначним попри префіксність; `[(a,0),(b,01),(c,10)]` неоднозначне, бо `[a,c]` та `[b,a]` обидві дають `010`.
- **Allen:** `[0,1)) і `[1,2)` — `MEETS`, а не `BEFORE`; обмін аргументів мусить повернути обернене відношення.
- **ATMS:** підтримка, що містить nogood, вилучається; строгі надмножини наявних підтримок теж; порожня підтримка `()) не тотожна відсутності альтернатив.
- **Згортка:** `[1,2,3]*[1,1]=[1,3,5,3]`, довжина `n+m-1`; жодного циклічного wrap-around чи неявної floating-rounding норми.
- **Розгортання фази:** для `[0,1,2,-1,0]` за періоду 4 очікується `[0,1,2,3,4]`; у напівперіодній нічиїй зберігається знак початкової різниці.

## Першоджерела

- [ANSI Common Lisp HyperSpec — ADJUST-ARRAY](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_adjust-array.html) та [MacLisp Reference Manual (1975), *REARRAY](https://softwarepreservation.computerhistory.org/LISP/MIT/MACLISP_Reference_Manual-Dec_17_1975.pdf).
- [The PSL Users Manual, версія 1997 (PDF)](https://reduce-algebra.sourceforge.io/lisp-docs/allman1.pdf), §8.2.2. Не приписувати всі деталі цій гілці донора PSL 1984 без окремої звірки версії.
- [Sardinas & Patterson (1963)](https://doi.org/10.1016/S0019-9958(63)80011-X) і [Sardinas/Patterson–Levenshtein (1967)](https://doi.org/10.1016/S0019-9958(67)80002-0).
- [Allen (1983), *Maintaining Knowledge about Temporal Intervals*](https://doi.org/10.1145/182.358434), [Doyle (1979), *A Truth Maintenance System*](https://doi.org/10.1016/0004-3702(79)90008-0), [de Kleer (1986), *Problem solving with the ATMS*](https://doi.org/10.1016/0004-3702(86)90082-2).
- [Convolution reference](https://numpy.org/doc/stable/reference/generated/numpy.convolve.html) і [phase unwrapping reference](https://numpy.org/doc/stable/reference/generated/numpy.unwrap.html) — лише cross-check прикладів/термінів; не мовна authority.

## Порядок продовження

1. Звірити спостережувані закони з усіма ратифікованими D1–D9 та вибраними D10 за exact behavior, а не за іменами.
2. Виконати незалежні позитивні/негативні оракули й derivability attack.
3. Залишити корінь у HOLD, якщо його можна виразити поточними законами; selection — окремий append-only перехід зі своїм точним SHA; placement і ratification — окремі рішення власника.
