; #1046 — transitional executor metadata subordinate to Canon()/function table.
; Identity authority: lib/surface/semantic-registry.lisp
; This file cannot mint semantic identities or define language meaning.
; Every SID below must already exist in the canonical function table.
; Retirement: fold these mechanism descriptors into the unified function-table
; row model once #1046 completes.

(
  (schema function-table-mechanisms/1)
  (authority "lib/surface/semantic-registry.lisp")
  (lifecycle transitional)
  (retirement-issue 1046)
  (rows
    (00000000 evaluator empty-list-ground)
    (00000001 evaluator quote-form)
    (00000010 evaluator atom-primitive)
    (00000011 evaluator eq-primitive)
    (00000100 evaluator cons-primitive)
    (00000101 evaluator car-primitive)
    (00000110 evaluator cdr-primitive)
    (00000111 evaluator cond-form)
    (00001000 evaluator lambda-form)
    (00001001 evaluator define-form)
    (00001011 evaluator define-form)
    ; Existing SID + only. These rows admit executors; they do not define +.
    ; Evidence donors: #988/#1042; Datalog execution replay: #1052.
    (00001100 common-lisp bounded-exact-add)
    (00001100 prolog bounded-exact-add)
    (00001100 clips bounded-exact-add)
    (00001100 datalog bounded-exact-add)))
