; #291 — exact quantity product/quotient preservation belongs to Lisp.
; This preserves the useful law retired from the legacy Rust truth-sentinel test:
; c * 1 second gives an exact distance, and dividing by the same second
; recovers the original exact speed-of-light quantity.
;
; Expected semantic relations live here as Lisp data. Rust may only observe
; the named pass/fail envelope.

(визначити exact-quantity-round-trip-rows
  (функція ()
    (нехай-послідовно ((one-second
             (make-quantity
               1
               (make-unit
                 (список (make-dimension (як-є second) 1)))))
           (speed
             (scientific-constant-quantity si:defining-speed-of-light))
           (distance
             (quantity-product speed one-second))
           (recovered
             (quantity-quotient distance one-second)))
      (список
        (список
          (як-є distance-shape)
          (однакові?
            distance
            (як-є
              (quantity/1
                299792458
                (unit/1 (dimension/1 metre 1)))))
          (як-є (structural-relation same)))
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
          (як-є (structural-relation same)))
        (список
          (як-є quotient-inverse)
          (однакові? recovered speed)
          (як-є (structural-relation same)))))))

(визначити exact-quantity-round-trip-check
  (функція (rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list)
       (як-є (exact-quantity-round-trip-witness (status pass))))
      ((атом? rows) (structural-kind atom)
       (список
         (як-є exact-quantity-round-trip-witness)
         (список (як-є status) (як-є fail))
         (список (як-є case) (як-є malformed-row-tail))
         (список (як-є actual) rows)))
      ((атом? rows) (structural-kind pair)
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (друге row) (третє row)) (structural-relation same)
            (exact-quantity-round-trip-check (решта rows)))
           ((однакові? (друге row) (третє row)) (structural-relation distinct)
            (список
              (як-є exact-quantity-round-trip-witness)
              (список (як-є status) (як-є fail))
              (список (як-є case) (перше row))
              (список (як-є actual) (друге row))
              (список (як-є expected) (третє row))))))))))

(визначити exact-quantity-round-trip-witness
  (функція ()
    (exact-quantity-round-trip-check (exact-quantity-round-trip-rows))))
