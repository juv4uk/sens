# ADR-006: Immutable Canon Bindings
# ADR-006: Непорушні зв'язування Канону

**Status:** Accepted / Прийнято  
**Date:** 2026-09-08  
**Authority:** Volodymyr / Vova (Owner directive)  
**Supersedes:** the 2026-09-06 Variant-A shadowing decision in `docs/research/canon-namespace-shadowing.md` for canon()+7 names only.

## 1. Decision / Рішення

`my-lisp` distinguishes ordinary lexical names from the finite set of ratified canon()+7 surface spellings.

The Canon set remains exactly:

```text
CANON_EMPTY_LIST
PRIM_QUOTE
PRIM_ATOM
PRIM_EQ
PRIM_CONS
PRIM_CAR
PRIM_CDR
PRIM_COND
```

`CANON_EMPTY_LIST` is the ground value `()`, not an eighth primitive operation.

For the seven primitive identities, every spelling already present in the immutable Canon registry — historical/English-facing, Ukrainian, Sanskrit, and symbolic shorthand — is a **reserved canonical spelling**.

A reserved canonical spelling:

1. resolves to Canon **before** ordinary lexical `Environment` lookup;
2. cannot be introduced by `define` / `def`;
3. cannot be used as a fixed, dotted-rest, or variadic `lambda` parameter;
4. therefore cannot be rebound indirectly through language-owned `let`, `let*`, or macro binders that lower to those binding mechanisms;
5. for callable Canon identities, resolves to one stable first-class operation handle per identity, shared by all human-language spellings;
6. for syntax-only Canon identities (`PRIM_QUOTE`, `PRIM_COND`), never becomes a callable/value binding merely because an `Environment` contains the same text.

## 2. Why this changes the old decision / Чому змінено попереднє рішення

The 2026-09-06 research decision deliberately preferred lexical symmetry:

```text
CANON defines meaning.
Environment binds names.
Names may change.
Meaning does not.
```

The new owner requirement is stronger: **Canon primitives must be immutable in actual program resolution, not only immutable as an external specification entity.**

That makes the old behavior insufficient. Under the old contract this was legal:

```lisp
(let ((car (lambda (x) 'shadowed)))
  (car '(a b)))
```

Under Contract 6.0 it is rejected as `InvalidForm` because `car` is a reserved spelling of `PRIM_CAR`.

This is an intentional breaking semantic change.

## 3. Finite reservation, not a magic namespace / Скінченне резервування, не магічний namespace

This ADR does **not** reserve a prefix such as `canon:*` and does not create a new syntactic form such as `(core ...)`.

Reservation is finite and data-driven:

```text
surface spelling
      │
      ▼
immutable CANON table
      │
      ├── reserved? ── yes ──► canonical identity
      │                         │
      │                         ├── value primitive ─► stable handle
      │                         └── special form ─────► syntax dispatch
      │
      └── no ─────────────────► ordinary Environment lookup
```

For an FPGA/C implementation this can be represented as a small fixed table of interned symbol IDs. No general string-prefix policy is required.

## 4. Scope boundary / Межа дії

The protected set is **only canon()+7**.

Ordinary builtins and derived/library operations remain lexically shadowable, including examples such as:

```text
+
map
read
vector
reason
```

Therefore Contract 6.0 preserves the Lisp principle that ordinary first-class operations are normal values while giving the foundational Canon a stronger ontological status.

## 5. Three-language consequence / Наслідок для трьох мов

Canonical EN/UK/SA names are no longer implemented as mutable surface aliases.

For example:

```text
car      ─┐
перше    ─┼──► PRIM_CAR ─► one immutable callable handle
ādi      ─┘
```

Likewise:

```text
quote / як-є / svarūpa  ─► PRIM_QUOTE  (syntax only)
cond  / за-умовою / …   ─► PRIM_COND   (syntax only)
```

Surface libraries must not `(define ...)` these names. They begin above Canon and define only necessary/derived vocabulary.

## 6. Conformance probes / Контрольні проби

A conforming implementation must demonstrate at least these observations:

```lisp
(car '(a b))                 => a
(перше '(a b))               => a
(ādi '(a b))                 => a

(def car 42)                 => InvalidForm
(def перше 42)               => InvalidForm
(def ādi 42)                 => InvalidForm
(lambda (car) car)           => InvalidForm
(lambda перше перше)         => InvalidForm

(def + (lambda (a b) 'x))
(+ 1 2)                       => x
```

The last probe is essential: it proves that the rule protects Canon rather than silently turning all builtins into keywords.

## 7. Contract effect / Вплив на контракт

This decision changes observable behavior and therefore bumps `language-contract.lisp` from **5.0 to 6.0**.

The older research document remains in the repository as historical evidence of the design path. ADR-006 is the newer normative authority for Canon binding semantics.
