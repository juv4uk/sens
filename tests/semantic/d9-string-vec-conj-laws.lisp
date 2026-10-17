; D9 STRING/VEC projection laws exercise production Core4 closures.
; Character strings use the ratified persistent list-carrier projection.
; vec-conj is not evidence of a separate mutable vector representation.
(list
  (equal? (string-first (list (quote a) (quote b))) (quote a))
  (equal? (string-rest (list (quote a) (quote b))) (list (quote b)))
  (equal? (string-append (list (quote a)) (list (quote b)))
          (list (quote a) (quote b)))
  (string-contains? (quote b) (list (quote a) (quote b)))
  (string-prefix? (list (quote a)) (list (quote a) (quote b)))
  (not? (string-prefix? (list (quote b)) (list (quote a) (quote b))))
  (equal? (string-slice (list (quote a) (quote b) (quote c))
                      #d24:000000000000000000000001
                      #d24:000000000000000000000011)
          (list (quote b) (quote c)))
  (equal? (vec-conj (list (quote a)) (quote b))
          (list (quote a) (quote b))))
