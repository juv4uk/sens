# D10 fill v1 — перший seed

**Статус:** RESEARCH / UNRATIFIED  
**Authority task:** #4012  
**Current ratified foundation:** #4008 / Contract 11.8 / D1–D9

## Стартова точка

D9 уже owner-ratified 512/512 під #4008.

Тому D9 coordinates є нормативними D9 identities, але вони не породжують D10 meanings автоматично.

У D10 зараз переходить лише доведений selector-generator law.

## Перші 256 meanings

D9 має 128 selector residents із proved-selector-generator basis.

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
D9 coordinate = normative D9 parent identity
D9 parent + one extra bit != automatic D10 semantic child
proved selector generator = may cross
```

Це дозволяє використовувати ратифікований D9 як стабільну батьківську основу, не плутаючи ширину з новим meaning.

## Заборонено

- Sens8/Sid8/Function8 placement authority;
- автоматичне p -> p0/p1 для всіх D9 meanings;
- host pointer/fd/ABI/backend як semantic identity;
- runtime callability із самого факту research residency;
- D10 ratification без окремого owner decision.

## Наступний крок

Добрати 768 distinct meanings через recovery, canonical Lisp libraries, history, math/logic families та нові language-visible operations. Meaning selection і placement лишаються окремими задачами.
