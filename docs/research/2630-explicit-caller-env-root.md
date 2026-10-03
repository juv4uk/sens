# #2630 — explicit caller environment root minimization

Status: SENS-DERIVATION research only.

## Result under test

explicit-caller-env = CARRIER-PREMISE

The witness separates operations over environment-shaped data from acquisition of the actual current caller context.

Current Core1 already exposes explicit environment operations:

    C1-LOOKUP(NAME, ENV, GLOBAL)
    C1-BIND(PARAMS, ARGS, ENV)

Once an environment value is explicitly supplied, ordinary lookup reproduces the body-level caller-only binding observation.

## Missing channel

Ordinary closure application evaluates expressions in the caller, but constructs the callee frame from:

    closure.environment + explicit argument slots

It does not insert calling_environment into the callee parameter slots.

Therefore two calls with the same explicit arguments but different caller-only bindings present the same explicit payload to the callee.

Historical FEXPR-style explicit-caller-env behavior distinguishes those calls only because the actual caller environment is supplied as an additional protocol input.

## Three-model attack

A — no environment channel:
same explicit args under caller x=42 and x=99 collide.

B — explicit environment-shaped data:
pass the environment as ordinary data and apply D4-style LOOKUP; the observation is reproduced.

C — automatic caller-environment injection:
the observation is reproduced, but reification/injection of the actual current context is a new acquisition channel.

## Classification

Not PROVEN-ROOT: lookup over explicit environment data is already expressible.

Not fully DERIVED: ordinary D1-D4 call semantics cannot recover the actual current caller environment from identical explicit arguments.

Therefore the honest bounded classification is CARRIER-PREMISE.

    width      = UNKNOWN
    coordinate = UNPLACED
    residents  = 0

## Reproduce

    python3 scripts/research-2630-explicit-caller-env-root.py

Expected:

    R3-EXPLICIT-CALLER-ENV=PASS
    root-status=CARRIER-PREMISE

## Principle

LOOKUP over an explicit environment is an operation. Obtaining the actual caller environment is a carrier/acquisition premise. Hiding the latter in host reflection is not derivation.