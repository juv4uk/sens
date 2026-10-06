# D10 historical MacLisp v2 — reader, symbol, array and print semantics

**Статус:** research / unratified  
**Issue:** #4042  
**Foundation:** #4008 / Contract 11.8 / D1–D9

Primary donor: MacLisp Reference Manual, 17 Dec 1975.

## Результат

```text
SELECT                    12
CURRENT-PROJECTION         9
HOLD / mechanism / math   11

D10 selected total       400/1024
law-forced placed        256
unplaced selected        144
remaining                624
ratified                    0
```

## SELECT — 12 meanings

```text
MAKNAM
IMPLODE
READLIST
EXPLODE
EXPLODEC
EXPLODEN
FLATSIZE
FLATC
MAPATOMS
MAKE-ARRAY
REARRAY
SORTCAR
```

### Symbol / reader representation

- **MAKNAM**: character/code list -> fresh uninterned symbol.
- **IMPLODE**: character/code list -> interned symbol.
- **READLIST**: character/code list -> S-expression through reader semantics.
- **MAPATOMS**: enumerate/apply over interned symbols without exposing obarray bucket representation.

### Printed representation

- **EXPLODE**: escaped/readable printed form -> character-object list.
- **EXPLODEC**: unescaped PRINC-like form -> character-object list.
- **EXPLODEN**: unescaped form -> numeric character-code list.
- **FLATSIZE**: size of escaped/readable printed representation.
- **FLATC**: size of unescaped printed representation.

These are related to WRITE-TO-STRING, but are retained as distinct historical language operations because their result carriers and escaping laws are explicit.

### Arrays

- **MAKE-ARRAY** abstracts the historical ARRAY/*ARRAY construction law while dropping pointer/property-list implementation accidents.
- **REARRAY** preserves contents while reshaping in row-major order.
- **SORTCAR** sorts by the CAR/key supplied to the comparison predicate.

## Historical projections — no new slot

```text
ASCII         -> CODE-CHAR
GET_PNAME     -> SYMBOL->STRING
CATENATE      -> STRING-APPEND
STRINGLENGTH  -> STRING-LENGTH
SUBSTR        -> STRING-SLICE
GETCHAR       -> SYMBOL->STRING + SCHAR
GETCHARN      -> GETCHAR + CHAR-CODE
SAMEPNAMEP    -> name projection + equality
ALPHALESSP    -> name projection + STRING<
```

They stay in historical provenance but do not consume D10 capacity.

## Kept outside this tranche

Implementation mechanisms:
`SUBRCALL`, `LSUBRCALL`, `ARRAYCALL`.

Host/file boundary:
`DUMPARRAYS`, `LOADARRAYS`.

Core-Math / machine carrier / nondeterminism review:
`FIX`, `FLOATP`, `BIGP`, `COS`, `RANDOM`, `SIGNP`.

## Sens8

Sens8 remains preserved in full as historical donor/provenance. This tranche neither deletes it nor uses its coordinates as placement authority.

## Geometry

All 12 selected meanings remain:

```text
coordinate = null
coordinate_basis = UNPLACED
ownership = CORE-OWNED-CANDIDATE
```

History supplies meanings; geometry remains a separate proof problem.
