# Physical binary D3 witness

The original `current-cond-reference.lisp` is the **current exact-width binary D3 COND reference**, exercised separately by the Rust `current_binary_preflight` test. It is not a historical Lisp program.

The new, standalone `current-cond-t5.lisp` is an exact copy of that binary-word program. It is a **new source cohort**, not a claimed historical migration of the preexisting reference. Its same-stem `current-cond-t5.sens` is canonical 30-byte physical T5; `current-cond-t5` is the canonical extensionless ASCII projection of 47 exact-width words.

The `Physical binary SENS CLI smoke` action executes physical T5 through both `sens` and `sens-trit`, and compares the bytes against precisely these source words; the unchanged source reference is independently checked by the Rust test. Physical transport parity does **not** certify a separate historical/original-source semantic oracle.

The proof-carrying migration gate must remain strict: no postdated physical T5 may masquerade as a historical original without a reviewed source-specific oracle.
