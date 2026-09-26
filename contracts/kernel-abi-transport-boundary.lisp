; #1117 — language Sens8 vs kernel ABI coordinate boundary.
;
; The language owns exact SID identity. External kernels may preserve one
; transport byte as an observation/ABI coordinate, but that wrapper is not
; the language's Sens8 type and may not become a reverse semantic authority.

(kernel-abi-transport-boundary/1
  (owner my-lisp)
  (language-identity-type Sens8)
  (shared-abi-type WsmKernelRequest)
  (shared-abi-field semantic_id)
  (shared-abi-storage opaque-u8)

  (kernel-wrapper-type SemanticId)
  (kernel-wrapper-role transport-coordinate-only)
  (wrapper-language-type-equivalence forbidden)
  (kernel-to-language-authority forbidden)
  (kernel-may-query-semantic-registry forbidden)
  (kernel-may-import-language-sid-type forbidden)
  (kernel-may-mint-semantic-identity forbidden)

  (shared-abi-source
    "crates/wsm-kernel-c-abi/src/lib.rs"
    "crates/wsm-kernel-c-abi/Cargo.toml")

  (kernel common-lisp
    "crates/wsm-common-lisp-kernel/src/lib.rs"
    "crates/wsm-common-lisp-kernel/Cargo.toml")
  (kernel prolog
    "crates/wsm-prolog-kernel/src/lib.rs"
    "crates/wsm-prolog-kernel/Cargo.toml")
  (kernel clips
    "crates/wsm-clips-kernel/src/lib.rs"
    "crates/wsm-clips-kernel/Cargo.toml")
  (kernel datalog
    "crates/wsm-datalog-kernel/src/lib.rs"
    "crates/wsm-datalog-kernel/Cargo.toml")

  (allowed-direction language-sid8-to-kernel-transport)
  (reverse-direction kernel-transport-to-language-meaning forbidden)
  (native-result-role observation-only)
  (diagnostic kernel-abi-transport-boundary-violation))