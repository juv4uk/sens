# Карта міграції легасі-COND — 42 файли, 1118 клауз

**Статус:** дослідницький звіт. Не ратифікує, не змінює драбину.

## Масштаб (виміряно інструментом авторитету `scripts/cond-modernize.py --scan lib`)
```
42 файли, 1118 клауз, 1117 HOLD, 0 auto-YES
найбільші: core.lisp 124 | core4.lisp 118 | meta-eval.lisp 79 | utf8.lisp 74
           forward.lisp 69 | knowledge.lisp 46 | reason.lisp 44
```
Корінь усіх червоних воріт: `D3:110 COND requires exactly (test expression); three-part compatibility is forbidden`.

## Правило заміни (виведене З ФАЙЛІВ, не вигадане)
```
(query) 1 X                        -> (query X)          тест істинний
(query) t X                        -> (query X)          t істинний
(query) 0 nil  (остання)           -> (t (00000001 ()))  конвенція файлу (else)
(query) 0 nil  (не остання)        -> прибрати           COND дефолтиться в nil  [ДОПУЩЕННЯ]
(query) NO X + (query) YES X        -> (t X)              обидві полярності = X
(query) EXPECTED X, EXPECTED-вираз -> ПОТРЕБУЄ РІШЕННЯ   (немає поля очікування у 2-частинній формі)
```
**Доведення для пар:** усі NO-клаузи з гіллям мають YES-двійника з ІДЕНТИЧНОЮ гілкою.

## Результат прогону (моїм мігратором `cond-migrate-pairs.py`)
```
conv=201  dropped=94  hold=29
13 файлів мігруються ЦІЛКОМ ЧИСТО (bal=True, parse=True, hold=0)
29 файлів мають 1 блокуючу клаузу
```
Чисті файли: epistemic, guard, machine/capability-axis, machine/lowering/semantic-x86-64,
machine/profile/minimal-runtime-x86-64, meta-eval-first-class, meta-eval-mutual,
persistent-map, reason, result-status, surface/semantic-registry-experiment, unify, world.

## Що блокує решту 29
«OTHER»-полярність: поле очікування — не `0/1`, а `t` або **довільний вираз**:
```
(t t t)
((truthy? value) t (00000001 ()))
((01110111 clause) (clause-kind rule) (01111001 item ...))
```
Старий COND мав поле «очікуваний результат»; новий 2-частинний — ні.
Природний переклад: `((equal? (query) EXPECTED) X)` — але це РІШЕННЯ АВТОРИТЕТУ.

## Межі
- Семантику не прогнано (немає cargo). Єдине допущення — прибрання не-останніх NO->nil.
- 2 баги у власному міграторі знайдено й виправлено (застарілі спани; порівняння dict-ів зі спанами).
