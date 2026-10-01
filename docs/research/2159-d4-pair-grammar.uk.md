# #2159 — D4 pair-grammar, перший повний перебір

Статус: лише research. Цей звіт не ратифікує жодного нового D4-коду.

## Кандидат A

```text
0000 APPLY
0001 EVAL

0010 LAMBDA
0011 DEFINE

0100 NOT
0101 <вільно>

0110 EVCON
0111 EVLIS

1000 LIST
1001 <вільно>

1010 CAAR
1011 CADR

1100 CDAR
1101 CDDR

1110 LOOKUP
1111 BIND
```

Чотири selector-адреси вже зафіксовані попереднім доказом композиції.

## Чому ця схема цікава

Кожен D3-префікс отримує локальну D4-смугу:

```text
000x meta execution
001x abstraction / definition
010x predicate refinement
011x evaluator traversal
100x construction
101x CAR composition
110x CDR composition
111x environment identity
```

Лише `101x/110x` зараз мають доведений prefix-generator law. Решта — гіпотези
розміщення / family affinity, а не автоматичне семантичне батьківство.

Два місця навмисно лишаються порожніми:

```text
0101
1001
```

Жодна функція не вигадується лише для заповнення D4.

## Простір пошуку

Виконуваний witness фіксує:

```text
1010 CAAR
1011 CADR
1100 CDAR
1101 CDDR
```

і вимагає, щоб чотири bootstrap-пари лишалися сусідніми:

```text
APPLY / EVAL
LAMBDA / DEFINE
EVCON / EVLIS
LOOKUP / BIND
```

`LIST`, `NOT` і два вільні слоти займають решту чотири позиції.

Разом перевіряється:

```text
69 120 розкладок
```

## Незалежні критерії

Один прихований зважений beauty-score не використовується.

### 1. Bootstrap relation adjacency

Рахується однобітна близькість лише для явно названих відношень із
поточного bootstrap/evaluator. Геометрія отримує бал лише після того, як саме
відношення задане незалежно від бітів.

### 2. D3-prefix family affinity

Окремо перевіряється, чи роль стоїть під D3-root із прямою поточною підставою:

- LAMBDA/DEFINE біля QUOTE;
- NOT біля ATOM або COND;
- EVCON/EVLIS біля COND;
- LIST біля CONS;
- LOOKUP біля EQ;
- BIND біля EQ або CONS.

Для APPLY/EVAL під `000` бал parent-affinity не дається: це поки
meta/bootstrap placement hypothesis, а не theorem із ground-role.

## Результат

```text
Кандидат A:
  relation adjacency = 10
  parent affinity     = 8

Глобальні максимуми:
  relation adjacency = 13
  parent affinity     = 8

Найкраща relation adjacency серед усіх розкладок із parent affinity = 8:
  10
```

Отже Candidate A досягає **максимальної parent affinity** і водночас
**найкращої можливої relation adjacency без втрати цього максимуму**.

Pareto-frontier для двох критеріїв:

```text
(relation adjacency, parent affinity)

(10, 8)
(12, 6)
(13, 5)
```

Candidate A лежить на Pareto-frontier.

Є 16 орієнтацій із тією самою парою `(10,8)`. Тобто розміщення family
визначене значно сильніше, ніж остаточний вибір 0/1 усередині кількох пар.

## Особливо цікаві однобітні сусіди Candidate A

```text
APPLY  <-> EVAL
APPLY  <-> LAMBDA
EVAL   <-> DEFINE
LAMBDA <-> DEFINE

EVCON  <-> EVLIS
EVCON  <-> LOOKUP
EVLIS  <-> BIND

LOOKUP <-> BIND
LOOKUP <-> CAAR
LOOKUP <-> CDAR
BIND   <-> CADR
BIND   <-> CDDR

LIST   <-> CAAR
LIST   <-> CDAR
```

Орієнтація LOOKUP особливо цікава щодо поточного Core1: lookup середовища
дістає key через CAAR-подібний шлях, а value — через CDAR-подібний. Це варто
перевіряти окремо як evidence, але це ще не закон.

## Що ще не вирішено

Перебір не доводить універсального значення останнього біта.

Для selector-family suffix theorem реальний:

```text
...0 = compose CAR
...1 = compose CDR
```

Для інших пар останній біт поки лише локальний індекс пари. Не можна
переносити selector-law на LAMBDA/DEFINE або APPLY/EVAL лише за аналогією.

16 рівноцінних варіантів `(10,8)` означають, що orientation потребує окремого
критерію: напрям виконання, introduction/elimination duality, migration cost,
self-description cost або hardware decode evidence.

## Відтворення

```sh
python3 scripts/research-2159-d4-pair-grammar.py
```

Очікуваний заголовок:

```text
placements=69120
candidate-a relation-adjacency=10
candidate-a parent-affinity=8
max relation-adjacency=13
max parent-affinity=8
best relation-adjacency at max parent-affinity=10
pareto=(10,8),(12,6),(13,5)
```

## Принцип

**Спочатку виводимо відношення; лише потім дозволяємо 4-бітному кубу їх стискати.**
