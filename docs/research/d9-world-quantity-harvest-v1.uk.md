# D9 world + quantity harvest v1 — 62 meanings

**Статус:** research / unratified  
**Issue:** #3992  
**Foundation:** #3960 / Contract 11.7

## Результат

```text
World algebra               32
Exact quantity/unit algebra 30
------------------------------
new meanings                62

D9 selected                375/512
placed                     128
unplaced                   247
remaining                  137
ratified D9                  0
```

## World algebra

Вибрані public semantics для:

- immutable world construction/projections;
- journal/tell/retract;
- module-scoped reasoning and advice;
- world navigation, diff and common ancestor;
- knowledge-package import/export shape;
- canonical content-address semantics.

Internal traversal helpers на кшталт `world-at-depth-from`, `world-climb-to-depth`, `world-common-ancestor-aligned` не отримали окремих slots.

## Exact quantity/unit algebra

Додані:

- dimension construction/predicates/projections;
- unit construction and exact product/quotient;
- quantity construction/projections and exact product/quotient;
- scientific-source records;
- scientific-constant record shape, status/kind validation and projections;
- projection of a scientific constant into ordinary knowledge clauses.

## Важлива межа constant track

Цей tranche **не** додає конкретні SI-константи з:

```text
lib/si.lisp
lib/si-derived.lisp
```

Тобто `c`, `h`, `e`, `k`, `N_A` та похідні physical constants не споживають D9 slots автоматично. Їхня authority лишається окремим constant/Core-Math питанням.

## Геометрія

Усі 62 meanings:

```text
coordinate = UNPLACED
```

Жоден source/legacy code не став placement authority.

**Meaning first, geometry later.**
