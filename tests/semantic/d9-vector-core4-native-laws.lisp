; Ratified D9 list-backed vector projections from live Core4 (no self-DEFINE).
; D9:101101101 VEC-EMPTY, 101010111 VEC-COUNT, 110000010 VEC-NTH.
; D1 vector expected (1 1 1 0 1 1); fourth tests wrong index (negative).
(список
  (equal? (вектор-порожній) (quote ()))
  (equal? (вектор-кількість
            (список (quote а) (quote б) (quote в)))
          #d24:000000000000000000000011)
  (equal? (vec-nth #d24:000000000000000000000001
            (список (quote а) (quote б) (quote в)))
          (quote б))
  (equal? (vec-nth #d24:000000000000000000000000
            (список (quote а) (quote б) (quote в)))
          (quote б))
  (equal? (vec-nth #d24:000000000000000000000010
            (список (quote а) (quote б) (quote в)))
          (quote в))
  (equal? (vec-count (vec-empty)) #d24:000000000000000000000000))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити вектор-кількість vec-count)
(визначити вектор-порожній vec-empty)
(визначити вектор-н-тий vec-nth)
