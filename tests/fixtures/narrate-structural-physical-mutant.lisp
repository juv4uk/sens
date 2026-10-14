; SENS-owned structural sublaw: only D2/D3/D4 shapes, no D7 Symbol coercion.
; The production definitions below come ONLY from physical narrate.sens.
; Each input shape is a literal SENS QUOTE; expected D1 bits are computed here.
(0011 структура--ні?
  (0010 (p)
    (110
      (p #d1:0)
      (#d1:1 #d1:1))))

(0011 структура--всі?
  (0010 (predicates)
    (110
      ((010 predicates) #d1:0)
      ((100 predicates) (структура--всі? (011 predicates)))
      (#d1:1 #d1:0))))

(структура--всі?
  (1110
    (narrate-proper-list? (001 ()))
    (narrate-proper-list? (001 (a)))
    (narrate-proper-list? (001 (a b c)))
    (структура--ні? (narrate-proper-list? (001 (a . b))))
    (структура--ні? (narrate-proper-list? (001 a)))
    (narrate-list-exact-two? (001 (a b)))
    (структура--ні? (narrate-list-exact-two? (001 (a))))
    (структура--ні? (narrate-list-exact-two? (001 (a b c))))
    (narrate-list-exact-three? (001 (a b c)))
    (структура--ні? (narrate-list-exact-three? (001 (a b))))
    (структура--ні? (narrate-list-exact-three? (001 (a b c d))))))
