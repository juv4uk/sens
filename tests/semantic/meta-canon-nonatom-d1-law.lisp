; Binary SENS owns the assertions. D3 EQ cannot compare a pair as an atom.
; A quoted source list is inert DATA, not a canonical function name.
; If a verdict is wrong, D3 CAR(QUOTE EMPTY) fails closed.

(110
  ((101 (my-canon-semantic-id (001 (car x))) (001 ())) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-semantic-id? (001 (car x)) 001) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

; Canon surfaces are projected to D3 explicitly: no historical W8 callability.

(110
  ((101 (my-canon-identity (001 car)) (001 car)) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-canon-identity (001 перше)) (001 car)) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-canon-identity (001 ādi)) (001 car)) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-lambda-name? (001 lambda)) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-definition-name? (001 def)) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (my-canon-name? (001 незнайоме)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))
