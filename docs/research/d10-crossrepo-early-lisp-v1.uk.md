# D10 cross-repo early Lisp recovery v1

**Status:** research / unratified  
**Issue:** #4071  
**Parent:** #4053  
**Foundation:** #4008 / Contract 11.8

Reviewed:
- juv4uk/mccarthy-eval
- juv4uk/lisp
- juv4uk/lisp-1
- juv4uk/LISP-2

## Selected

```text
APPQ
DEFINE-BATCH
CALL/CC
READTABLE
IF
NUMERIC-NOT-EQUAL
```

All six are Core candidates and remain **UNPLACED**.

## Projections / no-slot

Examples:
- DEFINE-SYNTAX -> D5 MACRO + D4 DEFINE
- READ-MANY -> D9 READ-ALL
- SLURP / SPIT -> D9 READ-FILE / WRITE-FILE
- SET! -> SET/SETQ family
- FIRST / REST -> CAR / CDR
- DEBUG -> tooling
- MOD -> HOLD until signed-modulus law is compared with current REMAINDER

## D10

```text
before      367
new           6
after       373/1024
placed      256
unplaced    117
remaining   651
ratified      0
```

No donor coordinates or implementation addresses are imported.
