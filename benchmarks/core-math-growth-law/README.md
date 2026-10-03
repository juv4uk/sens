# Core-Math growth-law research (#2425)

This benchmark formalizes the first bounded growth event using the neutral IR
from #2427 and the exact-Q positive control from #2433.

It intentionally distinguishes:

- **recursive declared closure — WITNESSED**: admitted rules generate NEG/DIV at
  depth 1 and SUB at depth 2, with SUB depending on generated NEG.
- **autonomous enumerative growth — NOT YET PROVED**: the current neutral spec
  still contains one declared generation rule for each generated result.

This distinction prevents “three names have formulas” from being overstated as
a language that autonomously discovers its entire closure.

Out of scope:
- minimal basis (#2426);
- growth phase/cache/persistence semantics (#2431);
- final operation identity (#2435).
