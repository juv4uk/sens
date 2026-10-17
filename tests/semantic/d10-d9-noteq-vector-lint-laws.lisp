; SENS laws for Core4-derived D10/D9 projections: 8 exact D1:YES.
; VECTOR->LIST / LIST->VECTOR shims below are test-local list-carrier projections only.
(0011 вектор->список
  (0010 (v) v))
(0011 список->вектор
  (0010 (xs) xs))
(list
  (numeric-not-equal? #d24:000000000000000000000001
                  #d24:000000000000000000000010)
  (not? (числа-нерівні? #d24:000000000000000000000001
                        #d24:000000000000000000000001))
  (equal? (вектор->список (list (quote a) (quote b)))
          (list (quote a) (quote b)))
  (equal? (список->вектор (list (quote x)))
          (list (quote x)))
  (equal? (vector-slice (list (quote a) (quote b) (quote c))
                        #d24:000000000000000000000001
                        #d24:000000000000000000000011)
          (list (quote b) (quote c)))
  (equal? (multiple-value-list (list (quote v)))
          (list (quote v)))
  (equal? (lint-size (list (quote a) (quote b) (quote c)))
          #d24:000000000000000000000011)
  (equal? (вектор->список (quote ())) (quote ())))
