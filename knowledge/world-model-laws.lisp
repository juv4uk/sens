; knowledge/world-model-laws.lisp
; Explicit physical/model laws for world reasoning.
; Authority: #3402. These laws are distinct from axioms, observations and
; arithmetic mechanisms.

(world-model-laws
  (schema . 1)
  (authority . 3402)
  (status . research-current)

  (laws
    (planck-energy-frequency
      (class . MODEL_LAW)
      (relation . "E = h * nu")
      (axiom-dependencies . (si:defining-planck-constant))
      (input-roles . ((h WORLD_DEFINITION_AXIOM)
                      (nu OBSERVATION-OR-DERIVED-FREQUENCY)))
      (output-role . DERIVED_FACT)
      (quantity-operation . quantity-product)
      (binary-function-role . multiplication)
      (assumptions . (frequency-describes-the-relevant-quantum-transition))
      (validity . conditional)
      (repo-witness . "tests/fixtures/exact-quantity-arithmetic-witness.lisp")
      (first-exact-replay
        . ((h . si:defining-planck-constant)
           (nu . si:defining-cesium-frequency)
           (result-kind . energy))))

    (light-propagation-distance
      (class . MODEL_LAW)
      (relation . "d = c * t")
      (axiom-dependencies . (si:defining-speed-of-light))
      (input-roles . ((c WORLD_DEFINITION_AXIOM)
                      (t OBSERVATION-OR-DERIVED-DURATION)))
      (output-role . DERIVED_FACT)
      (quantity-operation . quantity-product)
      (binary-function-role . multiplication)
      (assumptions . (light-propagation-at-c path-length-equals-speed-times-duration))
      (validity . conditional)
      (repo-witness . "tests/fixtures/exact-quantity-arithmetic-witness.lisp")))

  (certificate-required
    (axiom-ids)
    (law-id)
    (observation-ids)
    (binary-function-numbers)
    (operation-tree)
    (result)
    (dimension-unit)
    (assumptions)
    (uncertainty-exactness)
    (provenance))

  (rule
    . "dimensionally valid arithmetic alone does not create physical meaning"))
