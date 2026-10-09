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

(00001001 exact-quantity-arithmetic-rows
  (00001000 ()
    (10011101 ((planck
             (scientific-constant-quantity si:defining-planck-constant))
           (cesium
             (scientific-constant-quantity si:defining-cesium-frequency))
           (energy
             (quantity-product planck cesium))
           (one-second
             (make-quantity
               1
               (make-unit
                 (00100111 (make-dimension (00000001 second) 1)))))
           (speed
             (scientific-constant-quantity si:defining-speed-of-light))
           (distance
             (quantity-product speed one-second))
           (recovered
             (quantity-quotient distance one-second)))
      (00100111
        (00100111
          (00000001 planck-cesium-energy-shape)
          (00100010
            energy
            (00000001
              (quantity/1
                121822045942277331/20000000000000000000000000000000000000000
                (unit/1
                  (dimension/1 kilogram 1)
                  (dimension/1 metre 2)
                  (dimension/1 second -2)))))
          (00000001 (1)))
        (00100111
          (00000001 speed-times-second-distance-shape)
          (00100010
            distance
            (00000001
              (quantity/1
                299792458
                (unit/1 (dimension/1 metre 1)))))
          (00000001 (1)))
        (00100111
          (00000001 recovered-speed-shape)
          (00100010
            recovered
            (00000001
              (quantity/1
                299792458
                (unit/1
                  (dimension/1 metre 1)
                  (dimension/1 second -1)))))
          (00000001 (1)))
        (00100111
          (00000001 quotient-inverse)
          (00100010 recovered speed)
          (00000001 (1)))
        (00100111
          (00000001 si-numeric-views-match-authoritative-records)
          (00100111
            (00011100 si:cesium-frequency
               (scientific-constant-value si:defining-cesium-frequency))
            (00011100 si:speed-of-light
               (scientific-constant-value si:defining-speed-of-light))
            (00011100 si:planck-constant
               (scientific-constant-value si:defining-planck-constant))
            (00011100 si:elementary-charge
               (scientific-constant-value si:defining-elementary-charge))
            (00011100 si:boltzmann-constant
               (scientific-constant-value si:defining-boltzmann-constant))
            (00011100 si:avogadro-constant
               (scientific-constant-value si:defining-avogadro-constant))
            (00011100 si:luminous-efficacy
               (scientific-constant-value si:defining-luminous-efficacy)))
          (00000001 (1 1 1 1 1 1 1)))
        (00100111
          (00000001 speed-constant-knowledge-projection)
          (scientific-constant->clauses si:defining-speed-of-light)
          (00000001
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
        (00100111
          (00000001 malformed-short-constant-does-not-project)
          (scientific-constant->clauses
            (00000001 (scientific-constant/1 broken)))
          (00000001 ()))
        (00100111
          (00000001 invalid-string-name-does-not-project)
          (scientific-constant->clauses
            (00000001
              (scientific-constant/1 "not-a-symbol"
                (quantity/1 299792458
                  (unit/1
                    (dimension/1 metre 1)
                    (dimension/1 second -1)))
                exact-by-definition physical-defining si
                (science-source/1 bipm-si-brochure-9 2019))))
          (00000001 ()))))))

(00001001 exact-quantity-arithmetic-check
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (exact-quantity-arithmetic-witness (status pass))))
      ((00000010 rows) (1)
       (00100111
         (00000001 exact-quantity-arithmetic-witness)
         (00100111 (00000001 status) (00000001 fail))
         (00100111 (00000001 case) (00000001 malformed-row-tail))
         (00100111 (00000001 actual) rows)))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row))
            (exact-quantity-arithmetic-check (00000110 rows)))
           ((00100010
              (00100010 (00101111 row) (00110000 row))
              (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
            (00100111
              (00000001 exact-quantity-arithmetic-witness)
              (00100111 (00000001 status) (00000001 fail))
              (00100111 (00000001 case) (00000101 row))
              (00100111 (00000001 actual) (00101111 row))
              (00100111 (00000001 expected) (00110000 row))))))))))

(00001001 exact-quantity-arithmetic-witness
  (00001000 ()
    (exact-quantity-arithmetic-check (exact-quantity-arithmetic-rows))))

(exact-quantity-arithmetic-witness)
