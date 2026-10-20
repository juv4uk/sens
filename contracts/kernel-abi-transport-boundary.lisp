; #1117 / #2817 — канонічна доменна ідентичність проти координати застарілого ABI ядра.
;
; Мова володіє точною доменно-кваліфікованою ідентичністю. Зовнішні ядра можуть
; зберегти один історичний транспортний байт як координату спостереження/ABI,
; але ця обгортка явно застаріла і не може стати зворотною владою.

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