; #217 — Lisp-owned verifier for the canonical control-dispatch contract.
; The host transports contracts/control-dispatch-contract.lisp into
; `control-dispatch-document`; semantic expectations live here.

(def cd-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom found) (quote ()))
        (t (cdr found))))))

(def cd-find
  (lambda (identity entries)
    (cond
      ((atom entries) (quote ()))
      ((equal? (cd-field (car entries) (quote identity)) identity)
       (car entries))
      (t (cd-find identity (cdr entries))))))

(def cd-entry
  (lambda (identity)
    (cd-find identity (cdr control-dispatch-document))))

(def cd-expect
  (lambda (identity field expected)
    (let ((entry (cd-entry identity)))
      (cond
        ((atom entry) (list (quote missing-entry) identity))
        ((equal? (cd-field entry field) expected) (quote ()))
        (t
         (list
           (quote mismatch)
           identity
           field
           expected
           (cd-field entry field)))))))

(def cd-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (quote ()))
      ((atom (car checks)) (cd-first-failure (cdr checks)))
      (t (car checks)))))

(def control-dispatch-contract-witness
  (lambda ()
    (let ((failure
            (cd-first-failure
              (list
                (cd-expect (quote canonical-cond)
                           (quote semantic-id)
                           "0007")
                (cd-expect (quote canonical-cond)
                           (quote role)
                           (quote ordered-dispatch))
                (cd-expect (quote canonical-cond)
                           (quote generic-value-coercion)
                           (quote forbidden))
                (cd-expect (quote canonical-cond)
                           (quote nil-as-false)
                           (quote forbidden))
                (cd-expect (quote canonical-cond)
                           (quote host-bool-authority)
                           (quote forbidden))

                (cd-expect (quote exact-q-control)
                           (quote accepted-domain)
                           (quote exact-q-decision))
                (cd-expect (quote exact-q-control)
                           (quote yes-action)
                           (quote select))
                (cd-expect (quote exact-q-control)
                           (quote no-action)
                           (quote continue))

                (cd-expect (quote structural-control)
                           (quote implicit-consumption)
                           (quote forbidden))
                (cd-expect (quote structural-control)
                           (quote dispatch)
                           (quote explicit-match-required))

                (cd-expect (quote mathematical-result-control)
                           (quote implicit-consumption)
                           (quote forbidden))

                (cd-expect (quote reasoning-control)
                           (quote implicit-consumption)
                           (quote forbidden))
                (cd-expect (quote reasoning-control)
                           (quote dispatch)
                           (quote explicit-match-required))

                (cd-expect (quote no-answer-control)
                           (quote false-meaning)
                           (quote forbidden))
                (cd-expect (quote no-answer-control)
                           (quote implicit-consumption)
                           (quote forbidden))

                ; Syntax is deliberately not invented before the semantic
                ; protocol is stable. #217 may later ratify a matching surface.
                (cd-expect (quote structural-control)
                           (quote clause-syntax)
                           (quote not-yet-ratified))))))
      (cond
        ((not (eq (car control-dispatch-document)
                  (quote control-dispatch-contract/1)))
         (list (quote control-dispatch-contract-witness)
               (list (quote status) (quote fail))
               (list (quote detail) (quote schema))))
        ((atom failure)
         (list (quote control-dispatch-contract-witness)
               (list (quote status) (quote pass))
               (list (quote detail) (quote explicit-domain-control))))
        (t
         (list (quote control-dispatch-contract-witness)
               (list (quote status) (quote fail))
               (list (quote detail) failure)))))))
