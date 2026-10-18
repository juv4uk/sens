; D10 empty-queue/sortcar from core4; map-into/vector-list remain
; test-local research projections (no direct D10 mechanism admission).
; Eight real SENS D1 witnesses exercise resident definitions.
(0011 вектор->список
  (0010 (v) v))
(0011 список->вектор
  (0010 (xs) xs))
(список
  (черга-порожня? (як-є ()))
  (хибне? (черга-порожня? (список (quote a))))
  (equal? (сортувати-за-першим
            (list (list #d24:000000000000000000000010 (quote b))
                  (list #d24:000000000000000000000001 (quote a))))
          (list (list #d24:000000000000000000000001 (quote a))
                (list #d24:000000000000000000000010 (quote b))))
  (equal? (відобразити-у
            (lambda (x) x)
            (як-є ())
            (список (quote a) (quote b)))
          (список (quote a) (quote b)))
  (equal? (вектор->список (список (quote x)))
          (список (quote x)))
  (equal? (список->вектор (список (quote y)))
          (список (quote y)))
  (equal? (вектор->список (як-є ()))
          (як-є ()))
  (черга-порожня? (список->вектор (як-є ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити відобразити-у map-into)
(визначити хибне? not?)
