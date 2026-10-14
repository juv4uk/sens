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
      ((010 predicates) #d1:1)
      ((100 predicates) ; Structural equality is SENS-owned: neither Rust nor Python chooses words.
(0011 структура--рівні?
  (0010 (left right)
    (110
      ((010 left)
       (110
         ((010 right) (101 left right))
         (#d1:1 #d1:0)))
      ((010 right) #d1:0)
      ((структура--рівні? (100 left) (100 right))
       (структура--рівні? (011 left) (011 right)))
      (#d1:1 #d1:0))))

(структура--всі? (011 predicates)))
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
    (структура--ні? (narrate-list-exact-three? (001 (a b c d))))
    ; The full narrator's 2-item branch quotes D7 words is/a. That case
    ; is intentionally excluded until Text7-vs-Symbol identity is ratified.
    (структура--рівні? (narrate-fact (001 a)) (001 a))
    (структура--рівні? (narrate-fact (001 (a))) (001 (a)))
    (структура--рівні? (narrate-fact (001 (a b c d))) (001 (a b c d)))
    (структура--рівні? (narrate-fact (001 (a b c))) (001 (b a c)))
    (структура--рівні? (narrate-fact (001 ((a) b c))) (001 (b (a) c)))))
