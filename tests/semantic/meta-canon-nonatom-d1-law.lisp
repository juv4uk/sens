; Binary SENS owns the assertions. D3 EQ cannot compare a pair as an atom.
; A quoted source list is inert DATA, not a canonical function name.
; If a verdict is wrong, D3 CAR(QUOTE EMPTY) fails closed.

(110
  ((101 (my-canon-semantic-id (001 (car x))) (001 ())) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-semantic-id? (001 (car x)) 001) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))
