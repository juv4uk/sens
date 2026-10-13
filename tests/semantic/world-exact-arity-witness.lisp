; SENS-owned witness for the actual Lisp predicate world?.
; Primitive operators retain exact identities: D3 EQ/QUOTE and D1 values.
; world? is a local Lisp binding, not a ratified callable D10 identity.
;
; Every row compares the real result with a D1 bit inside SENS. The host only
; accepts the final exact D1 YES; it does not hold this table of expectations.

(101 (world? (001 (world () () ()))) 1)
(101 (world? (001 (world))) 0)
(101 (world? (001 (world parent))) 0)
(101 (world? (001 (world parent journal))) 0)
(101 (world? (001 (world parent journal metadata extra))) 0)
(101 (world? (001 (not-world parent journal metadata))) 0)
(101 (world? (001 ())) 0)
(101 (внутрішня-рівність-версій (empty-world) (001 (world () () ()))) 1)
(101 (внутрішня-рівність-версій (world-parent (empty-world)) (001 ())) 1)
(101 (внутрішня-рівність-версій (world-journal (empty-world)) (001 ())) 1)
(101 (внутрішня-рівність-версій (world-metadata (empty-world)) (001 ())) 1)
(101 (world-module-missing? (empty-world) (001 unknown)) 1)
(101 (внутрішня-рівність-версій
      (world-remove-first (001 x) (001 (a x b)))
      (001 (a b))) 1)
