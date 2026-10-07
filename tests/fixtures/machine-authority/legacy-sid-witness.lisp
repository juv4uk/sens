; #4057 deliberate negative witness.
; Contract authority is current, but the independent semantic witness uses the
; retired SID8 witness ontology. The guard must reject it.
(capability-provenance
  (name legacy-sid8-answer-key)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form add-r64-r64)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness native-result)
  (reverse-edge forbidden)
  (independent-semantic-witness (lisp-owned-expression 00001100))
  (representation-witness not-yet-required))
