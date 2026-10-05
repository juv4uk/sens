# Selector-family forecast under Contract 11.6 — #2322 / #3281

This witness is the current positive control for the CAR/CDR selector family.

It no longer models D3→D8 as one uninterrupted one-bit semantic ladder.

Current authority is:

```text
D3-D6  current selector semantics
D7     current Sound7/Text7 domain
D8     research / unratified
```

The current D3 selector roots from #3202 are:

```text
011 CDR
100 CAR
```

For D4-D6, the admitted selector law appends one choice bit:

```text
0 = compose CAR
1 = compose CDR
```

That yields exactly:

```text
D3  2 selectors
D4  4 selectors
D5  8 selectors
D6 16 selectors
```

## D7 boundary

D7 is not a selector rung. Under #3572 it owns Sound7/Text7 semantics.
Therefore this witness reports zero selector semantic residents in D7 and
never treats a D7 word as a selector parent merely because it has seven bits.

## D8 clean-room candidate

D8 remains research under Contract 11.6 / #3281.

The bounded selector hypothesis tested here is a direct two-step extension:

```text
current D6 selector × W2
        ↓
64 exact D8 coordinate candidates
```

Each current D6 selector receives the four two-choice suffixes
`00 01 10 11`. The resulting set contains 64 unique 8-bit coordinates.

As an independent coordinate check, that set is equal to expanding the current
D3 roots by five selector-choice bits. This equality does **not** introduce D7
semantic ancestry; it is only a second way to enumerate the same bit strings.

Reproduce:

```sh
python3 scripts/research-2322-generative-domain-forecast.py \
  --min-width 3 --max-width 8 \
  --out /tmp/generative-domain-forecast
```

Expected accounting:

| domain | selector coordinates | status |
|---|---:|---|
| D3 | 2 | current |
| D4 | 4 | current |
| D5 | 8 | current |
| D6 | 16 | current |
| D7 | 0 | selector semantics not admitted |
| D8 | 64 | research candidates only |

## Non-conclusions

This witness does not ratify any D8 resident, does not make the 64 candidates
callable, and says nothing positive about the other 192 D8 coordinates.

W8 capacity remains mechanical. Function8/Sens8 history is not semantic
authority.
