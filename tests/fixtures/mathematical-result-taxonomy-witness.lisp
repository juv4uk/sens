; #225 — Lisp-owned verifier for the mathematical-result taxonomy.
; The host transports contracts/mathematical-result-taxonomy.lisp into
; `mathematical-result-taxonomy-document`; every semantic expectation is here.

(00001001 mrt-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 mrt-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010 (mrt-field (00000101 entries) (00000001 identity)) identity)
       (00000101 entries))
      (t (mrt-find identity (00000110 entries))))))

(00001001 mrt-entry
  (00001000 (identity)
    (mrt-find identity (00000110 mathematical-result-taxonomy-document))))

(00001001 mrt-expect
  (00001000 (identity field expected)
    (10011100 ((entry (mrt-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity))
        ((00100010 (mrt-field entry field) expected) (00000001 ()))
        (t
         (00100111
           (00000001 mismatch)
           identity
           field
           expected
           (mrt-field entry field)))))))

(00001001 mrt-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) () (mrt-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1) (mrt-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 mathematical-result-taxonomy-witness
  (00001000 ()
    (10011100 ((failure
            (mrt-first-failure
              (00100111
                ; Global mathematical-result laws.
                (mrt-expect (00000001 laws)
                            (00000001 domain-owner)
                            (00000001 mathematical-result))
                (mrt-expect (00000001 laws)
                            (00000001 object-approximation-identity)
                            (00000001 distinct))
                (mrt-expect (00000001 laws)
                            (00000001 generic-truth-coercion)
                            (00000001 forbidden))
                (mrt-expect (00000001 laws)
                            (00000001 many-valued-collapse)
                            (00000001 forbidden))

                ; Standard mathematical classification examples.
                (mrt-expect (00000001 pi-example)
                            (00000001 number-system)
                            (00000001 real))
                (mrt-expect (00000001 pi-example)
                            (00000001 rationality)
                            (00000001 irrational))
                (mrt-expect (00000001 pi-example)
                            (00000001 algebraic-status)
                            (00000001 transcendental))
                (mrt-expect (00000001 pi-example)
                            (00000001 result-role)
                            (00000001 exact-object))

                (mrt-expect (00000001 sqrt2-example)
                            (00000001 number-system)
                            (00000001 real))
                (mrt-expect (00000001 sqrt2-example)
                            (00000001 rationality)
                            (00000001 irrational))
                (mrt-expect (00000001 sqrt2-example)
                            (00000001 algebraic-status)
                            (00000001 algebraic))
                (mrt-expect (00000001 sqrt2-example)
                            (00000001 result-role)
                            (00000001 exact-object))

                ; Approximation is a role of a result, not the identity of the
                ; target mathematical object. Its own approximant remains a
                ; mathematical object and the relation must carry a guarantee.
                (mrt-expect (00000001 approximation-role)
                            (00000001 required-metadata)
                            (00000001 (target approximant precision-or-error-guarantee)))
                (mrt-expect (00000001 approximation-role)
                            (00000001 approximant-remains-own-mathematical-object)
                            (00000001 t))

                ; Enclosures remain mathematical data as well.
                (mrt-expect (00000001 interval-enclosure-role)
                            (00000001 required-metadata)
                            (00000001 (target lower-bound upper-bound enclosure-guarantee)))

                ; Symbolic representation is not a many-valued truth state.
                (mrt-expect (00000001 symbolic-expression-role)
                            (00000001 many-valued-status)
                            (00000001 forbidden))))))
      (00000111
        ((00100001 (00000011 (00000101 mathematical-result-taxonomy-document)
                  (00000001 mathematical-result-taxonomy/1)))
         (00100111 (00000001 mathematical-result-taxonomy-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) (00000001 schema))))
        ((00000010 failure) () (00100111 (00000001 mathematical-result-taxonomy-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 standard-math-classification))))
        ((00000010 failure) (1) (00100111 (00000001 mathematical-result-taxonomy-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 detail) (00000001 standard-math-classification))))
        (t
         (00100111 (00000001 mathematical-result-taxonomy-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 detail) failure)))))))
