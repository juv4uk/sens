# Physical binary D3 witness

`current-cond-reference.lisp` is an **exact-width binary-word source**, containing only 0/1 tokens and whitespace. It is not historical text Lisp and contains no executable human names.

`current-cond-reference.sens` is the canonical **physical T5 byte stream** of precisely those words, and `current-cond-reference` (extensionless) is the deterministic ASCII view: one space per word and one final LF.

The executable two-field D3 COND example is defined by these identical-width words. The `current_binary_preflight` Rust test checks that the canonical binary source runs to structural `()`. The GitHub-hosted `Physical binary SENS CLI smoke` executes physical T5 through both `sens` and `sens-trit` and checks the source/bytes/view relationship. Equality of transports is not an independent semantic oracle.

Never replace the source with the obsolete commentary-form fragment, never use a three-field COND, and never claim source-to-binary parity from an unchecked `.sens`.
