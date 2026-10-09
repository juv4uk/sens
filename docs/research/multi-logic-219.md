# #219 — Multiple-valued logic research over knowledge islands

Status: research note, **not a language-law ratification**.

## Current model

```text
islands = observed knowledge / derivations / native kernel results
ocean   = ()  / Canon 0
logic   = an optional projection over observed islands
```

This note deliberately does **not** identify `()` with any truth value.

A logic may project an evidence state to "neither", "unknown", "both", etc., but
that projection happens *after* evidence exists as ordinary data. Canon 0 stays
below the projection.

## Three layers that must remain separate

1. **Multiplicity** — zero, one, or many native results.
2. **Evidence/provenance** — positive/negative observations and their independent derivation paths.
3. **Logic projection** — a named, replaceable interpretation of the evidence state.

No candidate logic is allowed to erase layers 1–2 and then become the source of
truth about what the system "really knows".

## Shared evidence corpus

The machine-readable companion is
`tests/fixtures/multi-logic-evidence-cases.lisp`.

| Case | Evidence before projection | Required preservation |
|---|---|---|
| E0 | no island result | `()` remains Canon-0 ocean |
| E1 | one positive derivation | positive evidence + provenance |
| E2 | one explicit negative derivation | negative evidence + provenance |
| E3 | independent positive and negative derivations | contradiction without explosion/fabrication |
| E4 | three independent positive derivations | multiplicity/provenance remains distinguishable before projection |
| E5 | incomplete search, no result yet | must not be confused with completed "no evidence" |
| E6 | completed bounded search, zero answers | search fact is preserved separately from truth |

## Candidate comparison

### Classical two-valued logic — control baseline

Values: T, F.

Useful as a baseline for domains that are already exact and total. It cannot
directly represent an information gap or simultaneous positive/negative
evidence without an extra convention outside the logic.

**Fit:** poor as the general island-evidence projection; still appropriate for
ordinary exact binary domains.

### Strong Kleene K3

Values are conventionally T, U, F, with U used for an indeterminate/undefined
case. Strong Kleene is a standard three-valued system for truth-value gaps.

For our corpus:

- E1 -> T
- E2 -> F
- E0 could be projected to U *only after* leaving Canon 0 and explicitly asking
  for a K3 view.
- E3 has no distinct "both positive and negative evidence" state; contradiction
  must be collapsed or represented outside K3.
- E4 collapses all positive derivation multiplicity to T.

**Observation:** good gap model, insufficient by itself for simultaneous
positive and negative evidence.

### Priest LP (Logic of Paradox)

LP is a three-valued paraconsistent logic whose middle value can be understood
as both true and false. Contradiction does not entail arbitrary conclusions.

For our corpus:

- E1 -> T
- E2 -> F
- E3 -> B (both)
- E4 -> T after projection, therefore provenance is lost by the projection.
- E0 has no native "neither / information gap" value in LP; `()` must remain
  outside LP or be forced into a value by an extra convention.

**Observation:** good contradiction model, poor standalone model for the ocean /
knowledge-gap distinction.

### Belnap-Dunn FOUR / FDE

FOUR distinguishes four information states that can be represented as two
independent evidence bits:

```text
N = (positive=0, negative=0)
T = (positive=1, negative=0)
F = (positive=0, negative=1)
B = (positive=1, negative=1)
```

This is especially relevant because the standard presentation is naturally
read in terms of positive and negative information about a database/query.
FOUR/FDE is both gap-tolerant and contradiction-tolerant.

For our corpus:

- E1 -> T
- E2 -> F
- E3 -> B
- E0 could project to N, but **N is not identified with `()`**. The former is
  a result of applying the FOUR view to an evidence record; the latter is the
  pre-projection Canon-0 ocean.
- E4 -> T, so derivation count/provenance must remain alongside the projection.

**Observation:** strongest current fit for a *replaceable evidence projection*,
not yet a language constitution.

### FOUR as a bilattice

The standard FOUR bilattice adds two distinct partial orderings:

- a truth ordering;
- an information/knowledge ordering.

That second ordering is important for this project because "more information"
is not the same claim as "more true". Moving from N to T, F, or B can be
described as information growth without pretending that contradiction is
ordinary failure.

**Observation:** the information ordering is architecturally promising for
knowledge islands, but it still does not encode derivation identity or source
provenance. Those remain separate data.

### Łukasiewicz L3 — graded third-value comparison

Ł3 is included as a contrast case: a third value can be interpreted as an
intermediate truth degree rather than an evidence gap or contradiction.

For our evidence corpus this is a weak fit:

- E0, E3, and vague/intermediate truth would compete for the same middle region
  unless extra metadata is retained;
- independent positive/negative evidence is not naturally represented as two
  orthogonal evidence dimensions;
- E4 still collapses provenance.

**Observation:** useful as evidence that "more truth values" alone does not
solve our problem. The semantics of the values matter.

## First comparison matrix

| Candidate | Gap | Contradiction | 0/1/N answers | Provenance | Natural relation to `()` |
|---|---:|---:|---:|---:|---|
| Classical 2 | no | no | external | external | none |
| K3 | yes | no distinct both | external | external | explicit projection to U only |
| LP | no gap value | yes | external | external | none |
| Belnap-Dunn FOUR/FDE | yes | yes | external | external | explicit projection to N only |
| FOUR bilattice | yes | yes | external | external | same as FOUR; adds information order |
| Ł3 | intermediate degree | not as evidence-pair | external | external | no privileged relation |

"external" is intentional: native result multiplicity and provenance are richer
than these truth-value algebras and must not be discarded.

## Current research conclusion

The first pass does **not** select a final logic.

It does establish three useful negative results:

1. K3 alone cannot express the E3 "positive + negative evidence" state.
2. LP alone cannot express the E0 information-gap state without an external convention.
3. No finite truth projection tested here preserves E4 independent derivation provenance.

And one positive hypothesis:

> Belnap-Dunn FOUR, especially viewed as a bilattice, is the strongest current
> candidate for an **optional projection over signed evidence**, because it
> distinguishes neither / positive-only / negative-only / both and separates
> information ordering from truth ordering.

This is not permission to identify `()` with N. The pipeline stays:

```text
() / Canon 0
    ↓ knowledge appears
evidence + provenance + multiplicity
    ↓ explicit named projection
FOUR / K3 / LP / another view
```

## Next executable experiment

Implement only a **data-level projection experiment**, not a new language law:

```text
(evidence POSITIVE-SOURCES NEGATIVE-SOURCES SEARCH-STATE)
        ↓
(project-four evidence)
(project-k3 evidence)
(project-lp evidence)
```

The experiment must prove:

- projection never mutates or replaces provenance;
- E0 stays distinguishable from the projection result N/U;
- E3 is preserved by FOUR and LP but not silently forced into K3;
- E4 projects to T while retaining all three source derivations in the original evidence record;
- incomplete search and completed zero-answer search remain distinct.

## References

- Stanford Encyclopedia of Philosophy, "Many-Valued Logic":
  https://plato.stanford.edu/entries/logic-manyvalued/
- Stanford Encyclopedia of Philosophy, "Paraconsistent Logic":
  https://plato.stanford.edu/entries/logic-paraconsistent/
- Stanford Encyclopedia of Philosophy, "Truth Values" (FOUR bilattice and information ordering):
  https://plato.stanford.edu/entries/truth-values/
- Stanford Encyclopedia of Philosophy, "Liar Paradox" (K3 gaps vs LP gluts):
  https://plato.stanford.edu/entries/liar-paradox/
- N. D. Belnap, "A Useful Four-Valued Logic" / "How a Computer Should Think",
  originally 1977; bibliographic context is listed in the SEP paraconsistent-logic entry.

## Research rule

**Knowledge forms islands. `()` is the ocean. Logic is a replaceable view over
the islands, not a machine for inventing land where none was observed.**
