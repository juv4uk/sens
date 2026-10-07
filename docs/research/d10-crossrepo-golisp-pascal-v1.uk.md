# D10 cross-repo golisp / pascal-lisp harvest v1

**Status:** research / unratified  
**Issue:** #4077  
**Parent:** #4053  
**Foundation:** #4008 / Contract 11.8

Reviewed:
- juv4uk/golisp @ 820a36ef45c3492e9d607b8f4e232222759014b3
- juv4uk/pascal-lisp @ 2679615f70498a1d463fc3379097d61f145d53f0

## Selected 22

Environment/type/numeric:
```text
NULL-ENVIRONMENT
CAPTURE-ENVIRONMENT
DEFINE-CUSTOM-TYPE
FIXNUM->FLONUM
MODULO
```

String/vector conversion:
```text
STRING-SPLIT STRING-JOIN STRING->VECTOR
LIST->VECTOR VECTOR-SLICE VECTOR->LIST VECTOR->STRING
```

Abstract port I/O:
```text
READ-CHAR READ-BYTE EOF-OBJECT?
WRITE-STRING WRITE-BYTE FLUSH
```

Channel algebra:
```text
MAKE-CHANNEL CHANNEL-SEND CHANNEL-RECEIVE
```

Multiple-value control:
```text
CALL-WITH-VALUES
```

## Boundary

The donor implementation uses Go channels, OS files and Pascal objects. None of those implementation identities are Core semantics.

Portable laws are retained; fd/pointer/goroutine/process identity is not.

## D10

```text
before      398
selected     22
after       420/1024
placed      256
unplaced    164
remaining   604
ratified      0
```

All 22 remain UNPLACED.
