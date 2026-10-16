; D8:01010111 NOTANY -> exact D1 PredicateBit (1 0 1).
; Positive: every element is a pair (ATOM returns D1:0).
; Negative: one atom witnesses ANY=true so NOTANY=false.
; Empty: NOTANY(ATOM, ()) = D1:1 (vacuous predicate).
(list
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (list (list (quote пара-а)) (list (quote пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (list (quote атом-а) (list (quote пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (list)))
