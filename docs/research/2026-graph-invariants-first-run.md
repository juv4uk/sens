# #2026 — name-erased typed graph invariants, first run

Status: research-only analysis on the #1962 Lisp I / Lisp 1.5 corpus.

## Input

- 34 semantic/research nodes
- 129 typed directed edges
- relation types from the current corpus such as `composition`, `structure`, `derivable`, `recursion`, `calls`

Primary refinement deliberately excludes:
- human node names as color inputs;
- seed3 / prefix bit codes;
- historical slot numbers.

Several modes add only non-name research metadata (`kind`, `era`, `prefix_evidence`) to test whether the topology itself is sufficient.

## First result

```text
mode                    classes  unique  collision cells
topology                   32       30       2
kind                       32       30       2
kind+era                   32       30       2
kind+era+evidence          32       30       2
```

The same two collision cells survive every name-erased mode:

```text
{lambda, label}
{caddr, cdar}
```

Both are also exact swap automorphisms of the current typed graph.

The call/recursion subgraph reproduces the expected non-trivial SCCs:

```text
{eval_lisp1, evcon_lisp1, evlis_lisp1}
{apply_lisp15, eval_lisp15, evcon_lisp15, evlis_lisp15}
```

## Strong falsifier 1 — ordered composition is missing

`CADDR` and `CDAR` are semantically distinct selector compositions.

The current graph records each through generic `composition` relations to CAR/CDR, but does not preserve enough ordered/multiplicity information to distinguish:

```text
CADDR = CAR ∘ CDR ∘ CDR
CDAR  = CDR ∘ CAR
```

Therefore:

> an unordered typed dependency graph is insufficient as a self-description proof substrate for selectors.

This is not evidence that names or bit codes should be injected. It is evidence that the relation kernel needs an **ordered proof/generator relation** (or equivalent certificate) when order is semantic.

This directly supports the separation:

```text
dependency graph
!=
canonical semantic proof path
```

## Strong falsifier 2 — binding semantics are under-described

`LAMBDA` and `LABEL` remain exact structural swap automorphisms even with `kind/era/prefix_evidence` metadata.

The current graph therefore does not encode the semantic distinction between:
- ordinary binding/function abstraction;
- recursive naming/binding.

Again the correct response is not a name-based tie-breaker.

The relation kernel needs evidence that represents the actual semantic distinction, for example a future derived/typed relation such as recursive binding — but #2023 must derive the minimal form rather than allocate an English relation name by fiat.

## Important positive result

30/34 corpus nodes become structurally unique under typed refinement without names or binary codes.

That is substantial evidence that the existing typed relations already carry significant semantic information.

But uniqueness is only **distinguishability evidence**, not proof of:
- semantic identity;
- necessity;
- canonicality.

## Automorphism result

Within stable WL cells there are exactly four automorphisms in the bounded search:

```text
identity
swap(lambda,label)
swap(caddr,cdar)
swap both pairs
```

So the two collisions are not merely a limitation of one WL refinement implementation: they are genuine symmetries of the current typed graph.

## Consequence for self-description

A self-describing SENS graph needs at least two kinds of information currently missing:

1. ordered/multiplicity-sensitive construction evidence for selector composition;
2. a real semantic distinction for recursive vs non-recursive binding forms.

This argues against a single generic `depends-on` relation as sufficient language knowledge.

## Consequence for #2034 automaton countermodel

Execution-state minimization is allowed to merge control states even when semantic identities differ.

Graph self-description is not.

Therefore automaton-state equivalence and semantic-graph equivalence must remain separate notions.

## Principle

**If two meanings are exact automorphisms of the name-erased graph, the graph does not yet contain the fact that distinguishes them.**
