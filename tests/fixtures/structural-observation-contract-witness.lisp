; #218 — Lisp-owned verifier for remaining structural-observation rows.
; The host transports the contract document into `structural-observation-document`.
;
; Case tables are verified one case at a time. This avoids asking the historical
; macro expander to reconstruct a nested dotted-alist literal merely to compare
; two pieces of semantic data. The contract remains authoritative; this witness
; only reads its fields and checks the required domain facts.

(00001001 so-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 so-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010 (so-field (00000101 entries) (00000001 identity)) identity)
       (00000101 entries))
      (t (so-find identity (00000110 entries))))))

(00001001 so-entry
  (00001000 (identity)
    (so-find identity (00000110 structural-observation-document))))

(00001001 so-case-find
  (00001000 (case-name cases)
    (00000111
      ((00000010 cases) () (00000001 ()))
      ((00000010 cases) (1) (00000001 ()))
      ((00100010 (so-field (00000101 cases) (00000001 when)) case-name)
       (00000101 cases))
      (t (so-case-find case-name (00000110 cases))))))

(00001001 so-expect
  (00001000 (identity field expected)
    (10011100 ((entry (so-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity))
        ((00100010 (so-field entry field) expected) (00000001 ()))
        (t (00100111 (00000001 mismatch) identity field expected
                 (so-field entry field)))))))

(00001001 so-expect-case
  (00001000 (identity case-name expected-result)
    (10011100 ((entry (so-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity))
        (t
         (10011100 ((case-entry
                 (so-case-find case-name (so-field entry (00000001 cases)))))
           (00000111
             ((00000010 case-entry) () (00100111 (00000001 missing-case) identity case-name))
             ((00000010 case-entry) (1) (00100111 (00000001 missing-case) identity case-name))
             ((00100010 (so-field case-entry (00000001 result)) expected-result)
              (00000001 ()))
             (t
              (00100111
                (00000001 case-mismatch)
                identity
                case-name
                expected-result
                (so-field case-entry (00000001 result)))))))))))

(00001001 so-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) () (so-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1) (so-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 structural-observation-contract-witness
  (00001000 ()
    (10011100 ((failure
            (so-first-failure
              (00100111
                ; #369: symbol? is a runtime class observation, not universal
                ; truth. Demand the explicit Lisp-owned result algebra first;
                ; this commit is intentionally RED until the contract is ratified.
                (so-expect "1023" (00000001 result-form) (00000001 class-membership))
                (so-expect "1023" (00000001 target-class) (00000001 symbol))
                (so-expect-case
                  "1023"
                  (00000001 symbol)
                  (00000001 (class-membership symbol member)))
                (so-expect-case
                  "1023"
                  (00000001 non-symbol)
                  (00000001 (class-membership symbol nonmember)))
                (so-expect "1023" (00000001 generic-truth-coercion) (00000001 forbidden))
                (so-expect "1023" (00000001 control-dispatch) (00000001 explicit-result-equality))

                ; #369: symbol? is a runtime class observation, not universal
                ; truth. Demand the explicit Lisp-owned result algebra first;
                ; this commit is intentionally RED until the contract is ratified.
                (so-expect "1023" (quote result-form) (quote class-membership))
                (so-expect "1023" (quote target-class) (quote symbol))
                (so-expect-case
                  "1023"
                  (quote symbol)
                  (quote (class-membership symbol member)))
                (so-expect-case
                  "1023"
                  (quote non-symbol)
                  (quote (class-membership symbol nonmember)))
                (so-expect "1023" (quote generic-truth-coercion) (quote forbidden))
                (so-expect "1023" (quote control-dispatch) (quote explicit-result-equality))

                ; #218 broader type/text queries: first make the witness demand
                ; explicit domain-owned result records. The contract update that
                ; satisfies these checks lands only after this witness is seen RED.
                (so-expect "1024" (00000001 result-form) (00000001 class-membership))
                (so-expect "1024" (00000001 target-class) (00000001 string))
                (so-expect-case
                  "1024"
                  (00000001 string)
                  (00000001 (class-membership string member)))
                (so-expect-case
                  "1024"
                  (00000001 non-string)
                  (00000001 (class-membership string nonmember)))
                (so-expect "1024" (00000001 generic-truth-coercion) (00000001 forbidden))
                (so-expect "1024" (00000001 control-dispatch) (00000001 explicit-result-equality))

                (so-expect "1025" (00000001 input-domain) (00000001 (string string)))
                (so-expect "1025" (00000001 result-form) (00000001 text-order))
                (so-expect-case
                  "1025"
                  (00000001 left-before-right)
                  (00000001 (text-order before)))
                (so-expect-case
                  "1025"
                  (00000001 same-text)
                  (00000001 (text-order same)))
                (so-expect-case
                  "1025"
                  (00000001 left-after-right)
                  (00000001 (text-order after)))
                (so-expect "1025" (00000001 outside-domain) (00000001 type-error))
                (so-expect "1025" (00000001 generic-truth-coercion) (00000001 forbidden))
                (so-expect "1025" (00000001 control-dispatch) (00000001 explicit-result-equality))

                (so-expect "1026" (00000001 result-form) (00000001 class-membership))
                (so-expect "1026" (00000001 target-class) (00000001 numeric-buffer))
                (so-expect-case
                  "1026"
                  (00000001 numeric-buffer)
                  (00000001 (class-membership numeric-buffer member)))
                (so-expect-case
                  "1026"
                  (00000001 non-numeric-buffer)
                  (00000001 (class-membership numeric-buffer nonmember)))
                (so-expect "1026" (00000001 generic-truth-coercion) (00000001 forbidden))
                (so-expect "1026" (00000001 control-dispatch) (00000001 explicit-result-equality))))))
      (00000111
        ((00100001 (00000011 (00000101 structural-observation-document)
                  (00000001 structural-observation-contract/1)))
         (00100111 (00000001 structural-observation-contract-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) (00000001 schema))))
        ((00000010 failure) () (00100111 (00000001 structural-observation-contract-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 explicit-domain-results))))
        ((00000010 failure) (1) (00100111 (00000001 structural-observation-contract-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 explicit-domain-results))))
        (t
         (00100111 (00000001 structural-observation-contract-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) failure)))))))
