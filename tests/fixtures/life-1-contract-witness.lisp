; Executable Lisp-owned witness for LIFE-1 contract.
; Host code may transport contracts/life-1-contract.lisp into
; life-1-document, but every semantic expectation is checked here.
;
; This witness uses Canon 6 explicit-result COND clauses. Canon 0 is data and
; list termination; it is never consumed as generic FALSE.

(00001001 life-1-schema
  (00001000 () (00000101 life-1-document)))

(00001001 life-1-entries
  (00001000 () (00000110 life-1-document)))

(00001001 life-1-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (0) (00000110 found))))))

(00001001 life-1-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (0)
       (00000111
         ((00000011 (life-1-field (00000101 entries) (00000001 identity)) identity)
          (1)
          (00000101 entries))
         ((00000011 (life-1-field (00000101 entries) (00000001 identity)) identity)
          (0)
          (life-1-find identity (00000110 entries))))))))

(00001001 life-1-entry
  (00001000 (identity)
    (life-1-find identity (life-1-entries))))

(00001001 life-1-check
  (00001000 (identity field expected)
    (10011100 ((entry (life-1-entry identity)))
      (00000111
        ((00000010 entry) ()
         (00100111 (00000001 missing-entry) identity))
        ((00000010 entry) (0)
         (00000111
           ((00000011 (life-1-field entry field) expected)
            (1)
            (00000001 ()))
           ((00000011 (life-1-field entry field) expected)
            (0)
            (00100111 (00000001 mismatch)
                  identity
                  field
                  expected
                  (life-1-field entry field)))))))))

(00001001 life-1-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (0)
       (00000111
         ((00000010 (00000101 checks)) ()
          (life-1-first-failure (00000110 checks)))
         ((00000010 (00000101 checks)) (0)
          (00000101 checks)))))))

(00001001 life-1-contract-witness
  (00001000 ()
    (10011100 ((failure
            (life-1-first-failure
              (00100111
                (life-1-check (00000001 life-trace)
                              (00000001 owner)
                              (00000001 sens))
                (life-1-check (00000001 life-trace)
                              (00000001 truth-value)
                              (00000001 forbidden))
                (life-1-check (00000001 source-observation)
                              (00000001 native-domain-preserved)
                              (00000001 yes))
                (life-1-check (00000001 source-observation)
                              (00000001 universal-result-normalization)
                              (00000001 forbidden))
                (life-1-check (00000001 projection)
                              (00000001 explicit)
                              (00000001 yes))
                (life-1-check (00000001 projection)
                              (00000001 partial)
                              (00000001 yes))
                (life-1-check (00000001 projection)
                              (00000001 semantic-equivalence-assumed)
                              (00000001 no))
                (life-1-check (00000001 target-invocation)
                              (00000001 kernel-reinterpretation)
                              (00000001 forbidden))
                (life-1-check (00000001 missing-source-kernel)
                              (00000001 changes-semantic-id-meaning)
                              (00000001 no))
                (life-1-check (00000001 first-vertical-slice)
                              (00000001 source)
                              (00000001 prolog))
                (life-1-check (00000001 first-vertical-slice)
                              (00000001 target)
                              (00000001 datalog))
                (life-1-check (00000001 first-vertical-slice)
                              (00000001 shared-result-type)
                              (00000001 forbidden))
                (life-1-check (00000001 liveness)
                              (00000001 fresh-checkout)
                              (00000001 required))))))
      (00000111
        ((00000011 (life-1-schema) (00000001 life-1-contract/1))
         (1)
         (00000111
           ((00000010 failure) ()
            (00100111 (00000001 life-1-contract-witness)
                  (00100111 (00000001 status) (00000001 pass))
                  (00100111 (00000001 detail)
                        (00000001 provenance-not-truth))))
           ((00000010 failure) (0)
            (00100111 (00000001 life-1-contract-witness)
                  (00100111 (00000001 status) (00000001 fail))
                  (00100111 (00000001 detail) failure)))))
        ((00000011 (life-1-schema) (00000001 life-1-contract/1))
         (0)
         (00100111 (00000001 life-1-contract-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail)
                     (00100111 (00000001 schema)
                           (life-1-schema)))))))))
