# D6 ratification non-contagion — #2725

Independent guard around owner decision OD-001 / #2723.

The guard accepts both legal phases:

- PRE: 16 selector-generated residents, 0 manual residents, 48 UNKNOWN; `001111` remains nonadmitted.
- POST: 16 selector-generated residents, exactly one manual resident at `001111`, 47 UNKNOWN.

It rejects automatic residency of:

- `001100` (parent duplicate),
- `001101` / `001110` (proof/middle corners),
- any of the 44 PURE-UNKNOWN coordinates,
- SET, RETURN, FEXPR, FSUBR, or TRANSFORMER through historical-name transfer.

The guard does not implement ratification and does not search free coordinates.
