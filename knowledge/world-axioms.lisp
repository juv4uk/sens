; knowledge/world-axioms.lisp
; Canonical name-erased primitive world-axiom authority.
; Authorities: #3374 #3386 #3434. Boot consumer: #3502.
;
; Canonical identity lives in the axiom objects below. Human SI names,
; compatibility aliases and descriptive dimension names are projections only.
; The 3-bit axiom ids are opaque stable ids, NOT function numbers and NOT
; arithmetic coordinates.

(world-axioms
  (schema . 2)
  (status . research-current)
  (class . WORLD_DEFINITION_AXIOM)
  (system-id . 000)
  (source-id . 000)
  (exactness . exact-by-definition)
  (id-semantics . opaque-stable-id-not-function-number)
  (dimension-basis-ids . (000 001 010 011 100 101 110))

  ; dimension-vector7 order is the exact order in dimension-basis-ids.
  ; Canonical objects contain no human constant names.
  (axioms
    (000
      (value . 9192631770)
      (number-system . exact-rational)
      (dimension-vector7 . (-1 0 0 0 0 0 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (001
      (value . 299792458)
      (number-system . exact-rational)
      (dimension-vector7 . (-1 1 0 0 0 0 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (010
      (value . 132521403/200000000000000000000000000000000000000000)
      (number-system . exact-rational)
      (dimension-vector7 . (-1 2 1 0 0 0 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (011
      (value . 801088317/5000000000000000000000000000)
      (number-system . exact-rational)
      (dimension-vector7 . (1 0 0 1 0 0 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (100
      (value . 1380649/100000000000000000000000000000)
      (number-system . exact-rational)
      (dimension-vector7 . (-2 2 1 0 -1 0 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (101
      (value . 602214076000000000000000)
      (number-system . exact-rational)
      (dimension-vector7 . (0 0 0 0 0 -1 0))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition))
    (110
      (value . 683)
      (number-system . exact-rational)
      (dimension-vector7 . (3 -2 -1 0 0 0 1))
      (system-id . 000)
      (source-id . 000)
      (exactness . exact-by-definition)))

  ; Everything below is a projection for humans/current library compatibility.
  ; Removing this section must not change axiom identity or exact values.
  (surface-projections
    (system
      (000 . SI))
    (sources
      (000 . (bipm-si-brochure-9 2019)))
    (dimensions
      (000 . second)
      (001 . metre)
      (010 . kilogram)
      (011 . ampere)
      (100 . kelvin)
      (101 . mole)
      (110 . candela))
    (axioms
      (000
        (record . si:defining-cesium-frequency)
        (projection . si:cesium-frequency)
        (compatibility-alias . delta-nu-cs))
      (001
        (record . si:defining-speed-of-light)
        (projection . si:speed-of-light)
        (compatibility-alias . c))
      (010
        (record . si:defining-planck-constant)
        (projection . si:planck-constant)
        (compatibility-alias . h))
      (011
        (record . si:defining-elementary-charge)
        (projection . si:elementary-charge)
        (compatibility-alias . e))
      (100
        (record . si:defining-boltzmann-constant)
        (projection . si:boltzmann-constant)
        (compatibility-alias . k))
      (101
        (record . si:defining-avogadro-constant)
        (projection . si:avogadro-constant)
        (compatibility-alias . n-a))
      (110
        (record . si:defining-luminous-efficacy)
        (projection . si:luminous-efficacy)
        (compatibility-alias . k-cd))))

  (epistemic-boundary
    (WORLD_DEFINITION_AXIOM . primitive-starting-fact)
    (MODEL_LAW . separately-admitted-world-relation)
    (OBSERVATION . contingent-external-evidence)
    (DERIVED_FACT . certified-consequence)
    (UNKNOWN . no-live-proof-path))

  (rule . "surface names are projections; primitive world identity is the name-erased exact axiom object"))
