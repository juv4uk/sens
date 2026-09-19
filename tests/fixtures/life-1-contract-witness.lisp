; Executable Lisp-owned witness for LIFE-1 contract.
; Host code may transport contracts/life-1-contract.lisp into
; life-1-document, but every semantic expectation is checked here.
;
; This witness uses Canon 6 explicit-result COND clauses. Canon 0 is data and
; list termination; it is never consumed as generic FALSE.

(def life-1-schema
  (lambda () (car life-1-document)))

(def life-1-entries
  (lambda () (cdr life-1-document)))

(def life-1-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom found) (structural-kind empty-list) (quote ()))
        ((atom found) (structural-kind pair) (cdr found))))))

(def life-1-find
  (lambda (identity entries)
    (cond
      ((atom entries) (structural-kind empty-list) (quote ()))
      ((atom entries) (structural-kind pair)
       (cond
         ((eq (life-1-field (car entries) (quote identity)) identity)
          (identity-relation same)
          (car entries))
         ((eq (life-1-field (car entries) (quote identity)) identity)
          (identity-relation distinct)
          (life-1-find identity (cdr entries))))))))

(def life-1-entry
  (lambda (identity)
    (life-1-find identity (life-1-entries))))

(def life-1-check
  (lambda (identity field expected)
    (let ((entry (life-1-entry identity)))
      (cond
        ((atom entry) (structural-kind empty-list)
         (list (quote missing-entry) identity))
        ((atom entry) (structural-kind pair)
         (cond
           ((eq (life-1-field entry field) expected)
            (identity-relation same)
            (quote ()))
           ((eq (life-1-field entry field) expected)
            (identity-relation distinct)
            (list (quote mismatch)
                  identity
                  field
                  expected
                  (life-1-field entry field)))))))))

(def life-1-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom checks) (structural-kind pair)
       (cond
         ((atom (car checks)) (structural-kind empty-list)
          (life-1-first-failure (cdr checks)))
         ((atom (car checks)) (structural-kind pair)
          (car checks)))))))

(def life-1-contract-witness
  (lambda ()
    (let ((failure
            (life-1-first-failure
              (list
                (life-1-check (quote life-trace)
                              (quote owner)
                              (quote my-lisp))
                (life-1-check (quote life-trace)
                              (quote truth-value)
                              (quote forbidden))
                (life-1-check (quote source-observation)
                              (quote native-domain-preserved)
                              (quote yes))
                (life-1-check (quote source-observation)
                              (quote universal-result-normalization)
                              (quote forbidden))
                (life-1-check (quote projection)
                              (quote explicit)
                              (quote yes))
                (life-1-check (quote projection)
                              (quote partial)
                              (quote yes))
                (life-1-check (quote projection)
                              (quote semantic-equivalence-assumed)
                              (quote no))
                (life-1-check (quote target-invocation)
                              (quote kernel-reinterpretation)
                              (quote forbidden))
                (life-1-check (quote missing-source-kernel)
                              (quote changes-semantic-id-meaning)
                              (quote no))
                (life-1-check (quote first-vertical-slice)
                              (quote source)
                              (quote prolog))
                (life-1-check (quote first-vertical-slice)
                              (quote target)
                              (quote datalog))
                (life-1-check (quote first-vertical-slice)
                              (quote shared-result-type)
                              (quote forbidden))
                (life-1-check (quote liveness)
                              (quote fresh-checkout)
                              (quote required)))))))
      (cond
        ((eq (life-1-schema) (quote life-1-contract/1))
         (identity-relation same)
         (cond
           ((atom failure) (structural-kind empty-list)
            (list (quote life-1-contract-witness)
                  (list (quote status) (quote pass))
                  (list (quote detail)
                        (quote provenance-not-truth))))
           ((atom failure) (structural-kind pair)
            (list (quote life-1-contract-witness)
                  (list (quote status) (quote fail))
                  (list (quote detail) failure)))))
        ((eq (life-1-schema) (quote life-1-contract/1))
         (identity-relation distinct)
         (list (quote life-1-contract-witness)
               (list (quote status) (quote fail))
               (list (quote detail)
                     (list (quote schema)
                           (life-1-schema)))))))))
