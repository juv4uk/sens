; PAIP FIND-IF-ANYWHERE: native SENS self-verdict, derived only from D3/D4.
; D10 coordinate 0011010011 remains research-only; no direct D10 opcode.
; Expected D1 vector: nested hit, miss, empty tree -> (1 0 0).
(list
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (list (list (quote яблуко) (list (quote слива))) (quote груша)))
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (list (list (quote яблуко)) (quote груша)))
  (дерево-має-збіг?
    (lambda (елемент) (equal? елемент (quote слива)))
    (quote ())))
