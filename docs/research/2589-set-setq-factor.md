# #2589 — SET / SETQ mutation-factor witness

Status: STRUCTURAL-DISCOVERY, research-only.

## Result

The bounded executable model factors the historical pair as:

```text
SETQ = syntax-fixed target
     + nearest-existing / fail shared-location update

SET  = D4 target evaluation
     + the same nearest-existing / fail shared-location update
```

After target normalization, the mutation observations are identical for:

- inherited binding update;
- nearest-shadow selection;
- missing-binding failure;
- resulting cell identity/value change.

A different evaluated target changes which location is selected, demonstrating
that target acquisition is independently observable, but it does not change the
mutation law.

## Width consequence

The local D6 pressure established for the SETQ shared-location core remains
evidence about the **mutation factor** under the D4 DEFINE + two-delta placement
model.

It does not, by itself, assign a D6 coordinate to historical SET:

```text
shared mutation factor       -> reuses SETQ-core evidence
SET target acquisition       -> composable with admitted D4 evaluation
SET surface width            -> UNKNOWN / UNPLACED
new coordinate               -> none
```

A future placement claim for SET must still prove a same-base binary
generator/quotient law. Historical name similarity is not placement evidence.

## Domain firewall

The witness carries an explicit negative control: a Core-Math target is rejected
before the Core mutation factor runs. Equal-looking bits or transforms cannot
transfer semantic identity across domains (#2508).

## Non-conclusions

- no `001111` residency decision;
- no SET resident;
- no production mutation implementation;
- no claim that D6 is a global information-theoretic minimum;
- no claim that target-evaluation policy is itself a new post-D4 root.
