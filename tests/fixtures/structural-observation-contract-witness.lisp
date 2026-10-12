; #218 — Lisp-owned verifier for remaining structural-observation rows.
; The host transports the contract document into `structural-observation-document`.
;
; Case tables are verified one case at a time. This avoids asking the historical
; macro expander to reconstruct a nested dotted-alist literal merely to compare
; two pieces of semantic data. The contract remains authoritative; this witness
; only reads its fields and checks the required domain facts.

(0011 so-field
  (0010 (entry field)
    (001000 ((found (11100 field entry)))
      (110
        ((010 found) () (001 ()))
        ((010 found) (1) (001 ()))
        (t (011 found))))))

(0011 so-find
  (0010 (identity entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (1) (001 ()))
      ((11110111 (so-field (100 entries) (001 identity)) identity)
       (100 entries))
      (t (so-find identity (011 entries))))))

(0011 so-entry
  (0010 (identity)
    (so-find identity (011 structural-observation-document))))

(0011 so-case-find
  (0010 (case-name cases)
    (110
      ((010 cases) () (001 ()))
      ((010 cases) (1) (001 ()))
      ((11110111 (so-field (100 cases) (001 when)) case-name)
       (100 cases))
      (t (so-case-find case-name (011 cases))))))

(0011 so-expect
  (0010 (identity field expected)
    (001000 ((entry (so-entry identity)))
      (110
        ((010 entry) () (1110 (001 missing-entry) identity))
        ((010 entry) (1) (1110 (001 missing-entry) identity))
        ((11110111 (so-field entry field) expected) (001 ()))
        (t (1110 (001 mismatch) identity field expected
                 (so-field entry field)))))))

(0011 so-expect-case
  (0010 (identity case-name expected-result)
    (001000 ((entry (so-entry identity)))
      (110
        ((010 entry) () (1110 (001 missing-entry) identity))
        ((010 entry) (1) (1110 (001 missing-entry) identity))
        (t
         (001000 ((case-entry
                 (so-case-find case-name (so-field entry (001 cases)))))
           (110
             ((010 case-entry) () (1110 (001 missing-case) identity case-name))
             ((010 case-entry) (1) (1110 (001 missing-case) identity case-name))
             ((11110111 (so-field case-entry (001 result)) expected-result)
              (001 ()))
             (t
              (1110
                (001 case-mismatch)
                identity
                case-name
                expected-result
                (so-field case-entry (001 result)))))))))))

(0011 so-first-failure
  (0010 (checks)
    (110
      ((010 checks) () (001 ()))
      ((010 checks) (1) (001 ()))
      ((010 (100 checks)) () (so-first-failure (011 checks)))
      ((010 (100 checks)) (1) (so-first-failure (011 checks)))
      (t (100 checks)))))

(0011 structural-observation-contract-witness
  (0010 ()
    (001000 ((failure
            (so-first-failure
              (1110
                ; #369: symbol? is a runtime class observation, not universal
                ; truth. Demand the explicit Lisp-owned result algebra first;
                ; this commit is intentionally RED until the contract is ratified.
                (so-expect "1023" (001 result-form) (001 class-membership))
                (so-expect "1023" (001 target-class) (001 symbol))
                (so-expect-case
                  "1023"
                  (001 symbol)
                  (001 (class-membership symbol member)))
                (so-expect-case
                  "1023"
                  (001 non-symbol)
                  (001 (class-membership symbol nonmember)))
                (so-expect "1023" (001 generic-truth-coercion) (001 forbidden))
                (so-expect "1023" (001 control-dispatch) (001 explicit-result-equality))

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
                (so-expect "1024" (001 result-form) (001 class-membership))
                (so-expect "1024" (001 target-class) (001 string))
                (so-expect-case
                  "1024"
                  (001 string)
                  (001 (class-membership string member)))
                (so-expect-case
                  "1024"
                  (001 non-string)
                  (001 (class-membership string nonmember)))
                (so-expect "1024" (001 generic-truth-coercion) (001 forbidden))
                (so-expect "1024" (001 control-dispatch) (001 explicit-result-equality))

                (so-expect "1025" (001 input-domain) (001 (string string)))
                (so-expect "1025" (001 result-form) (001 text-order))
                (so-expect-case
                  "1025"
                  (001 left-before-right)
                  (001 (text-order before)))
                (so-expect-case
                  "1025"
                  (001 same-text)
                  (001 (text-order same)))
                (so-expect-case
                  "1025"
                  (001 left-after-right)
                  (001 (text-order after)))
                (so-expect "1025" (001 outside-domain) (001 type-error))
                (so-expect "1025" (001 generic-truth-coercion) (001 forbidden))
                (so-expect "1025" (001 control-dispatch) (001 explicit-result-equality))

                (so-expect "1026" (001 result-form) (001 class-membership))
                (so-expect "1026" (001 target-class) (001 numeric-buffer))
                (so-expect-case
                  "1026"
                  (001 numeric-buffer)
                  (001 (class-membership numeric-buffer member)))
                (so-expect-case
                  "1026"
                  (001 non-numeric-buffer)
                  (001 (class-membership numeric-buffer nonmember)))
                (so-expect "1026" (001 generic-truth-coercion) (001 forbidden))
                (so-expect "1026" (001 control-dispatch) (001 explicit-result-equality))))))
      (110
        ((0100 (101 (100 structural-observation-document)
                  (001 structural-observation-contract/1)))
         (1110 (001 structural-observation-contract-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail) (001 schema))))
        ((010 failure) () (1110 (001 structural-observation-contract-witness)
               (1110 (001 status) (001 pass))
               (1110 (001 detail) (001 explicit-domain-results))))
        ((010 failure) (1) (1110 (001 structural-observation-contract-witness)
               (1110 (001 status) (001 pass))
               (1110 (001 detail) (001 explicit-domain-results))))
        (t
         (1110 (001 structural-observation-contract-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail) failure)))))))
