# #2117 — proposition co-reference beneath fact status

Research-only.

## Witness

Use the same three evidence occurrences:

```text
e1 : support
e2 : refute
e3 : support
```

Only change which occurrences are judged to concern the same proposition.

### Model A
```text
{e1,e2} -> BOTH/conflict
{e3}    -> supported
```

### Model B
```text
{e1,e3} -> supported
{e2}    -> refuted
```

### Model C
```text
{e1} -> supported
{e2} -> refuted
{e3} -> supported
```

The raw occurrence stream and polarity markers are identical in all three models.

Therefore proposition-level support/refutation/conflict is not determined until a **co-reference partition/relation** says which evidence occurrences are about the same proposition.

## Consequence

#2112's `ADMITTED/REFUTED/UNKNOWN` status layer already assumes a proposition identity/co-reference layer beneath it.

That layer must not be implemented by host string equality, table row identity, file location, or overwrite semantics without proof.

## Open question

The witness does not yet prove co-reference must be a full equivalence relation. Ambiguous, context-indexed, or partial co-reference remains open.

## Principle

**Before truth status, establish subject-matter identity: evidence can conflict only after we know it concerns the same proposition.**

Artifact: `scripts/research-2117-proposition-coreference.py`.