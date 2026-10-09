# #2755 — D6 input rebase after OD-005

This audit exists because merged #2750 changed the historical D5 evidence
surface after the original #2711 D6 theorem-input gate was frozen.

It deliberately makes **no placement decision**.

Current expected report:

```text
D5-HISTORICAL-ROWS=32
D5-HISTORICAL-UNALLOCATED=0
OLD-D6-D5-BASELINE=8+24+0
SETQ-D5=00111
SETQ-D6-CANDIDATE=D6:001111 (OD-001 owner-ready only)
D5-MISSING-PHASE=32
D5-MISSING-STATUS=32
D5-MISSING-SEMANTIC-RESIDENT=32
RESULT=D6-INPUT-REBASE-REQUIRED
```

The report means only:

1. OD-005 changed the evidence surface;
2. the full historical map does not yet encode the #2414
   HISTORICAL-INGEST vs SENS-DERIVATION distinction per row;
3. the old D6 placement ledger still freezes the pre-OD005 sparse D5 baseline;
4. SETQ currently has both a D5 historical coordinate and a D6 placement claim.

Until those are explicitly reconciled, no D6 occupancy may be inferred from
the new D5 map and the stale SETQ-only replay must remain held.

**Historical occupancy is not automatically semantic parenthood.**
