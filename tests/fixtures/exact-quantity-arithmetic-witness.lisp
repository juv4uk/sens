; #291 — exact quantity arithmetic laws are owned by Lisp.
; This witness preserves both the surviving Planck×Cs exact-energy law and
; the retired speed-of-light product->quotient inverse law before the last
; Rust semantic test for this slice is deleted.
;
; #369 extends the same Lisp-owned witness with quantity-library behavior that
; depends on symbol classification. The public projection is preserved rather
; than ratifying the validators' historical t/() implementation detail:
; a valid SI constant projects exactly, while a record whose NAME is a string
; does not project at all.

(load "lib/quantity.lisp")
(load "lib/si.lisp")

(0011 exact-quantity-arithmetic-rows
  (0010 ()
    ((функція (planck)
  ((функція (cesium)
    ((функція (energy)
      ((функція (one-second)
        ((функція (speed)
          ((функція (distance)
            ((функція (recovered)
              (1110
                      (1110
                        (001 planck-cesium-energy-shape)
                        (11110111
                          energy
                          (001
                            (quantity/1
                              121822045942277331/20000000000000000000000000000000000000000
                              (unit/1
                                (dimension/1 kilogram 1)
                                (dimension/1 metre 2)
                                (dimension/1 second -2)))))
                        (001 (1)))
                      (1110
                        (001 speed-times-second-distance-shape)
                        (11110111
                          distance
                          (001
                            (quantity/1
                              299792458
                              (unit/1 (dimension/1 metre 1)))))
                        (001 (1)))
                      (1110
                        (001 recovered-speed-shape)
                        (11110111
                          recovered
                          (001
                            (quantity/1
                              299792458
                              (unit/1
                                (dimension/1 metre 1)
                                (dimension/1 second -1)))))
                        (001 (1)))
                      (1110
                        (001 quotient-inverse)
                        (11110111 recovered speed)
                        (001 (1)))
                      (1110
                        (001 si-numeric-views-match-authoritative-records)
                        (1110
                          (11110111 si:cesium-frequency
                             (scientific-constant-value si:defining-cesium-frequency))
                          (11110111 si:speed-of-light
                             (scientific-constant-value si:defining-speed-of-light))
                          (11110111 si:planck-constant
                             (scientific-constant-value si:defining-planck-constant))
                          (11110111 si:elementary-charge
                             (scientific-constant-value si:defining-elementary-charge))
                          (11110111 si:boltzmann-constant
                             (scientific-constant-value si:defining-boltzmann-constant))
                          (11110111 si:avogadro-constant
                             (scientific-constant-value si:defining-avogadro-constant))
                          (11110111 si:luminous-efficacy
                             (scientific-constant-value si:defining-luminous-efficacy)))
                        (1110 (тотожне? 1 1) (тотожне? 1 1) (тотожне? 1 1) (тотожне? 1 1) (тотожне? 1 1) (тотожне? 1 1) (тотожне? 1 1)))
                      (1110
                        (001 speed-constant-knowledge-projection)
                        (scientific-constant->clauses si:defining-speed-of-light)
                        (001
                          (((scientific-constant si:speed-of-light))
                           ((constant-value si:speed-of-light 299792458))
                           ((constant-unit
                              si:speed-of-light
                              (unit/1
                                (dimension/1 metre 1)
                                (dimension/1 second -1))))
                           ((constant-status si:speed-of-light exact-by-definition))
                           ((constant-kind si:speed-of-light physical-defining))
                           ((constant-system si:speed-of-light si))
                           ((constant-source
                              si:speed-of-light
                              (science-source/1 bipm-si-brochure-9 2019))))))
                      (1110
                        (001 malformed-short-constant-does-not-project)
                        (scientific-constant->clauses
                          (001 (scientific-constant/1 broken)))
                        (001 ()))
                      (1110
                        (001 invalid-string-name-does-not-project)
                        (scientific-constant->clauses
                          (001
                            (scientific-constant/1 "not-a-symbol"
                              (quantity/1 299792458
                                (unit/1
                                  (dimension/1 metre 1)
                                  (dimension/1 second -1)))
                              exact-by-definition physical-defining si
                              (science-source/1 bipm-si-brochure-9 2019))))
                        (001 ()))))
              (quantity-quotient distance one-second)))
            (quantity-product speed one-second)))
          (scientific-constant-quantity si:defining-speed-of-light)))
        (make-quantity
                       1
                       (make-unit
                         (1110 (make-dimension (001 second) 1))))))
      (quantity-product planck cesium)))
    (scientific-constant-quantity si:defining-cesium-frequency)))
  (scientific-constant-quantity si:defining-planck-constant))))

(0011 exact-quantity-structural-equal?
  (0010 (left right)
    (110
      ((атом? left)
       (110
         ((атом? right) (тотожне? left right))
         ((атом? ()) (тотожне? 1 0))))
      ((атом? right) (тотожне? 1 0))
      ((exact-quantity-structural-equal? (перше left) (перше right))
       (exact-quantity-structural-equal? (решта left) (решта right)))
      ((атом? ()) (тотожне? 1 0)))))

(0011 exact-quantity-arithmetic-check
  (0010 (rows)
    ; D3 COND має рівно двопольові гілки; D1 1/0 — не третє поле.
    (110
      ((010 rows)
       (110
         ((101 rows (001 ()))
          (001 (exact-quantity-arithmetic-witness (status pass))))
         ((атом? ())
          (1110
            (001 exact-quantity-arithmetic-witness)
            (1110 (001 status) (001 fail))
            (1110 (001 case) (001 malformed-row-tail))
            (1110 (001 actual) rows)))))
      ((атом? ())
       (нехай ((row (100 rows)))
         (110
           ((exact-quantity-structural-equal? (1001 row) (10011 row))
            (exact-quantity-arithmetic-check (011 rows)))
           ((атом? ())
            (1110
              (001 exact-quantity-arithmetic-witness)
              (1110 (001 status) (001 fail))
              (1110 (001 case) (100 row))
              (1110 (001 actual) (1001 row))
              (1110 (001 expected) (10011 row))))))))))

(0011 exact-quantity-arithmetic-witness
  (0010 ()
    (exact-quantity-arithmetic-check (exact-quantity-arithmetic-rows))))

(exact-quantity-arithmetic-witness)
