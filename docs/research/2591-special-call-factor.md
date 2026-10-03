# #2591 — special-call protocol factorization

Phase: **STRUCTURAL-DISCOVERY**  
Domain: `Core.PostD4.SpecialCallProtocol`  
Binary object: **UNPLACED**

This report factors historical FEXPR/FSUBR, Hart MACRO, and current SENS
TRANSFORMER observations without inferring a width or coordinate.

## Five independently observable protocol axes

```text
A raw-form input
B explicit caller environment
C returned-form / caller re-evaluation
D expansion timing / locus
E invocation packaging (whole-call vs operands-only)
```

A/B/C are separated by the bounded eight-corner protocol cube (#2522/#2530).
D is separated by the OLD-vs-NEW definition/evaluation-time witness
(#2568/#2569). E is separated by the alias/head collision witness
(#2580/#2588, merged as 3d409736...).

Independent observable **axis** does not mean semantic root, bit, width, or
resident.

## Protocol matrix

```text
                       raw  caller-env  returned-form  timing           packaging
ordinary LAMBDA         0       0           0         evaluation       operands-only
FEXPR/FSUBR             1       1           0         evaluation       operands-only
Hart MACRO              1       0           1         definition       whole-call
SENS TRANSFORMER        1       0           1         evaluation       operands-only
```

## Important parent result

Current TRANSFORMER has strong same-base evidence with D4 LAMBDA (#2198/#2200):
the staged value preserves the same closure payload.

But the observable protocol difference from ordinary LAMBDA is not one delta:

```text
LAMBDA -> TRANSFORMER
  eager input  -> raw input
  direct value -> returned form / caller re-evaluation
```

The A/B/C cube proves these two dimensions are separable: raw input can exist
with direct-value result (historical FEXPR corner), so they cannot be collapsed
into one observable delta merely because one implementation packages them in a
single Macro value.

Therefore the archived `00101 TRANSFORMER` proposal is **not reusable as a
proved one-bit child** under #2236's current parent+one-delta law.

This does not prove TRANSFORMER needs D6. Axis count does not imply width.

## Remove-one attacks

- Remove raw-form input: unused undefined syntax becomes eager/fails.
- Remove explicit caller-env: caller-only binding disappears.
- Remove returned-form protocol: a returned symbol/form stays a value instead
  of executing/resolving in caller context.
- Remove timing: redefining a transformer can no longer separate Hart OLD from
  current SENS NEW behavior.
- Remove whole-call packaging: aliases with equal operands collide and the call
  head cannot be reconstructed.

## Structural verdict

```text
independently observable protocol axes = 5
proved semantic roots                 = 0
proved D5 children                    = 0
proved D6 children                    = 0
width                                 = UNKNOWN
coordinates                           = 0
```

The correct next question is which axes survive SENS derivation as independent
semantic roots and whether any surviving root has a proved same-base parent
with exactly one delta.

## Principle

**Factor observations first. A protocol cube is not a binary address map.**
