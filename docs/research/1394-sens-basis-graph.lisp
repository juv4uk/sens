; #1394 — виконувана схема дослідження базису СЕНС.
; Research-only. НЕ semantic authority. НЕ production dispatch.
;
; Мета: описати граф гіпотез про взаємну вивідність exact 8-bit functions
; без людських назв, без SID/name round-trip і без host semantic oracle.
;
; Важливо: порядок байтів нижче НЕ означає semantic order або важливість.

(sens-basis-research/1
  (issue 1394)
  (role research-only)
  (production-change none)

  (function-space
    (cardinality 256)
    (first 00000000)
    (last 11111111)
    (node-identity exact-eight-bits)
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
    unmeasured)

  (relation-schema
    (target exact-eight-bit-function)
    (basis exact-eight-bit-functions)
    (core explicit)
    (domain explicit)
    (bound explicit)
    (witness explicit)
    (classification one-of-allowed-classifications))

  (circularity-guards
    (target-in-basis reject)
    (human-surface-roundtrip reject)
    (sid-or-semantic-id-wrapper reject)
    (host-shape-oracle reject)
    (backend-semantic-enum reject)
    (foreign-operator-name-roundtrip reject)
    (hidden-target-through-generated-alias reject))

  (evidence-discipline
    (positive-edge requires-executable-witness)
    (negative-edge requires-explicit-bound)
    (basis-exchange is-not strict-reduction)
    (absence-of-edge is-not irreducibility)
    (unmeasured is-not false))

  ; Спочатку жодного semantic edge не оголошуємо.
  ; Наступний slice має додавати relation тільки разом із witness.
  (candidate-relations ())

  (first-falsification
    (remove-all-surface-tables
      expected research-schema-remains-addressable)
    (inject-target-into-basis
      expected circularity-reject)
    (replace-function-with-human-name
      expected node-key-reject)
    (omit-bound-from-negative-claim
      expected evidence-reject))

  (handoff
    (local-agent
      "реалізувати незалежний read-only runner над current main snapshot; не редагувати production runtime")
    (web-agent
      "додавати лише relations, для яких є explicit witness і current-Core scope")
    (reviewer
      "шукати приховану circularity, semantic ordering та host oracle leaks")))

