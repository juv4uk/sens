# #2077 — Foundation-0: exact bounded binary word law

Status: **candidate successor foundation**, research/shadow only.  
This document does not supersede Contract 10 by itself.

## Why this comes before domains, graphs and compilers

The current ratified contract says that the complete function identity universe is exactly 256 eight-bit forms.

The new evidence-driven work needs a weaker, more representation-independent foundation:

> a language identity carrier can be an exact bounded binary word without implying that every such word is a function or that width determines meaning.

That law is required before deciding:
- which domains exist;
- whether root+path is universal or local;
- how graphs explain meanings;
- how the compiler lowers identities;
- how wire framing works;
- whether a word has semantic admission at all.

## Candidate Foundation-0

Let a canonical word be:

```text
w ∈ {0,1}+
```

with an explicit word boundary. Whether the empty bit sequence `ε` is semantically admissible is intentionally unresolved under #2106.

Two words are identical iff every bit and the exact width match:

```text
w1 == w2
iff
len(w1) == len(w2)
and
bits(w1) == bits(w2)
```

Therefore:

```text
1 != 01 != 001
001 != 0010
```

A prefix relation does not collapse identity:

```text
001 prefix-of 0010
001 != 0010
```

## Boundary law

```text
10 001 01
```

is three already-bounded words.

It is not silently reinterpreted as:

```text
1000101
```

Likewise, internal `00` is ordinary word data. It is not an implicit separator.

Transport/source/container mechanisms may encode boundaries, but framing bits/bytes are not semantic bits.

## Epsilon is an open semantic question

At the carrier level, the empty sequence can be represented and round-tripped without contradiction. That does not make it an admitted SENS identity. Excluding it is also not yet derived.

Therefore Foundation-0 carries `ε` mechanically while leaving its semantic admission open to #2106.

## Semantic admission is separate

Syntactic validity does not create meaning.

```text
valid binary word
!=
admitted semantic identity
```

A word may be:
- admitted by a proven law;
- admitted as irreducible residue;
- reserved;
- unknown/unallocated.

Width alone cannot decide which one it is.

This prevents a new accidental ontology such as:

```text
3 bits -> one semantic domain
4 bits -> another semantic domain
8 bits -> functions
```

unless independent semantic evidence later proves such a classification.

## Projection law

A storage/backend projection may be optimized:

```text
width == 8
  -> checked Sens8/u8 projection
```

but that projection is not the language universe.

The executable witness proves:
- exact width-8 projection is reversible;
- non-8-bit words fail the Sens8 projection explicitly rather than being semantically rejected;
- numeric conversion is insufficient as canonical identity because leading zeroes disappear.

## Empty value boundary

Structural `()` is not automatically a binary word.

Foundation-0 deliberately does not decide whether any future admitted word denotes `()`.

That is a semantic theorem/admission problem, not a storage/identity-law consequence.

## Executable witness result

`scripts/research-2077-binary-word-law.py`:

```text
FOUNDATION-0 binary-word witness: PASS
small exhaustive round-trips: 8190
leading-zero distinctness: PASS
prefix-without-equality-collapse: PASS
multi-word boundary round-trip: PASS
internal-00-is-data: PASS
7/8/9 and 64/65 widths: PASS
4096-bit round-trip: PASS
Sens8 checked projection: PASS
numeric-collapse-detected: PASS
semantic-admission-independent-of-width: PASS
```

The witness framing format is intentionally non-authoritative.

## What survives from the SID8 doctrine

Several strong ideas survive unchanged:

- binary identity is not a human name;
- leading zeroes matter;
- host integer/opcode/enum labels do not own language meaning;
- surfaces are projections;
- execution substrates are mechanisms, not semantic authority;
- exact identity must survive round-trip.

Only one premise is challenged:

> exact width 8 as the permanent semantic ceiling.

## Required order before contract transfer

```text
Foundation-0 executable witness
 -> authority conflict inventory
 -> framing proof
 -> width-neutral carrier witness
 -> selector shadow migration
 -> rollback evidence
 -> successor contract ratification
 -> exact8 ontology guard replacement
 -> old exact8-only prose/guards retired
```

Do not reverse this order by making a Rust type or parser change the new law implicitly.

## Principle

**Bits define the word; evidence defines the meaning; machinery only carries or executes it.**
