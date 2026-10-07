; #4057 — machine-readable provenance for bounded machine capabilities.
; These rows describe realization evidence only. They never define SENS meaning.
; Current semantic authority is Contract 11.8 + ratified exact-domain laws.
; CI validates every row fail-closed through scripts/machine-authority-guard.lisp.
;
; independent-semantic-witness carries exact DomainIdentity literals. Width is
; part of identity; no historical SID8 byte or human spelling is used as a join.

(capability-provenance
  (name add-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form add-r64-r64)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression 01010))
  (representation-witness tests/fixtures/machine-representation-independence-witness.lisp))

(capability-provenance
  (name eq-cond-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form cmp-r64-r64+jnz-rel8)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_cond_profile.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression 101 110))
  (representation-witness not-yet-required))

(capability-provenance
  (name car-cons-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form store-pair+load-pair-head)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression 111 100))
  (representation-witness crates/my-lisp-host/tests/native_guest_abi.rs))
