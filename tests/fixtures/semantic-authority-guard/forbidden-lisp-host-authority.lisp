; Synthetic RED for #1347.
; A SENS-owned semantic source must not derive its semantic truth from Rust.

(language-contract
  (semantic-authority-source "crates/sens/src/eval/canon.rs")
  (law function-meaning comes-from-host))
