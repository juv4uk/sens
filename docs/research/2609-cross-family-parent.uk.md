# #2609 — типізований міжсімейний guard батьківства

Статус: лише дослідження STRUCTURAL-DISCOVERY.

## Питання

Після D4 маємо кілька окремо спостережуваних сімей факторів:

```text
MutationFamily
NonLocalControl
SpecialCallProtocol
```

Усі вони можуть говорити про «контекст», «середовище», «стан» чи «caller», але
спільна лексика не є доказом семантичного батьківства.

Умова placement із #2236 сильніша:

```text
той самий базовий семантичний об'єкт/операція
+ одна виконувана delta
= допустима породжена дитина
```

Цей witness машинно перевіряє перший рядок.

## Поточні типізовані дослідницькі форми

```text
MutationFamily
  носій: shared store/location
  операція: (store,target,value) -> updated store
  спостереження: store змінюється; звичайне продовження лишається

NonLocalControl
  носій: dynamic exit context
  операція: (value,exit-context) -> non-local transfer
  спостереження: continuation пропускається; store не змінюється

SpecialCallProtocol
  носій: source invocation/caller context
  операція: syntax/context -> direct value або replacement form
  спостереження: змінюється syntax/call protocol; mutation і non-local exit не потрібні
```

Це дескриптори доказу, не нові runtime-типи.

## Результат

Усі шість напрямків між різними сім'ями відхиляються як:

```text
DOMAIN-MISMATCH
NO-PROVED-SAME-BASE-PARENT
```

Це не твердження «неможливо назавжди». Майбутня bridge-теорема може відкрити
пару знову, але мусить явно назвати спільний носій/базову операцію і закон.

## Позитивний контроль

Guard не каже, що одна сім'я автоматично означає однобітну дитину.

DEFINE і SETQ-core належать до спільної binding/mutation сім'ї, але #2492/#2518
довели дві незалежні policy-delta.

Тому:

```text
same-family = необхідна умова-кандидат
same-family != достатній placement proof
```

## Відтворення

```sh
python3 scripts/research-2609-cross-family-parent.py
```

Очікується:

```text
CROSS-FAMILY-PARENT-GUARD=PASS
ROOTS-PROVEN=0
D5-RESIDENTS=0
COORDINATES-ALLOCATED=0
WIDTH-INFERENCE=NONE
```

## Принцип

**Новий біт може уточнювати семантичний об'єкт; він не може непомітно міняти,
який саме вид семантичного об'єкта обробляється.**
