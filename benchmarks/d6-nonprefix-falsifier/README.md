# D6 non-prefix falsifier (#2527)

Research-only representation attack on the merged #2511 binding-policy square.

It compares five models of the same four semantic states:

1. canonical D4-parent + two suffix bits;
2. typed two-factor coordinate;
3. quotient of derivation paths under commutation/idempotence;
4. explicit opaque residue table;
5. arbitrary global 2-bit numbering.

The checker separates:
- semantic distinction count;
- coordinate-law choice;
- printed payload width;
- external domain/parent context;
- table/index authority.

A shorter printed code does not falsify the two-axis semantic lower bound if the
missing information moves into a table or type/domain context.

No Core residency or D6 map mutation occurs here.
