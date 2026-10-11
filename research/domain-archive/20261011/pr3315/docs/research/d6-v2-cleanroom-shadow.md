# D6 v2 clean-room shadow — #3280

Current lower authority: D5 #3305 / Contract 11.3. D6 remains unratified under #3278.

## What is admitted in this shadow

Only the 16 selector descendants whose geometry is forced by the selector composition law:

```text
011000 CDAAAR   011001 CDAADR
011010 CDADAR   011011 CDADDR
011100 CDDAAR   011101 CDDADR
011110 CDDDAR   011111 CDDDDR

100000 CAAAAR   100001 CAAADR
100010 CAADAR   100011 CAADDR
100100 CADAAR   100101 CADADR
100110 CADDAR   100111 CADDDR
```

Everything else starts UNKNOWN in the new D6 coordinate space.

## Donor audit

Old D6 contributes useful semantic donors, but no coordinate authority.

Five historical residents are explicitly excluded from the clean Core candidate until mutation is separately admitted:

```text
RPLACA
RPLACD
SETF
NCONC
NREVERSE
```

They require destructive/generalized mutation that current SENS deliberately does not expose.

The other non-selector donor functions remain UNPLACED candidates. Existing law evidence is preserved separately: parity, LET/LET* binding order, macro expansion closure, numeric order lattice, set lattice, and selectors.

## Metrics

```text
capacity                  64
generated selectors       16
UNKNOWN coordinates       48
unplaced donor candidates 43
mutation donors excluded  5
lower-domain duplicates    0
```

This is not a full D6 proposal and not a ratification. It is the clean baseline from which D6 earns residents.
