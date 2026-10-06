# D9 laws v1 — перші локальні закони

**Статус:** research / unratified  
**Issue:** #3970  
**Foundation:** #3960 / Contract 11.7

Перевірено всі 20 перших non-selector D9 кандидатів.

## Результат

```text
PROVED family members       7
PROVED distinct semantic    1
UNDERDETERMINED            12
coordinates assigned        0
ratified D9 residents       0
```

## Доведені сімʼї

### Stream scoped resource

OPEN, CLOSE, WITH-OPEN-FILE.

На абстрактному handle-state:

```text
WITH-OPEN-FILE = OPEN -> lexical body -> CLOSE
```

Body result зберігається, а resource після scope закритий. Remove-one falsifier: забрати CLOSE — live-handle лишається.

Це не робить file descriptor або OS API частиною мови.

### Named descriptor generator

DEFSTRUCT, DEFTYPE, DEFINE-CONDITION.

Спільна форма:

```text
DEFINE-DESCRIPTOR(kind, name, payload)
```

kind є незалежною спостережуваною віссю. Якщо її прибрати, однакові names колапсують.

### Row-major indexing refinement

ROW-MAJOR-AREF є refinement щодо D8 AREF.

Для rank-1 вони збігаються. Для rank>1 linear index має власний deterministic row-major закон.

### NUNION mutation distinction

NUNION відрізняється від D6 UNION через alias-visible destructive update. Це стало легітимним для аналізу після того, як D8 ратифікував observable mutation через RPLACA/RPLACD.

## Поки UNDERDETERMINED

DRIBBLE, FFI-CALL, ARGLIST, &WHOLE, macro/meta family, ERROR-IF-NOT-ERROR, DEHANDLER, NRECONC.

Їх не викинуто. Просто поточних даних недостатньо для короткого незалежного закону.

## Межа геометрії

```text
proved semantic law != automatic coordinate
```

Усі 20 non-selector meanings все ще UNPLACED. Law-mining не виконав жодного gauge-fix і не ратифікував D9.
