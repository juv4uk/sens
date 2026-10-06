# D8 recovery candidate map

**Статус:** research / provisional. **D8 не ратифікований.**

Цей файл є точкою складання D8 після owner-principle #3920. Він не викидає попередні дослідження і не перетворює research coordinate на resident автоматично.

## Принцип

```text
1. необхідність
2. історична ранність
3. простий математичний/логічний закон
4. recovery того, що пропустили нижче
```

Ратифіковані D1–D7 не переставляються приховано.

## Перший provisional D8 candidate

```text
00000000  ENV-REFLECTION
```

Це **не ратифікація координати**. Це перше місце в ladder candidate map.

Причина: current SENS має живий `(env)`, який повертає видимі bindings, але D1–D7 не мають first-class environment reflection resident. Внутрішній environment evaluator-а не тотожний можливості програми перелічити своє середовище.

Історично споріднені слова:

```text
a
a-list / alist
association list
environment
env
```

Ранній `a-list` є представленням/контекстом evaluator-а; сучасний `ENV()` — окрема reflection-можливість. Їх не зливаємо без доказу.

Legacy `01001110` з поточного builtin implementation записується лише як provenance. Це **не** donor coordinate для D8.

## Відновлено, але слот не потрібний

```text
EQUAL   DERIVED-NO-SLOT
PAIR    DERIVED-NO-SLOT
AND     DERIVED-NO-SLOT
OR      DERIVED-NO-SLOT
DIVIDE  DERIVED/FOREIGN-REVIEW-NO-SLOT
```

`EQUAL/equal?` особливо важливий історично, але його structural law уже виражається через нижні структури. Історичну важливість не плутаємо з необхідністю нового resident.

## Ще не розкладено

```text
FSUBR                    UNRESOLVED-NO-SLOT
TRANSFORMER / HART-MACRO UNRESOLVED-NO-SLOT
ONEP/MINUSP/FIXP/FLOATP  RECOVERY-REVIEW
LOGOR/LOGAND/LOGXOR/
LEFTSHIFT                CORE-MATH-OR-MECHANISM-REVIEW
```

FSUBR і TRANSFORMER не втрачені: їхні protocol axes вже доведені й лишаються в recovery до exact-domain theorem.

## Попередні позитивні D8-дослідження збережено

Merged у main:

- TAKE/DROP × edge — #3667;
- ANY/ALL × predicate polarity — #3668;
- REDUCE/SCAN × direction — #3704;
- ZIP/UNZIP × orientation — #3712;
- DO/WHILE × condition/projection — #3779.

Відновлюються з незлитого #3783:

- NEG/ABS × RECIP;
- RASSOC/ACONS × association orientation;
- NTH/MAPLIST × traversal direction.

Їхні старі geometric coordinates зберігаються як research evidence. Вони **не переписуються** під `00000000...` і не губляться. Ladder coordinate для цих нових семантик буде призначений пізніше після recovery-ranking.

## Негативні результати теж збережено

#3778:

- CURRY/FLIP × swapped arguments — dependent axis;
- INTEGERP/RATIONALP × sign — unobservable axis;
- RECIP/EXPT × reciprocal/sign — dependent axes.

Негативний результат — це напрацьоване знання, а не сміття.

## Наступний крок

Наступний ladder slot видається лише після дешевого witness:

```text
не представлено D1–D7
+ не просто derived
+ необхідність/історія
+ простий закон
= наступний D8 candidate
```

Таким чином ми заповнюємо D8 і одночасно не втрачаємо жодної старої гілки дослідження.
