# my-lisp language core — SID8-only

This document describes the current function-identity model. Historical named
models belong in archive/research material and are not semantic authority.

## One function space

my-lisp has exactly one function-identity space:

    00000000
    ...
    11111111

That is exactly 256 function slots. The identity is the eight bits themselves.

A SID is not text, String, Symbol, a literal category, a decimal number, a
human name, an enum label, an opcode, or a backend identifier. Implementations
may temporarily carry the bits in machine storage, but storage does not create
another identity.

## Reader

Exactly eight bare 0/1 source characters are read directly into Sens8.

    00001100  -> Sens8 00001100
    12        -> ordinary exact decimal number
    101       -> ordinary exact decimal number

There is no reader mode that turns an eight-bit SID into a mathematical binary
integer.

At expression start, apostrophe is reader sugar for a list whose head is
SID 00000001 directly:

    'об'єкт
    (00000001 об'єкт)

The reader must not create an intermediate named function identity.

## Surfaces

Human-language and symbolic surfaces are optional source/UI routing metadata.
They are not functions and do not own meaning.

    surface/UI input
          ↓ mechanical lookup
    Sens8

The forbidden model is:

    name -> meaning -> SID
    SID  -> named semantic identity

Runtime and compiler logic must operate on Sens8 after source/UI routing.

## Core profiles

Core1, Core2, Core3 and Core4 are profiles of laws over the same function IDs:

    Sens8
      ↓
    selected Core profile
      ↓
    Lisp-owned law for that SID/profile
      ↓
    selected mechanism
      ↓
    observation/result

A Core profile never mints a new identity and never renames a SID.

## Execution mechanisms

Rust, C, Common Lisp, Prolog, Datalog, CLIPS, GraalVM, WASM, FPGA and other
substrates may provide mechanisms. A mechanism receives an already-selected
Sens8 and cannot redefine what that SID is.

Native operator names, opcodes and helper enums are mechanism-local metadata,
not my-lisp function identities.

## Compiler / IR rule

Compiler IR provenance may carry Sens8 and mechanism/profile facts. It must not
introduce a second named function ontology such as a canonical-identity enum or
a necessary-form identity enum.

## Empty structure is not a function ID

Contract 9 reserves all 00000000..11111111 for functions. Therefore the
historical implementation that reuses 00000000 for the empty-list ground
value is explicit migration debt, tracked by #1332.

The target invariant is:

    ()           -> structural value outside function SID space
    00000000     -> function identity

No replacement SID is to be allocated to ().

## Standing enforcement

- #1325 — permanent SID8-only language law
- #1327 — remove named runtime identity ontology
- #1328 — remove named necessary-form identity ontology
- #1329 — remove alternate-identity terminology
- #1330 — keep surfaces outside function ontology
- #1331 — executable standing guard
- #1332 — remove the empty-list collision from SID 00000000

The reference Rust implementation is evidence/mechanism, not semantic
authority. New code must make the eight-bit function identity visible instead
of replacing it with a word.

## Project boundary

Rust is a **reference implementation** and mechanism witness; Contract 9 and
the Lisp-owned executable evidence remain the language authority.

The current canonical source extension is **`.lisp`**. `.wsm` and `.my` are
legacy aliases only; file suffixes do not create language identity.

Authority precedence is documented in
[`semantic-authority-map.md`](semantic-authority-map.md). Under Contract 9,
older named-function descriptions in that map are migration debt/history where
they conflict with the SID8-only function-space law.
