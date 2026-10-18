; D8:01010111 NOTANY -> exact D1 PredicateBit (1 0 1).
; Positive: every element is a pair (ATOM returns D1:0).
; Negative: one atom witnesses ANY=true so NOTANY=false.
; Empty: NOTANY(ATOM, ()) = D1:1 (vacuous predicate).
(список
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список (список (quote пара-а)) (список (quote пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список (quote атом-а) (список (quote пара-б))))
  (жодне-не-задовольняє?
    (функція (х) (атом? х))
    (список)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
