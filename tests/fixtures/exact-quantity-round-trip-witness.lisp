; #291 — exact quantity product/quotient preservation belongs to Lisp.
; This preserves the useful law retired from the legacy Rust truth-sentinel test:
; c * 1 second gives an exact distance, and dividing by the same second
; recovers the original exact speed-of-light quantity.
;
; Expected semantic relations live here as Lisp data. Rust may only observe
; the named pass/fail envelope.

(def exact-quantity-round-trip-rows
  (lambda ()
    (let* ((one-second
             (make-quantity
               1
               (make-unit
                 (list (make-dimension (quote second) 1)))))
           (speed
             (scientific-constant-quantity si:defining-speed-of-light))
           (distance
             (quantity-product speed one-second))
           (recovered
             (quantity-quotient distance one-second)))
      (list
        (list
          (quote distance-shape)
          (equal?
            distance
            (quote
              (quantity/1
                299792458
                (unit/1 (dimension/1 metre 1)))))
          (quote (structural-relation same)))
        (list
          (quote recovered-speed-shape)
          (equal?
            recovered
            (quote
              (quantity/1
                299792458
                (unit/1
                  (dimension/1 metre 1)
                  (dimension/1 second -1)))))
          (quote (structural-relation same)))
        (list
          (quote quotient-inverse)
          (equal? recovered speed)
          (quote (structural-relation same)))))))

(def exact-quantity-round-trip-check
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (exact-quantity-round-trip-witness (status pass))))
      ((atom rows) (structural-kind atom)
       (list
         (quote exact-quantity-round-trip-witness)
         (list (quote status) (quote fail))
         (list (quote case) (quote malformed-row-tail))
         (list (quote actual) rows)))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (exact-quantity-round-trip-check (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (list
              (quote exact-quantity-round-trip-witness)
              (list (quote status) (quote fail))
              (list (quote case) (car row))
              (list (quote actual) (second row))
              (list (quote expected) (third row))))))))))

(def exact-quantity-round-trip-witness
  (lambda ()
    (exact-quantity-round-trip-check (exact-quantity-round-trip-rows))))
