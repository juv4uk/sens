; lib/si.lisp — 7 BIPM SI defining constants as exact scientific data
; 7 визначальних констант SI (BIPM 2019) як точні Lisp-дані
;
; Reference: BIPM SI Brochure (9th edition, 2019)
;
; Each defining constant has one authoritative finite-data record:
;
;   (scientific-constant/1 NAME
;     (quantity/1 VALUE
;       (unit/1 (dimension/1 BASE EXPONENT) ...))
;     exact-by-definition physical-defining si
;     (science-source/1 bipm-si-brochure-9 2019))
;
; Authoritative records live under the regular `si:defining-*` surface. The
; established numeric names remain backward-compatible arithmetic views, but
; their values are extracted from those records rather than duplicated as a
; second authority. lib/quantity.lisp provides the general validators/accessors;
; this file itself remains standalone-loadable and derives numeric views using
; only car/cdr.
;
; Every base dimension is a named `(dimension/1 BASE EXPONENT)` term so the
; same unit data is directly admissible to the Advice Taker knowledge grammar.
; Unit algebra itself is not claimed here.

(00001001 si:defining-cesium-frequency
  (00000001
    (scientific-constant/1 si:cesium-frequency
      (quantity/1 9192631770
        (unit/1
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-speed-of-light
  (00000001
    (scientific-constant/1 si:speed-of-light
      (quantity/1 299792458
        (unit/1
          (dimension/1 metre 1)
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-planck-constant
  (00000001
    (scientific-constant/1 si:planck-constant
      (quantity/1
        132521403/200000000000000000000000000000000000000000
        (unit/1
          (dimension/1 kilogram 1)
          (dimension/1 metre 2)
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-elementary-charge
  (00000001
    (scientific-constant/1 si:elementary-charge
      (quantity/1
        801088317/5000000000000000000000000000
        (unit/1
          (dimension/1 ampere 1)
          (dimension/1 second 1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-boltzmann-constant
  (00000001
    (scientific-constant/1 si:boltzmann-constant
      (quantity/1
        1380649/100000000000000000000000000000
        (unit/1
          (dimension/1 kilogram 1)
          (dimension/1 metre 2)
          (dimension/1 second -2)
          (dimension/1 kelvin -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-avogadro-constant
  (00000001
    (scientific-constant/1 si:avogadro-constant
      (quantity/1 602214076000000000000000
        (unit/1
          (dimension/1 mole -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(00001001 si:defining-luminous-efficacy
  (00000001
    (scientific-constant/1 si:luminous-efficacy
      (quantity/1 683
        (unit/1
          (dimension/1 candela 1)
          (dimension/1 kilogram -1)
          (dimension/1 metre -2)
          (dimension/1 second 3)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

; A scientific-constant/1 record stores its quantity in the third field; a
; quantity/1 stores its numeric value in the second field.
(00001001 si:constant-value
  (00001000 (constant)
    (00000101 (00000110 (00000101 (00000110 (00000110 constant)))))))

; Backward-compatible arithmetic surface, derived from the records above.
(00001001 si:cesium-frequency (si:constant-value si:defining-cesium-frequency))
(00001001 si:speed-of-light (si:constant-value si:defining-speed-of-light))
(00001001 si:planck-constant (si:constant-value si:defining-planck-constant))
(00001001 si:elementary-charge (si:constant-value si:defining-elementary-charge))
(00001001 si:boltzmann-constant (si:constant-value si:defining-boltzmann-constant))
(00001001 si:avogadro-constant (si:constant-value si:defining-avogadro-constant))
(00001001 si:luminous-efficacy (si:constant-value si:defining-luminous-efficacy))

; Transitional compatibility aliases. These are not canonical names and may
; be removed once repository callers have migrated to the descriptive surface.
(00001001 delta-nu-cs si:cesium-frequency)
(00001001 c si:speed-of-light)
(00001001 h si:planck-constant)
(00001001 e si:elementary-charge)
(00001001 k si:boltzmann-constant)
(00001001 n-a si:avogadro-constant)
(00001001 k-cd si:luminous-efficacy)
(00001001 si:delta-nu-cs si:cesium-frequency)
(00001001 si:c si:speed-of-light)
(00001001 si:h si:planck-constant)
(00001001 si:e si:elementary-charge)
(00001001 si:k si:boltzmann-constant)
(00001001 si:n-a si:avogadro-constant)
(00001001 si:k-cd si:luminous-efficacy)
