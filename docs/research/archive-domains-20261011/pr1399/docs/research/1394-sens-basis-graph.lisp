; #1394 — виконувана схема дослідження базису СЕНС.
; Research-only. НЕ semantic authority. НЕ production dispatch.
;
; Мета: описати граф гіпотез про взаємну вивідність exact 8-bit functions
; без людських назв, без legacy ID/name round-trip і без host semantic oracle.
;
; Важливо: порядок байтів нижче НЕ означає semantic order або важливість.
; Жодна красива гіпотеза не стає фактом без звірки з current main/evidence.

(sens-basis-research/1
  (issue 1394)
  (role research-only)
  (production-change none)

  (reality-gate
    (baseline-main "95ebc6678dd17e4130febf731f7a0160f0f889cd")
    (owner-directive 1384)
    (rule
      "Ідея допускається лише якщо не суперечить чинному спостережуваному стану, ратифікованому закону або stronger executable evidence.")
    (authority-conflict
      classify blocked-by-reality-drift
      do-not-infer-semantic-law)
    (historical-branch
      donor-only
      never-current-reality-by-itself))

  ; На baseline main реально існує перехідний drift між новою SENS-моделлю
  ; та старою нормативною/механічною термінологією. Це observation, не дозвіл
  ; вибрати з конфлікту зручну сторону.
  (observed-current-drift
    (language-contract contains-legacy-SID-vocabulary)
    (semantic-authority-map contains-historical-project-name)
    (function-table-mechanisms
      contains-transitional-00000000-empty-list-ground-row)
    (resolution
      "до reconciliation не будувати semantic conclusion на цих конфліктних місцях"))

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

  ; Спочатку жодного semantic edge не оголошуємо.
  ; Наступний slice має додавати relation тільки разом із current-baseline witness.
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

  (handoff
    (local-agent
      "реалізувати незалежний read-only runner над current main snapshot; не редагувати production runtime; окремо репортувати всі drift/conflicts")
    (web-agent
      "додавати лише relations, для яких є explicit current-baseline witness і current-Core scope")
    (reviewer
      "шукати приховану circularity, semantic ordering, host oracle leaks і підміну reality красивою моделлю")))

