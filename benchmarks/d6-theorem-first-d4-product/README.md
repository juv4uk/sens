# #2700 — current D4 + two-delta D6 product census

This witness protects an important distinction:

```text
two observable deltas
!=
proved two-bit product coordinate
```

Current controls:

- **DEFINE → shared-location update**: the already-known positive product control
  from #2511/#2518.  Its `001111` residency question is isolated in #2538.
- **LAMBDA → current TRANSFORMER**: at least two separable protocol deltas are
  observed, but #2591 does not prove independently specified middle corners,
  commutation, or an exact D6 generator.  Therefore it is a negative control
  for the shortcut “two axes ⇒ D6”.

The benchmark consumes the current post-D4 eligibility ledger and intentionally
fails if new D4+two-delta families appear without explicit review.

Expected result:

```text
RESULT=NO-NEW-D4-TWO-DELTA-FAMILY
```

The gate also consumes merged #2705 `post-d4-semantic-placement/placement.json`.
Across all 19 completed historical rows, the only `candidate_coordinate` is the
already-isolated SETQ `D6:001111` owner-ready candidate. Any additional placement
candidate makes this gate RED and requires fresh theorem review.
