; #216 — Lisp-owned verifier for contracts/exact-q-binary-contract.lisp.
; The host only transports the contract form into `exact-q-binary-document`.

(00001001 q-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 q-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010 (q-field (00000101 entries) (00000001 identity)) identity)
       (00000101 entries))
      (t (q-find identity (00000110 entries))))))

(00001001 q-domain-entry
  (00001000 ()
    (00000101 (00000110 exact-q-binary-document))))

(00001001 q-operation-entries
  (00001000 ()
    (00000110 (00000110 exact-q-binary-document))))

(00001001 q-entry
  (00001000 (identity)
    (q-find identity (q-operation-entries))))

(00001001 q-outcome-find
  (00001000 (meaning outcomes)
    (00000111
      ((00000010 outcomes) () (00000001 ()))
      ((00000010 outcomes) (1) (00000001 ()))
      ((00100010 (q-field (00000101 outcomes) (00000001 meaning)) meaning)
       (00000101 outcomes))
      (t (q-outcome-find meaning (00000110 outcomes))))))

(00001001 q-expect
  (00001000 (entry field expected)
    (00000111
      ((00000010 entry) () (00100111 (00000001 missing-entry) field expected))
      ((00000010 entry) (1) (00100111 (00000001 missing-entry) field expected))
      ((00100010 (q-field entry field) expected) (00000001 ()))
      (t (00100111 (00000001 mismatch) field expected (q-field entry field))))))

(00001001 q-expect-op
  (00001000 (identity field expected)
    (10011100 ((entry (q-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-operation) identity))
        ((00000010 entry) (1) (00100111 (00000001 missing-operation) identity))
        ((00100010 (q-field entry field) expected) (00000001 ()))
        (t (00100111 (00000001 operation-mismatch)
                 identity field expected (q-field entry field)))))))

(00001001 q-expect-outcome
  (00001000 (meaning numerator denominator canonical-write)
    (10011100 ((outcome
            (q-outcome-find
              meaning
              (q-field (q-domain-entry) (00000001 outcomes)))))
      (00000111
        ((00000010 outcome) () (00100111 (00000001 missing-outcome) meaning))
        ((00000010 outcome) (1) (00100111 (00000001 missing-outcome) meaning))
        ((00100001 (00100010 (q-field outcome (00000001 numerator)) numerator))
         (00100111 (00000001 outcome-numerator) meaning numerator
               (q-field outcome (00000001 numerator))))
        ((00100001 (00100010 (q-field outcome (00000001 denominator)) denominator))
         (00100111 (00000001 outcome-denominator) meaning denominator
               (q-field outcome (00000001 denominator))))
        ((00100001 (00100010 (q-field outcome (00000001 canonical-write)) canonical-write))
         (00100111 (00000001 outcome-write) meaning canonical-write
               (q-field outcome (00000001 canonical-write))))
        (t (00000001 ()))))))

(00001001 q-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) () (q-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1) (q-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 exact-q-binary-contract-witness
  (00001000 ()
    (10011100 ((failure
            (q-first-failure
              (00100111
                (q-expect (q-domain-entry)
                          (00000001 domain-owner)
                          (00000001 exact-q-decision))
                (q-expect (q-domain-entry)
                          (00000001 admissibility)
                          (00000001 all-required-values-exact-rational))
                (q-expect (q-domain-entry)
                          (00000001 outside-domain)
                          (00000001 no-answer))
                (q-expect (q-domain-entry)
                          (00000001 approximation-policy)
                          (00000001 forbidden))
                (q-expect (q-domain-entry)
                          (00000001 generic-truth-coercion)
                          (00000001 forbidden))
                (q-expect-outcome (00000001 no) 0 1 "0")
                (q-expect-outcome (00000001 yes) 1 1 "1")
                (q-expect-op "1014" (00000001 operand-domain)
                             (00000001 exact-rational-sequence))
                (q-expect-op "1015" (00000001 operand-domain)
                             (00000001 exact-rational-sequence))
                (q-expect-op "1016" (00000001 operand-domain)
                             (00000001 exact-rational-sequence))
                (q-expect-op "1017" (00000001 operand-domain)
                             (00000001 exact-rational-sequence))
                (q-expect-op "1018" (00000001 operand-domain)
                             (00000001 exact-rational-sequence))))))
      (00000111
        ((00100001 (00000011 (00000101 exact-q-binary-document)
                  (00000001 exact-q-binary-contract/1)))
         (00100111 (00000001 exact-q-binary-contract-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) (00000001 schema))))
        ((00000010 failure) () (00100111 (00000001 exact-q-binary-contract-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 exact-q-only))))
        ((00000010 failure) (1) (00100111 (00000001 exact-q-binary-contract-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 exact-q-only))))
        (t
         (00100111 (00000001 exact-q-binary-contract-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) failure)))))))
