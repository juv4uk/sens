# #2199 — D5 width lower-bound falsifier

Status: research-only.

## Why this exists

#2193 / PR #2194 proves a semantic lower bound:

```text
ordinary closure -> eager operands
transformer      -> raw operands
```

One undifferentiated call policy cannot satisfy both.

That does **not** yet prove that the minimum new exact-width identity has width 5.

The ratified D4 map still contains:

```text
0101 <unallocated>
1001 <unallocated>
```

and #2158 calls them intentionally unallocated, not permanently impossible.

## Current result

The executable witness enumerates the shorter escape hatches before considering the attractive D5 child:

```text
0101  allocation-only staged role
1001  allocation-only staged role
00101 staged child under 0010 LAMBDA
```

Under the current ratified wording, the two 4-bit models cannot yet be honestly rejected solely from the repository's semantic laws.

Therefore the current theorem state is deliberately:

```text
D5-WIDTH-LOWER-BOUND=NOT-PROVED
```

This is a useful result.  It prevents us from confusing:

```text
00101 is a coherent placement
```

with:

```text
width=5 is mathematically necessary
```

## What would upgrade the result

A later ratified argument must discharge both shorter escape classes:

1. D4 membership is semantically closed, not merely currently full except for two cells; and
2. unrelated allocation-only residency at `0101` / `1001` is forbidden by an admitted law, not by taste.

Only then, if a width-5 staged witness survives, may the script be changed to print:

```text
D5-WIDTH-LOWER-BOUND=PROVED
```

## Reproduce

```sh
python3 scripts/research-2199-d5-width-lower-bound.py
```

## Principle

**A wider domain is necessary only after every shorter honest representation has been falsified.**
