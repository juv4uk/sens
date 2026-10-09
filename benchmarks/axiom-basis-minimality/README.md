# Axiom basis minimality (#3420)

This probe treats the initial constants as candidate primitive knowledge roots
and attacks hidden-premise/circularity assumptions.

## Mathematical result

Using the **current ratified D5 arithmetic function numbers**

```text
01010
01011
10110
10111
```

and exact rational arithmetic, the required bounded seed closure

```text
{-2,-1,-1/2,0,1/2,1,2}
```

does **not** require all three candidate constants `{-1,0,1}`.

Under this operation set, a single nonzero unit seed is sufficient:

```text
{-1}  sufficient
{ 1}  sufficient
{ 0}  insufficient
```

This is deliberately relative to the operation basis. If DIFFERENCE or
QUOTIENT is later derived rather than primitive, the constant-minimality proof
must be rerun to avoid circular reasoning.

## World result

The probe reads the current `lib/si.lisp` and `lib/si-derived.lisp`
sources and performs source-level remove-one dependency accounting.

Current exact-derived corpus exercises:

```text
h   -> 5 derived constants
e   -> 5
k   -> 1
N_A -> 3
```

while:

```text
ΔνCs -> 0
c    -> 0
K_cd -> 0
```

inside the current `si-derived` corpus.

Zero consumers does **not** mean those SI defining axioms are redundant. It
identifies an application gap: they need explicit MODEL_LAW / OBSERVATION
witnesses such as the world-reasoning lanes already tracked in #3402/#3397.

The benchmark creates no parallel constant authority; the repository sources
remain the inputs.
