# #2023 selector relation-kernel reduction — first bounded result

Status: research-only. No relation codes, production semantics, runtime or compiler changes.

## Corpus

Input is the current #1962 bounded Lisp I / Lisp 1.5 node corpus from draft #1963.

Selector scope:

```text
101  CAR root
110  CDR root

1010
1011
1100
1101
10110
10111
```

Human operation names are not used by the executable reconstruction law.

## Live result

Executed on WSL against commit `a6a19b507b818acc07619a6b56daac904b53252a`.

```text
K0 flat explicit              20 stored per-node relation facts
K1 parent + edge              12 stored per-node relation facts
K2 parent only                 6 stored per-node relation facts
K3 intrinsic bits + law        0 stored per-node relation facts

family-law facts retained      2
```

The two retained family-law facts are:

```text
0 -> 101
1 -> 110
```

## Why K3 works locally

For an admitted selector word `w`:

```text
root(w)   = first 3 bits
parent(w) = drop last bit
edge(w)   = last bit
suffix(w) = bits after root
```

Therefore these are not independent stored semantic graph facts for this family.
They are deterministic projections of the canonical bounded binary identity.

Execution schedule is then reconstructed by the fixed local action:

```text
0 -> 101
1 -> 110
```

Example:

```text
10111
root   = 101
suffix = 11
schedule = 101,110,110
```

## What this deletes if it survives

For the selector family only:

- per-node `root-of` facts;
- per-node `prefix-parent` facts;
- per-node `edge-bit` facts;
- per-node mechanism-available facts;
- a duplicated execution-relation layer over information already present in the word.

This does **not** delete:
- the semantic identities;
- the canonical binary words;
- the two local action laws;
- typed evidence that this family law is valid.

## Negative control

Current CONS-family candidates `list` and `append` have no proven prefix word in the #1962 corpus.

Therefore K3 cannot reconstruct:

```text
parent
edge
root+suffix path
```

for them.

They remain outside this theorem. The selector result is deliberately not generalized.

## Architectural consequence

For strong generative families, the semantic graph need not duplicate relations that are already intrinsic to identity geometry.

A smaller split becomes possible:

```text
canonical word
  -> intrinsic lineage

small family law
  -> execution/proof action

typed graph
  -> only non-intrinsic semantic relations/evidence
```

This is compatible with the #2034 transducer result: execution control may be delegated to a small machine while the graph retains only semantic evidence that cannot be derived mechanically.

## Non-conclusions

This does not prove:
- that every SENS family has intrinsic prefix relations;
- that the global relation kernel has one primitive relation kind;
- that bīja3 is minimal;
- that typed dependency/call/control relations are redundant;
- that graph self-description is unnecessary.

## Next falsifiers

1. apply the same reduction to a non-selector positive family if one is ever proven;
2. test a recursive/SCC case where relation information is not encoded in the word;
3. let #2026 test whether name-erased graph distinguishability worsens after removing intrinsic selector edges;
4. let #2024 test whether proof certificates need any selector graph edge beyond the word + family law.

## Principle

**Do not store as a semantic relation what the canonical identity already proves mechanically.**
