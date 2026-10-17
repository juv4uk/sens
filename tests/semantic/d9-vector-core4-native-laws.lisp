; Ratified D9 list-backed vector projections from live Core4 (no self-DEFINE).
; D9:101101101 VEC-EMPTY, 101010111 VEC-COUNT, 110000010 VEC-NTH.
; D1 vector expected (1 1 1 0 1 1); fourth tests wrong index (negative).
(list
  (equal? (вектор-порожній) (quote ()))
  (equal? (вектор-кількість
            (list (quote а) (quote б) (quote в)))
          #d24:000000000000000000000011)
  (equal? (вектор-n-тий #d24:000000000000000000000001
            (list (quote а) (quote б) (quote в)))
          (quote б))
  (equal? (вектор-n-тий #d24:000000000000000000000000
            (list (quote а) (quote б) (quote в)))
          (quote б))
  (equal? (vec-nth #d24:000000000000000000000010
            (list (quote а) (quote б) (quote в)))
          (quote в))
  (equal? (vec-count (vec-empty)) #d24:000000000000000000000000))
