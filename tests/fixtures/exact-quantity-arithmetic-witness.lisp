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

(def exact-quantity-arithmetic-rows
  (lambda ()
    (let* ((planck
             (scientific-constant-quantity si:defining-planck-constant))
           (cesium
             (scientific-constant-quantity si:defining-cesium-frequency))
           (energy
             (quantity-product planck cesium))
           (one-second
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
          (quote planck-cesium-energy-shape)
          (equal?
            energy
            (quote
              (quantity/1
                121822045942277331/20000000000000000000000000000000000000000
                (unit/1
                  (dimension/1 kilogram 1)
                  (dimension/1 metre 2)
                  (dimension/1 second -2)))))
          (quote (1)))
        (list
          (quote speed-times-second-distance-shape)
          (equal?
            distance
            (quote
              (quantity/1
                299792458
                (unit/1 (dimension/1 metre 1)))))
          (quote (1)))
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
          (quote (1)))
        (list
          (quote quotient-inverse)
          (equal? recovered speed)
          (quote (1)))
        (list
          (quote si-numeric-views-match-authoritative-records)
          (list
            (= si:cesium-frequency
               (scientific-constant-value si:defining-cesium-frequency))
            (= si:speed-of-light
               (scientific-constant-value si:defining-speed-of-light))
            (= si:planck-constant
               (scientific-constant-value si:defining-planck-constant))
            (= si:elementary-charge
               (scientific-constant-value si:defining-elementary-charge))
            (= si:boltzmann-constant
               (scientific-constant-value si:defining-boltzmann-constant))
            (= si:avogadro-constant
               (scientific-constant-value si:defining-avogadro-constant))
            (= si:luminous-efficacy
               (scientific-constant-value si:defining-luminous-efficacy)))
          (quote (1 1 1 1 1 1 1)))
        (list
          (quote speed-constant-knowledge-projection)
          (scientific-constant->clauses si:defining-speed-of-light)
          (quote
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
        (list
          (quote malformed-short-constant-does-not-project)
          (scientific-constant->clauses
            (quote (scientific-constant/1 broken)))
          (quote ()))
        (list
          (quote invalid-string-name-does-not-project)
          (scientific-constant->clauses
            (quote
              (scientific-constant/1 "not-a-symbol"
                (quantity/1 299792458
                  (unit/1
                    (dimension/1 metre 1)
                    (dimension/1 second -1)))
                exact-by-definition physical-defining si
                (science-source/1 bipm-si-brochure-9 2019))))
          (quote ()))))))

(def exact-quantity-arithmetic-check
  (lambda (rows)
    (cond
      ((atom? rows) ()
       (quote (exact-quantity-arithmetic-witness (status pass))))
      ((atom? rows) (1)
       (list
         (quote exact-quantity-arithmetic-witness)
         (list (quote status) (quote fail))
         (list (quote case) (quote malformed-row-tail))
         (list (quote actual) rows)))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (1)
            (exact-quantity-arithmetic-check (cdr rows)))
           ((equal? (second row) (third row)) (0)
            (list
              (quote exact-quantity-arithmetic-witness)
              (list (quote status) (quote fail))
              (list (quote case) (car row))
              (list (quote actual) (second row))
              (list (quote expected) (third row))))))))))

(def exact-quantity-arithmetic-witness
  (lambda ()
    (exact-quantity-arithmetic-check (exact-quantity-arithmetic-rows))))

(exact-quantity-arithmetic-witness)
