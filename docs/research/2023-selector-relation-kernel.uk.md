# #2023 — редукція ядра зв’язків selector-family, перший bounded результат

Статус: лише дослідження. Жодних кодів relation, production semantics, runtime чи compiler змін.

## Корпус

Вхід — поточний bounded corpus Lisp I / Lisp 1.5 з #1962 у draft #1963.

Selector scope:

```text
101  root CAR
110  root CDR

1010
1011
1100
1101
10110
10111
```

Людські назви операцій не беруть участі у виконуваному законі реконструкції.

## Живий результат

Виконано у WSL на commit `a6a19b507b818acc07619a6b56daac904b53252a`.

```text
K0 flat explicit              20 stored per-node relation facts
K1 parent + edge              12 stored per-node relation facts
K2 parent only                 6 stored per-node relation facts
K3 intrinsic bits + law        0 stored per-node relation facts

family-law facts retained      2
```

Два збережені family-law facts:

```text
0 -> 101
1 -> 110
```

## Чому K3 працює локально

Для admitted selector word `w`:

```text
root(w)   = перші 3 біти
parent(w) = відкинути останній біт
edge(w)   = останній біт
suffix(w) = біти після root
```

Тому для цієї family це не незалежні stored semantic graph facts.
Це детерміновані проєкції canonical bounded binary identity.

Execution schedule після цього реконструюється фіксованою локальною дією:

```text
0 -> 101
1 -> 110
```

Приклад:

```text
10111
root   = 101
suffix = 11
schedule = 101,110,110
```

## Що це може видалити, якщо результат витримає перевірку

Лише для selector-family:

- per-node `root-of` facts;
- per-node `prefix-parent` facts;
- per-node `edge-bit` facts;
- per-node `mechanism-available` facts;
- дубльований execution-relation layer над інформацією, яка вже міститься у word.

Це **не** видаляє:
- semantic identities;
- canonical binary words;
- два local action laws;
- typed evidence, що цей family law справді valid.

## Negative control

Поточні CONS-family candidates `list` і `append` не мають proven prefix word у #1962 corpus.

Тому K3 не може реконструювати для них:

```text
parent
edge
root+suffix path
```

Вони лишаються поза цією теоремою. Selector-result навмисно не узагальнюється.

## Архітектурний наслідок

Для strong generative families semantic graph не мусить дублювати relations, які вже intrinsic до identity geometry.

Можлива менша архітектура:

```text
canonical word
  -> intrinsic lineage

small family law
  -> execution/proof action

typed graph
  -> лише non-intrinsic semantic relations/evidence
```

Це сумісно з результатом #2034: execution control може бути делегований малій machine, тоді як graph зберігає лише semantic evidence, яке неможливо вивести механічно.

## Non-conclusions

Це не доводить:
- що кожна SENS-family має intrinsic prefix relations;
- що global relation kernel має лише один primitive relation kind;
- що bīja3 minimal;
- що typed dependency/call/control relations зайві;
- що graph self-description непотрібний.

## Наступні falsifiers

1. застосувати ту саму редукцію до non-selector positive family, якщо така буде доведена;
2. перевірити recursive/SCC case, де relation information не закодована у word;
3. через #2026 перевірити, чи name-erased graph distinguishability не погіршується після видалення intrinsic selector edges;
4. через #2024 перевірити, чи proof certificate потребує selector graph edge понад word + family law.

## Принцип

**Не зберігати як semantic relation те, що canonical identity уже доводить механічно.**
