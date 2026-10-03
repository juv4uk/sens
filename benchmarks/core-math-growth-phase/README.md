# Core-Math growth-phase tournament (#2431)

This research compares five phase models over the same neutral dependency graph:

- A — static mathematical closure;
- B — naive monotone durable discovered-state;
- C — ephemeral derivation;
- D — cached derivation;
- E — explicit ratified promotion.

It intentionally selects no winner.

The strongest negative control is cache clearing: clearing a mechanism cache must
not change mathematical meaning. Therefore cache population is not semantic
language growth.

The second control is law withdrawal: removing the NEG law invalidates both NEG
and dependent SUB. A naive monotone state that cannot retract them is unsafe
without versioning/revalidation.
