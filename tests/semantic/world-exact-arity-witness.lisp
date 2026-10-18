; SENS-owned witness for the actual Lisp predicate world?.
; All primitive operators retain exact identities: D3 EQ/QUOTE and D1 bits.
; world? is a local Lisp binding, not an admitted D10 callable identity; do not
; invent a D10 call head merely to force this fixture into the pure .bits reader.
;
; Each form is a self-verdict: EQ compares world?'s actual D1 result to the
; expected D1 bit. The host runner checks only that every form returns D1 YES.

(тотожне? (world? (як-є (world () () ()))) так)
(тотожне? (world? (як-є (world))) ні)
(тотожне? (world? (як-є (world parent))) ні)
(тотожне? (world? (як-є (world parent journal))) ні)
(тотожне? (world? (як-є (world parent journal metadata extra))) ні)
(тотожне? (world? (як-є (not-world parent journal metadata))) ні)
(тотожне? (world? (як-є ())) ні)

; Existing observable world behavior stays a SENS-owned assertion too.
(тотожне? (внутрішня-рівність-версій (empty-world) (як-є (world () () ()))) так)
(тотожне? (внутрішня-рівність-версій (world-parent (empty-world)) (як-є ())) так)
(тотожне? (внутрішня-рівність-версій (world-journal (empty-world)) (як-є ())) так)
(тотожне? (внутрішня-рівність-версій (world-metadata (empty-world)) (як-є ())) так)
(тотожне? (world-module-missing? (empty-world) (як-є unknown)) так)
(тотожне? (внутрішня-рівність-версій
      (world-remove-first (як-є x) (як-є (a x b)))
      (як-є (a b))) так)

; SENS verifies the actual aligned-ancestor law, not a Rust/Python truth table.
(тотожне?
  (внутрішня-рівність-версій
    (world-common-ancestor-aligned (empty-world) (empty-world))
    (empty-world))
  так)

; Two distinct children share their immutable parent.
(тотожне?
  (внутрішня-рівність-версій
    (world-common-ancestor-aligned
      (world-tell (empty-world) (як-є astronomy) (як-є (planet earth)))
      (world-tell (empty-world) (як-є physics) (як-є (mass earth))))
    (empty-world))
  так)

; Divergent roots must return the named negative result.
(тотожне?
  (world-common-ancestor-aligned
    (make-world (як-є ()) (як-є (alpha)) (як-є ()))
    (make-world (як-є ()) (як-є (beta)) (як-є ())))
  (як-є World-no-common-ancestor))

; The recognition function returns exactly D1:YES or D1:NO.
(тотожне? (world-no-common-ancestor? (як-є World-no-common-ancestor)) так)
(тотожне? (world-no-common-ancestor? (empty-world)) ні)
(тотожне? (world-no-common-ancestor? (як-є unrelated-atom)) ні)

; NIL must not be dereferenced as an immutable world.
(тотожне?
  (world-common-ancestor-aligned (як-є ()) (empty-world))
  (як-є World-no-common-ancestor))

; Cross-depth LCA: a grandchild and its direct parent share the parent.
(тотожне?
  (внутрішня-рівність-версій
    (world-common-ancestor
      (world-tell
        (world-tell (empty-world) (як-є astronomy) (як-є (planet earth)))
        (як-є biology)
        (як-є (living earth)))
      (world-tell (empty-world) (як-є astronomy) (як-є (planet earth))))
    (world-tell (empty-world) (як-є astronomy) (як-є (planet earth))))
  так)

; Symmetry: argument order cannot change the semantic common ancestor.
(тотожне?
  (внутрішня-рівність-версій
    (world-common-ancestor
      (world-tell (empty-world) (як-є astronomy) (як-є (planet earth)))
      (world-tell
        (world-tell (empty-world) (як-є astronomy) (як-є (planet earth)))
        (як-є biology)
        (як-є (living earth))))
    (world-tell (empty-world) (як-є astronomy) (як-є (planet earth))))
  так)

; Distinct self-rooted worlds have no shared parent.
(тотожне?
  (world-common-ancestor
    (make-world (як-є ()) (як-є (alpha)) (як-є ()))
    (make-world (як-є ()) (як-є (beta)) (як-є ())))
  (як-є World-no-common-ancestor))

; Empty non-world input must stop without invoking a parent selector.
(тотожне?
  (world-common-ancestor (як-є ()) (empty-world))
  (як-є World-no-common-ancestor))

; Українські D8-проєкції перевіряються фізичним SENS-виконанням World.
; D8:11101101 текст-у-символ; D8:11110100 значення-у-текст.
; Ні бітова ширина, ні T5M не надають нової семантики цих викликів.
(тотожне? (внутрішній-символ? (як-є зірка)) так)
(тотожне? (внутрішній-символ? (як-є (зірка))) ні)
(тотожне? (внутрішній-символ? (як-є ())) ні)
(тотожне? (текст-у-символ (значення-у-текст (як-є зірка))) (як-є зірка))
(текст? (knowledge-content-address (як-є (зірка))))
(текст? (world-content-address (empty-world)))
