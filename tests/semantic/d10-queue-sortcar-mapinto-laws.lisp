; D10 empty-queue/sortcar from core4; map-into/vector-list remain
; test-local research projections (no direct D10 mechanism admission).
; Eight real SENS D1 witnesses exercise resident definitions.
(0011 відобразити-у
  (0010 (fn dest src)
    (відобразити fn src)))
(0011 вектор->список
  (0010 (v) v))
(0011 список->вектор
  (0010 (xs) xs))
(list
  (черга-порожня? (як-є ()))
  (not? (черга-порожня? (list (quote a))))
  (equal? (сортувати-за-першим
            (list (list #d24:000000000000000000000010 (quote b))
                  (list #d24:000000000000000000000001 (quote a))))
          (list (list #d24:000000000000000000000001 (quote a))
                (list #d24:000000000000000000000010 (quote b))))
  (equal? (відобразити-у
            (0010 (x) x)
            (як-є ())
            (list (quote a) (quote b)))
          (list (quote a) (quote b)))
  (equal? (вектор->список (list (quote x)))
          (list (quote x)))
  (equal? (список->вектор (list (quote y)))
          (list (quote y)))
  (equal? (вектор->список (як-є ()))
          (як-є ()))
  (черга-порожня? (список->вектор (як-є ()))))
