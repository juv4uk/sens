# D10 fill v1 — перший seed

**Статус:** RESEARCH / UNRATIFIED  
**Authority task:** #4012  
**Current ratified foundation:** #3960 / Contract 11.7 / D1–D8

## Стартова точка

D9 уже має повний research inventory 512/512, але ще не ратифікований.

Тому D10 не може просто успадкувати D9 coordinates.

Єдина геометрія, яка переходить зараз, — доведений selector-generator law.

## Перші 256 meanings

D9 має 128 selector candidates із PROVED-SELECTOR-GENERATOR.

Для кожного:

```text
D9 p
 -> D10 p0 : append A / compose CAR
 -> D10 p1 : append D / compose CDR
```

Отже:

```text
D10 capacity                 1024
selector-law candidates       256
remaining meanings            768
law-forced coordinates        256
unplaced selected               0
ratified D10 residents          0
```

## Authority boundary

```text
D9 semantic inventory = donor evidence
D9 unratified placement = no D10 authority
D9 proved selector law = may cross
```

Це дозволяє почати D10 до ратифікації D9, не змішуючи research coordinate choice з semantic authority.

## Заборонено

- Sens8/Sid8/Function8 placement authority;
- автоматичне p -> p0/p1 для всіх D9 meanings;
- host pointer/fd/ABI/backend як semantic identity;
- runtime callability із самого факту research residency;
- D10 ratification без окремого owner decision.

## Наступний крок

Добрати 768 distinct meanings через recovery, canonical Lisp libraries, history, math/logic families та нові language-visible operations. Meaning selection і placement лишаються окремими задачами.
