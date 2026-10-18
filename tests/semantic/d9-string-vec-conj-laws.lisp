; D9 STRING/VEC projection laws exercise production Core4 closures.
; Character strings use the ratified persistent list-carrier projection.
; vec-conj is not evidence of a separate mutable vector representation.
(список
  (equal? (рядок-перший (список (як-є a) (як-є b))) (як-є a))
  (equal? (рядок-решта (список (як-є a) (як-є b))) (список (як-є b)))
  (equal? (рядок-додати (список (як-є a)) (список (як-є b)))
          (список (як-є a) (як-є b)))
  (рядок-містить? (як-є b) (список (як-є a) (як-є b)))
  (рядок-префікс? (список (як-є a)) (список (як-є a) (як-є b)))
  (хибне? (рядок-префікс? (список (як-є b)) (список (як-є a) (як-є b))))
  (equal? (рядок-зріз (список (як-є a) (як-є b) (як-є c))
                      #d24:000000000000000000000001
                      #d24:000000000000000000000011)
          (список (як-є b) (як-є c)))
  (equal? (вектор-додати (список (як-є a)) (як-є b))
          (список (як-є a) (як-є b))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити рядок-додати string-append)
(визначити рядок-містить? string-contains?)
(визначити рядок-перший string-first)
(визначити рядок-префікс? string-prefix?)
(визначити рядок-решта string-rest)
(визначити рядок-зріз string-slice)
(визначити вектор-додати vec-conj)
