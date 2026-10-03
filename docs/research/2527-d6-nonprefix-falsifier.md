# #2527 — D6 non-prefix/product/quotient falsifier

Status: research-only.  
Phase: **STRUCTURAL-DISCOVERY**.

## Binary-domain record

```text
DOMAIN        Core D6
BINARY OBJECT four-state binding-policy product; no resident admitted
LAW           two independent commuting refinements form the semantic product
WITNESS       #2511 product square + #2523 local-width lower bound
FALSIFIER     non-prefix / factor / quotient / explicit-residue models
STATUS        theorem-scope attack
RELATION      Core-only
```

## Question

The local theorem says that, under a D4 parent plus independently observable
binary refinements, the shared-location policy needs two local distinctions.
Can another canonical representation preserve the same semantics with less
semantic structure?

The test compares:

1. ordered local path;
2. direct two-factor coordinate;
3. quotient of the two commuting derivation paths;
4. explicit residue/root;
5. arbitrary non-prefix D6 numbering;
6. a deliberately misleading two-bit external table index.

## Result

No tested model reduces the semantic distinction count below the two witnessed
axes while preserving the full four-state algebra without hidden authority.

```text
four observable states
=> two independent semantic axes
=> minimum two local binary distinctions without external table/context
```

A direct factor coordinate can print only the two local factor bits, but that
does not erase either factor. It is a representation of the same product.

A quotient removes duplicate **proof paths**:

```text
scope ; miss
miss  ; scope
```

by using the already-proved commutation law. It does not quotient away either
observable axis.

An explicit residue can name only the final endpoint with an arbitrary token,
but then it no longer represents the four-state product under test.

An arbitrary non-prefix table can encode all four states, but 24 equally valid
permutations exist. The interpretation therefore lives in table authority, not
in a derived coordinate law.

## Semantic / coordinate / accidental classification

This result deliberately reuses the classification discipline from #2494:

```text
two-axis product structure                    semantic-law
parent-prefix + two factor bits               coordinate-law
which semantic axis is printed as 01 vs 10    coordinate-law
arbitrary non-prefix enumeration              accidental-representation
short external table index                    accidental-representation
```

The important invariant is the both-refinements semantic endpoint. Under axis
relabeling the two middle corners exchange, while the endpoint remains the
both-axes corner. That does not make a particular physical bit polarity a
semantic law.

## #2508 standing guard

The same raw bits may occur in another domain. A Q-group-factor `11` is not a
binding-policy `11`. The executable witness rejects cross-domain application
even when the raw bit string is identical.

Therefore:

> semantic law identity never follows from the bit transform alone.

## Non-conclusions

This witness does **not**:

- ratify `001111`;
- admit `001100/01/10/11` into the D6 map;
- choose an axis polarity;
- close historical ingest;
- import Core-Math authority into Core.

The conservative D6 map remains owned by #2422.

## Phase-report line

```text
semantic product law = preserved
coordinate orientation = non-unique under axis swap
non-prefix/table encodings = representation alternatives, not semantic lower-bound falsifiers
```
