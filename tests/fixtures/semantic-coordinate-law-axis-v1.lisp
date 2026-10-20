; #834 — bounded semantic-coordinate law witness.
;
; This is evidence/projection data, not a second semantic registry.
; SID identity remains owned by lib/surface/semantic-registry.lisp.
; Mathematical result domains remain owned by #225 and their existing fixtures.
; Ukrainian projection only. Coordinates as decimal.

(визначити semantic-coordinate-law-axis-v1
  (як-є
    ((12
       (axis mathematical)
       (domain exact-rational-arithmetic)
       (witness exact-rational-sum)
       (evidence tests/fixtures/mathematical-result-v1.lisp))
     (4
       (axis equational-structure)
       (domain pair-construction)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (5
       (axis equational-structure)
       (domain pair-elimination)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (7
       (axis semantic-control)
       (domain non-mathematical-in-this-slice)
       (witness no-mathematical-law-claimed)
       (evidence contracts/control-dispatch-contract.lisp)))))

(визначити semantic-coordinate-law-row
  (функція (sid rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      ((тотожне? sid (перше (перше rows))) (перше rows))
      (так (semantic-coordinate-law-row sid (решта rows))))))

(визначити semantic-coordinate-law-for-sid
  (функція (sid)
    (semantic-coordinate-law-row sid semantic-coordinate-law-axis-v1)))
