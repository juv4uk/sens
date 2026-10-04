# Exact-Q constant bootstrap — #3374

Core-Math now has a ground layer.

## Ground constants

```text
-1  -> #q2:-1/1
 0  -> #q2:0/1
 1  -> #q2:1/1
```

These are exact mathematical values already representable in the repository.
They do not require a prior function definition.

## First function numbers

The witness characterizes current ratified D5 arithmetic numbers by their
action on the ground constants:

```text
01010
01011
10110
10111
```

Human names are validation projections only.

The complete 3×3 seed grid gives distinct extensional signatures for all four
function numbers.

## Growth from constants

The old seven-point Core-Math corpus is no longer treated as seven independent
premises:

```text
{-2,-1,-1/2,0,1/2,1,2}
```

Starting from only `{-1,0,1}`:

```text
2    = 01010(1,1)
-2   = 01010(-1,-1)
1/2  = 10111(1,2)
-1/2 = 10111(-1,2)
```

So 3 ground constants generate the other 4 witness constants.

## Operations derived from constants

On the generated seven-point corpus:

```text
NEG(x)   = 10110(-1,x)
RECIP(x) = 10111(1,x)
SUB(x,y) = 01010(x,10110(-1,y))
DIV(x,y) = 10110(x,10111(1,y))
```

The executable probe checks exact agreement with current arithmetic and keeps
division by zero explicitly undefined.

This gives Core-Math a non-circular growth direction:

```text
exact constants
  -> function behavior on constants
  -> generated exact values
  -> derived laws
  -> wider mathematics
```

The SI constants in `lib/si.lisp` are a later large exact-Q stress corpus,
not foundational axioms.
