; #1394 — виконувана схема дослідження базису СЕНС.
; Research-only. НЕ semantic authority. НЕ production dispatch.
;
; Baseline: sens/main@33bfb53a51beb81812bd97c14c710a1095b125a9
;
; Мета: описати граф гіпотез про взаємну вивідність exact 8-bit SENS functions
; без людських назв, без legacy ID/name round-trip і без host semantic oracle.
;
; Важливо: порядок байтів нижче НЕ означає semantic order або важливість.
; Жодна красива гіпотеза не стає фактом без звірки з current main/evidence.

(sens-basis-research/1
  (issue 1394)
  (role research-only)
  (production-change none)

  (reality-gate
    (baseline-main "33bfb53a51beb81812bd97c14c710a1095b125a9")
    (owner-directive 1384)
    (reconciliation-issues (1403 1406))
    (rule
      "Ідея допускається лише якщо не суперечить current executable behavior, owner-ratified law або stronger current evidence.")
    (historical-branch
      donor-only
      never-current-reality-by-itself)
    (authority-conflict
      classify blocked-by-reality-drift
      do-not-infer-semantic-law))

  ; Current-main reality check found a concrete drift:
  ; commit 170b2e7 already removed () from function 00000000 in runtime/IR,
  ; while Contract 9.0 and transitional mechanism metadata still describe that
  ; state as current debt / empty-list-ground. #1403 owns reconciliation.
  (observed-current-drift
    (empty-structure-runtime
      outside-function-space
      evidence "170b2e71ddfbf96d39c80c67888adc9770b66aa3")
    (language-contract
      still-describes-1332-as-current-debt)
    (function-table-mechanisms
      still-contains-00000000-empty-list-ground)
    (host-registration
      merged-main "33bfb53a51beb81812bd97c14c710a1095b125a9"
      generic-fallback-may-create-callability
      evidence-issue 1406
      red-witness-pr 1407)
    (resolution
      blocked-by-reality-drift-until-1403-and-1406))

  (function-space
    (cardinality 256)
    (first 00000000)
    (last 11111111)
    (node-key exact-eight-bit-function)
    (extra-identity-layer forbidden)
    (numeric-order-semantic-meaning forbidden))

  ; Перший bounded corpus — лише технічний зріз для перевірки machinery.
  ; Він не оголошує ці функції фундаментальнішими за решту.
  (seed-corpus
    00000000
    00000001
    00000010
    00000011
    00000100
    00000101
    00000110
    00000111)

  (allowed-classifications
    derived-on-declared-domain
    not-derived-within-bounded-search
    basis-exchange-only
    insufficient-evidence
    blocked-by-reality-drift
    unmeasured)

  (relation-schema
    (target exact-eight-bit-function)
    (basis exact-eight-bit-functions)
    (core explicit)
    (domain explicit)
    (baseline explicit)
    (bound explicit)
    (witness explicit)
    (classification one-of-allowed-classifications))

  (circularity-guards
    (target-in-basis reject)
    (human-surface-roundtrip reject)
    (legacy-id-wrapper reject)
    (host-shape-oracle reject)
    (backend-semantic-enum reject)
    (foreign-operator-name-roundtrip reject)
    (hidden-target-through-generated-alias reject))

  (evidence-discipline
    (positive-edge requires-executable-witness)
    (negative-edge requires-explicit-bound)
    (claim requires-current-baseline)
    (conflicting-authorities require-blocked-classification)
    (basis-exchange is-not strict-reduction)
    (absence-of-edge is-not irreducibility)
    (unmeasured is-not false)
    (old-branch-success is-not current-main-success))

  ; Поки #1403 і #1406 не звели current authoritative layers, жодного semantic edge
  ; для функцій, зачеплених drift, не оголошуємо.
  (candidate-relations ())

  (first-falsification
    (remove-all-surface-tables
      expected research-schema-remains-addressable)
    (inject-target-into-basis
      expected circularity-reject)
    (replace-function-with-human-name
      expected node-key-reject)
    (omit-bound-from-negative-claim
      expected evidence-reject)
    (use-historical-branch-as-current-proof
      expected reality-gate-reject)
    (claim-across-authority-drift
      expected blocked-by-reality-drift))

  (coordination
    (web-agent
      "підтримує schema/evidence classes; після #1403/#1406 додає перший current-main witness")
    (local-agent
      "незалежно перевіряє main@33bfb53: runtime () vs 00000000 та host-registration admission leak; production не редагує; контрприклади репортує в #1403/#1406")
    (reviewer
      "шукає circularity, semantic ordering, host oracle leaks і підміну evidence красивою моделлю")))
