# D9 library harvest v1 — 58 language-owned meanings

**Статус:** research / unratified  
**Issue:** #3983  
**Foundation:** #3960 / Contract 11.7

Цей tranche бере semantics не зі старих 8-бітних координат, а з реальних Lisp-визначень у канонічних бібліотеках.

## Результат

```text
persistent map       5
persistent vector    6
reasoning            7
unification          6
epistemic           11
knowledge            9
time                14
-----------------------
new D9 meanings     58

D9 selected total  226/512
law-forced placed  128
unplaced selected   98
remaining          286
ratified D9          0
```

## Persistent map

```text
MAP-EMPTY
MAP-INSERT
MAP-GET
MAP-CONTAINS?
MAP->LIST
```

Це immutable structural-sharing map algebra. Internal AVL helpers не стали residents.

## Persistent vector

```text
VEC-EMPTY
VEC-COUNT
VEC-NTH
VEC-CONJ
VEC->LIST
VEC-FROM-LIST
```

Так само взяті публічні semantics, а не internal tree/rotation helpers.

## Reasoning / unification

```text
REASON
PROVE-GOAL
PROVE-GOALS
EXPLAIN-PROOF
REASON-EXPLAIN
SOURCE-OF
PROVENANCE

LOGIC-VAR
VAR?
WALK
UNIFY
OCCURS-CHECK?
APPLY-SUBST
```

Це language-owned reasoning/unification operations, реалізовані в Lisp.

## Epistemic / knowledge

Додані record predicates/accessors, SUPPORTING-EVIDENCE та knowledge-base operations на кшталт MODULE-KNOWN?, MODULE-CLAUSES-NOW, REASON-IN, FORWARD-IN, CHECK-CONFLICT?, COLLECT-FACTS-ABOUT, DESCRIBE.

## Time

Важлива межа:

```text
raw host observation != Core semantic meaning
```

Тому не додані як residents:

```text
unix-time-now
ntp-query-raw
timezone-declarations-raw
```

Але додані Lisp-owned semantic wrappers/transforms:

```text
UTC-FROM-UNIX
UNIX-TIME-OBSERVATION->UTC
UTC-NOW
INTERNET-TIME-SYNC
MILLISECONDS-FROM-NANOSECONDS
MONO-MS
DEADLINE-FROM
DEADLINE-REACHED-AT?
DEADLINE-AFTER-NS
DEADLINE-REACHED?
ELAPSED-NS
TIMEZONE-DETECT
TIMEZONE-NAME
TIMEZONE-OFFSET-SECONDS
```

Тобто host постачає сирий факт, а meaning живе в Lisp.

## Координати

Жоден із 58 нових meanings не отримав D9 coordinate.

```text
meaning selected != placement proved
```

Старі semantic-registry 8-bit codes мають нульову D9 placement authority.
