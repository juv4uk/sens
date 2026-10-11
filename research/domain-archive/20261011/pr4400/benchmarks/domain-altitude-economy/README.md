# Domain Altitude Economy — #4394

Research-only benchmark for the Pareto frontier between semantic altitude and canonical semantic source-bit cost.

This directory deliberately does not define semantic meaning. It consumes provenance-bound measurements from the existing exact-width authority and reports representation economics only.

## Axes

- semantic_altitude_max_width: first proxy; maximum exact source width used.
- semantic_bits: canonical whole-program semantic source-bit measure from #4367/#4372. The runner never re-derives domain width.
- result_digest: execution-result digest. Candidate forms are comparable only when digests match exactly.

Program A dominates B iff A.semantic_altitude_max_width <= B.semantic_altitude_max_width and A.semantic_bits <= B.semantic_bits, with at least one strict inequality.

Equal-axis trade-offs remain on the Pareto frontier.

## Residency dividend

dividend_bits = expansion_semantic_bits - resident_semantic_bits

Aggregate per resident/corpus by summing that quantity only after the result digest equality gate.

Positive values mean the resident form is semantically denser in this corpus. They are not evidence for changing residency or authority.

## Input contract

The runner consumes a JSON manifest whose rows are already measured by the canonical source-bit pipeline. See schema.json.

A row must include resident and expansion semantic bit counts, resident and expansion maximum widths, one execution-result digest shared by both forms, and provenance for the authority/measurement source.

The manifest may also carry optional Cachegrind rows. Dynamic instruction measurements are reported separately from the static Pareto axes.

## First corpus

Candidate residents must be selected from repository evidence with a trustworthy lower-domain expansion/derivation. Names such as MEMBER and APPEND are examples only; selection is evidence-driven, not hand-authored from semantic intuition.

The initial target is about 20 D8/D9 residents across at least three distinct program corpora.

## Boundaries

This benchmark does not add, remove, or reassign residents; change D1-D9 authority; treat Rust, Cachegrind, or the runner as semantic authority; mix framing or byte-container slack into semantic payload bits; or choose a single universal optimum.

The optimizer/compiler may later choose among non-dominated projections for a target, but that remains a mechanism decision downstream of SENS authority.
