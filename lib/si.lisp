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

(визначити si:defining-cesium-frequency
  (як-є
    (scientific-constant/1 si:cesium-frequency
      (quantity/1 9192631770
        (unit/1
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(визначити si:defining-speed-of-light
  (як-є
    (scientific-constant/1 si:speed-of-light
      (quantity/1 299792458
        (unit/1
          (dimension/1 metre 1)
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(визначити si:defining-planck-constant
  (як-є
    (scientific-constant/1 si:planck-constant
      (quantity/1
        132521403/200000000000000000000000000000000000000000
        (unit/1
          (dimension/1 kilogram 1)
          (dimension/1 metre 2)
          (dimension/1 second -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(визначити si:defining-elementary-charge
  (як-є
    (scientific-constant/1 si:elementary-charge
      (quantity/1
        801088317/5000000000000000000000000000
        (unit/1
          (dimension/1 ampere 1)
          (dimension/1 second 1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(визначити si:defining-boltzmann-constant
  (як-є
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

(визначити si:defining-avogadro-constant
  (як-є
    (scientific-constant/1 si:avogadro-constant
      (quantity/1 602214076000000000000000
        (unit/1
          (dimension/1 mole -1)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

(визначити si:defining-luminous-efficacy
  (як-є
    (scientific-constant/1 si:luminous-efficacy
      (quantity/1 683
        (unit/1
          (dimension/1 candela 1)
          (dimension/1 kilogram -1)
          (dimension/1 metre -2)
          (dimension/1 second 3)))
      exact-by-definition physical-defining si
      (science-source/1 bipm-si-brochure-9 2019))))

; Exact D5:10011 CADDR followed by D4:1001 CADR.
; Only the projection is refactored; BIPM SI records remain unchanged.
; A scientific-constant/1 record stores its quantity in the third field; a
; quantity/1 stores its numeric value in the second field.
(визначити si:constant-value
  (функція (наукова-константа)
    (друге (третє наукова-константа))))

; Backward-compatible arithmetic surface, derived from the records above.
(визначити si:cesium-frequency (si:constant-value si:defining-cesium-frequency))
(визначити si:speed-of-light (si:constant-value si:defining-speed-of-light))
(визначити si:planck-constant (si:constant-value si:defining-planck-constant))
(визначити si:elementary-charge (si:constant-value si:defining-elementary-charge))
(визначити si:boltzmann-constant (si:constant-value si:defining-boltzmann-constant))
(визначити si:avogadro-constant (si:constant-value si:defining-avogadro-constant))
(визначити si:luminous-efficacy (si:constant-value si:defining-luminous-efficacy))

; Transitional compatibility aliases. These are not canonical names and may
; be removed once repository callers have migrated to the descriptive surface.
(визначити delta-nu-cs si:cesium-frequency)
(визначити c si:speed-of-light)
(визначити h si:planck-constant)
(визначити e si:elementary-charge)
(визначити k si:boltzmann-constant)
(визначити n-a si:avogadro-constant)
(визначити k-cd si:luminous-efficacy)
(визначити si:delta-nu-cs si:cesium-frequency)
(визначити si:c si:speed-of-light)
(визначити si:h si:planck-constant)
(визначити si:e si:elementary-charge)
(визначити si:k si:boltzmann-constant)
(визначити si:n-a si:avogadro-constant)
(визначити si:k-cd si:luminous-efficacy)
