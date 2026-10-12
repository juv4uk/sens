; Executable Lisp-owned witness for LIFE-1 contract.
; Host code may transport contracts/life-1-contract.lisp into
; life-1-document, but every semantic expectation is checked here.
;
; This witness uses Canon 6 explicit-result COND clauses. Canon 0 is data and
; list termination; it is never consumed as generic FALSE.

(0011 life-1-schema
  (0010 () (100 life-1-document)))

(0011 life-1-entries
  (0010 () (011 life-1-document)))

(0011 life-1-field
  (0010 (entry field)
    (001000 ((found (11100 field entry)))
      (110
        ((010 found) () (001 ()))
        ((010 found) (0) (011 found))))))

(0011 life-1-find
  (0010 (identity entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (0)
       (110
         ((101 (life-1-field (100 entries) (001 identity)) identity)
          (1)
          (100 entries))
         ((101 (life-1-field (100 entries) (001 identity)) identity)
          (0)
          (life-1-find identity (011 entries))))))))

(0011 life-1-entry
  (0010 (identity)
    (life-1-find identity (life-1-entries))))

(0011 life-1-check
  (0010 (identity field expected)
    (001000 ((entry (life-1-entry identity)))
      (110
        ((010 entry) ()
         (1110 (001 missing-entry) identity))
        ((010 entry) (0)
         (110
           ((101 (life-1-field entry field) expected)
            (1)
            (001 ()))
           ((101 (life-1-field entry field) expected)
            (0)
            (1110 (001 mismatch)
                  identity
                  field
                  expected
                  (life-1-field entry field)))))))))

(0011 life-1-first-failure
  (0010 (checks)
    (110
      ((010 checks) () (001 ()))
      ((010 checks) (0)
       (110
         ((010 (100 checks)) ()
          (life-1-first-failure (011 checks)))
         ((010 (100 checks)) (0)
          (100 checks)))))))

(0011 life-1-contract-witness
  (0010 ()
    (001000 ((failure
            (life-1-first-failure
              (1110
                (life-1-check (001 life-trace)
                              (001 owner)
                              (001 sens))
                (life-1-check (001 life-trace)
                              (001 truth-value)
                              (001 forbidden))
                (life-1-check (001 source-observation)
                              (001 native-domain-preserved)
                              (001 yes))
                (life-1-check (001 source-observation)
                              (001 universal-result-normalization)
                              (001 forbidden))
                (life-1-check (001 projection)
                              (001 explicit)
                              (001 yes))
                (life-1-check (001 projection)
                              (001 partial)
                              (001 yes))
                (life-1-check (001 projection)
                              (001 semantic-equivalence-assumed)
                              (001 no))
                (life-1-check (001 target-invocation)
                              (001 kernel-reinterpretation)
                              (001 forbidden))
                (life-1-check (001 missing-source-kernel)
                              (001 changes-semantic-id-meaning)
                              (001 no))
                (life-1-check (001 first-vertical-slice)
                              (001 source)
                              (001 prolog))
                (life-1-check (001 first-vertical-slice)
                              (001 target)
                              (001 datalog))
                (life-1-check (001 first-vertical-slice)
                              (001 shared-result-type)
                              (001 forbidden))
                (life-1-check (001 liveness)
                              (001 fresh-checkout)
                              (001 required))))))
      (110
        ((101 (life-1-schema) (001 life-1-contract/1))
         (1)
         (110
           ((010 failure) ()
            (1110 (001 life-1-contract-witness)
                  (1110 (001 status) (001 pass))
                  (1110 (001 detail)
                        (001 provenance-not-truth))))
           ((010 failure) (0)
            (1110 (001 life-1-contract-witness)
                  (1110 (001 status) (001 fail))
                  (1110 (001 detail) failure)))))
        ((101 (life-1-schema) (001 life-1-contract/1))
         (0)
         (1110 (001 life-1-contract-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail)
                     (1110 (001 schema)
                           (life-1-schema)))))))))
