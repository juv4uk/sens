; #1117 / #2864 — domain-qualified language identity vs kernel ABI coordinate boundary.
;
; The language owns exact domain-qualified identity. External kernels may
; preserve one transport byte only as an explicitly projected legacy/backend
; coordinate. Fitting in u8 does not grant a D3/D4/D5/D6 identity ABI access,
; and the wrapper may never become reverse semantic authority.

(kernel-abi-transport-boundary/1
  (owner sens)
  (language-identity-type CoreDomainIdentity)
  (shared-abi-type WsmKernelRequest)
  (shared-abi-field semantic_id)
  (shared-abi-storage opaque-u8)
  (shared-abi-identity-scope legacy-backend-anchor-only)
  (domain-to-kernel-transport explicit-projection-required)
  (domain-width-fit-implies-abi-admission forbidden)

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

  (allowed-direction explicit-legacy-backend-projection-to-kernel-transport)
  (reverse-direction kernel-transport-to-language-meaning forbidden)
  (native-result-role observation-only)
  (diagnostic kernel-abi-transport-boundary-violation))