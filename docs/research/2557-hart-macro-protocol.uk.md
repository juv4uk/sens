# #2557 — Протокольне свідоцтво Hart MACRO 1963

Фаза: `HISTORICAL-INGEST / PROTOCOL-COMPARISON`.

Ця нотатка фіксує лише історичні свідоцтва. Вона не виділяє SENS-координату,
ширину, resident чи семантичну authority.

## Історичний якір

Timothy P. Hart, **“MACRO Definitions for LISP,” MIT Artificial Intelligence
Memo 57, October 1963**.

Архів/індекс:
- Computer History Museum / Software Preservation Group, LISP 1.5 family:
  https://softwarepreservation.computerhistory.org/LISP/lisp15_family.html
- AIM-57 доступний через це джерело.
- Steele & Gabriel, *The Evolution of Lisp*, §3.3 відтворює текст memo і
  називає Hart 1963 історичним введенням Lisp macros.

Архів також фіксує LISP 1.5 library від листопада 1963, що містить MACRO.

## Протокол із memo Hart

Hart пропонує MACRO instruction expander, інтегрований у `define`.

Історичний протокол:
- macro definition посилається на функцію одного аргументу;
- цей аргумент — повна форма, що починається з імені macro;
- macro-функція повертає форму-заміну;
- повернене значення замінює початкову форму у function definitions;
- `define` виконує macro expansion;
- Hart наводить CSETQ як приклад наявного FEXPR, який можна замінити MACRO definition.

На трьох осях #2522/#2557:

```text
Hart MACRO (1963)
  raw operands / full form      = 1
  explicit caller-env input     = 0
  returned-form replacement     = 1
```

Остання вісь є історичним аналогом result re-evaluation: повернена форма не є
прямим значенням первинного виклику, а стає replacement program structure для
подальшої обробки.

## Порівняння

```text
historical FEXPR/FSUBR   = (raw=1, caller-env=1, result-re-eval=0)
Hart MACRO 1963          = (raw=1, caller-env=0, result-re-eval=1)
current SENS TRANSFORMER = (raw=1, caller-env=0, result-re-eval=1)
```

Обмежений висновок:

```text
FEXPR vs Hart MACRO       = ORTHOGONAL on caller-env/result axes
Hart MACRO vs TRANSFORMER = PROTOCOL-ALIGNED on the tracked three axes
```

`PROTOCOL-ALIGNED` не означає тотожність механізмів. Hart описує
DEFINE/expansion-time replacement; поточний SENS може реалізувати еквівалентне
спостережуване staging на іншій execution boundary.

## Межа placement

```text
current_domain_candidate = unresolved
binary_object            = unplaced
placement_status         = unplaced
exact_width              = unresolved
```

Хронологія та протокол не виділяють біти D5/D6.
