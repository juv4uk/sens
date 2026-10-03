# D6 historical-unplaced handoff (#2678)

This lane joins historical unresolved rows to current SENS evidence without
allocating a D6 coordinate.

Inputs are all existing machine-readable evidence:

- #2344 historical ledger;
- #2660/#2661 D6 unknown frontier;
- #2677/#2685 same-base parent tournament;
- #2679/#2683 domain firewall;
- #2663 non-local-exit exact-domain falsifier.

The output asks one narrow question for each historical unresolved row:

```text
historical fact
+ current semantic class
+ domain evidence
+ placement evidence
-> KEEP-UNPLACED unless an independent theorem exists
```

SET/SETQ, PROG, RETURN, FEXPR, FSUBR and historical TRANSFORMER are all
historical facts worth preserving. Their historical presence, names, order, or
proximity to free D6 coordinates are not placement authority.

Success is deliberately negative: all seven rows stay unplaced unless some
independent merged theorem says otherwise.
