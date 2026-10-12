; #225 — Lisp-owned verifier for the mathematical-result taxonomy.
; The host transports contracts/mathematical-result-taxonomy.lisp into
; `mathematical-result-taxonomy-document`; every semantic expectation is here.

(0011 mrt-field
  (0010 (entry field)
    (001000 ((found (11100 field entry)))
      (110
        ((010 found) () (001 ()))
        ((010 found) (1) (001 ()))
        (t (011 found))))))

(0011 mrt-find
  (0010 (identity entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (1) (001 ()))
      ((11110111 (mrt-field (100 entries) (001 identity)) identity)
       (100 entries))
      (t (mrt-find identity (011 entries))))))

(0011 mrt-entry
  (0010 (identity)
    (mrt-find identity (011 mathematical-result-taxonomy-document))))

(0011 mrt-expect
  (0010 (identity field expected)
    (001000 ((entry (mrt-entry identity)))
      (110
        ((010 entry) () (1110 (001 missing-entry) identity))
        ((010 entry) (1) (1110 (001 missing-entry) identity))
        ((11110111 (mrt-field entry field) expected) (001 ()))
        (t
         (1110
           (001 mismatch)
           identity
           field
           expected
           (mrt-field entry field)))))))

(0011 mrt-first-failure
  (0010 (checks)
    (110
      ((010 checks) () (001 ()))
      ((010 checks) (1) (001 ()))
      ((010 (100 checks)) () (mrt-first-failure (011 checks)))
      ((010 (100 checks)) (1) (mrt-first-failure (011 checks)))
      (t (100 checks)))))

(0011 mathematical-result-taxonomy-witness
  (0010 ()
    (001000 ((failure
            (mrt-first-failure
              (1110
                ; Global mathematical-result laws.
                (mrt-expect (001 laws)
                            (001 domain-owner)
                            (001 mathematical-result))
                (mrt-expect (001 laws)
                            (001 object-approximation-identity)
                            (001 distinct))
                (mrt-expect (001 laws)
                            (001 generic-truth-coercion)
                            (001 forbidden))
                (mrt-expect (001 laws)
                            (001 many-valued-collapse)
                            (001 forbidden))

                ; Standard mathematical classification examples.
                (mrt-expect (001 pi-example)
                            (001 number-system)
                            (001 real))
                (mrt-expect (001 pi-example)
                            (001 rationality)
                            (001 irrational))
                (mrt-expect (001 pi-example)
                            (001 algebraic-status)
                            (001 transcendental))
                (mrt-expect (001 pi-example)
                            (001 result-role)
                            (001 exact-object))

                (mrt-expect (001 sqrt2-example)
                            (001 number-system)
                            (001 real))
                (mrt-expect (001 sqrt2-example)
                            (001 rationality)
                            (001 irrational))
                (mrt-expect (001 sqrt2-example)
                            (001 algebraic-status)
                            (001 algebraic))
                (mrt-expect (001 sqrt2-example)
                            (001 result-role)
                            (001 exact-object))

                ; Approximation is a role of a result, not the identity of the
                ; target mathematical object. Its own approximant remains a
                ; mathematical object and the relation must carry a guarantee.
                (mrt-expect (001 approximation-role)
                            (001 required-metadata)
                            (001 (target approximant precision-or-error-guarantee)))
                (mrt-expect (001 approximation-role)
                            (001 approximant-remains-own-mathematical-object)
                            (001 t))

                ; Enclosures remain mathematical data as well.
                (mrt-expect (001 interval-enclosure-role)
                            (001 required-metadata)
                            (001 (target lower-bound upper-bound enclosure-guarantee)))

                ; Symbolic representation is not a many-valued truth state.
                (mrt-expect (001 symbolic-expression-role)
                            (001 many-valued-status)
                            (001 forbidden))))))
      (110
        ((0100 (101 (100 mathematical-result-taxonomy-document)
                  (001 mathematical-result-taxonomy/1)))
         (1110 (001 mathematical-result-taxonomy-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail) (001 schema))))
        ((010 failure) () (1110 (001 mathematical-result-taxonomy-witness)
               (1110 (001 status) (001 pass))
               (1110 (001 detail) (001 standard-math-classification))))
        ((010 failure) (1) (1110 (001 mathematical-result-taxonomy-witness)
               (1110 (001 status) (001 pass))
               (1110 (001 detail) (001 standard-math-classification))))
        (t
         (1110 (001 mathematical-result-taxonomy-witness)
               (1110 (001 status) (001 fail))
               (1110 (001 detail) failure)))))))
