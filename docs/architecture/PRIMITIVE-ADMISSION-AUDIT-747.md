# Primitive Admission Audit — first evidence slice (#747 / #734)

Status: **experimental audit, no renumbering and no deletion**.

This document applies Contract 7.0 / ADR-005 to a first representative slice of the
current contiguous byte-SID registry.  Classification here is evidence for later
migration decisions; it does **not** mutate an existing SID assignment.

## Admission rule

Keep first-class identity when the distinction is externally observable,
compositionally necessary, or must stay stable across multiple execution
witnesses. Prefer ordinary data or derived operations when existing identities
already express the behavior honestly. Kernel-private ontology and host/runtime
mechanism do not become language primitives merely because an implementation
needs them.

## First slice

| SID | Identity | Audit class | Evidence / decision |
|---|---|---|---|
| 00000000 | Canon 0 / `()` | **primitive-essential** | Ground empty list / absence point and list terminator; Contract 7.0 keeps it immutable. |
| 00000001 | `quote` | **primitive-essential** | Historical McCarthy root; controls evaluation rather than being a convenience function. |
| 00000010 | `atom` | **primitive-essential** | Structural distinction at the language boundary; executable Canon witnesses exist. |
| 00000011 | `eq` | **primitive-essential** | Stable identity relation in the historical root; not replaced by host equality. |
| 00000100 | `cons` | **primitive-essential** | Constructor for the fundamental pair structure; independent execution witnesses exist. |
| 00000101 | `car` | **primitive-shared** | Canon primitive and already has a real Common Lisp C-ABI execution witness. |
| 00000110 | `cdr` | **primitive-shared** | Canon primitive; structurally irreducible without another equivalent pair projection. |
| 00000111 | `cond` | **primitive-essential** | Language control form; not ordinary callable payload data. |
| 00001000 | `lambda` | **primitive-essential** | First-class lexical function construction; observable binding/evaluation behavior. |
| 00001001 | `define` | **primitive-essential** | Language binding operation; retains program-visible environment effect. |
| 00001100 | `+` | **primitive-shared** | Public exact arithmetic operation with independent semantic evidence; keep pending full arithmetic audit. |
| 00100111 | `list` | **derived-operation** | Can be constructed from `cons` + Canon 0; useful public operation, but derivability is executable and explicit. No deletion yet. |
| 00101000 | `length` | **derived-operation** | Recursive list traversal over `cdr`/Canon 0 can define it honestly. Keep SID until compatibility impact is measured. |
| 00101001 | `append` | **derived-operation** | Ordinary recursive list construction using `cons`/`car`/`cdr`; not inherently kernel-private. |
| 00101010 | `reverse` | **derived-operation** | Constructible from list primitives; convenience/performance does not by itself justify primitive status. |
| 00101011 | `nth` | **derived-operation** | Repeated `cdr` + `car`; candidate for demotion after compatibility witness. |
| 00101111 | `second` | **derived-operation** | Exactly `car(cdr(x))`; strong reclaim candidate. |
| 00110000 | `third` | **derived-operation** | Repeated `cdr` + `car`; strong reclaim candidate. |
| 00110001 | `fourth` | **derived-operation** | Repeated `cdr` + `car`; strong reclaim candidate. |
| 00110010 | `fifth` | **derived-operation** | Repeated `cdr` + `car`; strong reclaim candidate. |
| 00110011 | `caar` | **derived-operation** | `car(car(x))`; no separate ontology needed. |
| 00110100 | `cadr` | **derived-operation** | `car(cdr(x))`; overlaps the behavior of `second`. |
| 00110101 | `cddr` | **derived-operation** | `cdr(cdr(x))`; strong reclaim candidate. |
| 00110110 | `cadddr` | **derived-operation** | Pure composition of existing list primitives. |
| 01001000 | `print` | **primitive-candidate / observable effect** | Output is externally observable. Keep until print/princ/write-to-string ownership is audited as a family. |
| 01001101 | `eval` | **execution-specific / review** | Historically Lisp execution. Common Lisp is now the autonomous Lisp execution kernel, so this SID must not be generalized into a universal island invoke operation. |
| 01011010 | `mono-ns` | **runtime-mechanism boundary** | Raw monotonic clock observation is host/substrate-facing. Public policy may be derived in Lisp; primitive necessity needs separate evidence. |
| 01011100 | `ntp-query-raw` | **runtime-mechanism** | Raw external observation; explicitly should not grow semantic ontology merely because the host can perform it. |
| 01011101 | `timezone-declarations-raw` | **runtime-mechanism** | Mechanism-only raw observation; timezone interpretation is already Lisp-owned. |
| 01111011 | `forward-in` | **kernel-owned / optional** | Full production-rule execution now belongs naturally to the CLIPS island; keep compatibility until replacement witness covers callers. |
| 01111100 | `reason-in` | **kernel-owned / optional** | Broad search/reasoning should not force one my-lisp truth ontology over Prolog/Datalog/CLIPS. |
| 10000111 | `unify` | **kernel-owned / optional witness** | First-order unification is native Prolog territory; retain Lisp implementation only as optional/reference evidence where useful. |
| 10000100 | `provenance` | **primitive/data distinction under review** | Provenance is universally useful, but much of its richness can remain ordinary data. Do not demote until graph/result witnesses prove sufficient representation. |
| 10100010 | `process-run` | **public capability identity** | Externally observable language-visible operation over a raw host mechanism; current architecture intentionally distinguishes it from `process-run-raw`. |
| 10100110 | `read-file` | **public capability identity** | Language-visible operation; raw file bytes remain substrate mechanism. |
| 10100111 | `write-file` | **public capability identity** | Externally observable effect and existing public contract; not merely an implementation helper. |

## Concrete decisions from this slice

### Kept as primitive

`car` (SID `00000101`) remains first-class. It is part of the immutable
McCarthy root and now has more than one execution witness: the historical
my-lisp path and a real Common Lisp C-ABI witness. This is exactly the
multi-witness case ADR-005 says deserves stable identity.

### Demotion candidate

`second` (SID `00101111`) is the clearest derived-operation candidate:

```lisp
(car (cdr x))
```

No SID is deleted or renumbered by this audit. A later migration must first
prove compatibility and preserve any useful surface name as a derived
operation.

### Island-composition admission candidate: `invoke`

The four merged kernel boundaries now provide executable evidence that
**generic island invocation is a real cross-kernel operation**, while existing
`eval` is specifically Lisp execution and must not be silently widened to
mean Prolog query, CLIPS agenda execution, or Datalog fixpoint evaluation.

Therefore `invoke` is the first evidence-backed **new primitive candidate**
under #747.

It is deliberately **not admitted in this PR**. The current registry migration
has generated projections and guards pinned to Canon 0 + 167 identities. A
correct admission must be atomic:

1. append one contiguous free byte SID;
2. update the authoritative `sr/2` row;
3. regenerate the function table and meta-registry projections;
4. update exact-count migration guards intentionally;
5. add an executable four-kernel invocation witness;
6. prove the new identity carries no kernel-private semantics.

Until those steps happen together, treating `invoke` as admitted would create
a split semantic authority.

## Rejected primitive proposal

A separate primitive for **Common-Lisp-result**, **Prolog-result**,
**CLIPS-result**, or **Datalog-result** is rejected by current evidence.
`FourKernelObservation` already preserves producer-native results side by
side, and `NativeResultRef` can address those slots as ordinary data. Creating
four result-type SIDs would copy kernel-private ontology into the shared
registry without operational necessity.

## What this audit proves — and does not

This slice audits more than the 20 identities required by #747 acceptance and
records both keep and demotion decisions. It also identifies an evidence-backed
island-composition admission candidate and an explicit rejected candidate.

It does **not** complete #734, which requires accounting for every current
identity, and it does **not** close #747 yet because `invoke` has not undergone
the required atomic registry admission.


## Admission follow-up — `invoke` is now evidence-backed

The follow-up atomic migration admits `invoke` as SID `10101000`.
It satisfies the six conditions listed above together rather than piecemeal:

1. `10101000` is the next contiguous free byte SID;
2. `sr/2` is the authority row and generated projections are updated from it;
3. exact-count/contiguity guards advance to Canon 0 + 168 identities;
4. one real integration witness sends the same `invoke` SID through Common Lisp,
   Prolog, CLIPS and Datalog via the shared C ABI;
5. each kernel still receives its own native payload and returns its own native
   observation;
6. the witness checks only opaque SID provenance — it does not redefine
   `invoke` as CAR, a Prolog goal, a CLIPS command or a Datalog relation.

This closes the “new primitive admitted because of island composition” gap in
#747. It does not close #734, whose all-identity audit remains broader work.
