# #2162 — D4 polarity witness over current Core1

Status: research-only. This report does not ratify D4 codes.

## Question

After #2159 fixed a strong family layout, 16 within-pair orientations remained
tied. This witness asks whether current Core1 behavior gives a concrete reason
for choosing one member of each pair as suffix `0` and the other as suffix
`1`.

Candidate orientation:

```text
0000 APPLY   0001 EVAL
0010 LAMBDA  0011 DEFINE
0110 EVCON   0111 EVLIS
1110 LOOKUP  1111 BIND
```

The selector theorem remains independently fixed:

```text
1010 CAAR   1011 CADR
1100 CDAR   1101 CDDR
```

## Operational evidence from lib/core1.lisp

### LOOKUP / BIND

`C1-LOOKUP` searches existing frames. `C1-BIND` constructs new environment
cells with CONS and recurses over parameters/arguments.

This supports:

```text
1110 LOOKUP
1111 BIND
```

### EVCON / EVLIS

`C1-EVCON` evaluates tests until one branch is selected.
`C1-EVLIS` evaluates the whole form list and explicitly CONS-constructs the
result list.

This supports:

```text
0110 EVCON
0111 EVLIS
```

### APPLY / EVAL

`C1-APPLY` consumes an already-resolved callable and evaluated arguments,
dispatching to primitive or closure mechanism.

`C1-EVAL` performs the broader contextual interpretation path: lookup,
conditional evaluation, lexical binding, argument-list evaluation, then
application.

This supports:

```text
0000 APPLY
0001 EVAL
```

### LAMBDA / DEFINE

The LAMBDA path constructs a callable closure from the current lexical context.
DEFINE is top-level/program-owned and extends the persistent GLOBAL frame with a
new name/value binding.

This supports:

```text
0010 LAMBDA
0011 DEFINE
```

## Weak common polarity

The four pairs are consistent with a weaker operational reading:

```text
0 = operate on / select / use the current resolved focus
1 = continue / construct / expand the surrounding context
```

For selectors, the already-proven theorem has a sharper meaning:

```text
0 = compose CAR
1 = compose CDR
```

Do not replace that theorem with the weaker wording.

## Exhaustive orientation result

With the four source-backed pair preferences above there are `2^4 = 16`
within-pair orientations.

Exactly one orientation satisfies all four current Core1 witnesses:

```text
0000 APPLY   0001 EVAL
0010 LAMBDA  0011 DEFINE
0110 EVCON   0111 EVLIS
1110 LOOKUP  1111 BIND
```

This is an executable source-structure result, not a proof that suffix bit 1
has one universal semantic definition.

## Historical low-nibble check

A naive "compress old Function8 to its low four bits" law fails immediately:

- historical EVAL `01001101` would become `1101`, already proven CDDR;
- historical APPLY `10101111` would become `1111`, colliding with the
  environment lane candidate;
- LAMBDA/DEFINE low nibbles `1000/1001` would place them under CONS and lose
  the stronger QUOTE/syntax family affinity.

So D4 must be derived rather than truncated from the old table.

## Reproduce

```sh
python3 scripts/research-2162-d4-polarity.py
```

Expected headline:

```text
D4 polarity witness: PASS
orientation-space=16
best-operational-evidence-score=4
best-orientations=1
```

## Non-conclusion

This does not yet ratify the map. A semantics-preserving Core1 refactor must be
used as a falsifier: if the orientation evidence disappears under harmless
refactoring, the cross-pair polarity is too implementation-dependent.

## Principle

**Prefer a bit orientation that survives executable behavior, not a verbal
analogy.**
