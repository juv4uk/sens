; #291 — exact quantity arithmetic laws are owned by Lisp.
; Ukrainian projection only.
;
; #369: valid SI constant projects exactly; string NAME does not project.

(load "lib/quantity.lisp")
(load "lib/si.lisp")

(визначити exact-quantity-arithmetic-rows
  (функція ()
    ((функція (planck)
  ((функція (cesium)
    ((функція (energy)
      ((функція (one-second)
        ((функція (speed)
          ((функція (distance)
            ((функція (recovered)
              (список
                      (список
                        (як-є planck-cesium-energy-shape)
                        (однакові?
                          energy
                          (як-є
                            (quantity/1
                              121822045942277331/20000000000000000000000000000000000000000
                              (unit/1
                                (dimension/1 kilogram 1)
                                (dimension/1 metre 2)
                                (dimension/1 second -2)))))
                        (як-є (1)))
                      (список
                        (як-є speed-times-second-distance-shape)
                        (однакові?
                          distance
                          (як-є
                            (quantity/1
                              299792458
                              (unit/1 (dimension/1 metre 1)))))
                        (як-є (1)))
                      (список
                        (як-є recovered-speed-shape)
                        (однакові?
                          recovered
                          (як-є
                            (quantity/1
                              299792458
                              (unit/1
                                (dimension/1 metre 1)
                                (dimension/1 second -1)))))
                        (як-є (1)))
                      (список
                        (як-є quotient-inverse)
                        (однакові? recovered speed)
                        (як-є (1)))
                      (список
                        (як-є si-constant-projects)
                        (scientific-constant->clauses si:defining-speed-of-light)
                        (як-є (1)))
                      (список
                        (як-є string-name-does-not-project)
                        (scientific-constant->clauses
                          (як-є
                            (scientific-constant/1 "not-a-symbol"
                              (quantity/1 299792458
                                (unit/1
                                  (dimension/1 metre 1)
                                  (dimension/1 second -1)))
                              exact-by-definition physical-defining si
                              (science-source/1 bipm-si-brochure-9 2019))))
                        (як-є ()))))
              (quantity-quotient distance one-second)))
            (quantity-product speed one-second)))
          (scientific-constant-quantity si:defining-speed-of-light)))
        (make-quantity
                       1
                       (make-unit
                         (список (make-dimension (як-є second) 1))))))
      (quantity-product planck cesium)))
    (scientific-constant-quantity si:defining-cesium-frequency)))
  (scientific-constant-quantity si:defining-planck-constant))))

(визначити exact-quantity-structural-equal?
  (функція (left right)
    (за-умовою
      ((атом? left)
       (за-умовою
         ((атом? right) (тотожне? left right))
         ((атом? ()) (тотожне? 1 0))))
      ((атом? right) (тотожне? 1 0))
      ((exact-quantity-structural-equal? (перше left) (перше right))
       (exact-quantity-structural-equal? (решта left) (решта right)))
      ((атом? ()) (тотожне? 1 0)))))

(визначити exact-quantity-arithmetic-check
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (за-умовою
         ((тотожне? rows (як-є ()))
          (як-є (exact-quantity-arithmetic-witness (status pass))))
         ((атом? ())
          (список
            (як-є exact-quantity-arithmetic-witness)
            (список (як-є status) (як-є fail))
            (список (як-є case) (як-є malformed-row-tail))
            (список (як-є actual) rows)))))
      ((атом? ())
       (нехай ((row (перше rows)))
         (за-умовою
           ((exact-quantity-structural-equal? (друге row) (третє row))
            (exact-quantity-arithmetic-check (решта rows)))
           ((атом? ())
            (список
              (як-є exact-quantity-arithmetic-witness)
              (список (як-є status) (як-є fail))
              (список (як-є case) (перше row))
              (список (як-є actual) (друге row))
              (список (як-є expected) (третє row))))))))))

(визначити exact-quantity-arithmetic-witness
  (функція ()
    (exact-quantity-arithmetic-check (exact-quantity-arithmetic-rows))))

(exact-quantity-arithmetic-witness)
