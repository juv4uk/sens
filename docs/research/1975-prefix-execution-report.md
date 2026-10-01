# #1975 — first root+suffix execution witness

Research-only. No runtime/contracts/function-table change.

## Result

The proven selector family can be executed from:

```text
root mechanism + suffix bits
```

without one execution row per descendant.

Current bounded examples:

```text
1010     CAAR
1011     CADR
1101     CDDR
10111    THIRD-path
101111   FOURTH/CADDDR-path
1011111  FIFTH-path
```

The execution engine knows only:

```text
root 101 -> CAR
root 110 -> CDR

suffix 0 -> compose inner CAR
suffix 1 -> compose inner CDR
```

For a word such as:

```text
1011
```

the operations are stored outer-to-inner:

```text
CAR ∘ CDR
```

and therefore applied to data inner-to-outer.

## Parity method

`scripts/research-1975-prefix-execution.py` mechanically parses current
`lib/core.lisp` selector definitions and direct aliases.

The current source is used only as a parity oracle. The research executor
never looks up a descendant by name or by legacy Function8 row.

Three full binary-tree fixtures were used, plus domain-error controls.

## Live result

See `docs/research/1975-prefix-execution-run.txt`.

Summary:

```text
root mechanisms:                  2
suffix actions:                   2
bounded current names checked:    8
unique execution paths:           6
descendant execution lookup rows: 0
semantic nodes quotiented:        0
```

## What this proves

For the already-proven selector family, a binary word can be executable
structure rather than merely an address.

It is possible to reconstruct descendant behavior from a small root law
plus suffix bits.

## What this does NOT prove

It does not prove:
- that second and cadr are the same semantic identity;
- that fourth and cadddr must be one semantic node;
- that QUOTE/ATOM/EQ/CONS/COND have comparable generators;
- that production runtime should delete current rows yet;
- that the same framing should be used on raw wire.

Those remain owned by #1964/#1966/#1968/#1971.

## Deletion opportunity

This witness shows that **execution dispatch rows for derived selector
paths are not logically necessary** inside a generator-based executor.

Whether semantic registry rows remain for distinct meanings is a separate
question.

That distinction is essential:

```text
share execution machinery
!=
merge semantic nodes
```

## Next falsifier

Extend only after independent review:
- deeper randomly generated selector words;
- differential parity against generated nested CAR/CDR source;
- measure path-execution overhead vs current fixed-row lookup;
- cache only if evidence shows it helps.

Do not generalize to non-selector roots until #1968 supplies a positive law.
