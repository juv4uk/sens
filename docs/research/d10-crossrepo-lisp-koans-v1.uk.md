# D10 cross-repo Lisp Koans harvest v1

**Status:** research / unratified  
**Issue:** #4074  
**Parent:** #4053  
**Foundation:** #4008 / Contract 11.8

Donor pinned at:

`juv4uk/lisp-koans@57b901f8d4b16d66696896a745110b7561120da3`

## Review

The first donor-attested review set contained 36 Common Lisp operations.

The D1-D9 exact-identity gate rejected 11 rows already ratified in D8:

```text
VALUES
MULTIPLE-VALUE-BIND
MAKE-CONDITION
HANDLER-BIND
SIGNAL
HANDLER-CASE
SUBSEQ
CHAR
POSITION
FLET
LABELS
```

That leaves **25 new D10 Core candidates**.

## Selected families

- multiple-value projection: MULTIPLE-VALUE-LIST
- condition/type bridge: CHECK-TYPE
- hash-table algebra: MAKE-HASH-TABLE, HASH-TABLE-P, HASH-TABLE-COUNT, GETHASH
- type-specifier algebra: TYPEP, TYPE-OF, SUBTYPEP, COERCE, CHARACTERP, BIT-VECTOR-P
- generic sequence: CONCATENATE, SEARCH
- derived control: WHEN, UNLESS
- structured formatting: FORMAT
- CLOS: DEFCLASS, MAKE-INSTANCE, SLOT-VALUE, DEFGENERIC, DEFMETHOD
- binding/control: DESTRUCTURING-BIND, BLOCK, RETURN-FROM

## D10

```text
before       373
selected      25
after        398/1024
placed       256
unplaced     142
remaining    626
ratified       0
```

No CLOS object layout, hash bucket, handler stack address or donor implementation detail becomes semantic identity.

All 25 remain UNPLACED.
