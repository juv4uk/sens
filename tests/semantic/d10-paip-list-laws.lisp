; D10 PAIP research compositions: MKLIST, MAPPEND, one-level FLATTEN.
; Domain coordinates in lib/domains/d10.lisp; no D10 direct-call admission.
; Positive and falsifying D1 comparisons: expect (1 1 1 1 1 1 1 0 0 1).
(list
  (equal? (утворити-список (quote яблуко))
          (list (quote яблуко)))
  (equal? (утворити-список (list (quote яблуко) (quote груша)))
          (list (quote яблуко) (quote груша)))
  (null? (утворити-список (quote ())))
  (equal?
    (відобразити-й-додати
      (lambda (елемент) (list елемент (quote хвіст)))
      (list (quote яблуко) (quote груша)))
    (list (quote яблуко) (quote хвіст) (quote груша) (quote хвіст)))
  (null?
    (відобразити-й-додати
      (lambda (елемент) (list елемент)) (quote ())))
  (equal?
    (сплющити
      (list (list (quote яблуко) (quote груша))
            (quote слива) (list (quote вишня))))
    (list (quote яблуко) (quote груша) (quote слива) (quote вишня)))
  (equal?
    (сплющити
      (list (list (quote яблуко) (list (quote груша))) (quote слива)))
    (list (quote яблуко) (list (quote груша)) (quote слива)))
  (equal?
    (сплющити
      (list (list (quote яблуко) (list (quote груша))) (quote слива)))
    (list (quote яблуко) (quote груша) (quote слива)))
  (equal?
    (відобразити-й-додати
      (lambda (елемент) (list елемент (quote хвіст)))
      (list (quote яблуко) (quote груша)))
    (list (quote груша) (quote хвіст) (quote яблуко) (quote хвіст)))
  (null?
    (відобразити-й-додати
      (lambda (елемент) (quote ())) (list (quote яблуко))))
)
