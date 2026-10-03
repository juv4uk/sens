# 2751 — Full Historical Occupancy of Domain 6 (D6)

Status: RATIFIED OWNER DIRECTIVE. Replaces artificial 48-slot UNKNOWN sparse closure with full chronological early-Lisp capability projection following Domain 5 parents.

Українська версія: [2751-d6-historical-full-occupancy.uk.md](2751-d6-historical-full-occupancy.uk.md).

## 1. Context and Architectural Derivation

Domain 6 (6 bits, 64 coordinates) logically expands the 32 coordinates of Domain 5 ($D5$).
Each D5 function $P$ (5 bits) naturally branches into two 1-bit extensions ($P0$ and $P1$) in D6:

$$2 \times 32 = 64 \text{ coordinates}$$

Previous agent work had locked 48 coordinates as UNKNOWN/free, admitting only 16 selectors and struggling for days over candidate `001111` (OD-001). Under the owner's directive, Domain 6 is immediately and completely populated by the historical capabilities of early Lisp (Lisp 1.5, MacLisp, Scheme foundations).

## 2. Complete 64-Coordinate D6 Map

| Coordinate | D5 Parent | Function | Family | Description | Historical Origin |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `000000` | `00000` (EVALQUOTE) | `REPL` | system | Read-eval-print top-level conversational driver | Early interactive Lisp |
| `000001` | `00000` (EVALQUOTE) | `LOAD` | system | Sequential file-stream expression ingestion | Lisp 1.5 |
| `000010` | `00001` (FUNCTION) | `CLOSURE` | abstraction | Explicit heap-bound lexical environment closure | Lisp 1.5 / Scheme |
| `000011` | `00001` (FUNCTION) | `CURRY` | abstraction | Partial function application with bound prefix | Functional Lisp tradition |
| `000100` | `00010` (FEXPR) | `FSUBR` | special-form | Built-in non-evaluating kernel special form | Lisp 1.5 |
| `000101` | `00010` (FEXPR) | `LEXPR` | special-form | Variadic evaluated argument list receiver | MacLisp / Lisp 1.5 |
| `000110` | `00011` (MACRO) | `MACROEXPAND-1` | macro | Single-step macro expression expansion | Lisp 1.5 / Common Lisp |
| `000111` | `00011` (MACRO) | `MACROEXPAND` | macro | Full recursive macro expression reduction | Lisp 1.5 / Common Lisp |
| `001000` | `00100` (LABEL) | `LET` | binding | Parallel local lexical variable binding | MacLisp / Scheme |
| `001001` | `00100` (LABEL) | `LET*` | binding | Sequential local lexical variable binding | MacLisp / Scheme |
| `001010` | `00101` (PROG) | `DO` | control | Generalized stepped iterative loop | Lisp 1.5 / MacLisp |
| `001011` | `00101` (PROG) | `WHILE` | control | Conditional repetition loop primitive | Algorithmic Lisp |
| `001100` | `00110` (SET) | `RPLACA` | physical-mutation | In-place destructive replacement of pair CAR | Lisp 1.5 (§4.4) |
| `001101` | `00110` (SET) | `RPLACD` | physical-mutation | In-place destructive replacement of pair CDR | Lisp 1.5 (§4.4) |
| `001110` | `00111` (SETQ) | `SETF` | generalized-place | Generalized variable/accessor in-place update | MacLisp / Common Lisp |
| `001111` | `00111` (SETQ) | `DEFVAR` | state | Global variable declaration and root binding (OD-001) | Lisp 1.5 / Common Lisp |
| `010000` | `01000` (ZEROP) | `EVENP` | predicate | Parity test: integer is even | Lisp 1.5 |
| `010001` | `01000` (ZEROP) | `ODDP` | predicate | Parity test: integer is odd | Lisp 1.5 |
| `010010` | `01001` (NUMBERP) | `INTEGERP` | predicate | Type predicate: atom is an exact integer | Lisp 1.5 |
| `010011` | `01001` (NUMBERP) | `RATIONALP` | predicate | Type predicate: atom is an exact rational fraction | Lisp 1.5 / Core-Math |
| `010100` | `01010` (PLUS) | `ADD1` | arithmetic | Increment: $x + 1$ | Lisp 1.5 (§4.2) |
| `010101` | `01010` (PLUS) | `ABS` | arithmetic | Absolute value: $\|x\|$ | Lisp 1.5 (§4.2) |
| `010110` | `01011` (DIFFERENCE) | `SUB1` | arithmetic | Decrement: $x - 1$ | Lisp 1.5 (§4.2) |
| `010111` | `01011` (DIFFERENCE) | `NEG` | arithmetic | Additive inverse negation: $-x$ | Lisp 1.5 (§4.2) |
| `011000` | `01100` (GO) | `TAGBODY` | control | Low-level tagged goto-target statement body | Common Lisp / Scheme |
| `011001` | `01100` (GO) | `BLOCK` | control | Named lexical exit frame | Common Lisp / Scheme |
| `011010` | `01101` (RETURN) | `RETURN-FROM` | control | Targeted non-local return from named block | Common Lisp |
| `011011` | `01101` (RETURN) | `CATCH` | control | Dynamic non-local unwind handler (catch/throw) | MacLisp |
| `011100` | `01110` (LESSP) | `LEQ` (`<=`) | predicate | Non-strict numeric inequality $(\le)$ | Lisp 1.5 |
| `011101` | `01110` (LESSP) | `MIN` | arithmetic | Extremum: minimum of values | Lisp 1.5 (§4.2) |
| `011110` | `01111` (GREATERP) | `GEQ` (`>=`) | predicate | Non-strict numeric inequality $(\ge)$ | Lisp 1.5 |
| `011111` | `01111` (GREATERP) | `MAX` | arithmetic | Extremum: maximum of values | Lisp 1.5 (§4.2) |
| `100000` | `10000` (APPEND) | `NCONC` | list-structure | Destructive list concatenation without copying | Lisp 1.5 (§4.4) |
| `100001` | `10000` (APPEND) | `LENGTH` | list-structure | Exact element count of proper list | Lisp 1.5 |
| `100010` | `10001` (REVERSE) | `NREVERSE` | list-structure | In-place destructive list reversal | Lisp 1.5 |
| `100011` | `10001` (REVERSE) | `NTH` | list-structure | Zero-indexed element retrieval from list | Lisp 1.5 |
| `100100` | `10010` (TIMES) | `EXPT` | arithmetic | Exponential power: $x^y$ | Lisp 1.5 (§4.2) |
| `100101` | `10010` (TIMES) | `GCD` | arithmetic | Greatest common divisor for rational normalization | Lisp 1.5 / Core-Math |
| `100110` | `10011` (QUOTIENT) | `REMAINDER` | arithmetic | Exact integer division remainder (modulo) | Lisp 1.5 (§4.2) |
| `100111` | `10011` (QUOTIENT) | `RECIP` | arithmetic | Multiplicative inverse: $1/x$ | Lisp 1.5 / Core-Math |
| `101000` | `10100` (CAAAR) | `CAAAAR` | selector | 4-level composite selector | Lisp 1.5 |
| `101001` | `10100` (CAAAR) | `CAAADR` | selector | 4-level composite selector | Lisp 1.5 |
| `101010` | `10101` (CAADR) | `CAADAR` | selector | 4-level composite selector | Lisp 1.5 |
| `101011` | `10101` (CAADR) | `CAADDR` | selector | 4-level composite selector | Lisp 1.5 |
| `101100` | `10110` (CADAR) | `CADAAR` | selector | 4-level composite selector | Lisp 1.5 |
| `101101` | `10110` (CADAR) | `CADADR` | selector | 4-level composite selector | Lisp 1.5 |
| `101110` | `10111` (CADDR) | `CADDAR` | selector | 4-level composite selector | Lisp 1.5 |
| `101111` | `10111` (CADDR) | `CADDDR` | selector | 4-level composite selector | Lisp 1.5 |
| `110000` | `11000` (CDAAR) | `CDAAAR` | selector | 4-level composite selector | Lisp 1.5 |
| `110001` | `11000` (CDAAR) | `CDAADR` | selector | 4-level composite selector | Lisp 1.5 |
| `110010` | `11001` (CDADR) | `CDADAR` | selector | 4-level composite selector | Lisp 1.5 |
| `110011` | `11001` (CDADR) | `CDADDR` | selector | 4-level composite selector | Lisp 1.5 |
| `110100` | `11010` (CDDAR) | `CDDAAR` | selector | 4-level composite selector | Lisp 1.5 |
| `110101` | `11010` (CDDAR) | `CDDADR` | selector | 4-level composite selector | Lisp 1.5 |
| `110110` | `11011` (CDDDR) | `CDDDAR` | selector | 4-level composite selector | Lisp 1.5 |
| `110111` | `11011` (CDDDR) | `CDDDDR` | selector | 4-level composite selector | Lisp 1.5 |
| `111000` | `11100` (ASSOC) | `RASSOC` | lookup | Association list lookup by value | Lisp 1.5 |
| `111001` | `11100` (ASSOC) | `ACONS` | lookup | Cons key-value pair onto association list | Lisp 1.5 |
| `111010` | `11101` (MEMBER) | `INTERSECTION` | set-operation | Set intersection of lists | Lisp 1.5 |
| `111011` | `11101` (MEMBER) | `UNION` | set-operation | Set union of lists | Lisp 1.5 |
| `111100` | `11110` (PAIRLIS) | `MAPCAR` | higher-order | Element-wise mapping with result accumulation | Lisp 1.5 (§4.3) |
| `111101` | `11110` (PAIRLIS) | `MAPLIST` | higher-order | Sublist mapping with result accumulation | Lisp 1.5 (§4.3) |
| `111110` | `11111` (SUBST) | `SUBLIS` | tree-structure | Simultaneous multi-pair tree substitution | Lisp 1.5 (§4.3) |
| `111111` | `11111` (SUBST) | `COPY-TREE` | tree-structure | Complete structural recursive copy of S-expression | Lisp 1.5 |

## 3. Structural Properties

1. **Capacity:** Exactly 64 coordinates ($2^6$). 100% full occupancy. Zero UNKNOWN coordinates.
2. **Generative Symmetry:** Every single coordinate is derived from a D5 parent plus a single suffix bit ($P0$ and $P1$).
3. **Hardware / System completeness:** D6 incorporates destructive memory operations (`RPLACA`, `RPLACD`), deep loop execution (`DO`, `WHILE`), Lexical closures, macro transformations, advanced arithmetic (`EXPT`, `GCD`, `MOD`, `RECIP`), and full 4-level selectors.
