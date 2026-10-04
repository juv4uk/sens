# Cross-substrate conformance evidence matrix

**Status:** evidence inventory, not a blanket conformance claim

**Generated from live checkouts:** 2026-08-26

**Canonical fixture source:** `my-lisp/tests/fixtures/conformance.lisp` at
`f713d8a1d81d49369c2189a0d551924ed03937ac`

**CML checkout:** `ed0029b2cb95606c615a39953748ec2d9717f258`

**fpga-lisp checkout:** `0844de0fe2ed91334146f12654a9d70f662dbb37`

This document answers one narrow question: for each constitutive Tier-1
fixture, what class of evidence exists on each implementation path? It does
not promote harness inclusion to a passing run, RTL simulation to synthesis,
or synthesis to physical-hardware execution.

## Evidence vocabulary

| State | Maximum claim allowed |
|---|---|
| `HARNESS-COVERED` | The current source harness selects the fixture. No fresh run is implied. |
| `C-BACKEND-HARNESS` | CML's C-backend conformance harness selects and executes the fixture. No fresh run is implied. |
| `CML-STATIC` | CML checks the expected failure before RTL execution. This is compiler-front-end evidence, not RTL evidence. |
| `CML-RTL-HARNESS` | The CML pipeline selects the fixture for compile → assemble → Icarus RTL simulation → decode → compare. No fresh run is implied. |
| `UNSUPPORTED` | The implementation explicitly excludes the fixture from its claimed surface. |
| `MILESTONE-EQUIVALENT` | A direct fpga-lisp milestone exercises the same operation, sometimes on different literal data. It is not an exact-fixture pass. |
| `NO-DIRECT-WITNESS` | No exact or mapped direct fixture witness was found. It does not mean the operation is broken. |
| `NO-HW-WITNESS` | No physical-board execution of this fixture was found. |

The current CML compatibility record declares language contract 2.0, observes
upstream 3.0, and explicitly marks the upgrade as required. Its Tier-1
accounting is 35 selected: 25 supported-value, 7 supported-error and 3
unsupported-inexact. The fpga-lisp physical evidence is narrower: the board
has executed an ADD program returning tagged fixnum 7, including a persistent
flash cold-boot witness, but that path is not one of the Tier-1 fixtures below.

## Tier-1 fixture matrix

`Fxx` is the stable append-order position among Tier-1 records; `Lxx` is the
source line in the pinned canonical fixture file above.

| ID | Canonical expression | Rust | CML C | CML → FPGA RTL | Direct fpga-lisp | Physical board |
|---|---|---|---|---|---|---|
| F01/L12 | `(quote radio)` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M13 | NO-HW-WITNESS |
| F02/L13 | `(atom (quote radio))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M05 | NO-HW-WITNESS |
| F03/L14 | `(atom (quote ()))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F04/L15 | `(atom (quote (radio antenna)))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F05/L16 | `(eq (quote radio) (quote radio))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M05 | NO-HW-WITNESS |
| F06/L17 | `(eq (quote radio) (quote antenna))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F07/L18 | `(car (quote (radio antenna)))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M03/M04 | NO-HW-WITNESS |
| F08/L19 | `(cdr (quote (radio antenna)))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M04 | NO-HW-WITNESS |
| F09/L20 | `(cons (quote radio) (quote (antenna)))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M03 | NO-HW-WITNESS |
| F10/current | `(за-умовою (() (як-є wrong)) ((тотожне? (як-є x) (як-є x)) (як-є right)))` | HARNESS-COVERED | RETEST-PENDING | RETEST-PENDING | RETEST-PENDING | NO-HW-WITNESS |
| F11/L70 | `(eq 3 3)` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F12/L71 | `(eq 3 4)` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F13/L72 | `(eq "radio" "radio")` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F14/L73 | `(eq "\\r" "r")` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F15/L74 | three-clause `cond` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F16/L96 | `(car 5)` → `Type` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F17/L97 | `(car (quote ()))` → `Type` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F18/L98 | `(eq (quote (1)) (quote (2)))` → `Type` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F19/L99 | `(undefined-symbol)` → `UnknownSymbol` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-STATIC | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F20/L101 | `(quote a b)` → `Arity` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-STATIC | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F21/L102 | `(cons 1)` → `Arity` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-STATIC | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F22/L117 | dotted-pair `equal?` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT M32 | NO-HW-WITNESS |
| F23/L118 | `(car (quote (a b . c)))` | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F24/L119 | nested `cdr` on dotted pair | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F25/L127 | dotted variadic lambda | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F26/L128 | bare-symbol variadic lambda | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F27/L129 | variadic lambda arity failure | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F28/L132 | primitive `car` remains unshadowable | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F29/L149 | variadic `defmacro` expansion | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F30/L155 | fixnum zero is truthy | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT G8/JF test | NO-HW-WITNESS |
| F31/L156 | `(eq 3 3.0)` | HARNESS-COVERED | UNSUPPORTED: inexact-tag surface | UNSUPPORTED: no inexact tag | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F32/L157 | duplicate `(eq 3 3)` contract witness | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F33/L158 | `(eq 3.0 3.0)` | HARNESS-COVERED | UNSUPPORTED: inexact-tag surface | UNSUPPORTED: no inexact tag | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F34/L159 | `(= 3 3.0)` | HARNESS-COVERED | UNSUPPORTED: inexact-tag surface | UNSUPPORTED: no inexact tag | NO-DIRECT-WITNESS | NO-HW-WITNESS |
| F35/L214 | canonical zero-truthiness gate | HARNESS-COVERED | C-BACKEND-HARNESS | CML-RTL-HARNESS | MILESTONE-EQUIVALENT G8/JF test | NO-HW-WITNESS |

## Cross-cutting evidence that must not be projected onto every row

| Evidence | Exact scope | Excluded stronger claim |
|---|---|---|
| Gowin synthesis/PnR through M32: `Fmax 60.801 MHz`, no TNS, BSRAM 24/56 | Historical complete-design synthesis reported in `fpga-lisp/ecosystem-status.md` | Not synthesis evidence for current fpga-lisp HEAD; not fixture execution |
| Persistent ISA 1.1 image at fpga-lisp `092aa3b`: `Fmax 66.727 MHz`, TNS 0, external-flash verify | Exact bitstream and exact historical RTL revision | Not synthesis evidence for current HEAD `0844de0`; not Tier-1 conformance |
| Physical Tang Primer 25K: `ADD 3 4 → FIXNUM(7)`, no hardware error | One ADD/eval program path, including cold boot from flash | Not blanket M17–M34, ISA, or language-contract conformance |
| CML physical COM4 execution graph result `LispWord(7)` | One host-staged program/register-input path | Not cross-device transfer and not fixture-level parity |

## Source anchors

- Rust fixture runner: `my-lisp/crates/my-lisp/tests/mccarthy.rs`,
  `conformance_tests_from_my`.
- Canonical facts and tags: `my-lisp/tests/fixtures/conformance.lisp` and its
  `README.md`.
- CML→RTL selection and comparison:
  `cml/tests/conformance_test.rs`.
- CML C-backend accounting:
  `cml/tests/c_backend_conformance_test.rs`; expected aggregate
  `(35 selected, 25 supported-value, 7 supported-error, 3 unsupported-inexact)`.
- Declared support boundary and pinned evidence:
  `cml/compatibility.lisp`.
- Direct FPGA operation-to-milestone mapping:
  `fpga-lisp/fixture_coverage.py` and `docs/lisp-machine-plan.md`.
- Synthesis and physical-board evidence:
  `fpga-lisp/ecosystem-status.md`.

## Verification still required

This inventory was built read-only under memory pressure (swap was 1.8/2.0
GiB used), so no broad Rust/C/GCC/Icarus suite was launched. The next
evidence-producing run should generate a machine-readable per-fixture result
from each harness, including implementation SHA and evidence class. Until
then, every `*-HARNESS` cell above means selection by inspected current code,
not a fresh PASS.
