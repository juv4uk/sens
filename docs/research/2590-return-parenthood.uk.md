# #2590 — атака на parenthood RETURN / PROG

Статус: STRUCTURAL-DISCOVERY, лише дослідницький артефакт.

## Результат під перевіркою

Наявні виконувані свідки вже розділяють два випадки:

```text
GO
  -> локальний параметр finite-state + tail recursion

RETURN
  -> значення + найближчий активний dynamic exit context
  -> проходить крізь звичайні вкладені виклики
```

Новий обмежений verifier не перевизначає цю семантику. Він перевіряє лише
placement-питання, яке з неї випливає.

### Турнір D4-parent

```text
APPLY   = виклик callable
EVAL    = обчислення форми
LAMBDA  = побудова closure
COND    = локальний вибір гілки
RETURN  = динамічний нелокальний вихід
```

Жоден із перевірених D4-кандидатів не має тієї самої базової операції, що RETURN.

### CPS — це компіляція, не parenthood

Наявний D4-countermodel може відтворити поведінку RETURN, передаючи явний
`exit-k` крізь ланцюг вкладених helper-викликів. Це доводить whole-program
D4-компільованість, але змінює call protocol:

```text
початковий helper interface
    !=
helper + явний exit-k interface
```

Тому CPS не доводить локального same-base D4 parent.

### PROG

PROG лишається композицією:

```text
локальний GO state-machine
+ фактор нелокального RETURN
```

Окремий resident для всього PROG з цього не випливає.

## Cross-family control

RETURN змінює control target без необхідності shared-location mutation. Фактор
мутації #2589 змінює shared location при звичайному поверненні керування.
Обмежені спостереження тому тримають ці фактори окремими.

## Консервативний висновок

```text
GO                         = derived local structure
RETURN same-base D4 parent = не знайдено у перевіреному наборі
RETURN exact width          = UNKNOWN
RETURN root status          = NOT PROVED
PROG                        = composite
виділено координат          = 0
```

Жодного D5/D6 residency чи coordinate з цього звіту не випливає.
