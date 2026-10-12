; #749 — executable Lisp-owned witness for island compatibility.
;
; The host may transport contracts/island-compat-contract.lisp as bytes and
; bind it to island-compat-document. Every semantic expectation remains here.

(0011 island-compat-schema
  (0010 () (100 island-compat-document)))

(0011 island-compat-entries
  (0010 () (011 island-compat-document)))

(0011 island-compat-field
  (0010 (entry field)
    (001000 ((found (11100 field entry)))
      (110
        ((010 found) () (001 ()))
        ((010 found) (1) (001 ()))
        (t (011 found))))))

(0011 island-compat-find
  (0010 (identity entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (1) (001 ()))
      ((11110111 (island-compat-field (100 entries) (001 identity)) identity)
       (100 entries))
      (t (island-compat-find identity (011 entries))))))

(0011 island-compat-entry
  (0010 (identity)
    (island-compat-find identity (island-compat-entries))))

(0011 island-compat-check
  (0010 (identity field expected)
    (001000 ((entry (island-compat-entry identity)))
      (110
        ((010 entry) () (1110 (001 missing-entry) identity))
        ((010 entry) (1) (1110 (001 missing-entry) identity))
        ((11110111 (island-compat-field entry field) expected) (001 ()))
        (t (1110 (001 mismatch) identity field expected
                 (island-compat-field entry field)))))))

(0011 island-compat-first-failure
  (0010 (checks)
    (110
      ((010 checks) () (001 ()))
      ((010 checks) (1) (001 ()))
      ((010 (100 checks)) () (island-compat-first-failure (011 checks)))
      ((010 (100 checks)) (1) (island-compat-first-failure (011 checks)))
      (t (100 checks)))))

(0011 island-compat-witness
  (0010 ()
    (001000 ((failure
            (island-compat-first-failure
              (1110
                (island-compat-check
                  (001 semantic-id) (001 owner) (001 sens))
                (island-compat-check
                  (001 semantic-id) (001 representation) (001 opaque-u8))
                (island-compat-check
                  (001 semantic-id) (001 kernel-interpretation) (001 forbidden))
                (island-compat-check
                  (001 execution-witness) (001 cardinality) (001 zero-or-more))
                (island-compat-check
                  (001 execution-witness) (001 multiple-kernels-per-sid) (001 allowed))
                (island-compat-check
                  (001 island-call) (001 producer-required) (001 yes))
                (island-compat-check
                  (001 island-call) (001 provenance-preserved) (001 yes))
                (island-compat-check
                  (001 island-call) (001 universal-result-coercion) (001 forbidden))
                (island-compat-check
                  (001 zero-results) (001 result-count) 0)
                (island-compat-check
                  (001 zero-results) (001 literal-empty-list-alias) (001 forbidden))
                (island-compat-check
                  (001 one-result) (001 result-count) 1)
                (island-compat-check
                  (001 many-results) (001 result-count) (001 many))
                (island-compat-check
                  (001 many-results) (001 multiplicity-preserved) (001 yes))
                (island-compat-check
                  (001 bridge) (001 missing-bridge) (001 legal))
                (island-compat-check
                  (001 bridge) (001 semantic-equivalence-assumed) (001 no))
                (island-compat-check
                  (001 missing-kernel) (001 legal) (001 yes))
                (island-compat-check
                  (001 missing-kernel) (001 changes-sid-meaning) (001 no))
                (island-compat-check
                  (001 missing-kernel) (001 changes-registry-numbering) (001 no))))))
      (110
        ((101 (island-compat-schema) (001 island-compat-contract/1))
         (110
           ((010 failure) () (1110 (001 island-compat-witness)
                  (1110 (001 status) (001 pass))
                  (1110 (001 detail) (001 semantic-owner-island-mechanism))))
           ((010 failure) (1) (1110 (001 island-compat-witness)
                  (1110 (001 status) (001 pass))
                  (1110 (001 detail) (001 semantic-owner-island-mechanism))))
           (t
            (1110 (001 island-compat-witness)
                  (1110 (001 status) (001 fail))
                  (1110 (001 detail) failure)))))
        (t
         (1110 (001 island-compat-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail)
                     (1110 (001 schema) (island-compat-schema)))))))))
