; Ratified D9 list-backed vector projections from live Core4 (no self-DEFINE).
; D9:101101101 VEC-EMPTY, 101010111 VEC-COUNT, 110000010 VEC-NTH.
; D1 vector expected (1 1 1 0 1 1); fourth tests wrong index (negative).
(список
  (equal? (вектор-порожній) (як-є ()))
  (equal? (вектор-кількість
            (список (як-є а) (як-є б) (як-є в)))
          #d24:000000000000000000000011)
  (equal? (vec-nth #d24:000000000000000000000001
            (список (як-є а) (як-є б) (як-є в)))
          (як-є б))
  (equal? (vec-nth #d24:000000000000000000000000
            (список (як-є а) (як-є б) (як-є в)))
          (як-є б))
  (equal? (vec-nth #d24:000000000000000000000010
            (список (як-є а) (як-є б) (як-є в)))
          (як-є в))
  (equal? (vec-count (vec-empty)) #d24:000000000000000000000000))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити вектор-кількість vec-count)
(визначити вектор-порожній vec-empty)
(визначити вектор-н-тий vec-nth)
