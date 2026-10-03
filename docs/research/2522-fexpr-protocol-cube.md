# #2522 — FEXPR/FSUBR protocol cube

Status: research-only.

## Historical control

Appendix B of the *LISP 1.5 Programmer's Manual* makes the special-call
boundary explicit.

Ordinary EXPR/SUBR arguments are evaluated through `evlis`.

For FEXPR, the evaluator supplies both:

```text
cdr(form)   ; raw operand forms
a           ; current a-list / caller context
```

The interpreter describes the call structurally as:

```text
apply(fexpr, list(cdr(form), a), a)
```

FSUBR similarly receives the raw operand tail in AC and the current a-list in
`$ALIST`.

Source: *LISP 1.5 Programmer's Manual*, Appendix B, printed pp. 70–71.

## Three independent protocol axes

The executable witness factors:

```text
A operand mode
  0 eager values
  1 raw forms

B caller-context input
  0 unavailable as direct semantic input
  1 explicit caller environment/a-list

C result protocol
  0 returned object is the call value
  1 returned object is code and is re-evaluated in caller context
```

All eight corners have distinct signatures under three isolated probes.

### A — raw operand probe

An unused undefined second operand:

```text
eager -> error before body
raw   -> body may ignore it
```

### B — caller-context probe

The body asks for a caller-only binding not passed as an operand:

```text
no direct env -> unavailable
caller env    -> visible
```

### C — result-protocol probe

The body returns the symbol/form `x`, while the caller binds `x=42`:

```text
direct value -> x
form re-eval -> 42
```

Each axis can change while the other two stay fixed.

## Historical FEXPR/FSUBR classification

At this protocol level:

```text
operand = raw
env     = explicit caller context
result  = direct value
```

Because raw operand preservation and caller-context access are independently
observable, the current provisional Phase-E classification is:

```text
FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES
```

This does not mean two public primitive names or two binary residents. It means
the historical call protocol contains two independent semantic distinctions
beyond ordinary eager calls.

## Relation to current TRANSFORMER

The witness also inspects live `apply_macro`.

Current macro invocation:

```text
raw Expr operands
 -> quote as data
 -> transformer closure frame
 -> transformer body returns Value
 -> Value -> Expr
 -> tail-evaluate in calling_environment
```

The caller environment is not bound as an explicit transformer parameter.

Therefore the protocol comparison is:

```text
historical FEXPR:
  raw + explicit caller-env + direct-value

current TRANSFORMER:
  raw + no direct caller-env input + form-re-eval
```

They share the raw-call axis but differ on both context exposure and result
protocol. Under the current issue's relation vocabulary:

```text
TRANSFORMER-RELATION=ORTHOGONAL
```

This is protocol classification, not a claim about which system is more
expressive after arbitrary libraries or source transformation.

## Non-conclusions

No D5/D6 width follows from this cube.

No coordinate is allocated.

Historical property-list tags FEXPR/FSUBR are mechanism provenance, not binary
semantic authority.

The archived `00101 TRANSFORMER` placement remains archived.

## Principle

**Special-call semantics factor into observable dimensions; sharing raw
operands is not enough to collapse two protocols into one identity.**
