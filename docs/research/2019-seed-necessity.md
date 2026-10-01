# bīja3 necessity / reconstruction / smuggling (#2019)

**Agent:** grok-xai  
**Status lock:** every seed remains **premise** (#2018). This document does **not** upgrade status.  
**Not:** corpus pressure (#2031) · pure-graph pressure (#2035) · blind WSM (wsm#12)

## Question

```text
Can each seed be removed, reconstructed, or replaced
without smuggling an equivalent root back in?
```

Pressure maps answer “what depends on this in a graph”.  
This matrix answers “what *kind* of authority is at stake”.

## Capability classes

| class | seeds | role |
|-------|-------|------|
| ground_value | NIL | canonical empty / ground data |
| evaluation_control | QUOTE | suspend evaluation |
| type_predicate | ATOM | atom vs pair |
| identity_predicate | EQ | sameness |
| pair_constructor | CONS | build pairs |
| pair_destructor | CAR, CDR | projections + local generator |
| conditional_control | COND | controlled branch |

These classes are **labels for attack**, not allocated relation IDs (#2023).

## Hard observations (bounded, not theorems)

1. **CAR/CDR** — do not prioritize *deletion*. The open attack is *over-generalization* of the suffix generator, not removing the roots. Economy and I-refs already favor keeping them as roots of a family.

2. **CONS** — dual introduction form. A basis with CAR/CDR and no CONS is not a closed pair calculus unless construction is smuggled via host.

3. **QUOTE** — suspend-evaluation is a *kind* of capability (G4 boundary in language-core-axioms: not every power is computational composition). Classical reconstructions still need a quote barrier. High priority for alternative-basis *stories*, low confidence for “derive from CAR/CDR”.

4. **COND** — control root, not Boolean. Falsified AND/OR children do not remove COND; they block a cheap specialization.

5. **NIL** — may be data/racanā rather than operator seed. Open: whether `000` must sit in the *operator* bīja3 at all.

6. **ATOM / EQ** — predicates; tree equality needs EQ at leaves. Selector-style children for EQ already constrained by #2017.

## Smuggling test (required for any “derivation” claim)

A proposed reconstruction **fails** if it:

- reintroduces the same control under a new name;
- moves the power into undocumented host behavior;
- uses a falsified inference rule (Hamming rank, unordered support as parentage, SCC as meaning, …).

## Priority for alternative-basis work

```text
high     QUOTE, EQ, CONS, COND   — different capability classes; easy to fake-derive
medium   NIL, ATOM               — data/type boundary questions
low      CAR, CDR                — keep; attack generalization/certificates instead
```

## Explicit non-upgrades

| claim | allowed? |
|-------|----------|
| bīja3 is minimal | **no** |
| bīja3 is derived | **no** |
| CAR/CDR may stay roots under attack | descriptive only |
| variable-width works ⇒ seed minimal | **forbidden** (#2017 constraint) |

## Next honest steps

1. For QUOTE/COND: write one alternative basis *hypothesis* with full smuggling audit (still conjecture).
2. Consume #2031/#2035 only as prioritization, never as necessity.
3. Blind WSM (wsm#12) after freeze — compare distinctions, not codes.
4. Only then touch #2018 status cells.
