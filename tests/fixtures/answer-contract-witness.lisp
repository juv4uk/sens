; #1711 — transition Lisp-owned witness for answer-contract/2.
;
; Semantic expectations live here in Lisp data/code. Rust only transports the
; contract and invokes this witness. #1709 will replace the transition harness
; once the new one-bit/two-part evaluator path is live.

(00001001 answer-contract-schema
  (00001000 () (00000101 answer-contract-document)))

(00001001 answer-contract-entries
  (00001000 () (00000110 answer-contract-document)))

(00001001 answer-contract-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 answer-contract-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010
         (answer-contract-field (00000101 entries) (00000001 identity))
         identity)
       (00000101 entries))
      (t (answer-contract-find identity (00000110 entries))))))

(00001001 answer-contract-entry
  (00001000 (identity)
    (answer-contract-find identity (answer-contract-entries))))

(00001001 answer-contract-expect
  (00001000 (identity field expected)
    (10011100 ((entry (answer-contract-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity field expected))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity field expected))
        ((00100010 (answer-contract-field entry field) expected)
         (00000001 ()))
        (t
         (00100111
           (00000001 mismatch)
           identity
           field
           expected
           (answer-contract-field entry field)))))))

(00001001 answer-contract-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) ()
       (answer-contract-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1)
       (answer-contract-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 answer-contract-witness-record
  (00001000 (status detail)
    (00100111
      (00000001 answer-contract-witness)
      (00100111 (00000001 status) status)
      (00100111 (00000001 detail) detail))))

(00001001 answer-contract-witness
  (00001000 ()
    (10011100 ((failure
            (answer-contract-first-failure
              (00100111
                (answer-contract-expect
                  (00000001 structural-empty)
                  (00000001 predicate-answer)
                  (00000001 no))
                (answer-contract-expect
                  (00000001 structural-empty)
                  (00000001 false-sentinel)
                  (00000001 no))

                (answer-contract-expect
                  00000010
                  (00000001 domain-owner)
                  (00000001 predicate))
                (answer-contract-expect
                  00000010
                  (00000001 result-form)
                  (00000001 predicate-one-bit))
                (answer-contract-expect
                  00000010
                  (00000001 empty-structure-result)
                  (00000001 one))
                (answer-contract-expect
                  00000010
                  (00000001 pair-result)
                  (00000001 zero))
                (answer-contract-expect
                  00000010
                  (00000001 structural-kind-result)
                  (00000001 forbidden))

                (answer-contract-expect
                  00000011
                  (00000001 domain-owner)
                  (00000001 predicate))
                (answer-contract-expect
                  00000011
                  (00000001 result-form)
                  (00000001 predicate-one-bit))
                (answer-contract-expect
                  00000011
                  (00000001 same-atom-result)
                  (00000001 one))
                (answer-contract-expect
                  00000011
                  (00000001 distinct-atom-result)
                  (00000001 zero))
                (answer-contract-expect
                  00000011
                  (00000001 identity-relation-result)
                  (00000001 forbidden))
                (answer-contract-expect
                  00000011
                  (00000001 outside-domain)
                  (00000001 type-error))

                (answer-contract-expect
                  00000111
                  (00000001 domain-owner)
                  (00000001 control))
                (answer-contract-expect
                  00000111
                  (00000001 clause-shape)
                  (00000001 (test expression)))
                (answer-contract-expect
                  00000111
                  (00000001 select-on)
                  (00000001 one))
                (answer-contract-expect
                  00000111
                  (00000001 skip-on)
                  (00000001 zero))
                (answer-contract-expect
                  00000111
                  (00000001 three-part-clause)
                  (00000001 forbidden))
                (answer-contract-expect
                  00000111
                  (00000001 graded-answer-match)
                  (00000001 forbidden))

                (answer-contract-expect
                  (00000001 binary-only-boundary)
                  (00000001 predicate-width)
                  (00000001 one-bit))
                (answer-contract-expect
                  (00000001 binary-only-boundary)
                  (00000001 control-width)
                  (00000001 two-bit-default))
                (answer-contract-expect
                  (00000001 binary-only-boundary)
                  (00000001 text-width)
                  (00000001 seven-bit-upc7))
                (answer-contract-expect
                  (00000001 binary-only-boundary)
                  (00000001 function-width)
                  (00000001 eight-bit)))))))
      (00000111
        ((00000011 (answer-contract-schema) (00000001 answer-contract/2))
         (1)
         (00000111
           ((00000010 failure) ()
            (answer-contract-witness-record
              (00000001 pass)
              (00000001 one-bit-binary-foundation)))
           ((00000010 failure) (1)
            (answer-contract-witness-record
              (00000001 pass)
              (00000001 one-bit-binary-foundation)))
           (t
            (answer-contract-witness-record (00000001 fail) failure))))
        (t
         (answer-contract-witness-record
           (00000001 fail)
           (00100111 (00000001 schema) (answer-contract-schema))))))))

