; #834 — bounded semantic-coordinate law witness.
;
; This is evidence/projection data, not a second semantic registry.
; SID identity remains owned by lib/surface/semantic-registry.lisp.
; Mathematical result domains remain owned by #225 and their existing fixtures.
;
; A row may say that no mathematical law is claimed for an identity. That is
; an important negative witness: semantic meaning is broader than mathematics.

(def semantic-coordinate-law-axis-v1
  (quote
    ((00001100
       (axis mathematical)
       (domain exact-rational-arithmetic)
       (witness exact-rational-sum)
       (evidence tests/fixtures/mathematical-result-v1.lisp))
     (00000011
       (axis relation-law)
       (domain identity-relation)
       (witness same-atom-identity)
       (evidence contracts/structural-observation-contract.lisp))
     (00000100
       (axis equational-structure)
       (domain pair-construction)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (00000101
       (axis equational-structure)
       (domain pair-elimination)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (00000111
       (axis semantic-control)
       (domain non-mathematical-in-this-slice)
       (witness no-mathematical-law-claimed)
       (evidence contracts/control-dispatch-contract.lisp)))))

(def semantic-coordinate-law-row
  (lambda (sid rows)
    (cond
      ((atom? rows) ())
      ((equal? sid (car (car rows))) (car rows))
      (t (semantic-coordinate-law-row sid (cdr rows))))))

(def semantic-coordinate-law-for-sid
  (lambda (sid)
    (semantic-coordinate-law-row sid semantic-coordinate-law-axis-v1)))
