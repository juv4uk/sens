# Universal domain growth through D7 — #3198

Question: what rule can grow D1 -> D2 -> D3 -> D4 -> D5 -> D6 -> D7 without inventing a new global table at each width?

## Universal rule

    D(n+1) = Dn x D1 = { parent||0, parent||1 }
    Q(n+1) = Qn box K2

At every width capacity doubles, every parent gets two children, both old slices preserve all old adjacency, and one new matching edge joins the two copies of each parent.

Capacities: D1=2, D2=4, D3=8, D4=16, D5=32, D6=64, D7=128.

## Complement

The antipode anti_n(x) = x XOR (2^n-1) survives at every width as a geometric automorphism. It is not automatically semantic. A family must prove semantic duality independently.

## Selector positive control

Using the #3196 D3 roots CAR=100 and CDR=011 with local child law 0=A/CAR, 1=D/CDR:

    D3  2 selectors
    D4  4
    D5  8
    D6 16
    D7 32

The family always occupies one quarter of the domain. Inside this family complement remains semantic: it flips every A<->D in the selector path.

Example at D4:

    1000 CAAR <-> 0111 CDDR
    1001 CADR <-> 0110 CDAR

## External sanity check — not authority

The law above is derived without old placement tables. Existing current maps are used only as falsification data.

Prefix-fibre coherence:

    D3->D4 every parent has 2 slots; 6/8 sibling pairs share role
    D4->D5 every parent has 2 children; 13/16 share category
    D5->D6 every parent has 2 children; 29/32 share category

Global complement category coherence:

    D4 3/8
    D5 0/16
    D6 0/32

So prefix/fibre growth is strongly supported as the scalable shape. Full complement is not a universal category law.

## Meaning of the new bit

The appended bit has one universal structural meaning: which child in this parent fibre. Deeper meaning is family-owned. Selectors may prove 0=A and 1=D; another family may prove another binary distinction; UNKNOWN is allowed.

## D7

Pure geometry reaches D7 cleanly: capacity 128, selector subtree 32.

Current repository D7 is instead a role-sensitive Sound7/local-ordinal domain, and its own conformance witness says width-valid does not imply occupancy. Therefore Q7 exists mathematically, but current D7 is not automatically Core.D6 x D1.

Architectural choice: keep current D7 separate, or define a distinct Core.D7 if the Core ladder is meant to continue uninterrupted.

## Recommendation

    UNIVERSAL: Q(n+1) = Qn box K2; child = parent || bit
    GEOMETRY: anti_n(x) = NOT(x)
    SEMANTICS: local family law decides what child-bit and antipode mean

This separation scales through D7 without forcing numerology.
