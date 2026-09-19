; #228/#244 — Lisp-owned executable witness for the layered answer-contract data.
;
; contracts/answer-contract.lisp is pure data. The host test transports its
; UTF-8 source text into Lisp and defines `answer-contract-document` through
; the Lisp reader. This witness owns every semantic expectation below; Rust
; owns only file-byte transport because core my-lisp intentionally has no
; implicit filesystem capability.

(def answer-contract-schema
  (lambda () (car answer-contract-document)))

(def answer-contract-entries
  (lambda () (cdr answer-contract-document)))

(def answer-contract-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom found) (quote ()))
        (t (cdr found))))))

(def answer-contract-find
  (lambda (identity entries)
    (cond
      ((atom entries) (quote ()))
      ((equal?
         (answer-contract-field (car entries) (quote identity))
         identity)
       (car entries))
      (t (answer-contract-find identity (cdr entries))))))

(def answer-contract-entry
  (lambda (identity)
    (answer-contract-find identity (answer-contract-entries))))

(def answer-contract-witness-record
  (lambda (status detail)
    (list
      (quote answer-contract-witness)
      (list (quote status) status)
      (list (quote detail) detail))))

(def answer-contract-witness-expect
  (lambda (identity field expected)
    (let ((entry (answer-contract-entry identity)))
      (cond
        ((atom entry)
         (list (quote missing-entry) identity field expected))
        ((equal? (answer-contract-field entry field) expected)
         (quote ()))
        (t
         (list
           (quote mismatch)
           identity
           field
           expected
           (answer-contract-field entry field)))))))

; #244 negative law: Canon 0 is not an alias for any stronger domain-owned
; state. A pass is represented by () because this helper itself only reports
; a failure when an accidental semantic collapse is detected.
(def answer-contract-witness-expect-distinct
  (lambda (left right)
    (cond
      ((equal? left right)
       (list (quote unexpected-collapse) left right))
      (t (quote ())))))

(def answer-contract-witness-expect-missing
  (lambda (identity)
    (cond
      ((atom (answer-contract-entry identity)) (quote ()))
      (t (list (quote unexpected-entry) identity)))))

(def answer-contract-witness-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (quote ()))
      ((atom (car checks))
       (answer-contract-witness-first-failure (cdr checks)))
      (t (car checks)))))

(def answer-contract-witness
  (lambda ()
    (let ((failure
            (answer-contract-witness-first-failure
              (list
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote domain-owner)
                  (quote no-answer-boundary))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote answer-role)
                  (quote unspecialized-accumulator))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote indeterminacy)
                  (quote unresolved-specialization))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote specialization-policy)
                  (quote justified-only))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote cause-required)
                  (quote no))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote reentry)
                  (quote allowed-at-query-boundaries))
                (answer-contract-witness-expect
                  (quote canon-zero)
                  (quote result-form)
                  (quote empty-list))
                (answer-contract-witness-expect
                  "00000100"
                  (quote domain-owner)
                  (quote structure))
                (answer-contract-witness-expect
                  "00000100"
                  (quote result-form)
                  (quote pair))
                (answer-contract-witness-expect
                  "00000010"
                  (quote domain-owner)
                  (quote structural-observation))
                (answer-contract-witness-expect
                  "00000010"
                  (quote result-form)
                  (quote structural-kind))
                (answer-contract-witness-expect
                  "00000010"
                  (quote result-values)
                  (quote ((structural-kind empty-list)
                          (structural-kind pair)
                          (structural-kind atom))))
                (answer-contract-witness-expect
                  "00000010"
                  (quote no-answer)
                  (quote not-applicable))
                (answer-contract-witness-expect
                  "00000011"
                  (quote domain-owner)
                  (quote structural-observation))
                (answer-contract-witness-expect
                  "00000011"
                  (quote input-domain)
                  (quote (atom atom)))
                (answer-contract-witness-expect
                  "00000011"
                  (quote result-form)
                  (quote identity-relation))
                (answer-contract-witness-expect
                  "00000011"
                  (quote result-values)
                  (quote ((identity-relation same)
                          (identity-relation distinct))))
                (answer-contract-witness-expect
                  "00000011"
                  (quote outside-domain)
                  (quote type-error))
                (answer-contract-witness-expect
                  "00000011"
                  (quote no-answer)
                  (quote not-applicable))
                (answer-contract-witness-expect
                  "00011010"
                  (quote domain-owner)
                  (quote exact-q-decision))
                (answer-contract-witness-expect
                  "00011010"
                  (quote binary-values)
                  (quote ("0/1" "1/1")))
                (answer-contract-witness-expect
                  "00011010"
                  (quote outside-domain)
                  (quote delegate))
                (answer-contract-witness-expect
                  "00011010"
                  (quote unspecialized-result)
                  (quote ()))
                (answer-contract-witness-expect
                  "00001100"
                  (quote domain-owner)
                  (quote mathematical-result))
                (answer-contract-witness-expect
                  "00001100"
                  (quote unspecialized-result)
                  (quote ()))
                (answer-contract-witness-expect
                  "10000101"
                  (quote domain-owner)
                  (quote non-mathematical-reasoning))
                (answer-contract-witness-expect
                  "10000101"
                  (quote unspecialized-result)
                  (quote ()))
                (answer-contract-witness-expect
                  "10000101"
                  (quote no-answer)
                  (quote ()))
                (answer-contract-witness-expect
                  "00000111"
                  (quote domain-owner)
                  (quote control-consumer))
                (answer-contract-witness-expect
                  "00000111"
                  (quote unspecialized-result)
                  (quote ()))
                (answer-contract-witness-expect
                  "00000111"
                  (quote generic-value-coercion)
                  (quote forbidden))

                ; Canon 0 preserves unresolved specialization. These explicit
                ; negative witnesses prevent future code from silently
                ; rebranding () as one stronger answer or observation class.
                (answer-contract-witness-expect-distinct (quote ()) 0/1)
                (answer-contract-witness-expect-distinct (quote ()) 1/1)
                (answer-contract-witness-expect-distinct
                  (quote ()) (quote unknown))
                (answer-contract-witness-expect-distinct
                  (quote ()) (quote conflict))
                (answer-contract-witness-expect-distinct
                  (quote ()) (quote timeout))
                (answer-contract-witness-expect-distinct
                  (quote ()) (quote error))

                ; Human spellings stay in semantic-registry.lisp. The contract
                ; is keyed by semantic identity only. Canon 0 is the one special
                ; non-ID entry because the empty list has no lexical Canon ID.
                (answer-contract-witness-expect-missing (quote cons))
                (answer-contract-witness-expect-missing (quote reason))))))
      (cond
        ((eq (answer-contract-schema) (quote answer-contract/1))
         (cond
           ((atom failure)
            (answer-contract-witness-record
              (quote pass)
              (quote canon-zero-unspecialized-accumulator)))
           (t
            (answer-contract-witness-record (quote fail) failure))))
        (t
         (answer-contract-witness-record
           (quote fail)
           (list (quote schema) (answer-contract-schema))))))))
