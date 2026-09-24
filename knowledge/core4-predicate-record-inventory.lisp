; Core4 predicate/record migration inventory — #1259.
;
; Inventory only.  This file does not change any runtime result and does not
; define predicate semantics.  It records which Lisp-owned authority currently
; owns each result shape so later bounded migrations do not confuse a
; predicate answer with classifier/observer data.
;
; Roles:
;   predicate-question  — caller asks a yes/no-direction question.
;   classifier-observer — richer descriptive data is the point of the API.
;   control-consumer    — consumes another domain's exact result.
;   compatibility       — historical/migration-only behavior.
;   test-only           — evidence, never semantic authority.
;
; Migration rule:
;   predicate-question -> Core4 predicate-answer domain, one bounded slice.
;   classifier-observer -> retain unless an explicit separate issue changes it.
;   control-consumer -> update only after producer result law is ratified.
;   compatibility/test-only -> isolate; never use as new authority.
;
; Core1, Core2 and Core3 are explicitly out of scope.

(core4-predicate-record-inventory/1

  ((profile . core4)
   (status . inventory-only)
   (semantic-change . forbidden)
   (mass-string-replacement . forbidden)
   (core1-core2-core3 . out-of-scope))

  ((surface . atom)
   (sid . 00000010)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . classifier-observer)
   (current-result . structural-kind)
   (target-role . classifier-observer)
   (migration . retain-richer-classifier-data)
   (note . "If Core4 later needs atom? as a simple question, split that question from this classifier explicitly; do not erase structural-kind by replacement."))

  ((surface . eq)
   (sid . 00000011)
   (authority . contracts/answer-contract.lisp)
   (current-role . classifier-observer)
   (current-result . identity-relation)
   (target-role . predicate-question)
   (migration . bounded-after-selected-core-signal)
   (note . "Same SID identity. Core4 result law may change only through explicit profile selection; historical Core1/Core2 behavior is not rewritten."))

  ((surface . equal?)
   (sid . 00100010)
   (authority . contracts/deep-structural-relation-contract.lisp)
   (current-role . predicate-question)
   (current-result . structural-relation)
   (target-role . predicate-question)
   (migration . after-eq-vertical)
   (note . "Question already asks equality; migrate result domain in its own bounded slice, preserving any separate deep-structure observer if still needed."))

  ((surface . symbol?)
   (sid . 00100011)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . after-equal)
   (note . "Predicate spelling asks membership; richer class-membership data may remain in a separately named classifier/observer API."))

  ((surface . string?)
   (sid . 00100100)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . after-equal)
   (note . "Do not delete classifier data mechanically; separate simple question from richer observation if both are needed."))

  ((surface . numeric-buffer?)
   (sid . 00100110)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . after-equal)
   (note . "Same bounded-migration rule as other class predicates."))

  ((surface . cond)
   (sid . 00000111)
   (authority . contracts/control-dispatch-contract.lisp)
   (current-role . control-consumer)
   (current-result . explicit-result-equality)
   (target-role . control-consumer)
   (migration . producer-laws-first)
   (note . "COND consumes exact producer results. Do not change its law merely to hide a producer migration."))

  ((surface . historical-two-part-cond)
   (sid . 00000111)
   (authority . contracts/control-dispatch-contract.lisp)
   (current-role . compatibility)
   (current-result . historical-truthiness)
   (target-role . compatibility)
   (migration . isolate-until-retired)
   (note . "Compatibility is not Core4 predicate-answer authority."))

  ((surface . core4-eq-answer-1258)
   (sid . 00000011)
   (authority . experiments/core4-eq-answer-1258.lisp)
   (current-role . test-only)
   (current-result . string-transport-baseline)
   (target-role . test-only)
   (migration . replay-after-runtime-profile-selection)
   (note . "Merged experiment is evidence, not a second eq? semantic identity and not final carrier authority.")))
