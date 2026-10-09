# Pure-binary runnable SENS specimens — D1/D2/D3/D4/D7

The specimens use visible binary SENS words, not human Lisp spellings.
The D7 source is `d7-first-program.lisp`. The D3 sources are
`d3-cond-program.lisp` and `d3-primitives-program.lisp`; each same-stem
`.sens` is a **packed physical T5 byte stream**, and each extensionless file
is its exact-width visible decoder view. D3 source and view files contain only
0/1 words separated by whitespace; their physical `.sens` files contain
canonical T5 bytes in the range 0..242, not ASCII digits. The D7 specimen
contains a D4 definition, a D2-framed D7 Text7 binding, a D4 lambda, an exact
D1 return value, and a subsequent invocation of the binding through its D7
frame.

Tests in `crates/sens/tests/binary_program_e2e.rs` execute the D7 path and
read the committed physical T5 artifacts for both D3 specimens. Each D3 path
checks the packed bytes against its source and extensionless decoder view. The D3 specimen uses exact `110` COND, a first clause whose ATOM test is D1:0 (must skip), then an ATOM test returning D1:1 (must select). A negative case proves structural empty is not accepted as a predicate.

For the D7 specimen, the physical transport path is:

```text
source exact binary words
    -> encode to physical T5 byte stream
    -> decode physical T5 to width-qualified words
    -> parse via canonical D2 reader (no compatibility Lisp reader)
    -> evaluate D4/D7 lexical definition and call
    -> observe exact D1:1 (not host t)

D3 control specimen:
    -> physical T5 bytes
    -> exact-width D2 reader
    -> D3:110 COND + D3:010 ATOM
    -> exact D1 skip/select
    -> observe D1:1
```

It also proves fail-closed behavior for human executable spellings, noncallable
D7 data (including the two owner-reserved coordinates), and D10 width without
a ratified physical transport. The test **does not** claim independent
language-semantic oracle parity or a generalized D10 executor. Those require
separate Lisp-owned oracles/Vertical Day smoke; a matching encode/decode
digest alone is not proof of meaning.

CI: `.github/workflows/binary-program-e2e.yml`. The workflow runs on every
`main` push, on relevant PRs, and on manual dispatch, using **GitHub-hosted
Ubuntu**. It does not cancel itself when other agents advance `main`.
