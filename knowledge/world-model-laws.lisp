; Явні фізичні закони й закони моделі для міркувань про світ.
; Джерело: #3402. Ідентифікатори аксіом походять із knowledge/world-axioms.lisp.
; Людський запис формул є проєкцією; тотожність залежностей не
; визначається людськими назвами.

(world-model-laws
  (schema . 2)
  (authority . 3402)
  (status . research-current)

  (laws
    (000
      (class . MODEL_LAW)
      (axiom-dependencies . (010))
      (binary-function-number . (D5 10110))
      (input-roles . ((000 WORLD_DEFINITION_AXIOM)
                      (001 OBSERVATION-OR-DERIVED-FREQUENCY)))
      (output-role . DERIVED_FACT)
      (quantity-operation . quantity-product)
      (assumptions . (000))
      (validity . conditional)
      (repo-witness . "tests/fixtures/exact-quantity-arithmetic-witness.lisp")
      (first-exact-replay
        . ((axiom-id . 010)
           (frequency-axiom-id . 000)
           (result-kind-id . 000))))

    (001
      (class . MODEL_LAW)
      (axiom-dependencies . (001))
      (binary-function-number . (D5 10110))
      (input-roles . ((000 WORLD_DEFINITION_AXIOM)
                      (001 OBSERVATION-OR-DERIVED-DURATION)))
      (output-role . DERIVED_FACT)
      (quantity-operation . quantity-product)
      (assumptions . (001 010))
      (validity . conditional)
      (repo-witness . "tests/fixtures/exact-quantity-arithmetic-witness.lisp")))

  (surface-projections
    (laws
      (000
        (name . planck-energy-frequency)
        (relation . "E = h * nu")
        (assumption-000 . frequency-describes-the-relevant-quantum-transition))
      (001
        (name . light-propagation-distance)
        (relation . "d = c * t")
        (assumption-001 . light-propagation-at-c)
        (assumption-010 . path-length-equals-speed-times-duration))))

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

  ; Арифметика розмірностей сама собою не надає фізичного значення.
  (rule . "Сама лише розмірнісно коректна арифметика не створює фізичного змісту"))
