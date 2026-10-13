; The actual LCA must be found for unequal lineage depths without numeric D24.
; D3:101 checks exact D1 answers from Lisp-owned structural equality.
(101
  (внутрішня-рівність-версій
    (world-common-ancestor
      (world-tell
        (world-tell (empty-world) (001 astronomy) (001 (planet earth)))
        (001 biology)
        (001 (living earth)))
      (world-tell (empty-world) (001 astronomy) (001 (planet earth))))
    (world-tell (empty-world) (001 astronomy) (001 (planet earth))))
  #d1:1)
