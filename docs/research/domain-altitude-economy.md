# Domain-altitude economy

Дослідницький принцип з #4394 (без зміни семантичного authority, координат,
резидентності чи компіляторного значення). Оптимізація програми SENS — це
**двоосьова проблема Парето**, не скалярна ціль. Перша вісь — **семантична висота**
(початковий проксі: `max_width_used(program)`); друга — **бітова економність**
(`semantic_bits(program)` з SENS-власної правільної «лінійки» #4367/#4372). Програма A
домінує B лише коли висота й біти обидва ≤ з хоча б однією строгою нерівністю; коли
одна вісь покращується за рахунок іншої — обидва кандидати лишаються на Парето-фронті.
Свідомо немає універсального зваженого балу.

## Status

Research-only principle from #4394. This document does not change semantic
authority, domain coordinates, residency, or compiler meaning.

## Principle

Program optimization in SENS is a **two-axis Pareto problem**, not a scalar
objective.

The first axis is **semantic altitude**. The initial measurable proxy is:

`max_width_used(program)`

A later research phase may add a provenance-bound derivation-distance metric,
but derivation depth must remain separate from the width proxy.

The second axis is **bit economy**:

`semantic_bits(program)`

This must come from the canonical SENS-owned ruler (#4367/#4372). Framing bits,
tail-unused bits, byte padding, and total wire size remain separate accounting
layers (#2189/#2833).

Program A dominates program B only when:

`altitude(A) <= altitude(B)`
and
`bits(A) <= bits(B)`

with at least one strict inequality.

When one axis improves while the other worsens, both candidates remain on the
Pareto frontier.

There is intentionally **no universal weighted score** such as:

`a * altitude + b * bits`.

A target mechanism may choose among non-dominated projections later. Such a
choice is mechanism evidence, not semantic authority.

## Equivalence gate

A comparison is legal only after both candidates execute successfully and
produce the same result digest:

`digest(execute(A)) == digest(execute(B))`

Source resemblance, names, AST similarity, or intended meaning are not enough.

## Residency dividend

For a D8/D9 resident `r`, over a fixed provenance-bound corpus:

`dividend(r) = sum(D3_expansion_bits(program) - resident_bits(program))`

A positive value means the resident saves semantic source bits relative to its
validated D3 expansion over that corpus.

Zero or negative dividend is **research evidence only**. It does not remove,
demote, or invalidate the resident.

## Dynamic evidence

Optional Cachegrind instruction counts are a separate mechanism axis.

They may answer questions such as:

- whether the static representation frontier predicts execution work;
- whether a shorter semantic representation has lower or higher instruction cost;
- where a static Pareto ordering needs to be described as representation-only.

Dynamic instruction counts never override SENS semantic identity.

## Current experiment boundary

The first cohort is maintained in:

`benchmarks/domain-altitude-economy/corpus-v1.json`

The cohort is provenance-bound and deterministic. Every row must eventually
carry:

- exact D8/D9 identity provenance;
- a trustworthy D3 expansion or an explicit blocked status;
- an executable equivalence witness;
- equal result digests before comparison;
- exact semantic bit counts from the existing ruler.

The benchmark must remain descriptive. It is not a residency-selection or
semantic-removal mechanism.

## Research outputs

The intended machine-readable result is:

`evidence/d8-residency-dividend.tsv`

with separate fields for:

`semantic_bits_d3`
`semantic_bits_resident`
`max_width_d3`
`max_width_resident`
`pareto_status`
`residency_dividend`

Optional dynamic fields belong in a separate mechanism layer.

## Falsifiers

The principle should be weakened or rejected if:

1. equivalent projections cannot be reproduced by result digest;
2. the max-width proxy is not stable enough to produce a meaningful frontier;
3. static dividends change when only framing/padding changes;
4. dynamic execution routinely reverses static ordering in a way that makes
   static claims need an explicit representation-only qualification.

The correct negative result is valuable: this wing exists to measure the
economics of the vocabulary, not to prove that every resident is economical.
