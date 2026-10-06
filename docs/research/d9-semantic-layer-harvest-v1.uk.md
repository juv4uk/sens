# D9 semantic-layer harvest v1 — 65 API meanings

**Статус:** research / unratified  
**Issue:** #3990  
**Foundation:** #3960 / Contract 11.7

Цей tranche бере не internal helpers, а explicit language-owned API semantics із семи Lisp-модулів.

## Результат

```text
content-store      6
result-status     14
narrate            9
understand         7
utf8               5
translation       16
guard              8
--------------------
new meanings      65

D9 selected      313/512
placed           128
unplaced         185
remaining        199
ratified D9        0
```

## Що саме додано

### Content-addressed store

EMPTY-CONTENT-STORE, CONTENT-STORE-PUT/GET/CONTAINS?, CONTENT-STORE-PUT-WORLD, CONTENT-STORE-SIZE.

### Result-status algebra

Конструктори PROVED / UNKNOWN / PARTIAL / BLOCKED / DISPUTED / INVALID, їх status/payload projections, goal/opposite-goal semantics та explicit reasoning observations.

### Narration / understanding

Контрольований двосторонній міст structure ↔ text-shaped data:

```text
UNDERSTAND*   : controlled words -> knowledge/query structure
NARRATE*      : fact/proof/outcome -> controlled words
```

### UTF-8 / Unicode

UTF8-DECODE, UTF8-VALID?, UNICODE-SCALARS->STRING, UTF8-DECODE-STRING, UTF8-ENCODE-STRING.

Byte-level decode helpers лишилися implementation detail.

### Translation boundary

Вибрані proposal/review/evidence API semantics. Зовнішній translator не отримує semantic authority: Lisp review/admission лишається явною межею.

### Guard algebra

Явні decision/evidence predicates, finding construction, UNKNOWN routing, comparison, sync-window classification та generic reference lookup.

## Що навмисно НЕ вибрано

Helpers на кшталт:

```text
result-proper-list?
result-not-head?
narrate-proved-outcome
narrate-invalid-outcome-shape
narrate-outcome-arity?
strip-article
utf8-continuation-byte?
utf8-decode-onto
translation-envelope-valid?
translation-batch-valid?
```

Вони можуть бути корисними для реалізації/доказу, але поки не споживають окремий D9 semantic slot.

## Геометрія

Усі 65 нових meanings:

```text
coordinate = UNPLACED
```

Жоден source/legacy code не став D9 placement authority.

**Meaning first, geometry later.**
