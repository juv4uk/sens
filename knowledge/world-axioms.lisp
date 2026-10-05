; knowledge/world-axioms.lisp
; Machine-readable epistemic authority for initial world-definition axioms.
; Authority: #3374 / #3386.
;
; Numeric values are NOT duplicated here. Each axiom points to its single
; exact scientific-constant/1 record in lib/si.lisp.

(world-axioms
  (schema . 1)
  (authority . 3386)
  (status . current)
  (class . WORLD_DEFINITION_AXIOM)
  (system . SI)
  (source . (bipm-si-brochure-9 2019))
  (exactness . exact-by-definition)
  (value-authority . "lib/si.lisp")

  (axioms
    (delta-nu-cs
      (record . si:defining-cesium-frequency)
      (projection . si:cesium-frequency))
    (c
      (record . si:defining-speed-of-light)
      (projection . si:speed-of-light))
    (h
      (record . si:defining-planck-constant)
      (projection . si:planck-constant))
    (e
      (record . si:defining-elementary-charge)
      (projection . si:elementary-charge))
    (k
      (record . si:defining-boltzmann-constant)
      (projection . si:boltzmann-constant))
    (n-a
      (record . si:defining-avogadro-constant)
      (projection . si:avogadro-constant))
    (k-cd
      (record . si:defining-luminous-efficacy)
      (projection . si:luminous-efficacy)))

  (epistemic-boundary
    (world-definition-axiom . "exact defining fact in the selected SI system")
    (model-law . "relation licensed separately; not created by arithmetic")
    (observation . "contingent external input with provenance/uncertainty")
    (derived-fact . "result certified from admitted dependencies")
    (unknown . "no admitted evidence")))
