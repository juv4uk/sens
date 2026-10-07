# D10 cross-repo MAL harvest v1

**Issue:** #4053  
**Donor:** `juv4uk/mal/impls/common-lisp/src/core.lisp`  
**Status:** research / unratified

All 62 exported MAL `defmal` builtins are accounted for:

```text
SELECT-D10-CANDIDATE             22
CURRENT-OR-DERIVED-PROJECTION    38
HOLD-SEMANTIC-REVIEW              2
-----------------------------------
TOTAL                            62
```

The strongest new families are:

- mutable reference cells: REF-CELL / REF-CELLP / DEREF / RESET-REF! / SWAP-REF!;
- generic type predicates: LISTP / VECTORP / FUNCTIONP / MACROP / KEYWORDP / MAPP;
- map algebra: MAP-FROM-PAIRS / MAP-DISSOC / MAP-KEYS / MAP-VALUES;
- generic sequence algebra: SEQUENCE-EMPTY? / SEQUENCE-COUNT / SEQUENTIALP / SEQ-VIEW;
- metadata: WITH-META / META;
- KEYWORD construction.

Host-facing `readline` and `cl-eval` remain HOLD. Arithmetic, reader, vector, apply/map, file-read and similar spellings are lower or derived projections.

No MAL implementation detail or address is authoritative. All 22 selected meanings remain UNPLACED.

Result:

```text
D10 = 367/1024
placed = 256
unplaced = 111
remaining = 657
ratified = 0
```
