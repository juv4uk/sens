; Synthetic RED for #1347.
; A Lisp-owned semantic source must not derive its semantic truth from Rust.

(language-contract
  (semantic-authority-source "crates/my-lisp/src/eval/canon.rs")
  (law function-meaning comes-from-host))
