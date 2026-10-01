# #2162 — D4 polarity witness на поточному Core1

Статус: лише research. Цей звіт не ратифікує D4-коди.

## Питання

Після #2159 сильне family-розміщення лишило 16 рівноцінних орієнтацій усередині
пар. Цей witness перевіряє, чи дає поточна поведінка Core1 конкретну підставу
вибрати, хто в парі має suffix `0`, а хто suffix `1`.

Кандидат:

```text
0000 APPLY   0001 EVAL
0010 LAMBDA  0011 DEFINE
0110 EVCON   0111 EVLIS
1110 LOOKUP  1111 BIND
```

Selector theorem лишається незалежно зафіксованим:

```text
1010 CAAR   1011 CADR
1100 CDAR   1101 CDDR
```

## Операційні докази з lib/core1.lisp

### LOOKUP / BIND

`C1-LOOKUP` шукає в наявних frame. `C1-BIND` будує нові environment cells
через CONS і рекурсивно зв'язує params/args.

Отже:

```text
1110 LOOKUP
1111 BIND
```

### EVCON / EVLIS

`C1-EVCON` перевіряє умови, доки не вибере одну гілку.
`C1-EVLIS` обчислює весь список форм і явно CONS-будує список результатів.

Отже:

```text
0110 EVCON
0111 EVLIS
```

### APPLY / EVAL

`C1-APPLY` споживає вже розв'язану callable value та вже обчислені аргументи.

`C1-EVAL` виконує ширший контекстний шлях: lookup, conditional evaluation,
lexical binding, evaluation списку аргументів, а потім application.

Отже:

```text
0000 APPLY
0001 EVAL
```

### LAMBDA / DEFINE

LAMBDA створює callable closure з поточного lexical context.
DEFINE належить top-level/program path і розширює persistent GLOBAL frame новою
парою name/value.

Отже:

```text
0010 LAMBDA
0011 DEFINE
```

## Слабка спільна полярність

Чотири пари узгоджуються зі слабшим операційним читанням:

```text
0 = працювати з / вибрати / використати поточний розв'язаний фокус
1 = продовжити / побудувати / розширити навколишній контекст
```

Для selector-family вже існує сильніший доведений закон:

```text
0 = compose CAR
1 = compose CDR
```

Його не можна підміняти слабшою метафорою.

## Повний перебір орієнтацій

Для чотирьох пар існує `2^4 = 16` орієнтацій.

Рівно одна задовольняє всі чотири поточні Core1-witness:

```text
0000 APPLY   0001 EVAL
0010 LAMBDA  0011 DEFINE
0110 EVCON   0111 EVLIS
1110 LOOKUP  1111 BIND
```

Це executable source-structure evidence, але ще не доказ одного універсального
семантичного значення suffix bit 1.

## Перевірка старого low-nibble

Правило "стиснути Function8 до молодших чотирьох бітів" одразу ламається:

- історичний EVAL `01001101` став би `1101`, де вже доведений CDDR;
- історичний APPLY `10101111` став би `1111`, конфліктуючи з environment lane;
- LAMBDA/DEFINE `1000/1001` потрапили б під CONS, втрачаючи сильніший
  QUOTE/syntax family зв'язок.

Отже D4 треба виводити, а не обрізати зі старої таблиці.

## Відтворення

```sh
python3 scripts/research-2162-d4-polarity.py
```

Очікуваний результат:

```text
D4 polarity witness: PASS
orientation-space=16
best-operational-evidence-score=4
best-orientations=1
```

## Не-висновок

Карта ще не ратифікована. Потрібен semantics-preserving refactor Core1 як
фальсифікатор: якщо evidence зникає після нешкідливого рефакторингу, спільна
полярність надто залежить від реалізації.

## Принцип

**Орієнтація біта має пережити executable behavior, а не лише словесну
аналогію.**
