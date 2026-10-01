# #2175 — D5 selector subtree and residue

Status: research-only.

This witness establishes only the exact 5-bit selector descendants already
implied by the admitted CAR/CDR generator.

## Generator-owned D5

```text
10100 CAAAR
10101 CAADR
10110 CADAR
10111 CADDR

11000 CDAAR
11001 CDADR
11010 CDDAR
11011 CDDDR
```

They follow from the same local theorem used at D4:

```text
append 0 -> compose CAR
append 1 -> compose CDR
```

Examples:

```text
1010 CAAR
  +0 -> 10100 CAAAR
  +1 -> 10101 CAADR

1101 CDDR
  +0 -> 11010 CDDAR
  +1 -> 11011 CDDDR
```

## Capacity

Exact width=5 has:

```text
32 total words
8 generator-owned selector words
24 residue words
```

The 24 residue words are **unallocated**. They are not "free functions" and
receive no meaning from this report.

## Important boundary

The selector suffix law is local:

```text
selector family:
  0 = compose CAR
  1 = compose CDR
```

It must not be generalized to all D5 words without new evidence.

Likewise:

```text
prefix relation != semantic parenthood
```

A future macro/staging capability from #2173/#2174 may receive a D5 identity
only after its role is admitted and #2175 placement work evaluates the residue.

## Reproduce

```sh
python3 scripts/research-2175-d5-selector-residue.py
```

Expected headline:

```text
D5 selector/residue witness: PASS
width=5
capacity=32
generator-owned=8
residue=24
```

## Principle

**Generated cells are occupied by proof; residue stays empty until evidence
earns an address.**
