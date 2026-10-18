; D8:01010111 NOTANY -> exact D1 PredicateBit (1 0 1).
; Positive: every element is a pair (ATOM returns D1:0).
; Negative: one atom witnesses ANY=true so NOTANY=false.
; Empty: NOTANY(ATOM, ()) = D1:1 (vacuous predicate).
(список
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список (список (як-є пара-а)) (список (як-є пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список (як-є атом-а) (список (як-є пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список)))
