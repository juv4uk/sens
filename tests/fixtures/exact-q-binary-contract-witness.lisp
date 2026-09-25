; #216 — Lisp-owned verifier for contracts/exact-q-binary-contract.lisp.
; The host only transports the contract form into `exact-q-binary-document`.

(def q-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom? found) (quote ()))
        (t (cdr found))))))

(def q-find
  (lambda (identity entries)
    (cond
      ((atom? entries) (quote ()))
      ((equal? (q-field (car entries) (quote identity)) identity)
       (car entries))
      (t (q-find identity (cdr entries))))))

(def q-domain-entry
  (lambda ()
    (car (cdr exact-q-binary-document))))

(def q-operation-entries
  (lambda ()
    (cdr (cdr exact-q-binary-document))))

(def q-entry
  (lambda (identity)
    (q-find identity (q-operation-entries))))

(def q-outcome-find
  (lambda (meaning outcomes)
    (cond
      ((atom? outcomes) (quote ()))
      ((equal? (q-field (car outcomes) (quote meaning)) meaning)
       (car outcomes))
      (t (q-outcome-find meaning (cdr outcomes))))))

(def q-expect
  (lambda (entry field expected)
    (cond
      ((atom? entry) (list (quote missing-entry) field expected))
      ((equal? (q-field entry field) expected) (quote ()))
      (t (list (quote mismatch) field expected (q-field entry field))))))

(def q-expect-op
  (lambda (identity field expected)
    (let ((entry (q-entry identity)))
      (cond
        ((atom? entry) (list (quote missing-operation) identity))
        ((equal? (q-field entry field) expected) (quote ()))
        (t (list (quote operation-mismatch)
                 identity field expected (q-field entry field)))))))

(def q-expect-outcome
  (lambda (meaning numerator denominator canonical-write)
    (let ((outcome
            (q-outcome-find
              meaning
              (q-field (q-domain-entry) (quote outcomes)))))
      (cond
        ((atom? outcome) (list (quote missing-outcome) meaning))
        ((not? (equal? (q-field outcome (quote numerator)) numerator))
         (list (quote outcome-numerator) meaning numerator
               (q-field outcome (quote numerator))))
        ((not? (equal? (q-field outcome (quote denominator)) denominator))
         (list (quote outcome-denominator) meaning denominator
               (q-field outcome (quote denominator))))
        ((not? (equal? (q-field outcome (quote canonical-write)) canonical-write))
         (list (quote outcome-write) meaning canonical-write
               (q-field outcome (quote canonical-write))))
        (t (quote ()))))))

(def q-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) (quote ()))
      ((atom? (car checks)) (q-first-failure (cdr checks)))
      (t (car checks)))))

(def exact-q-binary-contract-witness
  (lambda ()
    (let ((failure
            (q-first-failure
              (list
                (q-expect (q-domain-entry)
                          (quote domain-owner)
                          (quote exact-q-decision))
                (q-expect (q-domain-entry)
                          (quote admissibility)
                          (quote all-required-values-exact-rational))
                (q-expect (q-domain-entry)
                          (quote outside-domain)
                          (quote no-answer))
                (q-expect (q-domain-entry)
                          (quote approximation-policy)
                          (quote forbidden))
                (q-expect (q-domain-entry)
                          (quote generic-truth-coercion)
                          (quote forbidden))
                (q-expect-outcome (quote no) 0 1 "0")
                (q-expect-outcome (quote yes) 1 1 "1")
                (q-expect-op "1014" (quote operand-domain)
                             (quote exact-rational-sequence))
                (q-expect-op "1015" (quote operand-domain)
                             (quote exact-rational-sequence))
                (q-expect-op "1016" (quote operand-domain)
                             (quote exact-rational-sequence))
                (q-expect-op "1017" (quote operand-domain)
                             (quote exact-rational-sequence))
                (q-expect-op "1018" (quote operand-domain)
                             (quote exact-rational-sequence))))))
      (cond
        ((not? (eq? (car exact-q-binary-document)
                  (quote exact-q-binary-contract/1)))
         (list (quote exact-q-binary-contract-witness)
               (list (quote status) (quote fail))
               (list (quote detail) (quote schema))))
        ((atom? failure)
         (list (quote exact-q-binary-contract-witness)
               (list (quote status) (quote pass))
               (list (quote detail) (quote exact-q-only))))
        (t
         (list (quote exact-q-binary-contract-witness)
               (list (quote status) (quote fail))
               (list (quote detail) failure)))))))
