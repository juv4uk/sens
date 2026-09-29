; Core4 predicate/record migration inventory — #1259 under Contract 9.
;
; The ONLY function identity in this file is the bare exact 8-bit value.
; Human surface names do not appear as function identities.
;
; This inventory classifies result roles only. It does not change runtime
; behavior and does not define predicate meaning.
;
; Roles:
;   predicate-question  — asks a directional question.
;   classifier-observer — returns richer descriptive observation data.
;   control-consumer    — consumes another operation's exact result domain.
;
; Core1, Core2 and Core3 are out of scope.

(core4-predicate-record-inventory/2

  ((profile . core4)
   (status . inventory-only)
   (function-identity . exact-8-bits-only)
   (named-function-ontology . forbidden)
   (semantic-change . forbidden)
   (mass-rewrite . forbidden)
   (performance-wrapper-audit . separate-axis-1277-1278)
   (host-capability-dispatch-gap . separate-axis-1276)
   (function-width-fpga-economics . separate-axis-1279-1280)
   (table-first-bootstrap-vision . out-of-scope-1281)
   (core1-core2-core3 . out-of-scope))

  ((function . 00000010)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . classifier-observer)
   (current-result . structural-kind)
   (target-role . classifier-observer)
   (migration . retain-richer-classifier-data))

  ((function . 00000011)
   (authority . tests/fixtures/semantic/eq-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((function . 00100010)
   (authority . tests/fixtures/semantic/predicate-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((function . 00100011)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00100100)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00100110)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00000111)
   (authority . contracts/control-dispatch-contract.lisp)
   (current-role . control-consumer)
   (current-result . explicit-result-equality)
   (target-role . control-consumer)
   (migration . producer-laws-first)
   (compatibility-result . historical-truthiness)
   (compatibility-role . compatibility-only)))
