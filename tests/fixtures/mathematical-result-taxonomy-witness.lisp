; #225 — Lisp-owned verifier for the mathematical-result taxonomy.
; The host transports contracts/mathematical-result-taxonomy.lisp into
; `mathematical-result-taxonomy-document`; every semantic expectation is here.

(def mrt-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom? found) (quote ()))
        (t (cdr found))))))

(def mrt-find
  (lambda (identity entries)
    (cond
      ((atom? entries) (quote ()))
      ((equal? (mrt-field (car entries) (quote identity)) identity)
       (car entries))
      (t (mrt-find identity (cdr entries))))))

(def mrt-entry
  (lambda (identity)
    (mrt-find identity (cdr mathematical-result-taxonomy-document))))

(def mrt-expect
  (lambda (identity field expected)
    (let ((entry (mrt-entry identity)))
      (cond
        ((atom? entry) (list (quote missing-entry) identity))
        ((equal? (mrt-field entry field) expected) (quote ()))
        (t
         (list
           (quote mismatch)
           identity
           field
           expected
           (mrt-field entry field)))))))

(def mrt-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) (quote ()))
      ((atom? (car checks)) (mrt-first-failure (cdr checks)))
      (t (car checks)))))

(def mathematical-result-taxonomy-witness
  (lambda ()
    (let ((failure
            (mrt-first-failure
              (list
                ; Global mathematical-result laws.
                (mrt-expect (quote laws)
                            (quote domain-owner)
                            (quote mathematical-result))
                (mrt-expect (quote laws)
                            (quote object-approximation-identity)
                            (quote distinct))
                (mrt-expect (quote laws)
                            (quote generic-truth-coercion)
                            (quote forbidden))
                (mrt-expect (quote laws)
                            (quote many-valued-collapse)
                            (quote forbidden))

                ; Standard mathematical classification examples.
                (mrt-expect (quote pi-example)
                            (quote number-system)
                            (quote real))
                (mrt-expect (quote pi-example)
                            (quote rationality)
                            (quote irrational))
                (mrt-expect (quote pi-example)
                            (quote algebraic-status)
                            (quote transcendental))
                (mrt-expect (quote pi-example)
                            (quote result-role)
                            (quote exact-object))

                (mrt-expect (quote sqrt2-example)
                            (quote number-system)
                            (quote real))
                (mrt-expect (quote sqrt2-example)
                            (quote rationality)
                            (quote irrational))
                (mrt-expect (quote sqrt2-example)
                            (quote algebraic-status)
                            (quote algebraic))
                (mrt-expect (quote sqrt2-example)
                            (quote result-role)
                            (quote exact-object))

                ; Approximation is a role of a result, not the identity of the
                ; target mathematical object. Its own approximant remains a
                ; mathematical object and the relation must carry a guarantee.
                (mrt-expect (quote approximation-role)
                            (quote required-metadata)
                            (quote (target approximant precision-or-error-guarantee)))
                (mrt-expect (quote approximation-role)
                            (quote approximant-remains-own-mathematical-object)
                            (quote t))

                ; Enclosures remain mathematical data as well.
                (mrt-expect (quote interval-enclosure-role)
                            (quote required-metadata)
                            (quote (target lower-bound upper-bound enclosure-guarantee)))

                ; Symbolic representation is not a many-valued truth state.
                (mrt-expect (quote symbolic-expression-role)
                            (quote many-valued-status)
                            (quote forbidden))))))
      (cond
        ((not? (eq? (car mathematical-result-taxonomy-document)
                  (quote mathematical-result-taxonomy/1)))
         (list (quote mathematical-result-taxonomy-witness)
               (list (quote status) (quote fail))
               (list (quote detail) (quote schema))))
        ((atom? failure)
         (list (quote mathematical-result-taxonomy-witness)
               (list (quote status) (quote pass))
               (list (quote detail) (quote standard-math-classification))))
        (t
         (list (quote mathematical-result-taxonomy-witness)
               (list (quote status) (quote fail))
               (list (quote detail) failure)))))))
