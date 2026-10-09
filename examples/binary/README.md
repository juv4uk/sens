# Pure-binary runnable SENS specimen — D1/D2/D4/D7

The file `d7-first-program.lisp` is **not human Lisp syntax**. Every payload
word in that source consists of only `0` and `1`, with ASCII whitespace
separating **exact-width** domain words. It contains a D4 definition,
a D2-framed D7 Text7 binding, a D4 lambda, an exact D1 return value, and a
subsequent invocation of the binding through its D7 frame.

A test in `crates/sens/tests/binary_program_e2e.rs` executes the complete
physical transport path:

```text
source exact binary words
    -> encode to physical T5 byte stream
    -> decode physical T5 to width-qualified words
    -> parse via canonical D2 reader (no compatibility Lisp reader)
    -> evaluate D4/D7 lexical definition and call
    -> observe exact D1:1 (not host t)
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
