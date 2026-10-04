# D5 v2 generator shadow — #3284

Research-only candidate after owner reset #3278.

The old D5 APPEND resident is removed because D4:1111 now owns the one admitted APPEND identity (#3287/#3291).

The freed list slot is not filled by another historical convenience. It is filled by an existing SENS generator:

```text
10100  REVERSE
10101  REVERSE-ONTO
```

Local law:

```text
REVERSE(x) = REVERSE-ONTO(x, ())
REVERSE-ONTO(x,y) = APPEND(REVERSE(x), y)
APPEND(x,y) = REVERSE-ONTO(REVERSE(x), y)
```

This is executable evidence from #3293/#3294.

Why this is stronger than NCONC/NREVERSE/LENGTH/NTH:
- NCONC/NREVERSE require destructive pair mutation, intentionally absent from current SENS;
- LENGTH/NTH are useful but do not explain the existing REVERSE/APPEND structure;
- REVERSE-ONTO already implements the stack-safe core law and compresses two other semantics.

The candidate remains 32/32, contains no lower-domain APPEND duplicate, restores deeper selector geometry, and improves one old LOCAL-ALGEBRA block into a SEMANTIC-GENERATOR block.

No global fifth-bit meaning is claimed.
