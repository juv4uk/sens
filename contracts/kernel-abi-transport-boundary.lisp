; #1117 / #2817 — canonical domain identity vs legacy kernel ABI coordinate.
;
; The language owns exact domain-qualified identity. External kernels may
; preserve one historical transport byte as an observation/ABI coordinate,
; but that wrapper is explicitly legacy and may not become reverse authority.

(kernel-abi-transport-boundary/1
  (owner sens)
  (language-identity-type CoreDomainIdentity)
  (shared-abi-type WsmKernelRequest)
  (shared-abi-field semantic_id)
  (shared-abi-storage opaque-u8)

  (kernel-wrapper-type LegacyAbiSemanticId)
  (kernel-wrapper-role transport-coordinate-only)
  (wrapper-language-type-equivalence forbidden)
  (kernel-to-language-authority forbidden)
  (kernel-may-query-semantic-registry forbidden)
  (kernel-may-import-language-identity-type forbidden)
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

  (allowed-direction language-domain-to-explicit-legacy-abi-projection)
  (reverse-direction kernel-transport-to-language-meaning forbidden)
  (native-result-role observation-only)
  (diagnostic kernel-abi-transport-boundary-violation))