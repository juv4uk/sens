# 2744 — Full Historical Occupancy of Domain 5 (D5)

Status: RATIFIED OWNER DIRECTIVE. Replaces artificial 24-slot UNKNOWN sparse closure with full chronological early-Lisp capability projection following Domains 1-4.

Українська версія: [2744-d5-historical-full-occupancy.uk.md](2744-d5-historical-full-occupancy.uk.md).

## 1. Context and Problem Statement

Previous agent consensus artificially restricted Domain 5 (5 bits, 32 coordinates) to exactly 8 selector descendants (`10100`..`10111`, `11000`..`11011`), declaring the remaining 24 slots "UNKNOWN/free" (#2505, #2724). Historical functions were either:
- rejected into higher widths (e.g. `SETQ` pushed into D6 `001111` under multi-delta claims);
- frozen without coordinates (`RETURN`, `FEXPR`, `MACRO` left unplaced);
- or completely banned from Core under a distorted interpretation of domain separation #2508 (`+`, `-`, `*`, `/` falsely relegated exclusively to Core-Math).

**Owner directive (2026-10-03):** Both Core and Core-Math must be complete and fully functional. D8 has not been reached; historical functions from early Lisp (McCarthy 1960, Lisp 1.5) that logically follow Domains 3-4 must immediately fill Domain 5.

## 2. Complete 32-Coordinate D5 Map

Every 5-bit coordinate in D5 is an exact 1-bit extension of its 4-bit D4 parent (`P0` and `P1`):

| Coordinate | D4 Parent | Function | Family | Description | Historical Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `00000` | `0000` (APPLY) | `EVALQUOTE` | evaluation | Top-level function evaluation over argument list | McCarthy 1960 / Lisp 1.5 |
| `00001` | `0000` (APPLY) | `FUNCTION` | abstraction | Lexical functional closure / FUNARG wrapper | Lisp 1.5 |
| `00010` | `0001` (EVAL) | `FEXPR` | evaluation | Special form evaluation over unevaluated operands | Lisp 1.5 (§4.1) |
| `00011` | `0001` (EVAL) | `MACRO` | evaluation | Syntactic form expansion and re-evaluation | Hart 1963 / Lisp 1.5 |
| `00100` | `0010` (LAMBDA) | `LABEL` | binding | Self-referential anonymous recursive lambda | McCarthy 1960 |
| `00101` | `0010` (LAMBDA) | `PROG` | control | Imperative sequence with local bindings and tags | Lisp 1.5 (§4.3) |
| `00110` | `0011` (DEFINE) | `SET` | state | Dynamic variable assignment `(set var val)` | Lisp 1.5 |
| `00111` | `0011` (DEFINE) | `SETQ` | state | Static symbol assignment `(setq sym val)` | Lisp 1.5 |
| `01000` | `0100` (NOT) | `ZEROP` | predicate | Numeric zero predicate | Lisp 1.5 (§4.2) |
| `01001` | `0100` (NOT) | `NUMBERP` | predicate | Numeric atom type predicate | Lisp 1.5 (§4.2) |
| `01010` | `0101` (D4-Arith) | `PLUS` (`+`) | arithmetic | Exact rational addition | McCarthy 1960 / Lisp 1.5 |
| `01011` | `0101` (D4-Arith) | `DIFFERENCE` (`-`) | arithmetic | Exact rational subtraction | McCarthy 1960 / Lisp 1.5 |
| `01100` | `0110` (EVCON) | `GO` | control | Unconditional jump to label inside `PROG` | Lisp 1.5 (§4.3) |
| `01101` | `0110` (EVCON) | `RETURN` | control | Non-local exit from `PROG` with result value | Lisp 1.5 (§4.3) |
| `01110` | `0111` (EVLIS) | `LESSP` (`<`) | predicate | Numeric strict inequality ordering | Lisp 1.5 (§4.2) |
| `01111` | `0111` (EVLIS) | `GREATERP` (`>`) | predicate | Numeric strict inequality ordering | Lisp 1.5 (§4.2) |
| `10000` | `1000` (LIST) | `APPEND` | list-structure | Concatenation of lists | McCarthy 1960 |
| `10001` | `1000` (LIST) | `REVERSE` | list-structure | Inversion of element order in list | McCarthy 1960 / Lisp 1.5 |
| `10010` | `1001` (D4-Arith) | `TIMES` (`*`) | arithmetic | Exact rational multiplication | McCarthy 1960 / Lisp 1.5 |
| `10011` | `1001` (D4-Arith) | `QUOTIENT` (`/`) | arithmetic | Exact rational division | McCarthy 1960 / Lisp 1.5 |
| `10100` | `1010` (CAAR) | `CAAAR` | selector | Path composition `car(car(car(x)))` | Lisp 1.5 |
| `10101` | `1010` (CAAR) | `CAADR` | selector | Path composition `car(car(cdr(x)))` | Lisp 1.5 |
| `10110` | `1011` (CADR) | `CADAR` | selector | Path composition `car(cdr(car(x)))` | Lisp 1.5 |
| `10111` | `1011` (CADR) | `CADDR` | selector | Path composition `car(cdr(cdr(x)))` | Lisp 1.5 |
| `11000` | `1100` (CDAR) | `CDAAR` | selector | Path composition `cdr(car(car(x)))` | Lisp 1.5 |
| `11001` | `1100` (CDAR) | `CDADR` | selector | Path composition `cdr(car(cdr(x)))` | Lisp 1.5 |
| `11010` | `1101` (CDDR) | `CDDAR` | selector | Path composition `cdr(cdr(car(x)))` | Lisp 1.5 |
| `11011` | `1101` (CDDR) | `CDDDR` | selector | Path composition `cdr(cdr(cdr(x)))` | Lisp 1.5 |
| `11100` | `1110` (LOOKUP) | `ASSOC` | lookup | Association list key search | McCarthy 1960 |
| `11101` | `1110` (LOOKUP) | `MEMBER` | lookup | List membership testing | McCarthy 1960 / Lisp 1.5 |
| `11110` | `1111` (BIND) | `PAIRLIS` | binding | Parallel key-value pairing into a-list | McCarthy 1960 |
| `11111` | `1111` (BIND) | `SUBST` | tree-structure | Recursive tree replacement in S-expression | McCarthy 1960 |

## 3. Structural Properties

1. **Capacity:** Exactly 32 coordinates ($2^5$). Zero holes, zero unallocated gaps.
2. **Generative symmetry:** Every coordinate is derived from a D4 semantic parent plus one suffix bit.
3. **Core completeness:** Core Lisp is fully capable of symbolic reasoning, arithmetic, recursion, state mutation, and imperative block execution without needing external ungrounded bridges or waiting for hypothetical future domains.
4. **Domain firewall preserved:** Core-Math remains the mathematical authority on the field $\mathbb{Q}$ and algebraic group laws; Core provides first-class executable binary instructions governed by those laws.
