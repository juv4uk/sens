# Compact languages: a study — and where SENS sits

Scope: a survey of languages/encodings that minimise *program size in bits*, and an
honest placement of SENS against them. Written to be verifiable, not promotional:
every claim about SENS below was measured against the repository's own tooling
(`migrate-three-pass.py`, `migrate-t5-batch.py`, `sens_t5_codec.py`, `lib/domains/*`).

## 1. The ladder of compactness

"Compactness" is not one axis. Three distinct things are routinely conflated:

| layer | what it is | examples |
|---|---|---|
| **meaning** | the exact identity of operations/computations | SENS exact-domain words |
| **recording of meaning** | a serialisation of that meaning | T5 `.sens`, BLC bitstream |
| **machine encoding** | a form for one physical machine | bytecode (WASM/JVM/CPython), native ISA |

Comparisons are only meaningful *within* a layer. A binary encoding will always beat
a text encoding; that says nothing about the languages.

## 2. Binary Lambda Calculus (BLC)

The reference point for minimal program size.

- Invented by **John Tromp (2004)**; a binary encoding of the untyped lambda calculus
  in **De Bruijn index** notation.
- Encoding: lambda = `00`, application = `01`, variable `n` = `1ⁿ0`.
- The shortest closed term is the identity, `blc(λ1) = 0010` — **4 bits**.
- Its purpose is theory, not production: a concrete basis for **Kolmogorov /
  descriptional complexity** ("a very simple and elegant concrete definition of
  descriptional complexity").
- Practical variant **BLC8**: byte-oriented I/O ("bit streams fare poorly in
  interfacing with the real world"); universal machine U8 = 355 bits as BLC (45 bytes
  in BLC8).
- Where it is actually used: research, toolkits (e.g. `cl-blc` — a library/CLI to
  read/eval/compile BLC), and competition/obfuscation (IOCCC 2012 winner implements
  the BLC universal machine in under 6K). **Not** an industrial language.

Primary source: John Tromp, *Binary Lambda Calculus* (tromp.github.io/cl/Binary_lambda_calculus.html).

## 3. Combinator bases (SK, Iota, Jot)

An alternative minimal basis: express computation with a handful of combinators and no
variables at all.

- **SK calculus**: S and K suffice for all computable functions; a program is a tree of
  S/K applications. Often *fewer bits* than lambda for the same term, because there is
  no binder structure.
- **Iota / Jot** (Barker): single-combinator / binary encodings that are, in places,
  even smaller than BLC.
- Same caveat as BLC: minimal, opaque, unverifiable by inspection.

## 4. What is actually used

The minimal-basis languages (BLC, SK, Iota, Jot) are **not** used in industry. What is
used for compact program representation is:

- **Bytecode VMs** — WebAssembly, JVM, CPython: each operation is typically ~1 byte
  (opcode), with *implicit* structure (no explicit delimiters).
- **Binary serialisation** — MessagePack, CBOR, Protobuf: compact *data*, not programs.
- **Forth** — dictionary of 1-byte words; embedded niche.

So: the languages that beat everyone on bits are the ones nobody runs; the ones people
run are compact on a *different* axis (machine encoding), not on the meaning axis.

## 5. Where SENS sits

SENS does **not** translate meaning: an operation's identity *is* its code. With the
domain ladder D1–D9 (D10 upcoming), any operation is **≤10 bits**, regardless of how
long its human name would be. That removes the name/syntax/opcode tax entirely.

Measured on the repository's own T5 pipeline (the four admitted fixtures):

- T5 round-trip (`decode_bytes → encode_words`) is **bitwise identical** on every file.
- Codes are the **ratified** ones (e.g. D3 `100` = CAR, confirmed by
  `knowledge/d1-d5-foundation.json`, `semantic_registry.rs`, `gpu_oracle_conformance.rs`).
- The stream spans the ladder: D1 (`0/1`), D3 (CAR/CDR/CONS/QUOTE/NIL/COND), D4 (`1000` = CAAR).

Cost: the codec writes `trits = "2".join(words)`, i.e. **one separator trit per word**,
then packs 5 trits/byte. That separator, not the trit packing, is the overhead:

| program | logical bits | T5 bytes | T5 bits | overhead |
|---|---|---|---|---|
| third | 131 | 38 | 304 | 2.32× |
| branch | 38 | 12 | 96 | 2.53× |
| caar | 68 | 20 | 160 | 2.35× |
| two-forms | 49 | 14 | 112 | 2.29× |

Overhead ≈ `1.6·(w+1)/w` for word width `w`: ≈2.1× at D3, ≈1.9× at D5, ≈1.8× at D9.
Small programs with many short words sit at the **worst** end; longer words amortise the
separator.

## 6. Honest comparison

- **Pure bit-golf**: BLC / SK / Iota win. SENS pays ~2× for explicit (D2) structure.
- **Verifiable recording**: SENS is alone. BLC is minimal but opaque; nothing proves a
  4-bit term does what it claims. SENS carries exact identities + a bitwise round-trip
  + authority-sourced codes.
- **Readable surface**: SENS can render the same meaning as human text; BLC cannot.

The defensible claim is therefore **"compactness with proven identity"**, not "smallest
program". The unique property is *combination*: minimum-ish size **and** exact meaning
**and** readable surface — no other compact language offers all three.

## 7. Open questions / boundaries

1. The canonical migrator currently admits only tiny fixtures; **all of `lib/` is
   blocked fail-closed** (e.g. `compiler-nucleus.lisp`: "word 4: requires exact D1..D9
   0/1 word, got 'compiler-authority-find'"). Compactness claims beyond the fixtures are
   therefore **derived, not yet measured** on large programs.
2. The D2 separator is the main handicap against BLC. Reducing it (implicit/self-delimiting
   structure, run-encoded domain tags) is the obvious lever — at the cost of some transparency.
3. Octet/`F==S` rules (non-octet programs are blocked as `.sens`) must be explicit criteria,
   not surprises, in any future benchmark or competition.
4. A competition format that SENS could own: *shortest exact-domain recording that provably
   round-trips and passes an independent oracle* — a game BLC cannot win, because BLC carries
   no verification.

## References

- John Tromp, *Binary Lambda Calculus* — https://tromp.github.io/cl/Binary_lambda_calculus.html
- IOCCC 2012 (tromp): BLC universal machine — https://github.com/ioccc-src/winner/blob/master/2012/tromp/README.md
- `cl-blc`: toolkit for BLC — https://codeberg.org/aartaka/cl-blc
- Repository authority for codes: `lib/domains/d1..d9.lisp`, `knowledge/d1-d9-foundation.json`,
  `crates/sens/src/semantic_registry.rs`, `crates/sens/src/domain_surface_registry_generated.rs`
- Repository T5 pipeline: `scripts/migrate-three-pass.py`, `scripts/migrate-t5-batch.py`,
  `scripts/sens_t5_codec.py`
