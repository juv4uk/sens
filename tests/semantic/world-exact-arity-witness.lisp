; SENS-owned witness for the actual Lisp predicate world?.
; All primitive operators retain exact identities: D3 EQ/QUOTE and D1 bits.
; world? is a local Lisp binding, not an admitted D10 callable identity; do not
; invent a D10 call head merely to force this fixture into the pure .bits reader.
;
; Each form is a self-verdict: EQ compares world?'s actual D1 result to the
; expected D1 bit. The host runner checks only that every form returns D1 YES.

(101 (world? (001 (world () () ()))) 1)
(101 (world? (001 (world))) 0)
(101 (world? (001 (world parent))) 0)
(101 (world? (001 (world parent journal))) 0)
(101 (world? (001 (world parent journal metadata extra))) 0)
(101 (world? (001 (not-world parent journal metadata))) 0)
(101 (world? (001 ())) 0)

; Existing observable world behavior stays a SENS-owned assertion too.
(101 (внутрішня-рівність-версій (empty-world) (001 (world () () ()))) 1)
(101 (внутрішня-рівність-версій (world-parent (empty-world)) (001 ())) 1)
(101 (внутрішня-рівність-версій (world-journal (empty-world)) (001 ())) 1)
(101 (внутрішня-рівність-версій (world-metadata (empty-world)) (001 ())) 1)
(101 (world-module-missing? (empty-world) (001 unknown)) 1)
(101 (внутрішня-рівність-версій
      (world-remove-first (001 x) (001 (a x b)))
      (001 (a b))) 1)

; SENS verifies the actual aligned-ancestor law, not a Rust/Python truth table.
(101
  (внутрішня-рівність-версій
    (world-common-ancestor-aligned (empty-world) (empty-world))
    (empty-world))
  1)

; Two distinct children share their immutable parent.
(101
  (внутрішня-рівність-версій
    (world-common-ancestor-aligned
      (world-tell (empty-world) (001 astronomy) (001 (planet earth)))
      (world-tell (empty-world) (001 physics) (001 (mass earth))))
    (empty-world))
  1)

; Divergent roots must return the named negative result.
(101
  (world-common-ancestor-aligned
    (make-world (001 ()) (001 (alpha)) (001 ()))
    (make-world (001 ()) (001 (beta)) (001 ())))
  (001 World-no-common-ancestor))

; The recognition function returns exactly D1:YES or D1:NO.
(101 (world-no-common-ancestor? (001 World-no-common-ancestor)) 1)
(101 (world-no-common-ancestor? (empty-world)) 0)
(101 (world-no-common-ancestor? (001 unrelated-atom)) 0)

; NIL must not be dereferenced as an immutable world.
(101
  (world-common-ancestor-aligned (001 ()) (empty-world))
  (001 World-no-common-ancestor))
