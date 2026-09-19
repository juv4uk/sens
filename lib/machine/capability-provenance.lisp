; #211 — machine-readable provenance for bounded machine capabilities.
; These rows describe realization evidence only. They never define Lisp meaning.
; CI validates every row fail-closed through scripts/machine-authority-guard.lisp.

(capability-provenance
  (name add-u64)
  (semantic-authority my-lisp)
  (admitted-form add-r64-r64)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (lisp-owned-expression "00001100"))
  (representation-witness tests/fixtures/machine-representation-independence-witness.lisp))

(capability-provenance
  (name eq-cond-u64)
  (semantic-authority my-lisp)
  (admitted-form cmp-r64-r64+jnz-rel8)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_cond_profile.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (lisp-owned-expression "00000011" 00000111))
  (representation-witness not-yet-required))

(capability-provenance
  (name car-cons-u64)
  (semantic-authority my-lisp)
  (admitted-form store-pair+load-pair-head)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (lisp-owned-expression "00000100" 00000101))
  (representation-witness crates/my-lisp-host/tests/native_guest_abi.rs))
