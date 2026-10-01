# #2193 — D5 semantic lower bound

Status: research-only.

## Result

Ordinary closures and raw-form transformers have an observable difference
**before the body runs**.

Use the same call shape:

```text
(f (quote ok) never-defined)
```

For an ordinary closure:

```text
(lambda (a b) a)
```

ordinary call semantics evaluate both operands first, so `never-defined`
must fail before the body can ignore `b`.

For a transformer/macro with the same parameter/body shape, existing
conformance requires the opposite result: the unused second operand remains a
raw form, so the call returns `ok`.

## Exhaustive one-mode model

With no semantic discriminator there are only two global operand policies:

```text
1. eager
2. raw
```

Their truth table is:

```text
                 ordinary closure   transformer
eager                 PASS             FAIL
raw                   FAIL             PASS
```

No one-mode model satisfies both.

A two-mode model with one discriminator does:

```text
ordinary closure -> eager
transformer      -> raw
```

Therefore the lower bound is:

> preserving both semantics under the same call syntax requires at least one
> observable stage/call-mode discriminator.

## Why this matters for D5

Strict Model C from #2185 — D4 only, with no hidden distinction — is falsified
if this lower bound survives review.

This does **not** prove that the discriminator must be represented as:

```text
00101 TRANSFORMER
```

Possible representations include:
- a distinct transformer value kind;
- an exact binary identity;
- a call-site stage marker;
- an explicit compiler/reader phase.

But any hidden Rust tag or environment flag still satisfies the lower bound by
being new semantics; it cannot honestly be counted as "D4 only".

## Reproduce

```sh
python3 scripts/research-2193-d5-lower-bound.py
```

Expected headline:

```text
D5 semantic lower-bound witness: PASS
one-mode-satisfies-both=0
one-discriminator-model: ordinary=PASS transformer=PASS
STRICT-D4-ONLY-WITHOUT-DISCRIMINATOR=FALSIFIED
```

## Principle

**If identical call syntax must choose two different pre-body evaluation
policies, the distinction must exist explicitly somewhere in the semantics.**
