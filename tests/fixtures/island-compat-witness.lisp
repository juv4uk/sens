; #749 — executable Lisp-owned witness for island compatibility.
;
; The host may transport contracts/island-compat-contract.lisp as bytes and
; bind it to island-compat-document. Every semantic expectation remains here.

(00001001 island-compat-schema
  (00001000 () (00000101 island-compat-document)))

(00001001 island-compat-entries
  (00001000 () (00000110 island-compat-document)))

(00001001 island-compat-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 island-compat-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010 (island-compat-field (00000101 entries) (00000001 identity)) identity)
       (00000101 entries))
      (t (island-compat-find identity (00000110 entries))))))

(00001001 island-compat-entry
  (00001000 (identity)
    (island-compat-find identity (island-compat-entries))))

(00001001 island-compat-check
  (00001000 (identity field expected)
    (10011100 ((entry (island-compat-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity))
        ((00100010 (island-compat-field entry field) expected) (00000001 ()))
        (t (00100111 (00000001 mismatch) identity field expected
                 (island-compat-field entry field)))))))

(00001001 island-compat-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) () (island-compat-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1) (island-compat-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 island-compat-witness
  (00001000 ()
    (10011100 ((failure
            (island-compat-first-failure
              (00100111
                (island-compat-check
                  (00000001 semantic-id) (00000001 owner) (00000001 my-lisp))
                (island-compat-check
                  (00000001 semantic-id) (00000001 representation) (00000001 opaque-u8))
                (island-compat-check
                  (00000001 semantic-id) (00000001 kernel-interpretation) (00000001 forbidden))
                (island-compat-check
                  (00000001 execution-witness) (00000001 cardinality) (00000001 zero-or-more))
                (island-compat-check
                  (00000001 execution-witness) (00000001 multiple-kernels-per-sid) (00000001 allowed))
                (island-compat-check
                  (00000001 island-call) (00000001 producer-required) (00000001 yes))
                (island-compat-check
                  (00000001 island-call) (00000001 provenance-preserved) (00000001 yes))
                (island-compat-check
                  (00000001 island-call) (00000001 universal-result-coercion) (00000001 forbidden))
                (island-compat-check
                  (00000001 zero-results) (00000001 result-count) 0)
                (island-compat-check
                  (00000001 zero-results) (00000001 literal-empty-list-alias) (00000001 forbidden))
                (island-compat-check
                  (00000001 one-result) (00000001 result-count) 1)
                (island-compat-check
                  (00000001 many-results) (00000001 result-count) (00000001 many))
                (island-compat-check
                  (00000001 many-results) (00000001 multiplicity-preserved) (00000001 yes))
                (island-compat-check
                  (00000001 bridge) (00000001 missing-bridge) (00000001 legal))
                (island-compat-check
                  (00000001 bridge) (00000001 semantic-equivalence-assumed) (00000001 no))
                (island-compat-check
                  (00000001 missing-kernel) (00000001 legal) (00000001 yes))
                (island-compat-check
                  (00000001 missing-kernel) (00000001 changes-sid-meaning) (00000001 no))
                (island-compat-check
                  (00000001 missing-kernel) (00000001 changes-registry-numbering) (00000001 no))))))
      (00000111
        ((00000011 (island-compat-schema) (00000001 island-compat-contract/1))
         (00000111
           ((00000010 failure) () (00100111 (00000001 island-compat-witness)
                  (00100111 (00000001 status) (00000001 pass))
                  (00100111 (00000001 detail) (00000001 semantic-owner-island-mechanism))))
           ((00000010 failure) (1) (00100111 (00000001 island-compat-witness)
                  (00100111 (00000001 status) (00000001 pass))
                  (00100111 (00000001 detail) (00000001 semantic-owner-island-mechanism))))
           (t
            (00100111 (00000001 island-compat-witness)
                  (00100111 (00000001 status) (00000001 fail))
                  (00100111 (00000001 detail) failure)))))
        (t
         (00100111 (00000001 island-compat-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail)
                     (00100111 (00000001 schema) (island-compat-schema)))))))))
