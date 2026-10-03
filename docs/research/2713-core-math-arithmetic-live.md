# #2713 — typed exact-Q arithmetic live witness

Status: research/integration only.

This witness connects an already-proved Core-Math factor law to the existing
exact SENS rational execution mechanism without claiming shared binary identity.

## Typed split

```text
Core-Math.QGroupFactor:
  0   additive family
  1   multiplicative family
  10  multiplicative inverse role (RECIP)

Core execution bridge:
  00001100  existing exact ADD execution
  00001110  existing exact MUL execution
  00001111  existing exact division execution; unary form supplies reciprocal
```

The two columns are **not the same domain**. The bridge is explicit and typed.

## Minimal basis

Only three bridge entries are admitted by this witness:

```text
ADD
MUL
RECIP
```

Derived behavior is constructed, not looked up:

```text
NEG(x)   = MUL(-1, x)
SUB(x,y) = ADD(x, NEG(y))
DIV(x,y) = MUL(x, RECIP(y))
```

No bridge rows exist for NEG/SUB/DIV.

## Exact corpus

```text
2 + 3       = 5
1/2 + 1/3   = 5/6
(-2) * 3    = -6
recip(2)    = 1/2
5 - 8       = -3
6 / 4       = 3/2
recip(0)    = UNDEFINED-MATHEMATICALLY
```

The executable source forms use exact binary Core execution identities in
function position rather than `+`, `-`, `*`, `/` or English names.

## Domain firewall

The witness proves complementarity only:

```text
Core-Math operation law
  -> typed bridge
  -> existing Core exact arithmetic mechanism
  -> exact rational value
```

It does not prove:
- shared Core/Core-Math binary identity;
- D5 or D6 arithmetic residency;
- historical LISP 1.5 arithmetic semantics;
- a six-independent-operation table.

The historical LISP 1.5 fixed-point RECIP rule remains a negative control:
fixed-point reciprocal is historically zero, while exact-Q reciprocal is a
different law.

## Principle

**Use three proved arithmetic capabilities and generate the familiar
conveniences; do not spend Core coordinates to mirror vocabulary.**
