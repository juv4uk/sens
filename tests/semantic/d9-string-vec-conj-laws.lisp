; D9 STRING/VEC projection laws exercise production Core4 closures.
; Character strings use the ratified persistent list-carrier projection.
; vec-conj is not evidence of a separate mutable vector representation.
(список
  (equal? (string-first (список (як-є a) (як-є b))) (як-є a))
  (equal? (string-rest (список (як-є a) (як-є b))) (список (як-є b)))
  (equal? (string-append (список (як-є a)) (список (як-є b)))
          (список (як-є a) (як-є b)))
  (string-contains? (як-є b) (список (як-є a) (як-є b)))
  (string-prefix? (список (як-є a)) (список (як-є a) (як-є b)))
  (хибне? (string-prefix? (список (як-є b)) (список (як-є a) (як-є b))))
  (equal? (string-slice (список (як-є a) (як-є b) (як-є c))
                      #d24:000000000000000000000001
                      #d24:000000000000000000000011)
          (список (як-є b) (як-є c)))
  (equal? (vec-conj (список (як-є a)) (як-є b))
          (список (як-є a) (як-є b))))
