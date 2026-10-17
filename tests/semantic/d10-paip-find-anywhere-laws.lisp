; PAIP FIND-IF-ANYWHERE: exact D1 verdicts from the pinned source law.
; D10:0011010011 remains a research candidate; this source-level helper does not admit a D10 opcode.
; PAIP applies the predicate to atoms including (); the empty-list case therefore tests ATOM semantics.
; Expected D1 vector: nested hit, miss, NIL atom, false predicate, hit on the right subtree -> (1 0 1 0 1).
(list
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (list (list (quote яблуко) (list (quote слива))) (quote груша)))
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (list (list (quote яблуко)) (quote груша)))
  (дерево-має-збіг?
    (lambda (елемент) (атом? елемент))
    (quote ()))
  (дерево-має-збіг?
    (lambda (елемент) #d1:0)
    (quote (яблуко груша)))
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (list (quote яблуко) (list (quote груша) (quote слива)))))
